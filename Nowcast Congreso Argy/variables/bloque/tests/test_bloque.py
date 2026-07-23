"""Tests offline de variables/bloque — SIN datos reales.

Fixture sintética que imita el esquema de la canónica (votos_resuelto + actas).
Se corre desde una copia en /tmp (protocolo de sync del proyecto).
Verifica: métricas por acta/bloque, cohesión de Rice, serie, y sobre todo el
PROYECTOR walk-forward (que no mira el futuro) y su formato compatible con el
escenario del ensemble.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import bloque as B  # noqa: E402


def _votos_sinteticos() -> pd.DataFrame:
    """Dos bloques, varias actas en el tiempo. Bloque A = oficialista disciplinado
    (casi siempre AFIRMATIVO, cohesión alta). Bloque B = opositor con fracturas."""
    filas = []
    fechas = pd.date_range("2022-01-01", periods=10, freq="60D")
    for i, f in enumerate(fechas):
        aid = f"acta{i}"
        # Bloque A: 9 AFIRM, 1 NEG -> dirección AFIRM, rice 0.8, desvio 0.1
        for j in range(9):
            filas.append((aid, f, "diputados", "OFI", f"a{j}", "AFIRMATIVO"))
        filas.append((aid, f, "diputados", "OFI", "a9", "NEGATIVO"))
        # Bloque B: alterna. En actas pares 6 NEG/4 AFIRM (dir NEG, fractura),
        # en impares 8 NEG/2 AFIRM (dir NEG, más cohesión). + 2 ausentes fijos.
        neg = 6 if i % 2 == 0 else 8
        afi = 10 - neg
        for j in range(neg):
            filas.append((aid, f, "diputados", "OPO", f"b{j}", "NEGATIVO"))
        for j in range(afi):
            filas.append((aid, f, "diputados", "OPO", f"b{neg+j}", "AFIRMATIVO"))
        filas.append((aid, f, "diputados", "OPO", "b_aus1", "AUSENTE"))
        filas.append((aid, f, "diputados", "OPO", "b_aus2", "ABSTENCION"))
    df = pd.DataFrame(filas, columns=["acta_id", "fecha", "camara",
                                      "bloque_linaje", "legislador_id", "conducta"])
    return df


def test_metricas_direccion_y_rice():
    v = _votos_sinteticos()
    mab = B.metricas_acta_bloque(v, min_emit=3)
    ofi = mab[mab["bloque_linaje"] == "OFI"].iloc[0]
    assert ofi["direccion"] == "AFIRMATIVO"
    assert abs(ofi["rice"] - 0.8) < 1e-9      # (9-1)/10
    assert abs(ofi["desvio"] - 0.1) < 1e-9    # min(9,1)/10
    opo = mab[(mab["bloque_linaje"] == "OPO") & (mab["acta_id"] == "acta0")].iloc[0]
    assert opo["direccion"] == "NEGATIVO"     # 6 neg vs 4 afirm
    assert abs(opo["desvio"] - 0.4) < 1e-9    # 4/10


def test_ausentes_no_emiten():
    # Los AUSENTE/ABSTENCION (NO_ACOMPANA) no cuentan como emitidos.
    v = _votos_sinteticos()
    mab = B.metricas_acta_bloque(v, min_emit=3)
    opo = mab[(mab["bloque_linaje"] == "OPO") & (mab["acta_id"] == "acta0")].iloc[0]
    assert opo["n_emit"] == 10                # 6+4, los 2 no-acompaña afuera


def test_serie_agrega_por_periodo():
    v = _votos_sinteticos()
    mab = B.metricas_acta_bloque(v, min_emit=3)
    s = B.serie_bloque(mab)
    assert {"periodo", "camara", "bloque_linaje", "bancas_medias",
            "share_afirmativo", "cohesion_media", "desvio_medio",
            "tasa_fractura"}.issubset(s.columns)
    ofi = s[s["bloque_linaje"] == "OFI"].iloc[0]
    assert ofi["share_afirmativo"] == 1.0     # siempre AFIRM
    opo = s[s["bloque_linaje"] == "OPO"].iloc[0]
    assert opo["share_afirmativo"] == 0.0     # siempre NEG
    assert opo["tasa_fractura"] > 0           # las actas pares se parten (rice<0.5)


def test_proyector_formato_ensemble():
    v = _votos_sinteticos()
    esc = B.proyectar_postura(v, "2023-06-01", "diputados", ventana_dias=730, min_actas=2, padron_path="__no__")
    assert isinstance(esc, list) and esc
    for b in esc:
        assert set(["bloque", "bancas", "linea", "desvio"]).issubset(b)
        assert b["linea"] in {"AFIRMATIVO", "NEGATIVO", "NO_ACOMPANA"}
        assert 0.0 <= b["desvio"] <= 1.0
        assert b["bancas"] > 0
    d = {b["bloque"]: b for b in esc}
    assert d["OFI"]["linea"] == "AFIRMATIVO"
    assert d["OPO"]["linea"] == "NEGATIVO"


def test_proyector_walk_forward_sin_leakage():
    # Con fecha temprana solo ve las primeras actas; nunca el futuro.
    v = _votos_sinteticos()
    # corte justo después de 3 actas (~2022-05-02); ventana amplia
    esc = B.proyectar_postura(v, "2022-05-10", "diputados", ventana_dias=3650, min_actas=1, padron_path="__no__")
    # el nº de actas usadas por OFI no puede exceder las anteriores a la fecha
    ofi = [b for b in esc if b["bloque"] == "OFI"][0]
    assert ofi["_n_actas"] <= 3
    # y mover la fecha hacia adelante nunca reduce la historia disponible
    esc2 = B.proyectar_postura(v, "2023-12-31", "diputados", ventana_dias=3650, min_actas=1, padron_path="__no__")
    ofi2 = [b for b in esc2 if b["bloque"] == "OFI"][0]
    assert ofi2["_n_actas"] >= ofi["_n_actas"]


def test_proyector_error_sin_historia():
    v = _votos_sinteticos()
    try:
        B.proyectar_postura(v, "2000-01-01", "diputados")
        assert False, "debía fallar sin historia previa"
    except ValueError:
        pass


def test_camara_inexistente_falla():
    v = _votos_sinteticos()
    try:
        B.proyectar_postura(v, "2023-06-01", "senado")
        assert False, "no hay senado en la fixture"
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [f for n, f in sorted(globals().items()) if n.startswith("test_")]
    ok = 0
    for f in fns:
        f()
        print(f"  OK  {f.__name__}")
        ok += 1
    print(f"\n{ok}/{len(fns)} chequeos OK")
