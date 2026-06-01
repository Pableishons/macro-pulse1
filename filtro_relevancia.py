# filtro_relevancia.py
# Clasifica hechos esenciales por relevancia usando Gemini Flash-Lite.
# Maneja rate limits del tier gratis con reintentos automáticos.

import os
import json
import time
import re
from google import genai
from dotenv import load_dotenv
from scraper_cmf import obtener_hechos_esenciales

# Cargar credenciales
load_dotenv()
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Configuración de rate limiting
DELAY_ENTRE_LLAMADAS = 8        # 8s entre cada llamada (margen vs 10/min real)
MAX_REINTENTOS = 2              # Si falla por 429, reintenta hasta 2 veces
# Si Gemini dice "espera X", usamos 45s para ir seguros
ESPERA_TRAS_429 = 45

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


def es_error_rate_limit(error_msg):
    """Detecta si el error es de rate limit (429)."""
    return "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg


def clasificar_hecho(hecho, reintentos=0):
    """Clasifica un hecho. Si choca con rate limit, espera y reintenta."""
    prompt = PROMPT_FILTRO.format(
        empresa=hecho["empresa"],
        materia=hecho["materia"],
        fecha=hecho["fecha"],
    )

    try:
        respuesta = cliente.models.generate_content(
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
        error_msg = str(e)

        # Si es rate limit y aún tenemos reintentos disponibles, esperamos
        if es_error_rate_limit(error_msg) and reintentos < MAX_REINTENTOS:
            print(
                f"      ⚠️ Rate limit alcanzado. Esperando {ESPERA_TRAS_429}s...")
            time.sleep(ESPERA_TRAS_429)
            print(
                f"      🔄 Reintentando (intento {reintentos + 1}/{MAX_REINTENTOS})...")
            return clasificar_hecho(hecho, reintentos + 1)

        # Si no es rate limit, o ya gastamos los reintentos, marcamos como baja
        return {
            "relevancia": "baja",
            "razon": f"Error: {error_msg[:60]}",
            "es_ipsa": False,
        }


def main():
    """Pipeline: obtener hechos + clasificar con manejo de rate limits."""

    print("=" * 80)
    print("  FILTRO DE RELEVANCIA - HECHOS ESENCIALES CMF")
    print("=" * 80)

    # Procesamos 15 (menos que 20, para no chocar con límite diario)
    hechos = obtener_hechos_esenciales(limite=15)
    if not hechos:
        print("❌ No hay hechos para procesar.")
        return

    total = len(hechos)
    tiempo_estimado = total * DELAY_ENTRE_LLAMADAS
    print(f"\n🤖 Clasificando {total} hechos con Gemini Flash-Lite...")
    print(f"⏱️  Esperando {DELAY_ENTRE_LLAMADAS}s entre llamadas")
    print(
        f"⏱️  Tiempo estimado: ~{tiempo_estimado // 60} min {tiempo_estimado % 60}s")
    print(f"🔄  Reintentos automáticos si choca con rate limit\n")

    resultados = []
    for i, hecho in enumerate(hechos, 1):
        print(f"  [{i}/{total}] {hecho['empresa'][:50]}...")
        clasificacion = clasificar_hecho(hecho)
        resultados.append({**hecho, **clasificacion})

        if i < total:
            time.sleep(DELAY_ENTRE_LLAMADAS)

    # Mostrar agrupados por relevancia
    print("\n" + "=" * 80)
    print("  RESULTADOS")
    print("=" * 80)

    for nivel in ["alta", "media", "baja"]:
        del_nivel = [r for r in resultados if r["relevancia"] == nivel]
        emoji = {"alta": "🔴", "media": "🟡", "baja": "⚪"}[nivel]

        print(f"\n{emoji} RELEVANCIA {nivel.upper()} ({len(del_nivel)} hechos)")
        print("-" * 80)

        for r in del_nivel:
            ipsa_tag = " [IPSA]" if r.get("es_ipsa") else ""
            print(f"  • {r['empresa']}{ipsa_tag}")
            print(f"    Materia: {r['materia']}")
            print(f"    Razón:   {r['razon']}")
            print()


if __name__ == "__main__":
    main()
