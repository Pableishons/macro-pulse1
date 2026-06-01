# series_bcch.py
# Catálogo de series del Banco Central que vamos a monitorear.

SERIES = [
    {
        "codigo": "F073.TCO.PRE.Z.D",
        "nombre": "Dólar observado",
        "unidad": "CLP/USD",
        "frecuencia": "diaria",
        "tipo": "nivel",
    },
    {
        "codigo": "F073.UFF.PRE.Z.D",
        "nombre": "UF",
        "unidad": "CLP",
        "frecuencia": "diaria",
        "tipo": "nivel",
    },
    {
        "codigo": "F022.TPM.TIN.D001.NO.Z.D",
        "nombre": "Tasa de Política Monetaria (TPM)",
        "unidad": "%",
        "frecuencia": "diaria",
        "tipo": "tasa",
    },
    {
        "codigo": "F074.IPC.VAR.Z.Z.C.M",
        "nombre": "IPC variación mensual",
        "unidad": "%",
        "frecuencia": "mensual",
        "tipo": "tasa",
    },
    {
        "codigo": "F032.IMC.IND.Z.Z.EP18.Z.Z.1.M",
        "nombre": "IMACEC (empalmado, desestacionalizado)",
        "unidad": "índice 2018=100",
        "frecuencia": "mensual",
        "tipo": "nivel",
    },
    # TODO: encontrar códigos correctos del IPC 12 meses y del IPC sin volátiles
    # El IPC sin volátiles ahora tiene canasta nueva (2024+) con nomenclatura distinta
]
