"""Tests sin red del desvío v2 (datos sintéticos). ADR-0004.
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


def filas(acta, blq, linaje, votos, anio=2010):
    return [
        {"acta_id": acta, "bloque_norm": blq, "bloque_linaje": linaje,
         "legislador_id": f"leg:{n}", "legislador_nombre": n, "voto": v,
         "anio": anio, "camara": "diputados", "fuente": "test", "fecha": "2010-05-01",
         "periodo": "2009-2011"}
        for n, v in votos
    ]


def main() -> None:
    filas_all = []
    # a1 — bloque A (6 escaños, linaje real): 4 AFIRMATIVO, 1 NEGATIVO, 1 AUSENTE.
    #      Línea = AFIRMATIVO (4/6 > 50%). El NEGATIVO y el AUSENTE desvían (estricta).
    #      (Con esto el linaje ESPACIO en a1 queda 7A-3N-3NO → mayoría AFIRMATIVO.)
    filas_all += filas("a1", "A", "ESPACIO", [("a1p", "AFIRMATIVO"), ("a2p", "AFIRMATIVO"),
                                              ("a3p", "AFIRMATIVO"), ("a4p", "AFIRMATIVO"),
                                              ("rebelde", "NEGATIVO"), ("borrado", "AUSENTE")])
    # a1 — bloque B (3 escaños): 2 AUSENTES, 1 vota AFIRMATIVO.
    #      Línea = NO_ACOMPANA (2/3). El que fue a votar desvía (caso inverso de Valle).
    filas_all += filas("a1", "B", "ESPACIO", [("b1", "AUSENTE"), ("b2", "AUSENTE"),
                                              ("presente", "AFIRMATIVO")])
    # a1 — bloque C (4 escaños, linaje real): 2 AFIRMATIVO y 2 NEGATIVO → empate.
    #      El linaje ESPACIO en a1 vota mayormente AFIRMATIVO (A aporta 3A+..., B 1A...) →
    #      desempate por linaje: los 2 NEGATIVO de C desvían.
    filas_all += filas("a1", "C", "ESPACIO", [("c1", "AFIRMATIVO"), ("c2", "AFIRMATIVO"),
                                              ("c3", "NEGATIVO"), ("c4", "NEGATIVO")])
    # a1 — bloque P (4 escaños, OTRO / PROVINCIAL): 2 AFIRMATIVO y 2 ABSTENCION → empate
    #      sin espacio real → desvío parcial 0.5 para los cuatro.
    filas_all += filas("a1", "P", "OTRO / PROVINCIAL", [("p1", "AFIRMATIVO"), ("p2", "AFIRMATIVO"),
                                                        ("p3", "ABSTENCION"), ("p4", "ABSTENCION")])
    # a2 — bloque A: línea NEGATIVO (3/5); uno se abstiene → desvía (estricta);
    #      monobloque M: línea = su propia conducta → desvío 0.
    filas_all += filas("a2", "A", "ESPACIO", [("a1p", "NEGATIVO"), ("a2p", "NEGATIVO"),
                                              ("a3p", "NEGATIVO"), ("rebelde", "ABSTENCION"),
                                              ("borrado", "NEGATIVO")])
    filas_all += filas("a2", "M", "OTRO / PROVINCIAL", [("solo", "AFIRMATIVO")])
    # suspendido (anotado en el nombre por la fuente): debe quedar excluido
    filas_all += filas("a2", "A", "ESPACIO", [("Perez Juan (Suspendido Art 70 C.N.)", "AUSENTE")])

    v = pd.DataFrame(filas_all)
    v["anio"] = v["anio"].astype("Int64")
    import numpy as np
    v["conducta"] = np.where(v["voto"].isin(["AFIRMATIVO", "NEGATIVO"]), v["voto"], "NO_ACOMPANA")
    v = D.excluir_no_medibles(v)
    check("suspendido excluido del universo medible",
          not v["legislador_nombre"].str.contains("Suspendido", na=False).any())
    d = D.marcar_desvios(v).set_index(["acta_id", "legislador_id"])

    check("a1/A: línea AFIRMATIVO con ausente contado en el total",
          d.loc[("a1", "leg:a1p"), "linea"] == "AFIRMATIVO")
    check("a1/A: el que votó NEGATIVO desvía", d.loc[("a1", "leg:rebelde"), "desvio"] == 1.0)
    check("a1/A: el AUSENTE desvía (estricta)", d.loc[("a1", "leg:borrado"), "desvio"] == 1.0)
    check("a1/A: los alineados no desvían", d.loc[("a1", "leg:a2p"), "desvio"] == 0.0)

    check("a1/B: línea = NO_ACOMPANA (bloque mayormente ausente)",
          d.loc[("a1", "leg:b1"), "linea"] == "NO_ACOMPANA")
    check("a1/B: el que fue a votar desvía (caso inverso)",
          d.loc[("a1", "leg:presente"), "desvio"] == 1.0)
    check("a1/B: los ausentes alineados", d.loc[("a1", "leg:b2"), "desvio"] == 0.0)

    check("a1/C: empate resuelto por linaje", d.loc[("a1", "leg:c1"), "metodo"] == "linaje")
    check("a1/C: los NEGATIVO desvían según la línea del espacio",
          d.loc[("a1", "leg:c3"), "desvio"] == 1.0 and d.loc[("a1", "leg:c1"), "desvio"] == 0.0)

    check("a1/P: empate provincial → método parcial", d.loc[("a1", "leg:p1"), "metodo"] == "parcial")
    check("a1/P: desvío parcial 0.5 para todos", d.loc[("a1", "leg:p1"), "desvio"] == 0.5
          and d.loc[("a1", "leg:p3"), "desvio"] == 0.5)

    check("a2/A: abstenerse con línea NEGATIVO desvía (estricta)",
          d.loc[("a2", "leg:rebelde"), "desvio"] == 1.0)
    check("a2/M: monobloque siempre alineado (mitigar con disciplina ideológica)",
          d.loc[("a2", "leg:solo"), "desvio"] == 0.0)

    dd = d.reset_index()
    idx = D.indice_por_legislador(dd, disputadas=set())
    reb = idx[idx["legislador_id"] == "leg:rebelde"].iloc[0]
    check("índice: rebelde 2/2 desvíos → tasa 1.0", reb["tasa_desvio"] == 1.0)
    ali = idx[idx["legislador_id"] == "leg:a2p"].iloc[0]
    check("índice: alineado tasa 0.0", ali["tasa_desvio"] == 0.0)

    pp = D.por_periodo(dd, disputadas=set())
    row = pp[(pp["legislador_id"] == "leg:p1") & (pp["periodo"] == "2009-2011")].iloc[0]
    check("por_periodo acumula desvíos parciales", row["n_desvios"] == 0.5)

    # disputada v2 (misma vara que datos/export)
    actas = pd.DataFrame({"acta_id": ["x1", "x2"], "camara": ["diputados"] * 2,
                          "tipo_mayoria": ["Más de la mitad"] * 2,
                          "n_afirmativos": [130, 200], "n_negativos": [127, 57]})
    disp = D.actas_disputadas(actas, pd.DataFrame({"acta_id": [], "voto": []}))
    check("disputada ±5% emitidos: 130-127 sí, 200-57 no", disp == {"x1"})

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
