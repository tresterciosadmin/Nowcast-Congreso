# -*- coding: utf-8 -*-
"""Tests del récord por ORIGEN (PROMPT-RECORD-POR-ORIGEN.md). Corre sin datos pesados."""
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import record_por_origen as r  # noqa: E402
import record_por_origen_brazos as b  # noqa: E402


# ── el objeto rho ──

def test_rho_sin_votos_de_un_origen_queda_en_cero():
    # sin votos de ningún origen, los dos lados quedan en su récord general: rho = 0
    assert r.rho_encogido(0, 0, 0, 0, 0.7) == pytest.approx(0.0)


def test_rho_oficialista_positivo_y_encogido():
    # 20/20 al Ejecutivo, 0/20 a la oposición, general 0,5
    rho = r.rho_encogido(20, 20, 0, 20, 0.5)
    assert 0.5 < rho < 1.0
    assert rho == pytest.approx((20 + 2.5) / 25 - 2.5 / 25)


def test_signo_lado_umbral_y_faltante():
    s = r.signo_lado(np.array([0.3, -0.3, 0.05, -0.09, np.nan]))
    assert s.tolist() == [1, -1, 0, 0, 0]


# ── el caso Pichetto: relabelar, no copiar ──

def test_pichetto_sin_cambiar_de_lado_conserva_el_signo():
    assert r.rho_heredado(0.4, 1, 1) == pytest.approx(0.4)
    assert r.rho_heredado(-0.3, -1, -1) == pytest.approx(-0.3)


def test_pichetto_cambiando_de_lado_lo_invierte():
    assert r.rho_heredado(0.4, 1, -1) == pytest.approx(-0.4)
    assert r.rho_heredado(-0.3, -1, 1) == pytest.approx(0.3)


def test_sin_lado_conocido_no_se_hereda_nada():
    assert r.rho_heredado(0.4, 0, 1) == 0 and r.rho_heredado(0.4, 1, 0) == 0


# ── el término en logit ──

def test_ajuste_no_mueve_nada_sin_origen_o_sin_rho():
    p = np.array([0.3, 0.8])
    assert np.allclose(b.ajustar_rho(p, [0.5, 0.5], [0, 0], 2.0), p)
    assert np.allclose(b.ajustar_rho(p, [0.0, 0.0], [1, -1], 2.0), p)


def test_ajuste_signo_por_origen():
    p = np.array([0.6, 0.6])
    q = b.ajustar_rho(p, [0.5, 0.5], [1, -1], 1.0)
    assert q[0] > 0.6 > q[1]


def test_signo_origen_oficialismo_no_se_usa():
    assert b.signo_origen(["EJECUTIVO", "OPOSICION", "OFICIALISMO", "DESCONOCIDO"]).tolist() == [1, -1, 0, 0]


# ── walk-forward ──

def test_previos_cuenta_solo_lo_anterior():
    df = pd.DataFrame({"k": ["a", "a", "b", "a"], "af": [1, 0, 1, 1]})
    n, a = b._previos(df, ["k"])
    assert n.tolist() == [0, 1, 0, 2] and a.tolist() == [0, 1, 0, 1]


def test_previos_estricta_no_cuenta_el_mismo_dia():
    # dos actas el mismo día (p.ej. general y un artículo de la misma ley): la segunda NO
    # puede usar la primera como historia, un nowcast previo a la sesión no la tiene
    df = pd.DataFrame({"k": ["a"] * 3, "af": [1, 0, 1],
                       "fecha": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-02-01"])})
    n, a = b._previos(df, ["k"], estricta=False)
    assert n.tolist() == [0, 1, 2]
    n, a = b._previos(df, ["k"], estricta=True)
    assert n.tolist() == [0, 1, 1] and a.tolist() == [0, 1, 1]


def _votos_lado():
    filas = []
    for i, f in enumerate(["2024-01-10", "2024-02-10", "2024-03-10", "2024-04-10", "2024-05-10"]):
        for lin, af in [("A", 1), ("B", 0)]:
            for j in range(3):
                filas.append(dict(era="MILEI", camara="diputados", bloque_linaje=lin,
                                  fecha=pd.Timestamp(f), origen_f="EJECUTIVO", af=af,
                                  acta_id=f"x{i}", legislador_id=f"{lin}{j}"))
    return pd.DataFrame(filas).sort_values("fecha").reset_index(drop=True)


def test_lado_walk_forward_espera_actas_y_no_mira_el_mismo_dia():
    v = _votos_lado()
    s = b.lado_walk_forward(v, min_actas=3)
    por_fecha = v.assign(s=s).groupby(["fecha", "bloque_linaje"])["s"].first().unstack()
    # las 3 primeras fechas: menos de 3 actas ANTERIORES -> lado 0 (no un default inventado)
    assert (por_fecha.iloc[:3] == 0).all().all()
    # la 4ª ya ve 3 actas anteriores: A oficialista, B enfrente
    assert por_fecha.iloc[3].tolist() == [1, -1]


def test_brazos_espejo_y_relacion():
    d = pd.DataFrame({
        "share": [0.5, 0.5, 0.5], "desvio": [0.0, 0.0, 0.0],
        "n_era": [10, 10, 0], "a_era": [10, 10, 0],
        "n_hist": [20, 20, 0], "a_hist": [15, 15, 0],
        "n_era_o": [4, 0, 0], "a_era_o": [0, 0, 0],
        "n_hist_o": [4, 0, 0], "a_hist_o": [0, 0, 0],
        "origen_conocido": [True, False, True],
        "rel": [1, 0, -1], "n_rel": [8, 0, 0], "a_rel": [8, 0, 0],
    })
    br = b.brazos(d)
    # A2 condiciona por origen: 0/4 al origen de esta acta tira para abajo aunque la era sea 10/10
    assert br.loc[0, "A2"] < 0.5 < br.loc[0, "A1"]
    # origen desconocido: A2 = A1
    assert br.loc[1, "A2"] == pytest.approx(br.loc[1, "A1"])
    # relación definida: B2 usa el récord de esa relación (8/8 -> arriba)
    assert br.loc[0, "B2"] > 0.8
    # sin votos de ningún tipo: todos caen a la rama de bloque, la misma para todos
    assert br.loc[2, ["A1", "A2", "A0", "B2"]].nunique() == 1


def test_cobertura_avisa_si_todo_cae_a_no_heredar(caplog):
    d = pd.DataFrame({"s_o": [1, -1], "s_now": [0, 0], "rho_her": [0.0, 0.0], "rel": [0, 0]})
    with caplog.at_level(logging.INFO, logger="record_por_origen_brazos"):
        c = b.cobertura(d)
    assert c["rho_heredado_no_nulo_en_EJEC_OPOS"] == 0.0
    assert any(rec.levelno == logging.WARNING and "NADA usa dato real" in rec.getMessage()
               for rec in caplog.records)
