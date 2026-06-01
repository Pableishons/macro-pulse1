# prueba_gemini.py
# Primer test con la librería oficial nueva de Gemini.

import os
from google import genai
from dotenv import load_dotenv

# Cargar credenciales
load_dotenv()

# Crear el cliente con la API key
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Hacer una pregunta simple para validar
print("Conectando con Gemini...")
respuesta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents="Saluda en una frase breve y dime qué modelo eres."
)

print("\nRespuesta de Gemini:")
print(respuesta.text)
