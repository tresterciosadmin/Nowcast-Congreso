"""Tests sin red de modelo/voto_individual/src/disciplina.py (datos sintéticos).
Correr: python modelo/voto_individual/tests/test_disciplina.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import disciplina as D  # noqa: E402

OK = 0


def check(nombre: str, cond: bool) -> None:
    global OK
    assert cond, f"FALLA: {nombre}"
    OK += 1
    print(f"  ok: {nombre}")


def bloque(acta, blq, votos, anio=2010, camara="diputados"):
    """Genera filas de votos sintéticos para un acta+bloque. votos = lista (nombre, voto)."""
    return [
        {"acta_id": acta, "bloque_norm": blq, "legislador_id": f"leg:{n}", "legislador_nombre": n,
         "voto": v, "anio": anio, "camara": camara, "fuente": "test"}
        for n, v in votos
    ]


def main() -> None:
    # Acta 1: bloque A de 7 (6 AFIRMATIVO, 1 díscolo NEGATIVO); bloque B de 2 (chico -> descartado)
    filas = bloque("a1", "A", [(f"a{i}", "AFIRMATIVO") for i in range(6)] + [("discolo", "NEGATIVO")])
    filas += bloque("a1", "B", [("b1", "NEGATIVO"), ("b2", "NEGATIVO")])
    # Acta 2: bloque A de 6, empate 3-3 tras LOO para algunos -> el LOO del votante define
    filas += bloque("a2", "A", [(f"a{i}", "AFIRMATIVO") for i in range(4)] + [("discolo", "NEGATIVO"), ("a9", "NEGATIVO")])
    v = pd.DataFrame(filas)

    d = D.marcar_desvios(v)

    check("bloque chico (B, n=2) queda fuera", not (d["bloque_norm"] == "B").any())
    a1 = d[d["acta_id"] == "a1"].set_index("legislador_nombre")["desvio"]
    check("díscolo marcado como desvío en a1", bool(a1["discolo"]))
    check("los 6 leales sin desvío en a1", int(a1.drop("discolo").sum()) == 0)
    # a2: para 'discolo', resto = 4 AFI vs 1 NEG -> desvío; para un AFI, resto = 3 AFI vs 2 NEG -> leal
    a2 = d[d["acta_id"] == "a2"].set_index("legislador_nombre")["desvio"]
    check("díscolo marcado en a2", bool(a2["discolo"]))
    check("afirmativo leal en a2", not bool(a2["a0"]))

    idx = D.indice_por_legislador(d)
    row = idx[idx["legislador_id"] == "leg:discolo"].iloc[0]
    check("tasa del díscolo = 1.0 (2 desvíos / 2 votos)", row["tasa_desvio"] == 1.0)
    row2 = idx[idx["legislador_id"] == "leg:a0"].iloc[0]
    check("tasa del leal = 0.0", row2["tasa_desvio"] == 0.0)

    gate = D.dimensionar_set_pivote(idx, min_votos=1)
    check("set pivote cuenta al díscolo en >=15%", gate["por_umbral"][">=15%"]["n_legisladores"] >= 1)
    check("medibles = legisladores con >=1 voto", gate["legisladores_medibles"] == len(idx))

    anual = D.por_anio(d)
    check("por_anio agrega por legislador x año", set(anual.columns) >= {"legislador_id", "anio", "tasa_desvio"})

    # período parlamentario
    d2 = d.assign(fecha="2010-05-01")
    d2["periodo"] = D.periodo_parlamentario(d2["fecha"], d2["anio"])
    check("2010 cae en período 2009-2011", (d2["periodo"] == "2009-2011").all())
    pp = D.por_periodo(d2)
    row = pp[pp["legislador_id"] == "leg:discolo"].iloc[0]
    check("por_periodo: díscolo con tasa 1.0 en su período", row["tasa_desvio"] == 1.0 and row["periodo"] == "2009-2011")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
