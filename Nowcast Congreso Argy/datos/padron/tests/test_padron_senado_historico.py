"""Tests offline de datos/padron/src/padron_senado_historico.py — sin red.

El test central es el de reconciliación de nombres. Fija los CUATRO senadores
reales que rompieron el padrón el 2026-08-08:

  - VISCHI, ALEJANDRO EDUARDO  vs  "Eduardo Vischi"     -> SON el mismo
  - PAGOTTO, Carlos Juan       vs  "Juan Carlos Romero" -> NO lo son
  - BENSUSAN, Daniel Pablo     vs  "Pablo Daniel Blanco"-> NO lo son

Los dos últimos comparten dos nombres de pila. Una regla de "comparten 2
tokens" los fusiona, inventa un senador que no existe y le adjudica votos
ajenos. Por eso el apellido manda.

    python datos/padron/tests/test_padron_senado_historico.py
"""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from padron_senado_historico import (  # noqa: E402
    BANCAS_SENADO,
    composicion_a_fecha,
    construir,
    _fusionar_consecutivos,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def wiki(filas):
    return pd.DataFrame(filas, columns=["senador", "provincia", "bloque",
                                        "desde", "hasta", "fuente", "nota"])


def oficial(filas):
    return pd.DataFrame(filas, columns=["legislador", "distrito", "bloque",
                                        "desde", "hasta", "fuente", "nota"])


# ────────────── reconciliación de nombres ──────────────
print("reconciliación de identidades")

W = wiki([
    ["Eduardo Vischi", "CORRIENTES", "UCR", "2021-12-10", "2023-12-09", "wikipedia:2021-2023", ""],
    ["Juan Carlos Romero", "SALTA", "JUSTICIALISTA", "2021-12-10", "2023-12-09", "wikipedia:2021-2023", ""],
    ["Pablo Daniel Blanco", "TIERRA DEL FUEGO", "UCR", "2021-12-10", "2023-12-09", "wikipedia:2021-2023", ""],
])
O = oficial([
    ["VISCHI, ALEJANDRO EDUARDO", "CORRIENTES", "UCR", "2021-12-10", "2027-12-09", "oficial:nomina_senado", ""],
    ["PAGOTTO, CARLOS JUAN", "LA RIOJA", "LA LIBERTAD AVANZA", "2023-12-10", "2029-12-09", "oficial:nomina_senado", ""],
    ["BENSUSAN, DANIEL PABLO", "LA PAMPA", "JUSTICIALISTA", "2021-12-10", "2027-12-09", "oficial:nomina_senado", ""],
])
df = construir(W, O)

claves = set(df["clave"])
check(len(claves) == 5,
      f"3 wiki + 3 oficiales con 1 coincidencia real = 5 personas (dio {len(claves)})")

vischi = df[df["legislador"].str.contains("VISCHI", case=False)]
check(vischi["clave"].nunique() == 1, "Vischi queda con UNA sola clave")
check(vischi["legislador"].iloc[0] == "VISCHI, ALEJANDRO EDUARDO",
      "se conserva el nombre completo de la nómina oficial")

romero = df[df["legislador"].str.contains("ROMERO", case=False)]
pagotto = df[df["legislador"].str.contains("PAGOTTO", case=False)]
check(len(romero) == 1 and len(pagotto) == 1,
      "Romero y Pagotto siguen siendo DOS personas pese a compartir 'Carlos Juan'")
check(romero["clave"].iloc[0] != pagotto["clave"].iloc[0],
      "Romero y Pagotto no comparten clave")

blanco = df[df["legislador"].str.contains("BLANCO", case=False)]
bensusan = df[df["legislador"].str.contains("BENSUSAN", case=False)]
check(len(blanco) == 1 and len(bensusan) == 1,
      "Blanco y Bensusán siguen siendo DOS pese a compartir 'Daniel Pablo'")

# ────────────── no más de 72 bancas ──────────────
print("\ncontrol de bancas")
comp = composicion_a_fecha(df, "2022-06-01")
check(comp["clave"].duplicated().sum() == 0, "nadie ocupa dos bancas a la vez")
check(len(comp) <= BANCAS_SENADO, "nunca más de 72 bancas a una fecha")

check(len(composicion_a_fecha(df, "2019-01-01")) == 0,
      "antes de la cobertura no hay nadie (no se extrapola)")
check(len(composicion_a_fecha(df, "2022-06-01")) > 0, "en el medio sí hay composición")

# ────────────── fusión de tramos ──────────────
print("\nfusión de tramos consecutivos")
W2 = wiki([
    ["Ana Perez", "SALTA", "UCR", "2017-12-10", "2019-12-09", "wikipedia:2017-2019", ""],
    ["Ana Perez", "SALTA", "UCR", "2019-12-10", "2021-12-09", "wikipedia:2019-2021", ""],
    ["Ana Perez", "SALTA", "UCR", "2021-12-10", "2023-12-09", "wikipedia:2021-2023", ""],
])
d2 = construir(W2, oficial([]).astype(object))
check(len(d2) == 1, f"tres períodos de wiki con el mismo bloque = 1 mandato (dio {len(d2)})")
check(d2["desde"].iloc[0] == "2017-12-10" and d2["hasta"].iloc[0] == "2023-12-09",
      "el tramo fusionado va de punta a punta")

print("\ncambio de bloque: NO se fusiona")
W3 = wiki([
    ["Ana Perez", "SALTA", "UCR", "2017-12-10", "2019-12-09", "wikipedia:2017-2019", ""],
    ["Ana Perez", "SALTA", "JUSTICIALISTA", "2019-12-10", "2021-12-09", "wikipedia:2019-2021", ""],
])
d3 = construir(W3, oficial([]).astype(object))
check(len(d3) == 2, "cambiar de bloque parte el mandato en dos tramos")

# ────────────── linaje sensible a la época ──────────────
print("\nlinaje según la época (ADR-0005)")
W4 = wiki([
    ["Juan Lopez", "SALTA", "JUSTICIALISTA", "2005-12-10", "2011-12-09", "wikipedia:x", ""],
    ["Maria Diaz", "SALTA", "JUSTICIALISTA", "2016-12-10", "2018-12-09", "wikipedia:y", ""],
])
d4 = construir(W4, oficial([]).astype(object)).set_index("legislador")
check(d4.loc["Juan Lopez", "bloque_linaje"] == "FdT-UxP (kirchnerismo)",
      "JUSTICIALISTA en 2005 es kirchnerismo")
check(d4.loc["Maria Diaz", "bloque_linaje"] == "PERONISMO FEDERAL",
      "el MISMO bloque en 2016 es peronismo federal (ventana temporal)")

# ────────────── robustez ──────────────
print("\nrobustez")
malas = wiki([
    ["Ana Perez", "SALTA", "UCR", "2021-12-10", "2019-12-09", "wikipedia:x", ""],   # invertida
    ["Luis Gomez", "SALTA", "UCR", "no es fecha", "2023-12-09", "wikipedia:x", ""],  # ilegible
    ["Eva Ruiz", "SALTA", "UCR", "2021-12-10", "2023-12-09", "wikipedia:x", ""],     # buena
])
d5 = construir(malas, oficial([]).astype(object))
check(len(d5) == 1 and d5["legislador"].iloc[0] == "Eva Ruiz",
      "las fechas invertidas o ilegibles se descartan y el resto sigue")

try:
    construir(pd.DataFrame({"senador": ["x"]}), oficial([]).astype(object))
    check(False, "faltar columnas debe levantar ValueError")
except ValueError:
    check(True, "faltar columnas levanta ValueError con mensaje claro")

d6 = construir(W, O)
check(list(d6.columns) == ["legislador", "clave", "legislador_id", "camara",
                           "distrito", "bloque", "bloque_norm", "desde", "hasta",
                           "bloque_linaje", "fuente", "nota"],
      "el contrato de columnas es el mismo que padron_diputados.csv")
check((d6["camara"] == "senado").all(), "cámara siempre 'senado'")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
