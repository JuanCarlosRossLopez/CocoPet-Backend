# train_models.py - Script completo para entrenar y configurar BongoPet
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from ml_models import BongoPetMLModels
from supabase import create_client, Client

# Configuración
EXCEL_FILE = 'bongopet3_limpio.xlsx'
MODELS_DIR = 'models'
SUPABASE_URL = "https://uzobkyyfdcnzpsyqpwix.supabase.co"  # Reemplazar
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV6b2JreXlmZGNuenBzeXFwd2l4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NzY0MTUsImV4cCI6MjA2OTI1MjQxNX0.BqQHq7lSIWkwaczL_s3cWiyzdEOTle03wrYcR4N9QFQ"  # Reemplazar

def setup_directories():
    """Crear directorios necesarios"""
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    print("✅ Directorios creados")

def load_and_prepare_data():
    """Cargar y preparar datos del Excel"""
    print("📁 Cargando datos del Excel...")
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"✅ Datos cargados: {len(df)} registros")
        
        # Validar columnas requeridas
        required_columns = ['latitud', 'longitud', 'producto', 'categoria', 'cantidad', 'precio', 'fecha']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Columnas faltantes: {missing_columns}")
        
        # Limpiar datos
        df = df.dropna(subset=['latitud', 'longitud', 'precio', 'cantidad'])
        print(f"✅ Datos limpiados: {len(df)} registros válidos")
        
        return df
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        return None

def train_machine_learning_models(df):
    """Entrenar todos los modelos de ML"""
    print("\n🤖 Entrenando modelos de Machine Learning...")
    
    # Inicializar modelo
    ml_model = BongoPetMLModels()
    
    # 1. Entrenar clustering geográfico
    print("🎯 Entrenando modelo K-means para clustering...")
    df_with_clusters, cluster_analysis = ml_model.train_clustering_model(df, n_clusters=8)
    
    # 2. Entrenar modelo de predicción de ventas
    print("📈 Entrenando Random Forest para predicción de ventas...")
    feature_importance = ml_model.train_sales_prediction_model(df_with_clusters)
    
    # 3. Generar predicciones por zona
    print("🗺️ Generando predicciones por zona...")
    zone_predictions = ml_model.get_zone_predictions(df_with_clusters, cluster_analysis)
    
    # 4. Guardar modelos
    print("💾 Guardando modelos entrenados...")
    ml_model.save_models(MODELS_DIR + '/')
    
    # 5. Guardar análisis en JSON
    results = {
        'cluster_analysis': cluster_analysis,
        'feature_importance': feature_importance,
        'zone_predictions': zone_predictions,
        'training_date': datetime.now().isoformat(),
        'total_records': len(df),
        'model_performance': {
            'clusters': len(cluster_analysis),
            'zones_predicted': len(zone_predictions)
        }
    }
    
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print("✅ Modelos entrenados y guardados exitosamente")
    return ml_model, results

def upload_data_to_supabase(df, results):
    """Subir datos a Supabase"""
    print("\n☁️ Subiendo datos a Supabase...")
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Preparar datos para subida
        ventas_data = []
        for _, row in df.iterrows():
            venta = {
                'id_venta': f"VTA{row.name + 7000}",  # Generar ID único
                'fecha': row['fecha'].strftime('%Y-%m-%d') if pd.notna(row['fecha']) else None,
                'hora': row.get('hora', '12:00 PM'),
                'latitud': float(row['latitud']),
                'longitud': float(row['longitud']),
                'producto': str(row['producto']),
                'categoria': str(row['categoria']),
                'cantidad': float(row['cantidad']),
                'precio': float(row['precio']),
                'marca': extract_brand(row['producto']),
                'cluster_asignado': int(row.get('cluster', -1)) if pd.notna(row.get('cluster', -1)) else None
            }
            ventas_data.append(venta)
        
        # Subir en lotes
        batch_size = 100
        total_uploaded = 0
        
        for i in range(0, len(ventas_data), batch_size):
            batch = ventas_data[i:i + batch_size]
            try:
                response = supabase.table('ventas').insert(batch).execute()
                total_uploaded += len(batch)
                print(f"📤 Subidos {total_uploaded}/{len(ventas_data)} registros")
            except Exception as e:
                print(f"⚠️ Error en lote {i//batch_size + 1}: {e}")
                continue
        
        # Subir información de zonas
        zonas_data = []
        for cluster_id, info in results['cluster_analysis'].items():
            zona = {
                'cluster_id': int(cluster_id),
                'nombre_zona': f"Zona {cluster_id}",
                'latitud_centro': float(info['coordenadas_centro']['lat']),
                'longitud_centro': float(info['coordenadas_centro']['lng']),
                'categoria_dominante': str(info['categoria_dominante']),
                'marca_dominante': str(info['marca_dominante']),
                'total_ventas': int(info['total_ventas']),
                'ingresos_totales': float(info['ingresos_totales']),
                'precio_promedio': float(info['precio_promedio'])
            }
            zonas_data.append(zona)
        
        response = supabase.table('zonas_geograficas').insert(zonas_data).execute()
        print(f"✅ Subidas {len(zonas_data)} zonas geográficas")
        
        print("✅ Datos subidos a Supabase exitosamente")
        
    except Exception as e:
        print(f"❌ Error subiendo a Supabase: {e}")
        print("💡 Verifica tu configuración de Supabase en el script")

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

