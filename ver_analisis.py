# ver_analisis.py
# Muestra los análisis profundos guardados en Supabase, bonitos.

import json
from db import get_cliente


def main():
    db = get_cliente()
    respuesta = db.table("hechos_esenciales") \
        .select("empresa, materia, fecha, relevancia, analisis_completo") \
        .not_.is_("analisis_completo", "null") \
        .order("creado_en", desc=True) \
        .limit(3) \
        .execute()

    for hecho in respuesta.data:
        print("=" * 80)
        print(f"📌 {hecho['empresa']}")
        print(
            f"   {hecho['materia']} · {hecho['fecha']} · relevancia: {hecho['relevancia']}")
        print("=" * 80)

        a = hecho["analisis_completo"]

        if "error" in a:
            print(f"⚠️ Error: {a['error']}")
            continue

        print(f"\n📰 Titular: {a.get('titular', '—')}")
        print(
            f"   Urgencia: {a.get('urgencia', '—')} · Magnitud: {a.get('magnitud_esperada', '—')}")
        print(f"   Ventana crítica: {a.get('ventana_critica', '—')}")

        vi = a.get("version_interna", {})
        print(f"\n📊 Resumen: {vi.get('resumen', '—')}")
        print(f"\n💡 Interpretación: {vi.get('interpretacion', '—')}")

        accion = vi.get("accion_corredora", {})
        print(f"\n🎯 Acción comercial:")
        print(f"   Con el papel:  {accion.get('tiene_el_papel', '—')}")
        print(f"   Sin el papel:  {accion.get('no_tiene_el_papel', '—')}")

        if vi.get("oportunidad_adicional"):
            print(f"\n✨ Oportunidad adicional: {vi['oportunidad_adicional']}")

        print(f"\n⚠️ Riesgos: {vi.get('riesgos', '—')}")

        print(f"\n📱 Forwardeable:")
        print(f"   {a.get('version_forwardeable', '—')}")

        tags = a.get("tags", [])
        if tags:
            print(f"\n🏷️ Tags: {', '.join(tags)}")

        print()


if __name__ == "__main__":
    main()
