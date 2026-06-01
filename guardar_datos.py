# guardar_datos.py
# Guarda las series económicas del BCCh en Supabase.
# Maneja deduplicación automática: si ya existe esa fecha+código, no la duplica.

from datetime import datetime
from db import get_cliente
from series_bcch import SERIES
from monitor_bcch import consultar_serie


def convertir_fecha(fecha_str):
    """
    Convierte la fecha que viene del BCCh ('01-04-2026') al formato
    que necesita PostgreSQL ('2026-04-01').
    """
    return datetime.strptime(fecha_str, "%d-%m-%Y").strftime("%Y-%m-%d")


def guardar_serie(serie, datos):
    """
    Guarda el dato actual y el anterior de una serie en Supabase.
    Retorna cuántas filas se insertaron realmente (0 si todas eran duplicados).
    """
    cliente = get_cliente()

    # Preparamos las dos filas a insertar: actual y anterior
    filas = [
        {
            "codigo": serie["codigo"],
            "nombre": serie["nombre"],
            "fecha": convertir_fecha(datos["fecha_actual"]),
            "valor": datos["valor_actual"],
            "unidad": serie["unidad"],
            "tipo": serie["tipo"],
        },
        {
            "codigo": serie["codigo"],
            "nombre": serie["nombre"],
            "fecha": convertir_fecha(datos["fecha_anterior"]),
            "valor": datos["valor_anterior"],
            "unidad": serie["unidad"],
            "tipo": serie["tipo"],
        },
    ]

    insertados = 0
    for fila in filas:
        try:
            cliente.table("series_bcch").insert(fila).execute()
            insertados += 1
        except Exception as e:
            # Si el error es por duplicado (UNIQUE constraint), lo ignoramos
            if "duplicate" in str(e).lower() or "23505" in str(e):
                pass  # No es error real, solo significa "ya existía"
            else:
                # Si es otro tipo de error, lo mostramos
                print(f"   ⚠️ Error al insertar {fila['fecha']}: {e}")

    return insertados


def main():
    print("=" * 70)
    print("  GUARDANDO SERIES BCCh EN SUPABASE")
    print("=" * 70)

    total_insertados = 0

    for serie in SERIES:
        print(f"\n📊 {serie['nombre']}")
        datos = consultar_serie(serie["codigo"])

        if datos is None:
            print(f"   ❌ No se pudo consultar")
            continue

        insertados = guardar_serie(serie, datos)
        total_insertados += insertados

        if insertados == 2:
            print(f"   ✅ 2 filas insertadas (actual + anterior)")
        elif insertados == 1:
            print(f"   ✅ 1 fila nueva insertada (la otra ya existía)")
        elif insertados == 0:
            print(f"   ℹ️ Ambas filas ya estaban en la base de datos")

    print("\n" + "=" * 70)
    print(f"  RESUMEN: {total_insertados} filas nuevas guardadas")
    print("=" * 70)


if __name__ == "__main__":
    main()
