"""Tests sin red de datos/export/src/export_base.py (datos sintéticos).
Correr: python datos/export/tests/test_export.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import export_base as E  # noqa: E402

OK = 0


def check(nombre: str, cond: bool) -> None:
    global OK
    assert cond, f"FALLA: {nombre}"
    OK += 1
    print(f"  ok: {nombre}")


def main() -> None:
    # gobiernos: cortes exactos
    g = E.gobierno(pd.Series(["2001-12-20", "2001-12-21", "2003-05-24", "2003-05-25",
                              "2015-12-09", "2015-12-10", "2023-12-10", None]),
                   pd.Series(["x", "x", "x", "x", "x", "x", "x", "manual_2026"]))
    check("20-dic-2001 es De la Rúa", g.iloc[0] == "1999-2001_DeLaRua")
    check("21-dic-2001 es Duhalde (transición)", g.iloc[1] == "2002-2003_Duhalde")
    check("24-may-2003 es Duhalde", g.iloc[2] == "2002-2003_Duhalde")
    check("25-may-2003 es Kirchner", g.iloc[3] == "2003-2007_Kirchner")
    check("09-dic-2015 es CFK-2", g.iloc[4] == "2011-2015_CFK-2")
    check("10-dic-2015 es Macri", g.iloc[5] == "2015-2019_Macri")
    check("10-dic-2023 es Milei", g.iloc[6] == "2023-2027_Milei")
    check("manual_2026 sin fecha es Milei", g.iloc[7] == "2023-2027_Milei")

    # normalización de mayorías
    n = E.normalizar_mayoria(pd.Series(["Más de la mitad", None, "Dos tercios",
                                        "DOS TERCIOS MIEMBROS DEL CUERPO", "Tres cuartos",
                                        "MAS 1/2 MIEMBROS DEL CUERPO", "La mitad más uno", "ABSOLUTA"]))
    check("'Más de la mitad' → SIMPLE", n.iloc[0] == "SIMPLE")
    check("sin dato → SIMPLE", n.iloc[1] == "SIMPLE")
    check("'Dos tercios' → DOS_TERCIOS (emitidos)", n.iloc[2] == "DOS_TERCIOS")
    check("'2/3 del cuerpo' → DOS_TERCIOS_CUERPO", n.iloc[3] == "DOS_TERCIOS_CUERPO")
    check("'Tres cuartos' → TRES_CUARTOS", n.iloc[4] == "TRES_CUARTOS")
    check("'1/2 miembros del cuerpo' → ABSOLUTA", n.iloc[5] == "ABSOLUTA")
    check("'La mitad más uno' → ABSOLUTA", n.iloc[6] == "ABSOLUTA")
    check("'ABSOLUTA' → ABSOLUTA", n.iloc[7] == "ABSOLUTA")

    # disputada: ejemplos de Valle
    a = pd.DataFrame({
        "acta_id": ["a1", "a2", "a3", "a4", "a5"],
        "camara": ["diputados"] * 5,
        # margen = 5% de los EMITIDOS (decisión Valle)
        # a1: 257 emitidos, simple, rechazo 57-200 (banda ±12.85) → NO disputada
        # a2: aprobación 130-127 simple (umbral 128.5, banda ±12.85) → disputada
        # a3: absoluta con 132 afirm (umbral 129, emitidos 232, banda ±11.6) → disputada
        # a4: absoluta con 150 afirm (umbral 129, emitidos 230, banda ±11.5) → NO disputada
        # a5: dos tercios de 240 emitidos (umbral 160) con 158 afirm (banda ±12) → disputada
        "n_afirmativos": [57, 130, 132, 150, 158],
        "n_negativos": [200, 127, 100, 80, 82],
        "n_abstenciones": [0] * 5, "n_ausentes": [0] * 5,
        "tipo_mayoria_norm": ["SIMPLE", "SIMPLE", "ABSOLUTA", "ABSOLUTA", "DOS_TERCIOS"],
    })
    d = E.calcular_disputada(a).set_index("acta_id")
    check("rechazo 57-200 simple NO disputada", d.loc["a1", "disputada"] == 0)
    check("aprobación 130 simple SÍ disputada (ej. de Valle)", d.loc["a2", "disputada"] == 1)
    check("umbral absoluta Dip = 129", d.loc["a3", "umbral_aprobacion"] == 129)
    check("132 vs absoluta SÍ disputada", d.loc["a3", "disputada"] == 1)
    check("150 vs absoluta NO disputada", d.loc["a4", "disputada"] == 0)
    check("dos tercios: umbral 160 sobre 240 emitidos", d.loc["a5", "umbral_aprobacion"] == 160)
    check("158 vs 160 SÍ disputada", d.loc["a5", "disputada"] == 1)
    check("margen_votos con signo: a2=+1.5", d.loc["a2", "margen_votos"] == 1.5)
    check("margen_votos negativo si faltaron: a5=-2", d.loc["a5", "margen_votos"] == -2)

    # sin totales → disputada vacía, no cero
    a2 = pd.DataFrame({"acta_id": ["x"], "camara": ["senado"], "n_afirmativos": [pd.NA],
                       "n_negativos": [pd.NA], "tipo_mayoria_norm": ["SIMPLE"]})
    d2 = E.calcular_disputada(a2)
    check("sin totales → disputada NA (vacío ≠ cero)", pd.isna(d2["disputada"].iloc[0]))

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
