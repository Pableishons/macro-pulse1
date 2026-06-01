# analisis_profundo.py
# Toma hechos clasificados como alta/media y genera análisis completo con Template #2.
# Usa Gemini 2.5 Flash (más capaz que Flash-Lite).

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from dotenv import load_dotenv
from db import get_cliente

load_dotenv()
cliente_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DELAY_ENTRE_LLAMADAS = 1
MAX_POR_CORRIDA = 20

# Template #2 — Hechos esenciales CMF (el que validamos en sesiones anteriores)
PROMPT_ANALISIS = """Eres un analista de inversiones senior de un banco chileno
enfocado en segmento alto patrimonio. Acabas de recibir un hecho esencial
reportado a la CMF.

CONTEXTO DEL BANCO:
- Productos principales afectados: Corredora de Bolsa, FFMM accionarios,
  FFMM de deuda corporativa
- Cliente objetivo: alto patrimonio con posiciones en acciones IPSA y mid caps

REGLAS DE ESCRITURA:
- Identifica el emisor y clasifica tipo de hecho (resultados, fusión/adquisición,
  dividendo, emisión, sanción, cambio directorio, contrato, otro)
- Magnitud esperada: alto (>5%), medio (2-5%), bajo (<2%), nulo
- Ventana crítica: pre-apertura, intradiario, semana, mensual
- Para 'acción corredora', bifurca: cliente CON el papel vs SIN
- NUNCA inventar nombres específicos de FFMM; usar categorías genéricas
- NUNCA inventar tickers; usar solo los explícitos en el hecho o IPSA obvios
- Versión interna: técnica con cifras. Forwardeable: 3-4 líneas

HECHO ESENCIAL:
Empresa: {empresa}
Materia: {materia}
Fecha: {fecha}
Contenido del documento:
{contenido}

Devuelve únicamente este JSON (sin texto adicional, sin markdown):
{{
  "titular": "máx 8 palabras, incluir emisor",
  "tipo_hecho": "categoría",
  "urgencia": "alta | media | baja",
  "magnitud_esperada": "alto | medio | bajo | nulo",
  "ventana_critica": "pre-apertura | intradiario | semana | mensual",
  "version_interna": {{
    "resumen": "qué pasó, máx 3 frases con cifras",
    "interpretacion": "qué significa, máx 4 frases",
    "accion_corredora": {{
      "tiene_el_papel": "qué decirle al cliente con posición",
      "no_tiene_el_papel": "qué decirle al cliente sin posición"
    }},
    "ffmm_relacionados": "categorías con exposición o null",
    "oportunidad_adicional": "ángulo extra o null",
    "riesgos": "qué podría cambiar la lectura"
  }},
  "version_forwardeable": "3-4 líneas con cifras y emisor",
  "tags": ["..."]
}}
"""


def descargar_contenido(url):
    """
    Descarga el contenido de un link CMF.
    Retorna texto plano o un mensaje de fallback si es PDF.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
        respuesta = requests.get(url, headers=headers, timeout=15)
        respuesta.raise_for_status()

        # Si es PDF, lo dejamos como "no procesable" por ahora
        content_type = respuesta.headers.get("Content-Type", "")
        if "pdf" in content_type.lower():
            return "[Documento en formato PDF, contenido no extraído]"

        # Si es HTML, extraemos el texto principal
        soup = BeautifulSoup(respuesta.text, "html.parser")

        # Limpiamos scripts, styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        texto = soup.get_text(separator="\n", strip=True)

        # Truncar a 4000 caracteres (más que suficiente para un hecho esencial)
        if len(texto) > 4000:
            texto = texto[:4000] + "... [truncado]"

        return texto if texto else "[Contenido vacío]"

    except Exception as e:
        return f"[Error al descargar: {str(e)[:60]}]"


def analizar_hecho(hecho):
    """Pasa el hecho por Gemini con Template #2."""
    print(f"      📥 Descargando contenido CMF...")
    contenido = descargar_contenido(hecho["link_cmf"])

    prompt = PROMPT_ANALISIS.format(
        empresa=hecho["empresa"],
        materia=hecho["materia"],
        fecha=hecho["fecha"],
        contenido=contenido,
    )

    try:
        respuesta = cliente_gemini.models.generate_content(
            model="gemini-2.5-flash",
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
        return {"error": f"No se pudo procesar: {str(e)[:100]}"}


def obtener_elegibles(limite):
    """Trae hechos alta/media sin análisis completo."""
    db = get_cliente()
    respuesta = db.table("hechos_esenciales") \
        .select("*") \
        .in_("relevancia", ["alta", "media"]) \
        .is_("analisis_completo", "null") \
        .order("creado_en", desc=True) \
        .limit(limite) \
        .execute()
    return respuesta.data


def guardar_analisis(numero_doc, analisis):
    """Guarda el JSON del análisis en Supabase."""
    db = get_cliente()
    db.table("hechos_esenciales") \
        .update({"analisis_completo": analisis}) \
        .eq("numero_doc", numero_doc) \
        .execute()


def main():
    print("=" * 80)
    print("  ANÁLISIS PROFUNDO — Template #2 (Gemini Flash)")
    print("=" * 80)

    elegibles = obtener_elegibles(limite=MAX_POR_CORRIDA)

    if not elegibles:
        print("\n✅ No hay hechos elegibles para análisis profundo.")
        return

    total = len(elegibles)
    print(f"\n📊 {total} hechos por analizar en profundidad")
    print(f"⏱️  Tiempo estimado: ~{total * 5} segundos\n")

    for i, hecho in enumerate(elegibles, 1):
        print(f"  [{i}/{total}] {hecho['empresa'][:50]} ({hecho['relevancia']})")

        analisis = analizar_hecho(hecho)

        if "error" in analisis:
            print(f"      ⚠️ {analisis['error']}")
        else:
            print(f"      ✅ {analisis.get('titular', '(sin titular)')}")

        guardar_analisis(hecho["numero_doc"], analisis)

        if i < total:
            time.sleep(DELAY_ENTRE_LLAMADAS)

    print("\n" + "=" * 80)
    print(f"  ✅ {total} análisis guardados en Supabase")
    print("=" * 80)


if __name__ == "__main__":
    main()
