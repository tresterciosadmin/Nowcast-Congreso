"""Tests offline de datos/expedientes/src/votacion_por_articulo.py — sin red.

Casos que ya rompieron algo una vez en este repo, o que rompería este módulo
si se reimplementara mal: la decisiva tiene que coincidir con la que ya usa
`cadena_camaras.parquet` (misma función, no una copia), y NINGUNA fila se
puede perder — al revés de `elegir_votacion`, acá "agregar, no reemplazar" es
el contrato.

    python datos/expedientes/tests/test_votacion_por_articulo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from votacion_por_articulo import construir, _resultado_clase  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ───────────────────────── _resultado_clase ─────────────────────────
print("_resultado_clase")
check(_resultado_clase("AFIRMATIVO") == "AFIRMATIVO", "mayúscula")
check(_resultado_clase("afirmativo") == "AFIRMATIVO", "minúscula")
check(_resultado_clase("afirmativa") == "AFIRMATIVO", "afirmativa (fem)")
check(_resultado_clase("NEGATIVO") == "NEGATIVO", "negativo")
check(_resultado_clase("negativa") == "NEGATIVO", "negativa (fem)")
check(_resultado_clase("NEGATIVO - CANCELADA LEV.VOT.") == "NEGATIVO", "negativo con sufijo")
check(_resultado_clase("NEGATIVO - EMPATE") == "NEGATIVO",
      "NEGATIVO - EMPATE: el resultado oficial (negativo) manda sobre la anotación")
check(_resultado_clase("EMPATE") == "EMPATE", "empate solo")
check(_resultado_clase("") == "OTRO", "vacío -> OTRO, no se adivina")
check(_resultado_clase(None) == "OTRO", "None -> OTRO")
check(_resultado_clase("cancelada lev.vot.") == "OTRO", "sin afirmativo/negativo -> OTRO")


# ───────────────────────── fixture: caso Ley Bases simplificado ──────
def fixture_ley_bases() -> pd.DataFrame:
    """3 actas: general OK, un artículo se cae, otro pasa. Reproduce en
    miniatura lo que pasó el 06-02-2024."""
    return pd.DataFrame([
        {"proyecto_id": "HCDN_TEST", "camara": "diputados", "acta_id": "a1",
         "fecha": "2024-02-02", "resultado": "afirmativo",
         "titulo": "LEY DE BASES. VOT. EN GENERAL."},
        {"proyecto_id": "HCDN_TEST", "camara": "diputados", "acta_id": "a2",
         "fecha": "2024-02-06", "resultado": "negativo",
         "titulo": "LEY DE BASES. TITULO II. CAPITULO I. ART. 5 INCISO A."},
        {"proyecto_id": "HCDN_TEST", "camara": "diputados", "acta_id": "a3",
         "fecha": "2024-02-06", "resultado": "afirmativo",
         "titulo": "LEY DE BASES. TITULO II. CAPITULO I. ART. 6."},
    ])


print("\nconstruir() — caso Ley Bases simplificado")
res = construir(fixture_ley_bases())
check(len(res) == 3, "ninguna fila se pierde (3 actas -> 3 filas)")
check(set(res["acta_id"]) == {"a1", "a2", "a3"}, "las tres actas siguen presentes")

dec = res[res["es_decisiva"]]
check(len(dec) == 1, "exactamente una decisiva por (proyecto, camara)")
check(dec.iloc[0]["acta_id"] == "a1", "la decisiva es la general (a1), no un artículo")
check(dec.iloc[0]["tipo_votacion"] == "general", "tipo_votacion de la decisiva")

no_dec = res[~res["es_decisiva"]]
check(no_dec["tipo_votacion"].isna().all(), "las no-decisivas no llevan tipo_votacion")
check(set(no_dec["acta_id"]) == {"a2", "a3"}, "a2 y a3 quedan como NO decisivas (antes se perdían)")

part = res[res["es_particular"]]
check(set(part["acta_id"]) == {"a2", "a3"}, "a2 y a3 matchean es_particular (tienen ARTICULO/TITULO/CAPITULO)")
check(not res.loc[res["acta_id"] == "a1", "es_particular"].iloc[0], "la general NO es particular")

check((res["n_actas_grupo"] == 3).all(), "n_actas_grupo cuenta el grupo entero")

a2 = res[res["acta_id"] == "a2"].iloc[0]
check(a2["resultado_clase"] == "NEGATIVO", "el artículo que se cae queda NEGATIVO")
a3 = res[res["acta_id"] == "a3"].iloc[0]
check(a3["resultado_clase"] == "AFIRMATIVO", "el artículo que pasa queda AFIRMATIVO")


# ───────────────────────── caso trivial: una sola acta ───────────────
print("\nconstruir() — proyecto con una sola acta (caso mayoritario, 85,6%)")
uno = pd.DataFrame([
    {"proyecto_id": "HCDN_UNICA", "camara": "senado", "acta_id": "b1",
     "fecha": "2020-05-01", "resultado": "AFIRMATIVO", "titulo": "Proyecto X"},
])
res1 = construir(uno)
check(len(res1) == 1, "una acta -> una fila")
check(bool(res1.iloc[0]["es_decisiva"]), "la única acta es decisiva")
check(res1.iloc[0]["n_actas_grupo"] == 1, "n_actas_grupo=1")


# ───────────────────────── no pierde filas con proyecto_id repetido
#                             en DOS cámaras (grupos independientes) ──
print("\nconstruir() — el mismo proyecto_id en las dos cámaras no se mezcla")
dos_camaras = pd.DataFrame([
    {"proyecto_id": "HCDN_BICAM", "camara": "diputados", "acta_id": "c1",
     "fecha": "2021-01-01", "resultado": "afirmativo", "titulo": "X en general"},
    {"proyecto_id": "HCDN_BICAM", "camara": "diputados", "acta_id": "c2",
     "fecha": "2021-01-02", "resultado": "negativo", "titulo": "X articulo 1"},
    {"proyecto_id": "HCDN_BICAM", "camara": "senado", "acta_id": "c3",
     "fecha": "2021-02-01", "resultado": "afirmativo", "titulo": "X en general"},
])
res2 = construir(dos_camaras)
check(len(res2) == 3, "3 actas -> 3 filas, ninguna cámara pisa a la otra")
dec2 = res2[res2["es_decisiva"]]
check(len(dec2) == 2, "una decisiva POR CADA (proyecto, camara): dos grupos, dos decisivas")
check(set(dec2["acta_id"]) == {"c1", "c3"}, "la decisiva de cada cámara es su propia general")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
