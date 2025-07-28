from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
import folium
from sklearn.cluster import DBSCAN
import os

mapa_ventas_bp = Blueprint('mapa_ventas', __name__, template_folder='../templates')

UPLOAD_FOLDER = 'uploads'
MAP_FOLDER = 'maps'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MAP_FOLDER, exist_ok=True)

@mapa_ventas_bp.route('/')
def index():
    return render_template('upload.html')

@mapa_ventas_bp.route('/maps/<filename>')
def serve_map(filename):
    return send_from_directory(MAP_FOLDER, filename)

@mapa_ventas_bp.route('/upload', methods=['POST'])
def upload():
    file = request.files['excel']
    if file.filename.endswith('.xlsx'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return redirect(url_for('mapa_ventas.mapa', filename=file.filename))
    return 'Archivo no válido. Debe ser .xlsx'

@mapa_ventas_bp.route('/ver/<filename>')
def mapa(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_excel(filepath)

    coords = df[['latitud', 'longitud']].dropna().values
    db = DBSCAN(eps=0.01, min_samples=2).fit(coords)
    df['cluster'] = db.labels_

    m = folium.Map(location=[df['latitud'].mean(), df['longitud'].mean()], zoom_start=13)

    color_list = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'lightblue']
    color_map = {}

    for i, row in df.iterrows():
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
            popup=f"Producto: {producto}<br>Cantidad: {cantidad}"
        ).add_to(m)

    map_path = os.path.join(MAP_FOLDER, f"map_{filename}.html")
    m.save(map_path)

    return render_template('map.html', map_file=f"map_{filename}.html")
