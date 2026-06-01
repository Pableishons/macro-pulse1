# prueba_bcch.py
# Primer script: conectarse a la API del Banco Central y traer el dólar observado.

import os
import requests
from dotenv import load_dotenv

# Cargar las credenciales desde el archivo .env
load_dotenv()

# Leer las credenciales en variables de Python
usuario = os.getenv("BCCH_USER")
password = os.getenv("BCCH_PASS")

# La URL base de la API del Banco Central
url_base = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"

# Los parámetros que le pasamos a la API
parametros = {
    "user": usuario,
    "pass": password,
    "function": "GetSeries",
    "timeseries": "F073.TCO.PRE.Z.D"
}

# Hacer la llamada a la API
print("Conectando con el Banco Central...")
respuesta = requests.get(url_base, params=parametros)

# Convertir la respuesta de JSON a un diccionario de Python
datos = respuesta.json()

# Mostrar si la consulta fue exitosa
print(f"Código de respuesta: {datos['Codigo']}")
print(f"Descripción: {datos['Descripcion']}")

# Si fue exitosa, mostrar el último valor disponible
if datos["Codigo"] == 0:
    serie = datos["Series"]
    observaciones = serie["Obs"]
    ultimo_dato = observaciones[-1]

    print(f"\nSerie: {serie['descripEsp']}")
    print(f"Total de observaciones históricas: {len(observaciones)}")
    print(f"\nÚltimo dato disponible:")
    print(f"  Fecha: {ultimo_dato['indexDateString']}")
    print(f"  Valor: ${ultimo_dato['value']} CLP/USD")
