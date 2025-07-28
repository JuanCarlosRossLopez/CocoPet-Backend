"""
Script de ejemplo para probar la API REST de CocoPet Backend
Ejecutar: python test_api.py
"""

import requests
import json
import os

# Configuración
API_BASE_URL = 'http://localhost:5000/api'
TEST_FILE_PATH = 'test_data.xlsx'  # Cambia por la ruta de tu archivo Excel

def test_health():
    """Probar endpoint de health check"""
    print("🔍 Probando Health Check...")
    try:
        response = requests.get(f'{API_BASE_URL}/health')
        if response.status_code == 200:
            print("✅ API funcionando correctamente")
            print(f"Respuesta: {response.json()}")
        else:
            print(f"❌ Error en health check: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def test_api_info():
    """Probar endpoint de información de la API"""
    print("🔍 Probando información de la API...")
    try:
        response = requests.get(f'{API_BASE_URL}')
        if response.status_code == 200:
            print("✅ Información obtenida correctamente")
            data = response.json()
            print(f"API: {data['message']}")
            print(f"Versión: {data['version']}")
            print("Endpoints disponibles:")
            for endpoint, url in data['endpoints'].items():
                print(f"  - {endpoint}: {url}")
        else:
            print(f"❌ Error al obtener información: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def test_upload_file():
    """Probar subida de archivo"""
    print("🔍 Probando subida de archivo...")
    
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Archivo de prueba no encontrado: {TEST_FILE_PATH}")
        print("💡 Crea un archivo Excel con columnas: latitud, longitud, producto, cantidad")
        return None
    
    try:
        with open(TEST_FILE_PATH, 'rb') as file:
            files = {'file': file}
            response = requests.post(f'{API_BASE_URL}/upload', files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("✅ Archivo subido correctamente")
            print(f"Archivo: {data['filename']}")
            print(f"Registros: {data['records_count']}")
            return data['filename']
        else:
            print(f"❌ Error al subir archivo: {response.status_code}")
            print(f"Respuesta: {response.json()}")
            return None
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {TEST_FILE_PATH}")
        return None
    print("-" * 50)

def test_list_files():
    """Probar listado de archivos"""
    print("🔍 Probando listado de archivos...")
    try:
        response = requests.get(f'{API_BASE_URL}/files')
        if response.status_code == 200:
            data = response.json()
            print("✅ Archivos listados correctamente")
            if data['files']:
                print("Archivos disponibles:")
                for file_info in data['files']:
                    print(f"  - {file_info['filename']} ({file_info['size']} bytes)")
            else:
                print("No hay archivos disponibles")
        else:
            print(f"❌ Error al listar archivos: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def test_get_data(filename):
    """Probar obtención de datos procesados"""
    if not filename:
        print("⏭️ Saltando prueba de datos (no hay archivo)")
        return
    
    print(f"🔍 Probando obtención de datos para: {filename}")
    try:
        response = requests.get(f'{API_BASE_URL}/data/{filename}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos obtenidos correctamente")
            stats = data['statistics']
            print(f"Total de registros: {stats['total_records']}")
            print(f"Productos únicos: {stats['unique_products']}")
            print(f"Cantidad total: {stats['total_quantity']}")
            print(f"Clusters encontrados: {stats['clusters_found']}")
            print(f"Centro geográfico: {stats['center']}")
            
            # Mostrar algunos datos de ejemplo
            if data['data']:
                print("Ejemplo de datos:")
                for i, record in enumerate(data['data'][:3]):  # Mostrar primeros 3
                    print(f"  {i+1}. {record['producto']}: {record['cantidad']} unidades "
                          f"en ({record['latitud']}, {record['longitud']}) - Cluster {record['cluster']}")
        else:
            print(f"❌ Error al obtener datos: {response.status_code}")
            print(f"Respuesta: {response.json()}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def test_generate_map(filename):
    """Probar generación de mapa"""
    if not filename:
        print("⏭️ Saltando prueba de mapa (no hay archivo)")
        return
    
    print(f"🔍 Probando generación de mapa para: {filename}")
    try:
        response = requests.post(f'{API_BASE_URL}/map/{filename}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Mapa generado correctamente")
            print(f"URL del mapa: {data['map_url']}")
            print(f"Archivo del mapa: {data['map_filename']}")
        else:
            print(f"❌ Error al generar mapa: {response.status_code}")
            print(f"Respuesta: {response.json()}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def test_analytics(filename):
    """Probar análisis de datos"""
    if not filename:
        print("⏭️ Saltando prueba de análisis (no hay archivo)")
        return
    
    print(f"🔍 Probando análisis para: {filename}")
    try:
        response = requests.get(f'{API_BASE_URL}/analytics/{filename}')
        if response.status_code == 200:
            data = response.json()
            print("✅ Análisis obtenido correctamente")
            analytics = data['analytics']
            print(f"Ventas totales: {analytics['total_sales']}")
            print(f"Promedio de venta: {analytics['average_sale']:.2f}")
            print(f"Centro geográfico: {analytics['geographic_center']}")
            
            print("Análisis por producto:")
            for product in analytics['products']:
                print(f"  - {product['producto']}: {product['total_cantidad']} total, "
                      f"{product['numero_ventas']} ventas")
        else:
            print(f"❌ Error al obtener análisis: {response.status_code}")
            print(f"Respuesta: {response.json()}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
    print("-" * 50)

def main():
    """Función principal para ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas de la API CocoPet Backend")
    print("=" * 50)
    
    # Probar endpoints básicos
    test_health()
    test_api_info()
    test_list_files()
    
    # Probar subida de archivo (si existe)
    uploaded_filename = test_upload_file()
    
    # Probar endpoints que requieren archivo
    test_get_data(uploaded_filename)
    test_generate_map(uploaded_filename)
    test_analytics(uploaded_filename)
    
    print("🏁 Pruebas completadas")
    print("\n💡 Consejos:")
    print("- Asegúrate de que el servidor Flask esté ejecutándose en localhost:5000")
    print("- Crea un archivo Excel de prueba con las columnas requeridas")
    print("- Revisa la documentación en API_DOCUMENTATION.md")

if __name__ == "__main__":
    main()