def generate_reports(results):
    """Generar reportes de análisis"""
    print("\n📊 Generando reportes...")
    
    # Reporte de clusters
    cluster_report = []
    for cluster_id, info in results['cluster_analysis'].items():
        cluster_report.append({
            'Zona': f"Zona {cluster_id}",
            'Ventas': info['total_ventas'],
            'Ingresos': f"${info['ingresos_totales']:,.2f}",
            'Categoría Dominante': info['categoria_dominante'],
            'Marca Popular': info['marca_dominante'],
            'Precio Promedio': f"${info['precio_promedio']:.2f}",
            'Día Popular': info.get('dia_semana_popular', 'N/A')
        })
    
    cluster_df = pd.DataFrame(cluster_report)
    cluster_df.to_csv('reporte_zonas.csv', index=False, encoding='utf-8')
    print("✅ Reporte de zonas guardado: reporte_zonas.csv")
    
    # Reporte de importancia de características
    importance_report = []
    for model_type, features in results['feature_importance'].items():
        for feature, importance in features.items():
            importance_report.append({
                'Modelo': model_type.capitalize(),
                'Característica': feature,
                'Importancia': f"{importance:.4f}"
            })
    
    importance_df = pd.DataFrame(importance_report)
    importance_df.to_csv('reporte_importancia_caracteristicas.csv', index=False, encoding='utf-8')
    print("✅ Reporte de características guardado: reporte_importancia_caracteristicas.csv")

def create_requirements_file():
    """Crear archivo requirements.txt"""
    requirements = """
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
flask==2.3.2
flask-cors==4.0.0
flask-jwt-extended==4.5.2
supabase==1.0.3
openpyxl==3.1.2
joblib==1.3.1
werkzeug==2.3.6
python-dotenv==1.0.0
""".strip()
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ Archivo requirements.txt creado")

def create_config_files():
    """Crear archivos de configuración"""
    
    # .env file
    env_content = """
# Configuración de la aplicación BongoPet
FLASK_APP=app.py
FLASK_ENV=development
JWT_SECRET_KEY=tu-clave-secreta-jwt-muy-segura
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
MODELS_DIR=models
"""
    
    with open('.env', 'w') as f:
        f.write(env_content.strip())
    print("✅ Archivo .env creado")
    
    # Docker Compose (opcional)
    docker_compose = """
version: '3.8'
services:
  bongopet-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - bongopet-api
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose.strip())
    print("✅ Archivo docker-compose.yml creado")

def main():
    """Función principal de entrenamiento"""
    print("🚀 Iniciando entrenamiento completo de BongoPet ML")
    print("=" * 50)
    
    # 1. Configurar directorios
    setup_directories()
    
    # 2. Cargar datos
    df = load_and_prepare_data()
    if df is None:
        print("❌ No se pudieron cargar los datos. Abortando.")
        return
    
    # 3. Entrenar modelos
    ml_model, results = train_machine_learning_models(df)
    
    # 4. Subir datos a Supabase (comentar si no tienes configurado)
    # upload_data_to_supabase(df, results)
    
    # 5. Generar reportes
    generate_reports(results)
    
    # 6. Crear archivos de configuración
    create_requirements_file()
    create_config_files()
    
    # 7. Resumen final
    print("\n" + "=" * 50)
    print("🎉 ENTRENAMIENTO COMPLETADO")
    print("=" * 50)
    print(f"📊 Total de registros procesados: {len(df):,}")
    print(f"🎯 Zonas identificadas: {len(results['cluster_analysis'])}")
    print(f"📈 Modelos entrenados: K-means + Random Forest")
    print(f"💾 Modelos guardados en: {MODELS_DIR}/")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Instalar dependencias: pip install -r requirements.txt")
    print("2. Configurar Supabase en .env")
    print("3. Ejecutar API: python app.py")
    print("4. Desplegar frontend React")
    print("\n🔗 ARCHIVOS GENERADOS:")
    print("- models/ (modelos ML)")
    print("- analysis_results.json")
    print("- reporte_zonas.csv")
    print("- reporte_importancia_caracteristicas.csv")
    print("- requirements.txt")
    print("- .env")
    print("- docker-compose.yml")

if __name__ == "__main__":
    main()