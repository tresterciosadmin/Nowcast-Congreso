"""Tests sin red de variables/legislador/src/ficha.py (datos sintéticos).
Correr: python variables/legislador/tests/test_ficha.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ficha as F  # noqa: E402

OK = 0


def check(nombre: str, cond: bool) -> None:
    global OK
    assert cond, f"FALLA: {nombre}"
    OK += 1
    print(f"  ok: {nombre}")


def main() -> None:
    # Legislador X: 2 actas en 2005 (bloque A) y 1 en 2009 (bloque B), 1 ausencia.
    # Legislador Y: 1 acta, siempre presente.
    v = pd.DataFrame([
        {"acta_id": "a1", "legislador_id": "leg:x", "legislador_nombre": "PEREZ, Juan",
         "bloque_norm": "A", "bloque_linaje": "A", "distrito": "Córdoba",
         "voto": "AFIRMATIVO", "anio": 2005, "camara": "diputados", "fuente": "test"},
        {"acta_id": "a2", "legislador_id": "leg:x", "legislador_nombre": "PEREZ, Juan",
         "bloque_norm": "A", "bloque_linaje": "A", "distrito": "Córdoba",
         "voto": "AUSENTE", "anio": 2005, "camara": "diputados", "fuente": "test"},
        {"acta_id": "a3", "legislador_id": "leg:x", "legislador_nombre": "Perez, Juan",
         "bloque_norm": "B", "bloque_linaje": "B", "distrito": "Córdoba",
         "voto": "NEGATIVO", "anio": 2009, "camara": "diputados", "fuente": "test"},
        {"acta_id": "a1", "legislador_id": "leg:y", "legislador_nombre": "GOMEZ, Ana",
         "bloque_norm": "A", "bloque_linaje": "A", "distrito": "Salta",
         "voto": "ABSTENCION", "anio": 2005, "camara": "senado", "fuente": "test"},
    ])
    v["anio"] = v["anio"].astype("Int64")
    v["fecha"] = v["anio"].map({2005: "2005-06-01", 2009: "2009-03-01"})
    v["periodo"] = F.periodo_parlamentario(v["fecha"], v["anio"])

    bloques = F.historial_bloques(v)
    bx = bloques[bloques["legislador_id"] == "leg:x"]
    check("historial de bloques: X pasó por 2 bloques", len(bx) == 2)
    check("rango de años del bloque A de X = 2005-2005",
          bx[bx["bloque_norm"] == "A"].iloc[0][["anio_desde", "anio_hasta"]].tolist() == [2005, 2005])

    disc = pd.DataFrame([{"legislador_id": "leg:x", "n_votos": 2, "tasa_desvio": 0.5,
                          "tasa_desvio_disputadas": 0.5}])
    f = F.ficha(v, bloques, disc)
    fx = f[f["legislador_id"] == "leg:x"].iloc[0]
    check("una ficha por legislador", len(f) == 2)
    check("presentismo de X = 2/3", abs(fx["presentismo"] - round(2 / 3, 4)) < 1e-9)
    check("trayectoria de X = A → B", fx["trayectoria_bloques"] == "A → B")
    check("bloque último de X = B", fx["bloque_ultimo"] == "B")
    check("distrito de X = Córdoba", fx["distrito"] == "Córdoba")
    check("tasa de desvío integrada desde voto_individual", fx["tasa_desvio"] == 0.5)
    fy = f[f["legislador_id"] == "leg:y"].iloc[0]
    check("Y sin disciplina queda con NA (no 0)", pd.isna(fy["tasa_desvio"]))
    check("pct_abstencion de Y = 1.0 (sobre presentes)", fy["pct_abstencion"] == 1.0)

    anual = F.por_anio(v, None)
    ax = anual[(anual["legislador_id"] == "leg:x") & (anual["anio"] == 2005)].iloc[0]
    check("por año: X 2005 con 2 votaciones y presentismo 0.5",
          ax["n_votaciones"] == 2 and ax["presentismo"] == 0.5)

    # período parlamentario: recambio = 10-dic de años impares
    import pandas as _pd
    per = F.periodo_parlamentario(
        _pd.Series(["2005-06-01", "2005-12-10", "2005-12-09", "2006-03-01", None]),
        _pd.Series([2005, 2005, 2005, 2006, 2026]),
    )
    check("jun-2005 pertenece a 2003-2005", per.iloc[0] == "2003-2005")
    check("10-dic-2005 arranca 2005-2007", per.iloc[1] == "2005-2007")
    check("09-dic-2005 sigue en 2003-2005", per.iloc[2] == "2003-2005")
    check("2006 (año par) es 2005-2007", per.iloc[3] == "2005-2007")
    check("sin fecha, año par 2026 -> 2025-2027", per.iloc[4] == "2025-2027")

    fx2 = f[f["legislador_id"] == "leg:x"].iloc[0]
    check("ficha lista los períodos de X", fx2["periodos"] == "2003-2005; 2007-2009" and fx2["n_periodos"] == 2)

    pp = F.por_periodo(v, None)
    px = pp[(pp["legislador_id"] == "leg:x") & (pp["periodo"] == "2003-2005")].iloc[0]
    check("por_periodo: X en 2003-2005 con 2 votaciones y presentismo 0.5",
          px["n_votaciones"] == 2 and px["presentismo"] == 0.5)

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
