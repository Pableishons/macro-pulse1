# guardar_hechos.py
# Captura hechos esenciales CMF y los guarda en Supabase.
# No los analiza con IA todavía: solo los persiste para análisis posterior.

from db import get_cliente
from scraper_cmf import obtener_hechos_esenciales


def guardar_hecho(hecho):
    """
    Guarda un hecho esencial en Supabase.
    Retorna True si lo insertó, False si ya existía.
    """
    cliente = get_cliente()

    fila = {
        "numero_doc": hecho["numero_doc"],
        "fecha": hecho["fecha"],
        "empresa": hecho["empresa"],
        "materia": hecho["materia"],
        "link_cmf": hecho["link_cmf"],
        "analizado": False,  # Aún no pasó por IA
    }

    try:
        cliente.table("hechos_esenciales").insert(fila).execute()
        return True
    except Exception as e:
        # Si es duplicado (UNIQUE en numero_doc), no es error real
        if "duplicate" in str(e).lower() or "23505" in str(e):
            return False
        # Cualquier otro error sí lo reportamos
        print(f"   ⚠️ Error al insertar {hecho['numero_doc']}: {e}")
        return False


def main():
    print("=" * 70)
    print("  CAPTURANDO HECHOS ESENCIALES CMF EN SUPABASE")
    print("=" * 70)

    hechos = obtener_hechos_esenciales(limite=30)
    if not hechos:
        print("❌ No hay hechos para procesar.")
        return

    nuevos = 0
    existentes = 0

    for hecho in hechos:
        if guardar_hecho(hecho):
            nuevos += 1
            print(f"   ✅ {hecho['empresa'][:60]}")
        else:
            existentes += 1

    print("\n" + "=" * 70)
    print(f"  RESUMEN")
    print("=" * 70)
    print(f"  Hechos nuevos guardados: {nuevos}")
    print(f"  Hechos ya existentes:    {existentes}")
    print(f"  Total revisados:         {len(hechos)}")


if __name__ == "__main__":
    main()
