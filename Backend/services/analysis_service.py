import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# El nuevo SDK detecta GEMINI_API_KEY del archivo .env automaticamente
client = genai.Client()

# Instrucciones del sistema para Gemini
instrucciones = """
Eres CampusCare, el asistente de apoyo emocional del proyecto universitario Keystone.
Tu objetivo es brindar acompanamiento inicial a estudiantes, facilitando la expresion de sus emociones.
REGLA 1: No eres un psicologo y no das diagnosticos clinicos.
REGLA 2: Eres empatico, calido y ofreces recomendaciones basicas de autocuidado.

Analiza el mensaje del estudiante y devuelve UNICAMENTE un objeto JSON valido con dos claves:
- "response": Tu respuesta empatica redactada para el estudiante.
- "risk_level": Evalua la situacion y escribe solo "bajo", "moderado" o "critico". Usa "critico" si detectas ideacion suicida, desesperanza extrema, aislamiento severo o pensamientos autodestructivos.
"""

# Lista de modelos en orden de preferencia.
# Probamos en cascada hasta que uno funcione (tu cuenta puede no tener cuota en todos).
MODELOS_CANDIDATOS = [
    'gemini-2.5-flash',
    'gemini-3-flash',
    'gemini-flash-latest',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
]


async def _intentar_modelo(modelo: str, message: str):
    return await client.aio.models.generate_content(
        model=modelo,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=instrucciones,
            response_mime_type="application/json",
            temperature=0.7,
        )
    )


async def analyze_and_respond(message: str) -> dict:
    ultimo_error = None
    modelo_usado = None
    response = None

    for modelo in MODELOS_CANDIDATOS:
        try:
            response = await _intentar_modelo(modelo, message)
            modelo_usado = modelo
            print(f"OK - Modelo usado: {modelo}")
            break
        except Exception as e:
            err = str(e)
            if any(kw in err for kw in ["429", "RESOURCE_EXHAUSTED", "404", "400", "INVALID_ARGUMENT", "NOT_FOUND", "PERMISSION_DENIED"]):
                print(f"AVISO - {modelo} no disponible: {err[:120]}")
                ultimo_error = e
                continue
            ultimo_error = e
            break

    if response is None:
        error_str = str(ultimo_error) if ultimo_error else ""
        print(f"ERROR EXACTO EN GEMINI: {ultimo_error}")
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            friendly = "Lo siento, hoy ya agote mi cuota diaria de IA en todos los modelos disponibles. Vuelve manana - y mientras tanto, recuerda: respira profundo, tu Jardin Interior te espera."
        elif "API_KEY" in error_str or "401" in error_str or "permission" in error_str.lower():
            friendly = "No puedo conectarme con la IA en este momento (problema de credenciales). Avisa al equipo de Keystone."
        else:
            friendly = "Estoy teniendo un problema tecnico para responderte. Si sientes que necesitas ayuda urgente, recuerda que tienes el boton SOS a tu derecha."
        return {"response": friendly, "risk_level": "bajo"}

    try:
        texto = response.text.strip()
        if texto.startswith("```json"):
            texto = texto[7:-3].strip()
        elif texto.startswith("```"):
            texto = texto[3:-3].strip()
        data = json.loads(texto)
        if data.get("risk_level") == "critico":
            data["response"] += "\n\nContacto de emergencia: 1-800-CAMPUS."
        print(f"Exito ({modelo_usado}) - Riesgo: {data.get('risk_level')}")
        return data
    except Exception as e:
        print(f"Error parseando respuesta de {modelo_usado}: {e}")
        return {
            "response": "Recibi tu mensaje pero no pude procesarlo del todo. Puedes intentarlo de nuevo?",
            "risk_level": "bajo"
        }


from fastapi import APIRouter
from pydantic import BaseModel

analysis_router = APIRouter()


class EmotionData(BaseModel):
    student_id: str
    emotion: str


@analysis_router.post("/emotion")
def save_emotion(data: EmotionData):
    print(f"Emocion registrada - Estudiante: {data.student_id}, Emocion: {data.emotion}")
    return {"status": "ok", "emotion": data.emotion}
