import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar la llave
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Buscando modelos compatibles...")
print("-" * 30)

# Listar todos los modelos disponibles para tu cuenta que sirvan para generar texto
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    print("-" * 30)
    print("¡Búsqueda terminada!")
except Exception as e:
    print(f"Error al conectar: {e}")