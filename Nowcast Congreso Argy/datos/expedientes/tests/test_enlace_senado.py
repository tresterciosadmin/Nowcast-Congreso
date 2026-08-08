"""Tests offline de datos/expedientes/src/enlace_senado.py — sin red, sin datos reales.

Cada test fija una forma REAL en que el enlace se puede romper. Un enlace que
matchea de más es peor que uno que matchea de menos: un falso positivo mete la
votación de otro proyecto en la cadena de dos cámaras y contamina
P(revisora | aprobó origen), que es justo lo que el módulo existe para medir.

    python datos/expedientes/tests/test_enlace_senado.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enlace_senado import (  # noqa: E402
    construir_cadena,
    construir_enlace,
    normalizar_expediente,
    prefijo,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ───────────────────────── normalización ─────────────────────────
print("normalizar_expediente")

check(normalizar_expediente("CD-38/22-PL") == "0038-CD-2022",
      "formato Senado con sufijo -PL")
check(normalizar_expediente("S-2234/22-PD") == "2234-S-2022",
      "formato Senado origen propio")
check(normalizar_expediente("PE-184/21-AC") == "0184-PE-2021",
      "formato Senado mensaje del Ejecutivo")
check(normalizar_expediente("1623-D-2018") == "1623-D-2018",
      "formato HCDN se conserva")
check(normalizar_expediente("16-D-2018") == "0016-D-2018",
      "HCDN con número corto se rellena a 4 dígitos")
check(normalizar_expediente("0016-PE-2019") == "0016-PE-2019",
      "HCDN del Ejecutivo")
# La canónica mezcla año de 4 y de 2 dígitos según la fuente. Exigir 4 dejaba
# 1.628 actas de Diputados sin enlazar; lo detectó la corrida real del 08-08.
check(normalizar_expediente("5094-D-18") == "5094-D-2018",
      "HCDN con año de 2 dígitos")
check(normalizar_expediente("82-S-17") == "0082-S-2017",
      "HCDN corto con año de 2 dígitos")
check(normalizar_expediente("16-JGM-11") == "0016-JGM-2011",
      "HCDN con letra de 3 caracteres (Jefatura de Gabinete)")
check(normalizar_expediente("  cd-38/22  ") == "0038-CD-2022",
      "tolera minúsculas y espacios")

# Lo que NO debe parsear: ante la duda, None.
for basura in [None, "", "  ", "sin datos", "NAN", "-", "varios", "38/22",
               "expediente 38", float("nan")]:
    check(normalizar_expediente(basura) is None,
          f"basura {basura!r} debe dar None, no un match inventado")

check(prefijo("0038-CD-2022") == "CD", "prefijo CD")
check(prefijo(None) is None, "prefijo de None")
check(prefijo("cualquiera") is None, "prefijo de algo mal formado")


# ───────────────────────── fixtures ─────────────────────────
def fixture():
    actas = pd.DataFrame([
        # cadena completa: mismo proyecto votado en las dos cámaras
        {"acta_id": "dip:1", "camara": "diputados", "expediente": "7435-D-2018",
         "fecha": "2018-11-07", "resultado": "APROBADO"},
        {"acta_id": "sen:1", "camara": "senado", "expediente": "CD-57/18-PL",
         "fecha": "2018-12-05", "resultado": "APROBADO"},
        # sólo Senado, origen propio
        {"acta_id": "sen:2", "camara": "senado", "expediente": "S-108/18-PD",
         "fecha": "2018-08-01", "resultado": "APROBADO"},
        # expediente que no existe en el maestro
        {"acta_id": "sen:3", "camara": "senado", "expediente": "CD-999/18-PL",
         "fecha": "2018-09-01", "resultado": "RECHAZADO"},
        # expediente ilegible
        {"acta_id": "sen:4", "camara": "senado", "expediente": "sin datos",
         "fecha": "2018-09-02", "resultado": None},
        # acta sin expediente: no debe aparecer en la salida
        {"acta_id": "sen:5", "camara": "senado", "expediente": None,
         "fecha": "2018-09-03", "resultado": None},
        # dos votaciones del mismo proyecto en Diputados (vuelve en revisión)
        {"acta_id": "dip:2", "camara": "diputados", "expediente": "7435-D-2018",
         "fecha": "2019-02-20", "resultado": "APROBADO"},
    ])
    actas["fecha"] = pd.to_datetime(actas["fecha"])
    expedientes = pd.DataFrame([
        {"proyecto_id": "HCDN1", "camara_origen": "Diputados",
         "exp_diputados": "7435-D-2018", "exp_senado": "0057-CD-2018",
         "tipo": "LEY", "titulo": "cadena completa"},
        {"proyecto_id": "HCDN2", "camara_origen": "Senado",
         "exp_diputados": "0108-S-2018", "exp_senado": "0108-S-2018",
         "tipo": "LEY", "titulo": "origen senado"},
    ])
    return actas, expedientes


print("\nconstruir_enlace")
actas, expedientes = fixture()
enl = construir_enlace(actas, expedientes)

check(len(enl) == 6, f"las actas sin expediente se excluyen (esperaba 6, dio {len(enl)})")
check(set(enl["acta_id"]) == {"dip:1", "dip:2", "sen:1", "sen:2", "sen:3", "sen:4"},
      "conjunto de actas con expediente")

por_acta = enl.set_index("acta_id")
check(por_acta.loc["dip:1", "proyecto_id"] == "HCDN1", "acta de Diputados enlaza por exp_diputados")
check(por_acta.loc["sen:1", "proyecto_id"] == "HCDN1",
      "acta del Senado enlaza al MISMO proyecto por la numeración CD")
check(por_acta.loc["sen:1", "metodo"] == "exp_senado", "método correcto para el Senado")
check(bool(por_acta.loc["sen:1", "es_cruce"]) is True, "prefijo CD marca cruce entre cámaras")
check(bool(por_acta.loc["sen:2", "es_cruce"]) is False, "prefijo S no es cruce")
check(pd.isna(por_acta.loc["sen:3", "proyecto_id"]),
      "expediente inexistente NO debe enlazar (falso positivo)")
check(pd.isna(por_acta.loc["sen:4", "proyecto_id"]), "expediente ilegible no enlaza")
check(por_acta.loc["sen:4", "clave"] is None, "expediente ilegible deja clave nula")

print("\nambigüedad: una clave que apunta a dos proyectos NO debe enlazar")
amb = pd.concat([expedientes, pd.DataFrame([{
    "proyecto_id": "HCDN9", "camara_origen": "Diputados",
    "exp_diputados": "9999-D-2018", "exp_senado": "0057-CD-2018",  # choca con HCDN1
    "tipo": "LEY", "titulo": "duplicado"}])], ignore_index=True)
enl_amb = construir_enlace(actas, amb).set_index("acta_id")
check(pd.isna(enl_amb.loc["sen:1", "proyecto_id"]),
      "clave ambigua se descarta en vez de elegir una al azar")

print("\nconstruir_cadena")
cad = construir_cadena(enl, expedientes).set_index("proyecto_id")
check(int(cad.loc["HCDN1", "n_camaras"]) == 2, "HCDN1 tiene votación en las dos cámaras")
check(int(cad.loc["HCDN2", "n_camaras"]) == 1, "HCDN2 sólo en una")
check(cad.loc["HCDN1", "acta_sen"] == "sen:1", "acta del Senado en la cadena")
check(cad.loc["HCDN1", "acta_dip"] == "dip:2",
      "con dos votaciones en la misma cámara se toma la ÚLTIMA")
check(int((cad["n_camaras"] == 2).sum()) == 1, "una sola cadena completa en la fixture")

print("\nrobustez")
try:
    construir_enlace(pd.DataFrame({"acta_id": ["x"]}), expedientes)
    check(False, "faltar columnas debe levantar ValueError")
except ValueError:
    check(True, "faltar columnas levanta ValueError con mensaje claro")

vacio = construir_enlace(actas.iloc[0:0].copy(), expedientes)
check(len(vacio) == 0, "entrada vacía devuelve salida vacía, no rompe")

sin_col = expedientes.drop(columns=["exp_senado"])
enl_sc = construir_enlace(actas, sin_col).set_index("acta_id")
check(pd.isna(enl_sc.loc["sen:1", "proyecto_id"]),
      "si falta exp_senado el módulo sigue corriendo y no enlaza el Senado")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
