from flask import Blueprint, request, jsonify
import os
import pandas as pd
from datetime import datetime
from uuid import uuid4
import json

api_train_bp = Blueprint('api_train', __name__)

# Ruta al archivo donde se guardan los entrenamientos
TRAIN_LOG_FILE = os.path.join(os.getcwd(), 'data', 'predictions.json')
os.makedirs(os.path.dirname(TRAIN_LOG_FILE), exist_ok=True)
if not os.path.exists(TRAIN_LOG_FILE):
    with open(TRAIN_LOG_FILE, 'w') as f:
        json.dump([], f)

def load_predictions():
    with open(TRAIN_LOG_FILE, 'r') as f:
        return json.load(f)

def save_prediction(entry):
    history = load_predictions()
    history.insert(0, entry)
    with open(TRAIN_LOG_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@api_train_bp.route('/train', methods=['POST'])
def train_model():
    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({"error": "Falta el nombre del archivo"}), 400

        # Ruta completa al archivo subido
        filepath = os.path.join(os.getcwd(), 'uploads', filename)
        if not os.path.exists(filepath):
            return jsonify({"error": f"Archivo no encontrado: {filename}"}), 404

        # Leer el archivo con pandas
        df = pd.read_excel(filepath) if filename.endswith('.xlsx') else pd.read_csv(filepath)

        # Simulación de entrenamiento: obtener número de filas, columnas, etc.
        num_rows = len(df)
        num_columns = len(df.columns)

        new_entry = {
            "id": str(uuid4()),
            "product": f"Entrenamiento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "category": "Entrenamiento de modelo",
            "zone": "N/A",
            "period": f"{num_rows} filas, {num_columns} columnas",
            "predictedSales": num_rows,
            "confidence": 100,
            "trend": "stable",
            "previousPeriod": 0,
            "createdAt": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        save_prediction(new_entry)

        return jsonify(new_entry), 200

    except Exception as e:
        print("❌ Error en entrenamiento:", str(e))
        return jsonify({"error": str(e)}), 500
