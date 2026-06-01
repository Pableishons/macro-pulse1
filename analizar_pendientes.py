# analizar_pendientes.py
# Toma hechos esenciales sin clasificar y los procesa con Gemini.
# Versión optimizada para tier pagado (sin esperas artificiales).

import os
import json
import time
from google import genai
from dotenv import load_dotenv
from db import get_cliente

load_dotenv()
cliente_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Rate limiting suave (1.000 RPM en pagado = ~17/s, ponemos 0.5s para tener margen)
DELAY_ENTRE_LLAMADAS = 0.5

# Sin límite por corrida ahora
MAX_POR_CORRIDA = 100  # Por si acaso, no más de 100 de una

PROMPT_FILTRO = """Eres un analista de inversiones senior de un banco chileno
enfocado en segmento alto patrimonio (HNW). Te llega un hecho esencial CMF.

Tu tarea: clasificar la relevancia para un cliente que invierte en
acciones IPSA, mid caps chilenas, bonos corporativos y fondos mutuos.

REGLAS CLAVE (en este orden de prioridad):

1. Si el emisor es un FONDO DE INVERSIÓN o ADMINISTRADORA GENERAL DE FONDOS
   no listado, la relevancia es BAJA por defecto.

2. Si la materia es "Otros" sin contexto adicional, relevancia BAJA.

3. Para EMPRESAS LISTADAS (IPSA o mid caps):
   - ALTA: fusiones, OPA, profit warning, cambio de CEO/Presidente directorio,
     emisión de bonos, aumento capital material, sanciones graves,
     contratos materiales, dividendos extraordinarios.
   - MEDIA: juntas extraordinarias con propuestas, cambios de gerentes no C-level,
     dividendos ordinarios, colocaciones rutinarias.
   - BAJA: cambios formales (representante legal, directorio filial no listada).

4. Para AUDITORAS, CONSULTORAS, SOCIEDADES NO LISTADAS:
   relevancia BAJA salvo evento materialmente excepcional.

5. NUNCA inventes información. Si tienes duda, BAJA.

EMPRESAS IPSA RELEVANTES (referencia):
Falabella, CCU, Banco de Chile, Banco Santander, Banco Itaú, Banco BCI,
Banco Falabella, Cencosud, Copec, Enel, Colbún, Aguas Andinas, AntarChile,
Quiñenco, SQM, CAP, CMPC, Empresas COPEC, ECL, LATAM, Parque Arauco,
SMU, Mall Plaza, Ripley, Sigdo Koppers, Sonda, Vapores.

HECHO ESENCIAL:
Empresa: {empresa}
Materia: {materia}
Fecha: {fecha}

Devuelve únicamente este JSON (sin texto adicional, sin markdown):
{{
  "relevancia": "alta | media | baja",
  "razon": "máximo 12 palabras",
  "es_ipsa": true | false
}}
"""


def clasificar_hecho(hecho):
    """Clasifica un hecho usando Gemini Flash-Lite."""
    prompt = PROMPT_FILTRO.format(
        empresa=hecho["empresa"],
        materia=hecho["materia"],
        fecha=hecho["fecha"],
    )

    try:
        respuesta = cliente_gemini.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )

        texto = respuesta.text.strip()
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
            texto = texto.strip()

        return json.loads(texto)

    except Exception as e:
        return {
            "relevancia": "baja",
            "razon": f"Error: {str(e)[:50]}",
            "es_ipsa": False,
        }


def obtener_pendientes(limite):
    """Trae los hechos esenciales que todavía no han sido analizados."""
    db = get_cliente()
    respuesta = db.table("hechos_esenciales") \
        .select("*") \
        .eq("analizado", False) \
        .order("creado_en", desc=True) \
        .limit(limite) \
        .execute()
    return respuesta.data


def actualizar_hecho(numero_doc, clasificacion):
    """Actualiza una fila en Supabase con el resultado del análisis."""
    db = get_cliente()
    db.table("hechos_esenciales") \
        .update({
            "relevancia": clasificacion["relevancia"],
            "razon": clasificacion["razon"],
            "es_ipsa": clasificacion["es_ipsa"],
            "analizado": True,
        }) \
        .eq("numero_doc", numero_doc) \
        .execute()


def main():
    print("=" * 80)
    print("  ANÁLISIS DE HECHOS PENDIENTES (tier pagado)")
    print("=" * 80)

    pendientes = obtener_pendientes(limite=MAX_POR_CORRIDA)

    if not pendientes:
        print("\n✅ No hay hechos pendientes de análisis.")
        return

    total = len(pendientes)
    print(f"\n📊 {total} hechos pendientes de clasificar")
    print(f"⏱️  Tiempo estimado: ~{total} segundos\n")

    contador = {"alta": 0, "media": 0, "baja": 0}

    for i, hecho in enumerate(pendientes, 1):
        print(f"  [{i}/{total}] {hecho['empresa'][:50]}...")

        clasificacion = clasificar_hecho(hecho)
        actualizar_hecho(hecho["numero_doc"], clasificacion)

        rel = clasificacion["relevancia"]
        if rel in contador:
            contador[rel] += 1

        emoji = {"alta": "🔴", "media": "🟡", "baja": "⚪"}.get(rel, "❓")
        ipsa = " [IPSA]" if clasificacion.get("es_ipsa") else ""
        print(f"      {emoji} {rel.upper()}{ipsa} — {clasificacion['razon']}")

        if i < total:
            time.sleep(DELAY_ENTRE_LLAMADAS)

    print("\n" + "=" * 80)
    print("  RESUMEN")
    print("=" * 80)
    print(f"  🔴 Alta:  {contador['alta']}")
    print(f"  🟡 Media: {contador['media']}")
    print(f"  ⚪ Baja:  {contador['baja']}")
    print(f"  Total:    {sum(contador.values())}")


if __name__ == "__main__":
    main()
