# db.py
# Cliente de conexión a Supabase. Centralizado para reutilizarlo en todos los scripts.

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Variables globales para el cliente (singleton pattern simple)
_cliente: Client = None


def get_cliente() -> Client:
    """
    Devuelve un cliente Supabase. Lo crea la primera vez y lo reutiliza después.
    Centralizar evita crear conexiones innecesarias.
    """
    global _cliente

    if _cliente is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "Faltan credenciales SUPABASE_URL o SUPABASE_KEY en .env"
            )

        _cliente = create_client(url, key)

    return _cliente
