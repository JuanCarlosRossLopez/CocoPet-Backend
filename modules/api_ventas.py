from flask import Blueprint, request, jsonify, send_from_directory
import pandas as pd
import folium
from sklearn.cluster import DBSCAN
import os
import json
from werkzeug.utils import secure_filename

api_ventas_bp = Blueprint('api_ventas', __name__)

UPLOAD_FOLDER = 'uploads'
MAP_FOLDER = 'maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MAP_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_ventas_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar que la API está funcionando"""
    return jsonify({
        'status': 'success',
        'message': 'API está funcionando correctamente',
        'version': '1.0.0'
    }), 200

@api_ventas_bp.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para subir archivos Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No se encontró ningún archivo en la petición'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No se seleccionó ningún archivo'
            }), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Validar que el archivo tenga las columnas necesarias
            try:
                df = pd.read_excel(filepath)
                required_columns = ['latitud', 'longitud', 'producto', 'cantidad']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    os.remove(filepath)  # Eliminar archivo inválido
                    return jsonify({
                        'status': 'error',
                        'message': f'El archivo debe contener las columnas: {", ".join(missing_columns)}'
                    }), 400
                
                return jsonify({
                    'status': 'success',
                    'message': 'Archivo subido correctamente',
                    'filename': filename,
                    'records_count': len(df)
                }), 200
                
            except Exception as e:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({
                    'status': 'error',
                    'message': f'Error al leer el archivo Excel: {str(e)}'
                }), 400
        
        return jsonify({
            'status': 'error',
            'message': 'Tipo de archivo no permitido. Use archivos .xlsx o .xls'
        }), 400
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error interno del servidor: {str(e)}'
        }), 500

@api_ventas_bp.route('/files', methods=['GET'])
def list_files():
    """Endpoint para listar archivos disponibles"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file_stats = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'modified': file_stats.st_mtime
                })
        
        return jsonify({
            'status': 'success',
            'files': files
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al listar archivos: {str(e)}'
        }), 500

@api_ventas_bp.route('/data/<filename>', methods=['GET'])
def get_data(filename):
    """Endpoint para obtener datos procesados en formato JSON"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': 'Archivo no encontrado'
            }), 404
        
        df = pd.read_excel(filepath)
        
        # Limpiar datos nulos
        df_clean = df[['latitud', 'longitud', 'producto', 'cantidad']].dropna()
        
        # Aplicar clustering
        coords = df_clean[['latitud', 'longitud']].values
        db = DBSCAN(eps=0.01, min_samples=2).fit(coords)
        df_clean = df_clean.copy()
        df_clean['cluster'] = db.labels_
        
        # Convertir a formato JSON amigable
        data = []
        for _, row in df_clean.iterrows():
            data.append({
                'latitud': float(row['latitud']),
                'longitud': float(row['longitud']),
                'producto': str(row['producto']),
                'cantidad': int(row['cantidad']),
                'cluster': int(row['cluster'])
            })
        
        # Calcular estadísticas
        stats = {
            'total_records': len(data),
            'unique_products': df_clean['producto'].nunique(),
            'total_quantity': int(df_clean['cantidad'].sum()),
            'clusters_found': len(set(df_clean['cluster'])) - (1 if -1 in df_clean['cluster'].values else 0),
            'center': {
                'latitud': float(df_clean['latitud'].mean()),
                'longitud': float(df_clean['longitud'].mean())
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': data,
            'statistics': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al procesar datos: {str(e)}'
        }), 500

@api_ventas_bp.route('/map/<filename>', methods=['POST'])
def generate_map(filename):
    """Endpoint para generar mapa y devolver la URL"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': 'Archivo no encontrado'
            }), 404
        
        df = pd.read_excel(filepath)
        df_clean = df[['latitud', 'longitud', 'producto', 'cantidad']].dropna()
        
        # Aplicar clustering
        coords = df_clean[['latitud', 'longitud']].values
        db = DBSCAN(eps=0.01, min_samples=2).fit(coords)
        df_clean = df_clean.copy()
        df_clean['cluster'] = db.labels_
        
        # Crear mapa
        center_lat = df_clean['latitud'].mean()
        center_lon = df_clean['longitud'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        
        # Colores para clusters
        color_list = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'lightblue']
        color_map = {}
        
        # Agregar marcadores
        for _, row in df_clean.iterrows():
            cluster = row['cluster']
            producto = row['producto']
            cantidad = row['cantidad']
            
            if (cluster, producto) not in color_map:
                color_map[(cluster, producto)] = color_list[len(color_map) % len(color_list)]
            
            folium.CircleMarker(
                location=[row['latitud'], row['longitud']],
                radius=5 + cantidad,
                color=color_map[(cluster, producto)],
                fill=True,
                fill_opacity=0.6,
                popup=f"Producto: {producto}<br>Cantidad: {cantidad}<br>Cluster: {cluster}"
            ).add_to(m)
        
        # Guardar mapa
        map_filename = f"map_{filename}.html"
        map_path = os.path.join(MAP_FOLDER, map_filename)
        m.save(map_path)
        
        return jsonify({
            'status': 'success',
            'message': 'Mapa generado correctamente',
            'map_url': f'/api/map-file/{map_filename}',
            'map_filename': map_filename
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al generar mapa: {str(e)}'
        }), 500

@api_ventas_bp.route('/map-file/<filename>', methods=['GET'])
def serve_map_file(filename):
    """Endpoint para servir archivos de mapa"""
    try:
        return send_from_directory(MAP_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'message': 'Archivo de mapa no encontrado'
        }), 404

@api_ventas_bp.route('/analytics/<filename>', methods=['GET'])
def get_analytics(filename):
    """Endpoint para obtener análisis avanzado de los datos"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': 'Archivo no encontrado'
            }), 404
        
        df = pd.read_excel(filepath)
        df_clean = df[['latitud', 'longitud', 'producto', 'cantidad']].dropna()
        
        # Análisis por producto
        product_analysis = df_clean.groupby('producto').agg({
            'cantidad': ['sum', 'mean', 'count'],
            'latitud': 'mean',
            'longitud': 'mean'
        }).round(4)
        
        product_stats = []
        for producto in product_analysis.index:
            product_stats.append({
                'producto': producto,
                'total_cantidad': int(product_analysis.loc[producto, ('cantidad', 'sum')]),
                'promedio_cantidad': float(product_analysis.loc[producto, ('cantidad', 'mean')]),
                'numero_ventas': int(product_analysis.loc[producto, ('cantidad', 'count')]),
                'centro_geografico': {
                    'latitud': float(product_analysis.loc[producto, ('latitud', 'mean')]),
                    'longitud': float(product_analysis.loc[producto, ('longitud', 'mean')])
                }
            })
        
        return jsonify({
            'status': 'success',
            'analytics': {
                'products': product_stats,
                'total_sales': int(df_clean['cantidad'].sum()),
                'average_sale': float(df_clean['cantidad'].mean()),
                'geographic_center': {
                    'latitud': float(df_clean['latitud'].mean()),
                    'longitud': float(df_clean['longitud'].mean())
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al generar análisis: {str(e)}'
        }), 500
