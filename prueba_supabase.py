# prueba_supabase.py
# Test rápido: ¿podemos conectarnos a Supabase y leer las tablas?

from db import get_cliente


def main():
    print("Conectando a Supabase...")
    cliente = get_cliente()

    # Intentamos leer las tablas (deberían estar vacías)
    print("\nLeyendo series_bcch...")
    respuesta = cliente.table("series_bcch").select("*").execute()
    print(f"  Filas encontradas: {len(respuesta.data)}")

    print("\nLeyendo hechos_esenciales...")
    respuesta = cliente.table("hechos_esenciales").select("*").execute()
    print(f"  Filas encontradas: {len(respuesta.data)}")

    print("\n✅ Conexión exitosa con Supabase")


if __name__ == "__main__":
    main()
