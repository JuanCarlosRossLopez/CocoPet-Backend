from flask import Flask
from flask_cors import CORS
from modules.mapa_ventas import mapa_ventas_bp

app = Flask(__name__)
CORS(app)  # Habilitar CORS para todas las rutas

# Registrar blueprint
app.register_blueprint(mapa_ventas_bp, url_prefix='/mapa-ventas')

if __name__ == '__main__':
    app.run(debug=True)
