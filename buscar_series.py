# buscar_series.py
# Búsqueda específica para encontrar IMACEC e IPC vigentes.

import os
import bcchapi
from dotenv import load_dotenv

load_dotenv()

siete = bcchapi.Siete(os.getenv("BCCH_USER"), os.getenv("BCCH_PASS"))

print("\n" + "=" * 70)
print("  Buscando: IMACEC empalmado base 2018")
print("=" * 70)

# Buscamos "Imacec" sin filtros y revisamos TODOS los resultados mensuales
resultados = siete.buscar("Imacec")
mensuales = resultados[resultados["frequencyCode"] == "MONTHLY"]

# Filtramos solo los que contienen "2018" o "empalmada" en el nombre
for _, fila in mensuales.iterrows():
    nombre = str(fila["spanishTitle"]).lower()
    if "2018" in nombre or "empalmada" in nombre:
        print(f"\n  Código: {fila['seriesId']}")
        print(f"  Nombre: {fila['spanishTitle']}")

print("\n" + "=" * 70)
print("  Buscando: IPC (índice y variaciones)")
print("=" * 70)

# Para IPC probamos varios términos
for termino in ["IPC general", "IPC sin volátiles", "IPC subyacente"]:
    print(f"\n  --- Búsqueda: '{termino}' ---")
    resultados = siete.buscar(termino)
    mensuales = resultados[resultados["frequencyCode"] == "MONTHLY"].head(10)

    if len(mensuales) == 0:
        print("    (sin resultados)")
        continue

    for _, fila in mensuales.iterrows():
        nombre = str(fila["spanishTitle"]).lower()
        # Solo mostramos los que parecen ser dato real, no expectativa
        if "expectativa" not in nombre and "encuesta" not in nombre:
            print(f"\n    Código: {fila['seriesId']}")
            print(f"    Nombre: {fila['spanishTitle']}")
