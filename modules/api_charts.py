from flask import Blueprint, request, jsonify, send_from_directory
import pandas as pd
import folium
from sklearn.cluster import DBSCAN
import os
import json
from werkzeug.utils import secure_filename

api_charts_bp = Blueprint('api_charts', __name__)

UPLOAD_FOLDER = 'uploads'
MAP_FOLDER = 'maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MAP_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@api_charts_bp.route('/charts/<filename>', methods=['GET'])
def get_charts_data(filename):
    """Endpoint para obtener datos procesados para gráficas de tendencias, distribución y rendimiento"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'status': 'error',
                'message': 'Archivo no encontrado'
            }), 404
        
        # Leer datos del Excel
        df = pd.read_excel(filepath)
        
        # Validar columnas necesarias
        required_columns = ['fecha', 'categoria', 'cantidad', 'precio', 'latitud', 'longitud', 'producto']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'status': 'error',
                'message': f'El archivo debe contener las columnas: {", ".join(missing_columns)}'
            }), 400
        
        # Limpiar datos
        df_clean = df.dropna(subset=required_columns)
        
        # Convertir fecha a datetime
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'])
        df_clean['mes_str'] = df_clean['fecha'].dt.strftime('%Y-%m')
        df_clean['semana_str'] = df_clean['fecha'].dt.strftime('%Y-W%U')
        df_clean['ingresos'] = df_clean['cantidad'] * df_clean['precio']
        
        # 1. DATOS PARA GRÁFICA DE TENDENCIAS DE VENTAS
        # Tendencia por mes
        tendencia_mensual = df_clean.groupby('mes_str').agg({
            'cantidad': 'sum',
            'ingresos': 'sum',
            'id_venta': 'count'  # número de transacciones
        }).reset_index()
        
        # Tendencia por semana (últimas 12 semanas)
        tendencia_semanal = df_clean.groupby('semana_str').agg({
            'cantidad': 'sum',
            'ingresos': 'sum',
            'id_venta': 'count'
        }).reset_index().tail(12)
        
        # Tendencia diaria (últimos 30 días)
        df_clean['fecha_str'] = df_clean['fecha'].dt.strftime('%Y-%m-%d')
        tendencia_diaria = df_clean.groupby('fecha_str').agg({
            'cantidad': 'sum',
            'ingresos': 'sum',
            'id_venta': 'count'
        }).reset_index().tail(30)
        
        # 2. DATOS PARA DISTRIBUCIÓN POR CATEGORÍA
        distribucion_categoria = df_clean.groupby('categoria').agg({
            'cantidad': 'sum',
            'ingresos': 'sum',
            'id_venta': 'count',
            'precio': 'mean'
        }).reset_index()
        
        distribucion_categoria['porcentaje_cantidad'] = (
            distribucion_categoria['cantidad'] / distribucion_categoria['cantidad'].sum() * 100
        ).round(2)
        
        distribucion_categoria['porcentaje_ingresos'] = (
            distribucion_categoria['ingresos'] / distribucion_categoria['ingresos'].sum() * 100
        ).round(2)
        
        # Productos más vendidos por categoría
        productos_por_categoria = []
        for categoria in df_clean['categoria'].unique():
            df_cat = df_clean[df_clean['categoria'] == categoria]
            top_productos = df_cat.groupby('producto').agg({
                'cantidad': 'sum',
                'ingresos': 'sum'
            }).nlargest(5, 'cantidad').reset_index()
            
            productos_por_categoria.append({
                'categoria': categoria,
                'top_productos': [
                    {
                        'producto': row['producto'],
                        'cantidad': int(row['cantidad']),
                        'ingresos': float(row['ingresos'])
                    } for _, row in top_productos.iterrows()
                ]
            })
        
        # 3. DATOS PARA RENDIMIENTO DE ZONA (CLUSTERING GEOGRÁFICO)
        from sklearn.cluster import DBSCAN
        import numpy as np
        
        # Aplicar clustering geográfico
        coords = df_clean[['latitud', 'longitud']].values
        db = DBSCAN(eps=0.005, min_samples=3).fit(coords)  # eps más pequeño para mejor granularidad
        df_clean['zona'] = db.labels_
        
        # Análisis por zona
        rendimiento_zona = df_clean.groupby('zona').agg({
            'cantidad': 'sum',
            'ingresos': 'sum',
            'id_venta': 'count',
            'precio': 'mean',
            'latitud': 'mean',
            'longitud': 'mean'
        }).reset_index()
        
        # Filtrar zonas válidas (no ruido)
        rendimiento_zona = rendimiento_zona[rendimiento_zona['zona'] != -1]
        
        # Calcular métricas adicionales por zona
        rendimiento_zona['ingresos_promedio_por_venta'] = (
            rendimiento_zona['ingresos'] / rendimiento_zona['id_venta']
        ).round(2)
        
        rendimiento_zona['densidad_ventas'] = rendimiento_zona['id_venta']  # número de ventas como proxy de densidad
        
        # Análisis de categorías por zona
        zona_categoria = df_clean[df_clean['zona'] != -1].groupby(['zona', 'categoria']).agg({
            'cantidad': 'sum',
            'ingresos': 'sum'
        }).reset_index()
        
        # 4. MÉTRICAS COMPARATIVAS Y RANKINGS
        # Ranking de zonas por diferentes métricas
        ranking_zonas = {
            'por_ingresos': [
                {
                    'zona': int(row['zona']),
                    'ingresos': float(row['ingresos']),
                    'latitud': float(row['latitud']),
                    'longitud': float(row['longitud'])
                } for _, row in rendimiento_zona.nlargest(10, 'ingresos').iterrows()
            ],
            'por_cantidad': [
                {
                    'zona': int(row['zona']),
                    'cantidad': int(row['cantidad']),
                    'latitud': float(row['latitud']),
                    'longitud': float(row['longitud'])
                } for _, row in rendimiento_zona.nlargest(10, 'cantidad').iterrows()
            ],
            'por_densidad': [
                {
                    'zona': int(row['zona']),
                    'densidad_ventas': int(row['densidad_ventas']),
                    'latitud': float(row['latitud']),
                    'longitud': float(row['longitud'])
                } for _, row in rendimiento_zona.nlargest(10, 'densidad_ventas').iterrows()
            ]
        }
        
        # 5. ESTADÍSTICAS GENERALES PARA CONTEXTO
        estadisticas_generales = {
            'total_ventas': int(df_clean['id_venta'].count()),
            'total_ingresos': float(df_clean['ingresos'].sum()),
            'total_productos_vendidos': int(df_clean['cantidad'].sum()),
            'ticket_promedio': float(df_clean['ingresos'].mean()),
            'precio_promedio': float(df_clean['precio'].mean()),
            'categorias_activas': int(df_clean['categoria'].nunique()),
            'productos_unicos': int(df_clean['producto'].nunique()),
            'zonas_identificadas': int(len(rendimiento_zona)),
            'periodo_datos': {
                'inicio': df_clean['fecha'].min().strftime('%Y-%m-%d'),
                'fin': df_clean['fecha'].max().strftime('%Y-%m-%d'),
                'dias_totales': int((df_clean['fecha'].max() - df_clean['fecha'].min()).days + 1)
            }
        }
        
        # Preparar respuesta
        response_data = {
            'status': 'success',
            'charts_data': {
                # Datos para gráfica de tendencias
                'tendencias': {
                    'mensual': [
                        {
                            'periodo': row['mes_str'],
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos']),
                            'transacciones': int(row['id_venta'])
                        } for _, row in tendencia_mensual.iterrows()
                    ],
                    'semanal': [
                        {
                            'periodo': row['semana_str'],
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos']),
                            'transacciones': int(row['id_venta'])
                        } for _, row in tendencia_semanal.iterrows()
                    ],
                    'diaria': [
                        {
                            'periodo': row['fecha_str'],
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos']),
                            'transacciones': int(row['id_venta'])
                        } for _, row in tendencia_diaria.iterrows()
                    ]
                },
                
                # Datos para distribución por categoría
                'distribucion_categoria': {
                    'resumen': [
                        {
                            'categoria': row['categoria'],
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos']),
                            'transacciones': int(row['id_venta']),
                            'precio_promedio': float(row['precio']),
                            'porcentaje_cantidad': float(row['porcentaje_cantidad']),
                            'porcentaje_ingresos': float(row['porcentaje_ingresos'])
                        } for _, row in distribucion_categoria.iterrows()
                    ],
                    'productos_por_categoria': productos_por_categoria
                },
                
                # Datos para rendimiento de zona
                'rendimiento_zona': {
                    'zonas': [
                        {
                            'zona': int(row['zona']),
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos']),
                            'transacciones': int(row['id_venta']),
                            'precio_promedio': float(row['precio']),
                            'latitud': float(row['latitud']),
                            'longitud': float(row['longitud']),
                            'ingresos_promedio_por_venta': float(row['ingresos_promedio_por_venta']),
                            'densidad_ventas': int(row['densidad_ventas'])
                        } for _, row in rendimiento_zona.iterrows()
                    ],
                    'zona_categoria': [
                        {
                            'zona': int(row['zona']),
                            'categoria': row['categoria'],
                            'cantidad': int(row['cantidad']),
                            'ingresos': float(row['ingresos'])
                        } for _, row in zona_categoria.iterrows()
                    ],
                    'rankings': ranking_zonas
                },
                
                # Estadísticas generales
                'estadisticas': estadisticas_generales
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al procesar datos para gráficas: {str(e)}'
        }), 500

@api_charts_bp.route('/charts/<filename>/trend', methods=['GET'])
def get_trend_data(filename):
    """Endpoint específico para datos de tendencias con parámetros personalizables"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404
        
        # Parámetros de consulta
        periodo = request.args.get('periodo', 'mensual')  # mensual, semanal, diario
        metrica = request.args.get('metrica', 'ingresos')  # ingresos, cantidad, transacciones
        limite = int(request.args.get('limite', 12))  # número de períodos a mostrar
        
        df = pd.read_excel(filepath)
        df_clean = df.dropna(subset=['fecha', 'cantidad', 'precio'])
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'])
        df_clean['ingresos'] = df_clean['cantidad'] * df_clean['precio']
        
        # Agrupar según el período solicitado
        if periodo == 'diario':
            df_clean['periodo'] = df_clean['fecha'].dt.strftime('%Y-%m-%d')
        elif periodo == 'semanal':
            df_clean['periodo'] = df_clean['fecha'].dt.strftime('%Y-W%U')
        else:  # mensual
            df_clean['periodo'] = df_clean['fecha'].dt.strftime('%Y-%m')
        
        # Agregar datos según la métrica
        if metrica == 'cantidad':
            tendencia = df_clean.groupby('periodo')['cantidad'].sum().tail(limite)
        elif metrica == 'transacciones':
            tendencia = df_clean.groupby('periodo').size().tail(limite)
        else:  # ingresos
            tendencia = df_clean.groupby('periodo')['ingresos'].sum().tail(limite)
        
        # Calcular crecimiento porcentual
        tendencia_data = []
        valores = tendencia.values
        for i, (periodo, valor) in enumerate(tendencia.items()):
            crecimiento = 0
            if i > 0:
                crecimiento = ((valor - valores[i-1]) / valores[i-1] * 100) if valores[i-1] != 0 else 0
            
            tendencia_data.append({
                'periodo': periodo,
                'valor': float(valor),
                'crecimiento_porcentual': round(crecimiento, 2)
            })
        
        return jsonify({
            'status': 'success',
            'tendencia': tendencia_data,
            'parametros': {
                'periodo': periodo,
                'metrica': metrica,
                'limite': limite
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al obtener datos de tendencia: {str(e)}'
        }), 500

@api_charts_bp.route('/charts/<filename>/heatmap', methods=['GET'])
def get_heatmap_data(filename):
    """Endpoint para datos de mapa de calor por zona y tiempo"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404
        
        df = pd.read_excel(filepath)
        df_clean = df.dropna(subset=['fecha', 'latitud', 'longitud', 'cantidad', 'precio'])
        df_clean['fecha'] = pd.to_datetime(df_clean['fecha'])
        df_clean['ingresos'] = df_clean['cantidad'] * df_clean['precio']
        
        # Crear grids geográficos para el heatmap
        # Dividir el área en una cuadrícula
        lat_bins = pd.cut(df_clean['latitud'], bins=10, include_lowest=True)
        lon_bins = pd.cut(df_clean['longitud'], bins=10, include_lowest=True)
        
        df_clean['lat_bin'] = lat_bins
        df_clean['lon_bin'] = lon_bins
        
        # Agregar por día de la semana y hora
        df_clean['dia_semana'] = df_clean['fecha'].dt.day_name()
        df_clean['hora'] = pd.to_datetime(df_clean['hora'], format='%I:%M %p').dt.hour
        
        # Heatmap geográfico por ingresos
        heatmap_geografico = df_clean.groupby(['lat_bin', 'lon_bin']).agg({
            'ingresos': 'sum',
            'cantidad': 'sum',
            'latitud': 'mean',
            'longitud': 'mean'
        }).reset_index()
        
        # Convertir bins a strings para JSON
        heatmap_geografico['lat_bin_str'] = heatmap_geografico['lat_bin'].astype(str)
        heatmap_geografico['lon_bin_str'] = heatmap_geografico['lon_bin'].astype(str)
        
        # Heatmap temporal (día de semana vs hora)
        heatmap_temporal = df_clean.groupby(['dia_semana', 'hora'])['ingresos'].sum().reset_index()
        
        return jsonify({
            'status': 'success',
            'heatmap_data': {
                'geografico': [
                    {
                        'lat_bin': row['lat_bin_str'],
                        'lon_bin': row['lon_bin_str'],
                        'ingresos': float(row['ingresos']),
                        'cantidad': int(row['cantidad']),
                        'latitud': float(row['latitud']),
                        'longitud': float(row['longitud'])
                    } for _, row in heatmap_geografico.iterrows()
                ],
                'temporal': [
                    {
                        'dia_semana': row['dia_semana'],
                        'hora': int(row['hora']),
                        'ingresos': float(row['ingresos'])
                    } for _, row in heatmap_temporal.iterrows()
                ]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al generar datos de heatmap: {str(e)}'
        }), 500