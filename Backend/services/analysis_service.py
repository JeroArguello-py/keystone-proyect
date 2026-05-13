import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# 1. El nuevo SDK detecta automáticamente tu GEMINI_API_KEY del archivo .env
client = genai.Client()

# 2. Instrucciones del sistema
instrucciones = """
Eres CampusCare, el asistente de apoyo emocional del proyecto universitario Keystone.
Tu objetivo es brindar acompañamiento inicial a estudiantes, facilitando la expresión de sus emociones.
REGLA 1: No eres un psicólogo y no das diagnósticos clínicos.
REGLA 2: Eres empático, cálido y ofreces recomendaciones básicas de autocuidado.

Analiza el mensaje del estudiante y devuelve ÚNICAMENTE un objeto JSON válido con dos claves:
- "response": Tu respuesta empática redactada para el estudiante.
- "risk_level": Evalúa la situación y escribe solo "bajo", "moderado" o "crítico". Usa "crítico" si detectas ideación suicida, desesperanza extrema, aislamiento severo o pensamientos autodestructivos.
"""

async def analyze_and_respond(message: str) -> dict:
    try:
        # 3. Llamada a la API usando la nueva sintaxis asíncrona (aio)
        # Usamos gemini-2.0-flash-lite porque tiene 1500 RPD gratis (la mas alta del free tier)
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=instrucciones,
                response_mime_type="application/json",  # Forzamos el formato JSON
                temperature=0.7,
            )
        )
        
        texto = response.text.strip()
        
        # Limpiador de Markdown por si Gemini envía el JSON envuelto
        if texto.startswith("```json"):
            texto = texto[7:-3].strip()
        elif texto.startswith("```"):
            texto = texto[3:-3].strip()

        data = json.loads(texto)
        
        # Protocolo de alerta: Si hay riesgo crítico, activamos la notificación institucional [cite: 57, 72]
        if data.get("risk_level") == "crítico":
            data["response"] += "\n\n⚠️ Contacto de emergencia: 1-800-CAMPUS."
            
        print(f"Éxito - Riesgo detectado: {data.get('risk_level')}")
        return data
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ ERROR EXACTO EN GEMINI: {e}")
        # Mensaje empático según el tipo de error
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            friendly = ("Lo siento, justo ahora mis circuitos están saturados (cuota diaria de IA alcanzada). "
                        "Vuelve en unas horas — y mientras tanto, recuerda: respira profundo, "
                        "tu Jardín Interior te espera. 🌱")
        elif "API_KEY" in error_str or "401" in error_str or "permission" in error_str.lower():
            friendly = ("No puedo conectarme con la IA en este momento (problema de credenciales). "
                        "Avisa al equipo de Keystone para que lo revisen.")
        else:
            friendly = ("Estoy teniendo un problema técnico para responderte. "
                        "Si sientes que necesitas ayuda urgente, recuerda que tienes el botón SOS a tu derecha.")
        return {"response": friendly, "risk_level": "bajo"}
    
from fastapi import APIRouter
from pydantic import BaseModel

analysis_router = APIRouter()

class EmotionData(BaseModel):
    student_id: str
    emotion: str

@analysis_router.post("/emotion")
def save_emotion(data: EmotionData):
    print(f"Emoción registrada - Estudiante: {data.student_id}, Emoción: {data.emotion}")
    return {"status": "ok", "emotion": data.emotion}