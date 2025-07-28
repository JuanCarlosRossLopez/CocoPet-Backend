"""
Script para probar específicamente el archivo bongopet3_limpio.xlsx
"""

import requests
import json
import time

# Configuración
API_BASE_URL = 'http://localhost:5000/api'
FILENAME = 'bongopet3_limpio.xlsx'

def wait_for_server():
    """Esperar a que el servidor esté listo"""
    print("🔄 Esperando a que el servidor esté listo...")
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get(f'{API_BASE_URL}/health', timeout=5)
            if response.status_code == 200:
                print("✅ Servidor listo!")
                return True
        except requests.RequestException:
            pass
        
        print(f"   Intento {attempt + 1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ No se pudo conectar al servidor")
    return False

def test_health():
    """Probar endpoint de health check"""
    print("\n🔍 Probando Health Check...")
    try:
        response = requests.get(f'{API_BASE_URL}/health')
        if response.status_code == 200:
            data = response.json()
            print("✅ API funcionando correctamente")
            print(f"   Status: {data['status']}")
            print(f"   Versión: {data['version']}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_files_list():
    """Verificar que el archivo esté en la lista"""
    print(f"\n🔍 Verificando que {FILENAME} esté disponible...")
    try:
        response = requests.get(f'{API_BASE_URL}/files')
        if response.status_code == 200:
            data = response.json()
            files = [f['filename'] for f in data['files']]
            if FILENAME in files:
                print(f"✅ Archivo {FILENAME} encontrado en el servidor")
                file_info = next(f for f in data['files'] if f['filename'] == FILENAME)
                print(f"   Tamaño: {file_info['size']} bytes")
                return True
            else:
                print(f"❌ Archivo {FILENAME} NO encontrado")
                print(f"   Archivos disponibles: {files}")
                return False
        else:
            print(f"❌ Error al listar archivos: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_data_processing():
    """Probar procesamiento de datos del archivo"""
    print(f"\n🔍 Probando procesamiento de datos de {FILENAME}...")
    try:
        response = requests.get(f'{API_BASE_URL}/data/{FILENAME}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos procesados correctamente")
            
            stats = data['statistics']
            print(f"   📊 Estadísticas:")
            print(f"      - Total de registros: {stats['total_records']}")
            print(f"      - Productos únicos: {stats['unique_products']}")
            print(f"      - Cantidad total vendida: {stats['total_quantity']}")
            print(f"      - Clusters encontrados: {stats['clusters_found']}")
            print(f"      - Centro geográfico: ({stats['center']['latitud']:.4f}, {stats['center']['longitud']:.4f})")
            
            # Mostrar algunos registros de ejemplo
            if data['data'] and len(data['data']) > 0:
                print(f"   📋 Primeros 3 registros:")
                for i, record in enumerate(data['data'][:3]):
                    print(f"      {i+1}. {record['producto']}: {record['cantidad']} unidades")
                    print(f"         Ubicación: ({record['latitud']:.4f}, {record['longitud']:.4f})")
                    print(f"         Cluster: {record['cluster']}")
            
            return True
        else:
            print(f"❌ Error al procesar datos: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('message', 'Error desconocido')}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_map_generation():
    """Probar generación de mapa"""
    print(f"\n🔍 Probando generación de mapa para {FILENAME}...")
    try:
        response = requests.post(f'{API_BASE_URL}/map/{FILENAME}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Mapa generado correctamente")
            print(f"   📍 URL del mapa: {data['map_url']}")
            print(f"   📁 Archivo generado: {data['map_filename']}")
            
            # Verificar que el mapa sea accesible
            map_response = requests.get(f"http://localhost:5000{data['map_url']}")
            if map_response.status_code == 200:
                print("   ✅ Mapa accesible desde la URL")
            else:
                print("   ⚠️ Mapa generado pero no accesible desde la URL")
            
            return True
        else:
            print(f"❌ Error al generar mapa: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('message', 'Error desconocido')}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_analytics():
    """Probar análisis de datos"""
    print(f"\n🔍 Probando análisis de datos para {FILENAME}...")
    try:
        response = requests.get(f'{API_BASE_URL}/analytics/{FILENAME}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Análisis completado correctamente")
            
            analytics = data['analytics']
            print(f"   📈 Resumen general:")
            print(f"      - Ventas totales: {analytics['total_sales']}")
            print(f"      - Promedio por venta: {analytics['average_sale']:.2f}")
            print(f"      - Centro geográfico: ({analytics['geographic_center']['latitud']:.4f}, {analytics['geographic_center']['longitud']:.4f})")
            
            print(f"   🏷️ Análisis por producto:")
            for i, product in enumerate(analytics['products'][:5]):  # Mostrar top 5
                print(f"      {i+1}. {product['producto']}:")
                print(f"         - Total vendido: {product['total_cantidad']}")
                print(f"         - Número de ventas: {product['numero_ventas']}")
                print(f"         - Promedio por venta: {product['promedio_cantidad']:.2f}")
                print(f"         - Centro: ({product['centro_geografico']['latitud']:.4f}, {product['centro_geografico']['longitud']:.4f})")
            
            if len(analytics['products']) > 5:
                print(f"      ... y {len(analytics['products']) - 5} productos más")
            
            return True
        else:
            print(f"❌ Error al obtener análisis: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('message', 'Error desconocido')}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas para bongopet3_limpio.xlsx")
    print("=" * 60)
    
    # Esperar a que el servidor esté listo
    if not wait_for_server():
        print("\n❌ No se puede continuar sin el servidor")
        return
    
    # Ejecutar todas las pruebas
    tests = [
        ("Health Check", test_health),
        ("Lista de Archivos", test_files_list),
        ("Procesamiento de Datos", test_data_processing),
        ("Generación de Mapa", test_map_generation),
        ("Análisis de Datos", test_analytics)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
        
        if not success:
            print(f"\n⚠️ {test_name} falló. ¿Continuar con las siguientes pruebas? (s/n)")
            # Para automatización, continuamos automáticamente
            print("   Continuando automáticamente...")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📋 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡Todas las pruebas pasaron! Tu API está funcionando perfectamente.")
        print("\n🌐 Puedes acceder a:")
        print(f"   - API Info: http://localhost:5000/api")
        print(f"   - Datos procesados: http://localhost:5000/api/data/{FILENAME}")
        print(f"   - Interfaz web: http://localhost:5000/mapa-ventas")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print(f"\n💡 Para generar un mapa, puedes hacer POST a:")
    print(f"   http://localhost:5000/api/map/{FILENAME}")

if __name__ == "__main__":
    main()
