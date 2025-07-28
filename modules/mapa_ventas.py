from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, jsonify
import pandas as pd
import folium
from sklearn.cluster import DBSCAN
import os
import logging
from datetime import datetime

logging.basicConfig(filename='cargas.log', level=logging.INFO)

mapa_ventas_bp = Blueprint('mapa_ventas', __name__, template_folder='../templates')

UPLOAD_FOLDER = 'uploads'
MAP_FOLDER = 'maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MAP_FOLDER, exist_ok=True)

# ⛳ Página principal
@mapa_ventas_bp.route('/')
def index():
    return render_template('upload.html')

# 🗂️ Servidor de mapa HTML
@mapa_ventas_bp.route('/maps/<filename>')
def serve_map(filename):
    return send_from_directory(MAP_FOLDER, filename)

# 📥 Subida de archivo Excel
@mapa_ventas_bp.route('/upload', methods=['POST'])
def upload():
    if 'excel' not in request.files:
        logging.warning(f"[{datetime.now()}] ❌ Carga fallida: no se encontró 'excel' en request.files")
        return 'No se recibió archivo válido', 400

    file = request.files['excel']
    if file.filename == '':
        logging.warning(f"[{datetime.now()}] ⚠️ Archivo vacío recibido")
        return 'Archivo vacío', 400

    if file.filename.endswith('.xlsx'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        logging.info(f"[{datetime.now()}] 📥 Archivo guardado: {file.filename}")
        return redirect(url_for('mapa_ventas.mapa', filename=file.filename))
    
    logging.warning(f"[{datetime.now()}] ❌ Tipo de archivo no soportado: {file.filename}")
    return 'Archivo no válido. Debe ser .xlsx', 400

# 🗺️ Visualización de mapa con filtros separados
@mapa_ventas_bp.route('/ver/<filename>')
def mapa(filename):
    producto = request.args.get('producto')
    categoria = request.args.get('categoria')  # Nuevo filtro
    min_cantidad = request.args.get('min_cantidad', type=int)
    max_cantidad = request.args.get('max_cantidad', type=int)

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        logging.error(f"[{datetime.now()}] ❌ Archivo no encontrado: {filename}")
        return 'Archivo no encontrado', 404

    df = pd.read_excel(filepath)
    coords = df[['latitud', 'longitud']].dropna().values
    db = DBSCAN(eps=0.01, min_samples=2).fit(coords)
    df['cluster'] = db.labels_

    # Filtros individuales
    if producto:
        df = df[df['producto'] == producto]
    if categoria:
        df = df[df['categoria'] == categoria]
    if min_cantidad is not None:
        df = df[df['cantidad'] >= min_cantidad]
    if max_cantidad is not None:
        df = df[df['cantidad'] <= max_cantidad]

    if df.empty:
        logging.warning(f"[{datetime.now()}] 📭 Filtros vacíos en {filename}")
        return 'No hay datos que coincidan con los filtros aplicados', 204

    # 🎨 Mapa con categoría en popup
    m = folium.Map(location=[df['latitud'].mean(), df['longitud'].mean()], zoom_start=13)
    color_list = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'lightblue']
    color_map = {}

    for _, row in df.iterrows():
        key = (row['cluster'], row['producto'])
        if key not in color_map:
            color_map[key] = color_list[len(color_map) % len(color_list)]

        folium.CircleMarker(
            location=[row['latitud'], row['longitud']],
            radius=5 + row['cantidad'],
            color=color_map[key],
            fill=True,
            fill_opacity=0.6,
            popup=f"""
                Producto: {row['producto']}<br>
                Cantidad: {row['cantidad']}<br>
                Categoría: {row['categoria']}
            """
        ).add_to(m)

    map_path = os.path.join(MAP_FOLDER, f"map_{filename}.html")
    m.save(map_path)
    registrar_filtros_aplicados(filename, producto, min_cantidad, max_cantidad)

    return render_template('map.html', map_file=f"map_{filename}.html")


# 📝 Bitácora de filtros aplicados
def registrar_filtros_aplicados(filename, producto, min_cant, max_cant):
    log_path = "logs/bitacora_filtros.csv"
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "a") as log:
        log.write(f"{filename},{producto},{min_cant},{max_cant},{datetime.now()}\n")

# 🧠 Entrenamiento y clustering centralizado
@mapa_ventas_bp.route('/api/train', methods=['POST'])
def train_clusters():
    data = request.get_json()
    filename = data.get('filename')
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return {'error': 'Archivo no encontrado'}, 404

    df = pd.read_excel(filepath)
    coords = df[['latitud', 'longitud']].dropna().values
    db = DBSCAN(eps=0.01, min_samples=2).fit(coords)
    df['cluster'] = db.labels_

    resultados = []
    for cluster_id in sorted(df['cluster'].unique()):
        if cluster_id == -1:
            continue
        subset = df[df['cluster'] == cluster_id]
        centroide = {
            'lat': float(subset['latitud'].mean()),
            'lon': float(subset['longitud'].mean())
        }
        productos = subset.groupby('producto')['cantidad'].sum().to_dict()
        cantidad_total = int(subset['cantidad'].sum())

        resultados.append({
            'cluster': int(cluster_id),
            'centroide': centroide,
            'productos': productos,
            'cantidad_total': cantidad_total
        })

    return jsonify(resultados)

# 📦 Listado limpio de productos únicos
@mapa_ventas_bp.route('/api/productos/<filename>')
def lista_productos(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return {'error': 'Archivo no encontrado'}, 404

    df = pd.read_excel(filepath)
    productos = sorted(df['producto'].dropna().unique().tolist())
    return jsonify({'productos': productos})

@mapa_ventas_bp.route('/api/categorias/<filename>')
def lista_categorias(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return {'error': 'Archivo no encontrado'}, 404

    df = pd.read_excel(filepath)
    categorias = sorted(df['categoria'].dropna().unique().tolist())
    return jsonify({'categorias': categorias})
