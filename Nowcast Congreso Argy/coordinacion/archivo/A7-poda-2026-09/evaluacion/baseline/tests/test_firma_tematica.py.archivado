# -*- coding: utf-8 -*-
"""Tests de la firma temática del desvío (ADR-0032). Corre sin datos pesados."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import firma_tematica_desvio as f  # noqa: E402
import firma_tematica_fase1_2 as f12  # noqa: E402


def _base():
    filas = []
    for leg, desv in [("a", [0, 0, 1, 1]), ("b", [0, 0, 0, 0])]:
        for i, dv in enumerate(desv):
            filas.append(dict(acta_id=f"x{i}", legislador_id=leg, presente=True, contestada=True,
                              disputada=False, desvio=float(dv), areas=["ENER"] if i < 2 else ["JUST"],
                              era=1, voto="AFIRMATIVO", camara="diputados", bloque_norm="B",
                              bloque_linaje="L", fecha=pd.Timestamp("2016-01-01")))
    return pd.DataFrame(filas)


def test_areas_de_saca_aux_y_duplicados():
    assert f.areas_de("ECON.DEUDA;ECON.PRESU;AUX.TRAMITE;TRAB.X") == ["ECON", "TRAB"]
    assert f.areas_de(None) == [] and f.areas_de(float("nan")) == []


def test_era_de_limites():
    e = f.era_de(pd.Series(pd.to_datetime(["2015-12-09", "2015-12-10", "2019-12-10", "2023-12-10"])))
    assert e.tolist() == [0, 1, 2, 3]


def test_filtro_desconocido_falla_fuerte():
    # sin default silencioso: un filtro mal escrito NO puede degradar a 'todas'
    with pytest.raises(ValueError):
        f._filtrar(_base(), "disputadas")


def test_celdas_y_totales():
    d = _base()
    c = f.celdas(d).set_index(["legislador_id", "area"])
    assert c.loc[("a", "ENER"), "d"] == 0.0 and c.loc[("a", "JUST"), "d"] == 1.0
    t = f.totales(d).set_index("legislador_id")
    assert t.loc["a", "dbar"] == 0.5 and t.loc["b", "dbar"] == 0.0


def test_centrado_suma_cero_ponderada_y_no_es_lealtad():
    """Un legislador parejo (mismo desvío en todas las áreas) tiene d~ = 0: el centrado
    borra la lealtad. Es el corazón del diseño."""
    d = _base()
    d.loc[d.legislador_id == "a", "desvio"] = 0.5  # parejo
    c = f.celdas(d).merge(f.totales(d), on=["legislador_id", "era"])
    c["dc"] = (c.n * c.d + f.K_SHRINK * c.dbar) / (c.n + f.K_SHRINK) - c.dbar
    assert np.allclose(c[c.legislador_id == "a"].dc, 0.0)


def test_corr_none_con_muestra_chica_o_constante():
    assert f12._r([1, 2], [1, 2]) is None
    assert f12._r([1] * 6, list(range(6))) is None


def test_gobernadores_csv_integridad():
    p = f.REPO / "datos/padron/data/gobernadores.csv"
    g = pd.read_csv(p)
    assert g.provincia.nunique() == 24
    assert (g.groupby("provincia").size() == 4).all()
    assert set(g.coincide_con_ejecutivo) <= {"si", "no", "parcial"}
    assert set(g.confianza) <= {"alta", "media", "baja"}
    assert g.fuente.notna().all()  # cada fila rastreable


def test_gobernadores_no_esta_enchufado():
    """Orden de Franco: contrato disponible, sin consumidor. Si alguien lo importa, este
    test avisa."""
    prohibidos = ("modelo", "variables", "producto")
    for carpeta in prohibidos:
        for py in (f.REPO / carpeta).rglob("*.py"):
            assert "gobernadores.csv" not in py.read_text(encoding="utf-8", errors="ignore"), py
