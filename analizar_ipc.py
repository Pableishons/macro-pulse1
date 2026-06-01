# analizar_ipc.py
# Toma el último dato del IPC desde BCCh y lo procesa con Gemini.

import os
import json
from google import genai
from dotenv import load_dotenv
from monitor_bcch import consultar_serie

# Cargar credenciales
load_dotenv()

# Configurar cliente Gemini
cliente = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# El Template #3 que validamos juntos para series económicas
PROMPT_TEMPLATE = """Eres un analista de inversiones senior de un banco chileno
enfocado en segmento alto patrimonio. Acabas de recibir un nuevo dato económico.

CONTEXTO DEL BANCO:
- Productos: DAP, FFMM, Corredora de Bolsa, APV
- Cliente objetivo: alto patrimonio, decisor informado
- Audiencia: Pablo (Segment Manager) y ejecutivos de cuenta

REGLAS DE ESCRITURA:
- Lo más importante: comparar contra (a) expectativa de mercado, (b) proyección BCCh,
  (c) mes anterior. La 'sorpresa' vale más que el nivel absoluto.
- Cuantificar la implicancia para tasas (pb), tipo de cambio, UF
- Si el dato cambia la lectura de la próxima RPM, decirlo explícito
- NUNCA inventar nombres específicos de FFMM; usar categorías genéricas
- Versión interna: técnica. Forwardeable: 3-4 líneas planas
- Resumen e interpretación: máximo 4 frases cortas cada uno

DATO NUEVO:
- Indicador: {indicador}
- Valor: {valor_actual}%
- Fecha: {fecha_actual}

CONTEXTO HISTÓRICO:
- Mes anterior: {fecha_anterior}, {valor_anterior}%
- Variación vs mes anterior: {variacion_pb} pb

EXPECTATIVAS PREVIAS:
- Consenso mercado (estimado): {consenso}
- Proyección IPoM más reciente: 4,0% para diciembre 2026

Devuelve únicamente este JSON (sin texto adicional, sin markdown):
{{
  "titular": "máx 8 palabras",
  "tipo_sorpresa": "muy_positiva | positiva | en_linea | negativa | muy_negativa",
  "urgencia": "alta | media | baja",
  "version_interna": {{
    "resumen": "el número y la sorpresa, 2 frases",
    "interpretacion": "qué significa, mecanismo, implicancia para próxima RPM, max 4 frases",
    "acciones": {{
      "DAP": "qué hacer + cifra + por qué",
      "FFMM": "idem",
      "Corredora": "idem"
    }},
    "implicancia_uf": "movimiento esperado UF próximo mes o null",
    "oportunidad_adicional": "ángulo extra o null",
    "riesgos": "qué cambiaría la lectura"
  }},
  "version_forwardeable": "3-4 líneas con cifras",
  "tags": ["..."]
}}
"""


def analizar_ipc():
    """Trae el IPC desde BCCh y lo procesa con Gemini."""

    print("📥 Trayendo último dato del IPC desde BCCh...")
    datos = consultar_serie("F074.IPC.VAR.Z.Z.C.M")

    if datos is None:
        print("❌ No se pudo obtener el IPC")
        return

    # Calcular variación en puntos base
    variacion_pb = (datos["valor_actual"] - datos["valor_anterior"]) * 100

    print(f"   IPC {datos['fecha_actual']}: {datos['valor_actual']}%")
    print(
        f"   IPC anterior {datos['fecha_anterior']}: {datos['valor_anterior']}%")
    print(f"   Variación: {variacion_pb:+.0f} pb\n")

    # Construir el prompt con los datos reales
    prompt = PROMPT_TEMPLATE.format(
        indicador="IPC variación mensual",
        valor_actual=datos["valor_actual"],
        fecha_actual=datos["fecha_actual"],
        valor_anterior=datos["valor_anterior"],
        fecha_anterior=datos["fecha_anterior"],
        variacion_pb=f"{variacion_pb:+.0f}",
        consenso="0,8% - 1,0% (estimado base IPoM)",
    )

    print("🤖 Enviando a Gemini para análisis...")
    respuesta = cliente.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    print("\n" + "=" * 70)
    print("  RESPUESTA DE GEMINI")
    print("=" * 70)
    print(respuesta.text)

    # Intentar parsear como JSON para validar estructura
    try:
        # Limpiamos posibles ```json al inicio y ``` al final
        texto_limpio = respuesta.text.strip()
        if texto_limpio.startswith("```"):
            texto_limpio = texto_limpio.split("```")[1]
            if texto_limpio.startswith("json"):
                texto_limpio = texto_limpio[4:]
            texto_limpio = texto_limpio.strip()

        analisis = json.loads(texto_limpio)
        print("\n✅ JSON válido. Análisis estructurado disponible.")
        print(f"\n📌 Titular: {analisis['titular']}")
        print(f"📌 Urgencia: {analisis['urgencia']}")
        print(f"📌 Sorpresa: {analisis['tipo_sorpresa']}")
    except json.JSONDecodeError as e:
        print(f"\n⚠️ La respuesta no es JSON válido: {e}")


if __name__ == "__main__":
    analizar_ipc()
