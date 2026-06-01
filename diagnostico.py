# diagnostico.py
# Script temporal para ver qué credenciales se están leyendo del .env

import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print("=" * 60)
print("Diagnóstico de credenciales Supabase")
print("=" * 60)
print(f"\nSUPABASE_URL leída:")
print(f"  >>>{url}<<<")
print(f"  Tipo: {type(url).__name__}")
print(f"  Longitud: {len(url) if url else 0} caracteres")

print(f"\nSUPABASE_KEY leída:")
print(f"  Primeros 20 chars: {key[:20] if key else 'None'}...")
print(f"  Longitud: {len(key) if key else 0} caracteres")
