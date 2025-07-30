from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime
from uuid import uuid4

api_predictions_bp = Blueprint('api_predictions', __name__)

# Ruta del archivo JSON que actuará como base de datos temporal
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PREDICTIONS_FILE = os.path.join(BASE_DIR, '..', 'data', 'predictions.json')

# Asegurar que la carpeta y el archivo existan
os.makedirs(os.path.dirname(PREDICTIONS_FILE), exist_ok=True)
if not os.path.exists(PREDICTIONS_FILE):
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump([], f)

# Cargar predicciones
def load_predictions():
    with open(PREDICTIONS_FILE, 'r') as f:
        return json.load(f)

# Guardar predicciones
def save_predictions(predictions):
    with open(PREDICTIONS_FILE, 'w') as f:
        json.dump(predictions, f, indent=2)

# GET /api/predictions
@api_predictions_bp.route('/predictions', methods=['GET'])
def get_predictions():
    return jsonify(load_predictions())

# POST /api/predictions
@api_predictions_bp.route('/predictions', methods=['POST'])
def add_prediction():
    try:
        data = request.get_json()
        required = ['product', 'category', 'zone', 'period', 'predictedSales', 'confidence', 'trend', 'previousPeriod']
        if not all(field in data for field in required):
            return jsonify({'error': 'Campos faltantes'}), 400

        new_prediction = {
            'id': str(uuid4()),
            'product': data['product'],
            'category': data['category'],
            'zone': data['zone'],
            'period': data['period'],
            'predictedSales': data['predictedSales'],
            'confidence': data['confidence'],
            'trend': data['trend'],
            'previousPeriod': data['previousPeriod'],
            'createdAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        predictions = load_predictions()
        predictions.insert(0, new_prediction)
        save_predictions(predictions)

        return jsonify(new_prediction), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
