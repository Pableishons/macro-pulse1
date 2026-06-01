# scraper_cmf.py
# Trae los hechos esenciales recientes de CMF (vía visfin.cl).

import requests
from bs4 import BeautifulSoup


URL_VISFIN = "https://www.visfin.cl/hechos-esenciales"


def obtener_hechos_esenciales(limite=10):
    """
    Trae los hechos esenciales más recientes desde visfin.cl.
    Retorna una lista de diccionarios con fecha, empresa, materia y link.
    """
    # Headers para que el servidor no nos rechace
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    print(f"📥 Descargando hechos esenciales desde visfin.cl...")
    respuesta = requests.get(URL_VISFIN, headers=headers, timeout=15)
    respuesta.raise_for_status()  # Lanza error si el servidor responde mal

    # Parsear el HTML con BeautifulSoup
    soup = BeautifulSoup(respuesta.text, "html.parser")

    # Buscar la tabla. En esta página hay una sola tabla principal.
    tabla = soup.find("table")
    if tabla is None:
        print("⚠️ No se encontró tabla en la página")
        return []

    # Obtener todas las filas, excepto la cabecera
    filas = tabla.find_all("tr")[1:]  # [1:] salta la cabecera

    hechos = []
    for fila in filas[:limite]:
        celdas = fila.find_all("td")
        if len(celdas) < 4:
            continue

        # Extraer el link al documento oficial CMF
        link_tag = celdas[3].find("a")
        link = link_tag["href"] if link_tag else None
        numero = link_tag.text.strip() if link_tag else None

        hechos.append({
            "fecha": celdas[0].text.strip(),
            "empresa": celdas[1].text.strip(),
            "materia": celdas[2].text.strip(),
            "numero_doc": numero,
            "link_cmf": link,
        })

    return hechos


def mostrar_hechos(hechos):
    """Imprime los hechos esenciales en formato legible."""
    print("\n" + "=" * 80)
    print(f"  HECHOS ESENCIALES CMF - últimos {len(hechos)}")
    print("=" * 80)

    for i, hecho in enumerate(hechos, 1):
        print(f"\n{i}. {hecho['fecha']}")
        print(f"   Empresa:  {hecho['empresa']}")
        print(f"   Materia:  {hecho['materia']}")
        print(f"   Doc CMF:  {hecho['numero_doc']}")


def main():
    hechos = obtener_hechos_esenciales(limite=10)
    if hechos:
        mostrar_hechos(hechos)
        print(f"\n✅ {len(hechos)} hechos esenciales obtenidos correctamente.")
    else:
        print("❌ No se obtuvieron hechos esenciales.")


if __name__ == "__main__":
    main()
