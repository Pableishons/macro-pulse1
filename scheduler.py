# scheduler.py
# Orquestador que ejecuta todo el pipeline de Macro Pulse.
# Diseñado para correr cada 15 minutos en Railway.

import sys
import traceback
from datetime import datetime


def log(mensaje):
    """Imprime con timestamp para trazabilidad en Railway logs."""
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ahora}] {mensaje}", flush=True)


def ejecutar_paso(nombre, funcion_main):
    """Ejecuta un paso del pipeline con manejo de errores."""
    log(f"▶️  Iniciando: {nombre}")
    try:
        funcion_main()
        log(f"✅ Completado: {nombre}")
        return True
    except Exception as e:
        log(f"❌ Error en {nombre}: {e}")
        traceback.print_exc()
        return False


def main():
    log("=" * 60)
    log("MACRO PULSE — PIPELINE COMPLETO")
    log("=" * 60)

    # Importamos solo cuando se ejecuta (evita errores al cargar)
    from guardar_datos import main as guardar_series
    from guardar_hechos import main as guardar_hechos
    from analizar_pendientes import main as filtrar_relevancia
    from analisis_profundo import main as analisis_completo

    pasos_ok = 0
    pasos_total = 4

    # Paso 1: actualizar series BCCh
    if ejecutar_paso("1/4 Series BCCh", guardar_series):
        pasos_ok += 1

    # Paso 2: capturar hechos esenciales CMF
    if ejecutar_paso("2/4 Hechos CMF", guardar_hechos):
        pasos_ok += 1

    # Paso 3: filtrar relevancia con Gemini Flash-Lite
    if ejecutar_paso("3/4 Filtro IA", filtrar_relevancia):
        pasos_ok += 1

    # Paso 4: análisis profundo de hechos alta/media
    if ejecutar_paso("4/4 Análisis profundo", analisis_completo):
        pasos_ok += 1

    log("=" * 60)
    log(f"PIPELINE FINALIZADO: {pasos_ok}/{pasos_total} pasos exitosos")
    log("=" * 60)

    # Si algún paso falló, salimos con código de error (Railway lo registra)
    if pasos_ok < pasos_total:
        sys.exit(1)


if __name__ == "__main__":
    main()
