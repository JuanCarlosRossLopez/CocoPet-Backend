from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging

import openai

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
api_chatgpt_bp = Blueprint('api_chatgpt', __name__)
logging.basicConfig(filename='logs/chatgpt.log', level=logging.INFO)

SYSTEM_PROMPT = (
    "Eres un asistente experto en veterinaria. Respondes exclusivamente dentro del ámbito veterinario "
    "y no das información ni opiniones sobre temas no relacionados. Estás entrenado para brindar ayuda en: "
    "• Enfermedades comunes en animales domésticos (perros, gatos, aves, reptiles, etc.) "
    "• Vacunación, desparasitación, síntomas, primeros auxilios y prevención "
    "• Alimentación especializada: dietas veterinarias, alimentos balanceados, alergias alimentarias "
    "• Comportamiento animal y bienestar "
    "• Productos veterinarios: antipulgas, desparasitantes, vacunas, collares, suplementos nutricionales, shampoos, etc. "
    "• Medicamentos de uso veterinario: antibióticos, analgésicos, antiinflamatorios, protectores gástricos, tratamientos endocrinos y antiparasitarios "
    "• Protocolos de uso típico de marcas comerciales reconocidas (Bravecto, NexGard, Milbemax, Royal Canin, Hill's, Frontline, etc.) "
    "• Razas, características fisiológicas, cuidados particulares según especie o edad "
    "• Recomendaciones preventivas, calendario de vacunación, necesidades según etapa de vida del animal "
    "• Diagnóstico preliminar orientativo basado en síntomas generales, sin sustituir opinión médica profesional "

    "Si el usuario realiza una pregunta fuera del contexto veterinario — como deportes, política, tecnología, historia humana, matemáticas, recetas de cocina o eventos no relacionados — debes responder educadamente: "
    "'Este asistente está diseñado exclusivamente para temas veterinarios. ¿Te gustaría saber algo relacionado con mascotas, cuidados o salud animal?' "

    "Nunca debes responder temas humanos, políticos, técnicos ajenos, ni emitir opiniones personales, ni sugerencias fuera del dominio veterinario. "
    "Evita descripciones detalladas de procedimientos quirúrgicos o dosis exactas que requieran supervisión profesional. "
    "No afirmes información que no esté respaldada por evidencia veterinaria común o práctica clínica estandarizada."
)

@api_chatgpt_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")

    if not user_input:
        return jsonify({"error": "No se recibió mensaje"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        )
        answer = response.choices[0].message.content
        logging.info(f"User: {user_input}\nBot: {answer}")
        return jsonify({
            "response": answer,
            "conversation_id": "mock-session-id",
        })

    except openai.RateLimitError as e:
        logging.warning("Se excedió la cuota de OpenAI: %s", str(e))
        return jsonify({
            "error": "La cuota de uso ha sido superada. Verifica tu cuenta en OpenAI.",
            "type": "rate_limit"
        }), 429

