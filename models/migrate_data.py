# migrate_data.py - Migrar datos del Excel a Supabase
import pandas as pd
import numpy as np
from supabase import create_client, Client
from datetime import datetime, timedelta
import uuid
import logging

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = "https://uzobkyyfdcnzpsyqpwix.supabase.co"  # Reemplazar
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6b2JreXlmZGNuenBzeXFwd2l4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NzY0MTUsImV4cCI6MjA2OTI1MjQxNX0.BqQHq7lSIWkwaczL_s3cWiyzdEOTle03wrYcR4N9QFQ"  # Reemplazar
 # Reemplazar con tu clave real

def extract_brand(producto):
    """Extraer marca del producto"""
    producto = str(producto).lower()
    if 'nupec' in producto:
        return 'Nupec'
    elif 'nexgard' in producto:
        return 'Nexgard'
    elif 'royal canin' in producto:
        return 'Royal Canin'
    elif 'hills' in producto:
        return 'Hills'
    elif 'purina' in producto:
        return 'Purina'
    elif 'bravecto' in producto:
        return 'Bravecto'
    elif 'frontline' in producto:
        return 'Frontline'
    else:
        return 'Otras'

def migrate_excel_to_supabase():
    """Migrar datos del Excel a Supabase"""
    try:
        # Conectar a Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Conexión a Supabase establecida")
        
        # Leer archivo Excel
        try:
            df = pd.read_excel('bongopet3_limpio.xlsx')
            logger.info(f"✅ Excel cargado: {len(df)} registros")
        except FileNotFoundError:
            logger.error("❌ Archivo bongopet3_limpio.xlsx no encontrado")
            return
        
        # Limpiar datos
        df = df.dropna(subset=['latitud', 'longitud', 'precio', 'cantidad'])
        logger.info(f"✅ Datos limpiados: {len(df)} registros válidos")
        
        # Verificar si ya hay datos
        existing_data = supabase.table('ventas').select('id').limit(1).execute()
        if existing_data.data:
            logger.info("⚠️ Ya hay datos en la tabla ventas")
            response = input("¿Deseas eliminar los datos existentes y recargar? (y/n): ")
            if response.lower() == 'y':
                # Eliminar datos existentes
                supabase.table('ventas').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
                logger.info("🗑️ Datos existentes eliminados")
            else:
                logger.info("📊 Manteniendo datos existentes")
                return
        
        # Preparar datos para inserción
        ventas_data = []
        batch_size = 100
        
        for index, row in df.iterrows():
            # Generar ID único
            venta_id = str(uuid.uuid4())
            
            # Procesar fecha
            try:
                if pd.notna(row['fecha']):
                    fecha = pd.to_datetime(row['fecha']).date()
                else:
                    fecha = datetime.now().date()
            except:
                fecha = datetime.now().date()
            
            # Procesar hora
            hora = str(row.get('hora', '12:00 PM'))
            
            # Crear registro
            venta = {
                'id': venta_id,
                'id_venta': f"VTA{7000 + index}",
                'fecha': fecha.isoformat(),
                'hora': hora,
                'latitud': float(row['latitud']),
                'longitud': float(row['longitud']),
                'producto': str(row['producto']),
                'categoria': str(row['categoria']),
                'cantidad': float(row['cantidad']),
                'precio': float(row['precio']),
                'marca': extract_brand(row['producto']),
                'cluster_asignado': None,  # Se calculará después
                'proveedor_id': None,  # Se asignará después
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            ventas_data.append(venta)
        
        # Insertar datos en lotes
        total_inserted = 0
        for i in range(0, len(ventas_data), batch_size):
            batch = ventas_data[i:i + batch_size]
            
            try:
                response = supabase.table('ventas').insert(batch).execute()
                total_inserted += len(batch)
                logger.info(f"📤 Insertados {total_inserted}/{len(ventas_data)} registros")
            except Exception as e:
                logger.error(f"❌ Error insertando lote {i//batch_size + 1}: {e}")
                continue
        
        logger.info(f"✅ Migración completada: {total_inserted} registros insertados")
        
        # Verificar datos insertados
        count_response = supabase.table('ventas').select('id', count='exact').execute()
        logger.info(f"📊 Total de ventas en BD: {count_response.count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        return False

def create_sample_data():
    """Crear datos de ejemplo si no hay Excel"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        logger.info("🔧 Creando datos de ejemplo...")
        
        # Datos de ejemplo
        sample_data = []
        
        productos = [
            {'nombre': 'Nupec Adulto Razas Medianas/Grandes 20kg', 'categoria': 'Alimento', 'precio': 1800, 'cantidad': 20},
            {'nombre': 'Nexgard Spectra 7.6-15kg', 'categoria': 'Medicamento', 'precio': 350, 'cantidad': 1},
            {'nombre': 'Nupec Weight Control 15kg', 'categoria': 'Alimento', 'precio': 1940, 'cantidad': 15},
            {'nombre': 'Royal Canin Mini Adult 7.5kg', 'categoria': 'Alimento', 'precio': 650, 'cantidad': 7.5},
            {'nombre': 'Bravecto 20-40kg', 'categoria': 'Medicamento', 'precio': 850, 'cantidad': 1},
        ]
        
        # Coordenadas de Cancún
        cancun_coords = [
            (21.1619, -86.8515),  # Centro
            (21.1702, -86.8451),  # Zona Norte
            (21.1539, -86.8862),  # Zona Sur
            (21.1936, -86.8863),  # Zona Este
            (21.1454, -86.8272),  # Zona Oeste
        ]
        
        # Generar 50 registros de ejemplo
        for i in range(50):
            producto = productos[i % len(productos)]
            coords = cancun_coords[i % len(cancun_coords)]
            
            # Variar un poco las coordenadas
            lat = coords[0] + np.random.uniform(-0.01, 0.01)
            lng = coords[1] + np.random.uniform(-0.01, 0.01)
            
            # Fecha aleatoria en los últimos 30 días
            fecha = datetime.now() - timedelta(days=np.random.randint(0, 30))
            
            venta = {
                'id': str(uuid.uuid4()),
                'id_venta': f"VTA{8000 + i}",
                'fecha': fecha.date().isoformat(),
                'hora': f"{np.random.randint(8, 20)}:{np.random.randint(0, 59):02d}",
                'latitud': lat,
                'longitud': lng,
                'producto': producto['nombre'],
                'categoria': producto['categoria'],
                'cantidad': producto['cantidad'],
                'precio': producto['precio'],
                'marca': extract_brand(producto['nombre']),
                'cluster_asignado': i % 8,  # 8 clusters
                'proveedor_id': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            sample_data.append(venta)
        
        # Insertar datos de ejemplo
        response = supabase.table('ventas').insert(sample_data).execute()
        
        if response.data:
            logger.info(f"✅ {len(sample_data)} registros de ejemplo creados")
            return True
        else:
            logger.error("❌ Error creando datos de ejemplo")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error creando datos de ejemplo: {e}")
        return False

if __name__ == "__main__":
    print("🐕 BongoPet - Migración de Datos")
    print("=" * 40)
    
    # Verificar configuración
    if SUPABASE_KEY == "tu-anon-key":
        print("❌ ERROR: Configura tu SUPABASE_KEY en el script")
        exit(1)
    
    # Intentar migrar desde Excel
    if migrate_excel_to_supabase():
        print("✅ Datos migrados desde Excel exitosamente")
    else:
        print("⚠️ No se pudo migrar desde Excel, creando datos de ejemplo...")
        if create_sample_data():
            print("✅ Datos de ejemplo creados")
        else:
            print("❌ Error creando datos")
    
    print("\n💡 Ahora puedes probar:")
    print("   - http://localhost:5000/api/analytics/summary")
    print("   - Tu dashboard React debería mostrar datos")