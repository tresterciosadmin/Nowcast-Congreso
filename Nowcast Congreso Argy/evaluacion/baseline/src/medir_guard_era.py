# -*- coding: utf-8 -*-
"""Mide el GUARD DE ERA sobre la rama del récord individual (URGENTE 9).

**Por qué un proxy y no el baseline completo.** `baseline_voto_individual.py` tarda
~1,5 min cada 150 actas porque proyecta la postura de bloque acta por acta; sobre el
censo (6.091 actas) no entra en una sesión. Este script aísla **la única pieza que el
guard toca**: el récord individual y su caída a la rama de bloque. Es una comparación
**pareada** sobre exactamente los mismos votos, así que la DIFERENCIA entre modos es
limpia aunque los niveles no sean idénticos a los del baseline completo.

Control de que el proxy no miente (04-09-2026): reproduce el skill del censo del 03-09
—Diputados 0,131 contra 0,130 publicado, Senado 0,074 contra 0,072— y los dos valles de
era. El mismo proxy es el que midió el merge de ids.

Los tres modos, iguales a los de `baseline_voto_individual.py --guard-era`:

    off      el récord acumula sobre TODA la historia (lo que se venía midiendo)
    corte    el récord se reinicia en cada era (lo que el motor YA hace, con fecha fija)
    shrink   corte + Empirical-Bayes k=5 contra el récord del LINAJE en la misma era

NO TOCA EL REPO: sólo lee. Escribe el resumen en outputs/.

    python evaluacion/baseline/src/medir_guard_era.py

Mide ademas el barrido de `MIN_HIST_INDIVIDUAL`, que el encogimiento dejo sin trabajo.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("medir_guard_era")

MIN_HIST_INDIVIDUAL = 8
K_SHRINK = 5.0
MODOS = ("off", "corte", "shrink")

BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
        pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
ETIQ = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


def _repo() -> Path:
    p = Path(__file__).resolve()
    for c in [p, *p.parents]:
        if (c / "coordinacion").is_dir() and (c / "variables").is_dir():
            return c
    raise FileNotFoundError("no encontre la raiz del repo")


REPO = _repo()


def _metricas(p: np.ndarray, y: np.ndarray) -> dict:
    """Brier y skill contra la tasa base. Skill > 0 = el modelo le gana a decir
    siempre la tasa base; = 0 la empata."""
    if len(p) == 0:
        return {}
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    br, bb = float(((p - y) ** 2).mean()), float(((y.mean() - y) ** 2).mean())
    return {"n": int(len(y)), "brier": round(br, 5),
            "skill": round(1 - br / bb, 4) if bb > 0 else None,
            "accuracy": round(float(((p >= 0.5) == (y == 1)).mean()), 4)}


def cargar() -> pd.DataFrame:
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar as cargar_bloque  # type: ignore
    v = cargar_bloque()
    v = v[v["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    return v.sort_values("fecha").reset_index(drop=True)


def eras_de(fechas: pd.Series) -> pd.Series:
    """Era de cada fecha, delegando en el motor pero UNA VEZ POR FECHA DISTINTA.

    `fechas.map(era_de)` sobre 1.016.058 filas tarda minutos; hay ~2.800 fechas
    distintas (una por sesion), asi que el mapa se arma sobre las unicas. El calendario
    sigue siendo el del motor: no se copia aca.
    """
    sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
    from nowcast_puertas import era_de  # type: ignore
    mapa = {f: era_de(f) for f in pd.unique(fechas)}
    return fechas.map(mapa)


def _walk_forward(d: pd.DataFrame, llave: list[str]):
    """(media, n) de los votos ANTERIORES de cada grupo, en orden de fecha.

    Idéntico a `shift(1).expanding().mean()` pero con cumsum: sobre 1.016.058 filas y
    ~2.300 grupos el `transform(lambda)` tarda minutos y esto son segundos. Se verifica
    contra la versión lenta en `tests/test_medir_guard_era.py`, que es la única razón
    por la que se puede confiar en el atajo.
    """
    g = d.groupby(llave, sort=False)["af"]
    n = g.cumcount()
    prev = g.cumsum() - d["af"]
    return (prev / n).where(n > 0), n.astype(float)


def predecir(v: pd.DataFrame, modo: str) -> pd.DataFrame:
    """p por voto, con el mismo reparto de ramas que el motor: récord individual si
    tiene n>=8 en su historia disponible, si no el récord de su linaje."""
    d = v.copy()
    d["_era"] = eras_de(d["fecha"])
    llave = ["legislador_id"] if modo == "off" else ["legislador_id", "_era"]
    d["rec"], d["n"] = _walk_forward(d, llave)
    # respaldo: el récord del LINAJE, siempre cortado por era (es lo que hace el motor
    # con `proyectar_postura` desde el 22-07, y no es lo que se está evaluando acá)
    d["anc"], _ = _walk_forward(d, ["bloque_linaje", "_era"])
    if modo == "shrink":
        mez = (d["n"] * d["rec"].fillna(0.0) + K_SHRINK * d["anc"]) / (d["n"] + K_SHRINK)
        d["rec"] = mez.where(d["anc"].notna() & d["rec"].notna(), d["rec"])
    usa_ind = d["rec"].notna() & (d["n"] >= MIN_HIST_INDIVIDUAL)
    d["p"] = np.where(usa_ind, d["rec"], d["anc"])
    d["rama"] = np.where(usa_ind, "individual", "bloque")
    return d[d["p"].notna()]


def resumen(d: pd.DataFrame) -> dict:
    era = pd.cut(d["fecha"], bins=BINS, labels=ETIQ)
    return {
        "global": _metricas(d.p.values, d.y.values),
        "pct_rama_individual": round(float((d.rama == "individual").mean()) * 100, 2),
        "por_camara": {c: _metricas(g.p.values, g.y.values)["skill"]
                       for c, g in d.groupby("camara")},
        "por_era": {str(e): _metricas(g.p.values, g.y.values)["skill"]
                    for e, g in d.assign(_e=era).groupby("_e", observed=True)},
        "por_rama": {r: _metricas(g.p.values, g.y.values)
                     for r, g in d.groupby("rama")},
    }


def barrer_min_hist(v: pd.DataFrame, valores=(1, 2, 3, 5, 8, 12, 20, 40)) -> dict:
    """Cuanto cuesta el umbral `MIN_HIST_INDIVIDUAL`, ahora que el record se encoge.

    Antes del encogimiento, el umbral era la unica proteccion contra creerle a un record
    de 3 votos: o le creias entero o lo tirabas. Con Empirical-Bayes esa proteccion es
    continua —con n=1 el record queda en ~0,83 del share de su bloque, que es justo lo
    que el umbral queria conseguir— asi que el umbral pasa a ser redundante. Este barrido
    mide si ademas es DANINO.

    Se corre con la clave del motor: (camara, legislador_id, era).
    """
    d = predecir(v, "shrink")
    out = {}
    for mh in valores:
        usa = d["rec"].notna() & (d["n"] >= mh)
        p = np.where(usa, d["rec"], d["anc"])
        ok = ~pd.isna(p)
        dd, pp = d[ok], p[ok]
        era = pd.cut(dd["fecha"], bins=BINS, labels=ETIQ)
        out[mh] = {
            "global": _metricas(pp, dd.af.values),
            "pct_rama_bloque": round(float((~usa[ok]).mean()) * 100, 2),
            "por_era": {str(e): _metricas(pp[(era == e).values],
                                          dd.af.values[(era == e).values])["skill"]
                        for e in ETIQ},
        }
    return out


def main(argv) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    v = cargar()
    logger.info("votos emitidos: %d | legisladores: %d", len(v), v.legislador_id.nunique())
    res = {"_que_es": "Guard de era sobre la rama del record individual (URGENTE 9). "
                      "Proxy pareado sobre los mismos votos; la diferencia entre modos "
                      "es lo que vale, no el nivel absoluto.",
           "_n_votos": int(len(v)), "resultados": {}}
    for modo in MODOS:
        d = predecir(v, modo).rename(columns={"af": "y"})
        res["resultados"][modo] = resumen(d)
        r = res["resultados"][modo]
        logger.info("%-7s skill %.4f | rama individual %.2f%% | desde 2023 %s | 2015-2019 %s",
                    modo, r["global"]["skill"], r["pct_rama_individual"],
                    r["por_era"].get("desde 2023"), r["por_era"].get("2015-2019"))
    res["min_hist"] = barrer_min_hist(v)
    logger.info("barrido de MIN_HIST_INDIVIDUAL (con el record ya encogido):")
    for mh, r in res["min_hist"].items():
        logger.info("  n>=%-3d skill %.4f | rama bloque %5.2f%% | desde 2023 %s",
                    mh, r["global"]["skill"], r["pct_rama_bloque"],
                    r["por_era"].get("desde 2023"))
    out = REPO / "evaluacion" / "baseline" / "outputs" / "guard_era_medicion.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
