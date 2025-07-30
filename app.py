from flask import Flask, jsonify
from flask_cors import CORS
from modules.mapa_ventas import mapa_ventas_bp
from modules.api_ventas import api_ventas_bp
from modules.api_charts import api_charts_bp
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB por defecto
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAP_FOLDER'] = os.getenv('MAP_FOLDER', 'maps')

# Configurar CORS
cors_origins = os.getenv('CORS_ORIGINS', '*')
if cors_origins == '*':
    CORS(app)
else:
    CORS(app, origins=cors_origins.split(','))

# Registrar blueprints
app.register_blueprint(mapa_ventas_bp, url_prefix='/mapa-ventas')  # Rutas web existentes
app.register_blueprint(api_ventas_bp, url_prefix='/api')  # Nuevas rutas API REST
app.register_blueprint(api_charts_bp,url_prefixs='/charts')

# Endpoint raíz de la API
@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'message': 'CocoPet Backend API',
        'version': os.getenv('API_VERSION', '1.0.0'),
        'endpoints': {
            'health': '/api/health',
            'upload': '/api/upload',
            'files': '/api/files',
            'data': '/api/data/<filename>',
            'generate_map': '/api/map/<filename>',
            'analytics': '/api/analytics/<filename>',
            'charts':'/api/charts/<filename>',
            'trend':'/charts/<filename>/trend',
            'heatmap':'/charts/<filename>/heatmap'
        },
        'documentation': 'Ver API_DOCUMENTATION.md para más detalles'
    })

# Endpoint raíz general
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'CocoPet Backend - Servidor funcionando',
        'api_url': '/api',
        'web_interface': '/mapa-ventas'
    })

if __name__ == '__main__':
    app.run(debug=True)
