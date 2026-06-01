# monitor_bcch.py
# Monitor de series económicas del Banco Central.
# Consulta todas las series del catálogo y muestra último valor + variación.

import os
import requests
from dotenv import load_dotenv
from series_bcch import SERIES  # Importamos el catálogo

# Cargar credenciales
load_dotenv()
usuario = os.getenv("BCCH_USER")
password = os.getenv("BCCH_PASS")

# URL base de la API
URL_BASE = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"


def consultar_serie(codigo):
    """
    Consulta una serie del BCCh y devuelve los últimos dos datos disponibles.
    Si algo falla, devuelve None.
    """
    parametros = {
        "user": usuario,
        "pass": password,
        "function": "GetSeries",
        "timeseries": codigo,
    }

    respuesta = requests.get(URL_BASE, params=parametros)
    datos = respuesta.json()

    # Si la API devolvió error, mostramos el detalle y retornamos None
    if datos.get("Codigo") != 0:
        print(
            f"   ⚠️ API respondió: Código {datos.get('Codigo')} - {datos.get('Descripcion')}")
        return None

    observaciones = datos["Series"]["Obs"]

    # Filtramos solo las observaciones con valor válido
    validas = [obs for obs in observaciones if obs["statusCode"] == "OK"]

    if len(validas) < 2:
        return None

    # Tomamos los dos últimos valores válidos
    actual = validas[-1]
    anterior = validas[-2]

    return {
        "fecha_actual": actual["indexDateString"],
        "valor_actual": float(actual["value"]),
        "fecha_anterior": anterior["indexDateString"],
        "valor_anterior": float(anterior["value"]),
    }


def mostrar_serie(serie, datos):
    """Imprime una serie en formato legible según su tipo."""
    nombre = serie["nombre"]
    unidad = serie["unidad"]
    tipo = serie.get("tipo", "nivel")  # Por defecto asumimos "nivel"

    if datos is None:
        print(f"❌ {nombre}: error al consultar")
        return

    actual = datos["valor_actual"]
    anterior = datos["valor_anterior"]
    var_abs = actual - anterior

    # Flecha según si subió, bajó o se mantuvo
    if var_abs > 0:
        flecha = "↑"
    elif var_abs < 0:
        flecha = "↓"
    else:
        flecha = "→"

    print(f"\n📊 {nombre}")
    print(
        f"   Valor actual:    {actual:,.2f} {unidad}  ({datos['fecha_actual']})")
    print(
        f"   Valor anterior:  {anterior:,.2f} {unidad}  ({datos['fecha_anterior']})")

    if tipo == "tasa":
        # Para tasas: expresamos en puntos base (pb) y puntos porcentuales (pp)
        var_pb = var_abs * 100  # 0.25% = 25 pb
        print(
            f"   Variación:       {flecha} {var_abs:+.2f} pp  ({var_pb:+.0f} pb)")
    else:
        # Para niveles: variación absoluta y porcentual
        if anterior != 0:
            var_pct = (var_abs / anterior) * 100
        else:
            var_pct = 0
        print(
            f"   Variación:       {flecha} {var_abs:+,.2f}  ({var_pct:+.2f}%)")


def main():
    """Función principal: consulta todas las series del catálogo."""
    print("=" * 60)
    print("  MONITOR DE SERIES BCCh")
    print("=" * 60)

    for serie in SERIES:
        datos = consultar_serie(serie["codigo"])
        mostrar_serie(serie, datos)

    print("\n" + "=" * 60)


# Esta línea hace que main() solo se ejecute si corremos este archivo
# directamente (no si lo importamos desde otro lugar)
if __name__ == "__main__":
    main()
