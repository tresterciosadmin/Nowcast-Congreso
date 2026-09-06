"""PASO 3 — Estima theta: el corrimiento del voto en las mociones SOBRE TABLAS.

§III.A.5 de FORMULA-COMPLETA.md:

    logit(P_i^tablas) = logit( P_i^bloque(s_l, d_i) ) + theta + gamma_tab * z_ICG

LA PIEZA QUE HACE ESTO DISTINTO DEL RECINTO NORMAL. En la via sobre tablas **el corte
`n_i >= 8` del record propio NO aplica**: la P_i de base es la RAMA DE BLOQUE, siempre.
No es un capricho — es lo unico que la medicion del 26-08 respalda:

    en Diputados, sobre tablas:   linea de bloque acierta 95,4%
                                  record propio acierta  45,0%  (Brier 0,435,
                                                                 peor que decir 0,50)

El legislador sin dictamen no cae en si mismo: cae en su bloque, mas fuerte. Sacada la
informacion cara, queda la barata.

QUE SE ESPERA DE THETA. La hipotesis original era theta > 0 ("acompanar el tratamiento es
mas barato que acompanar la ley"). La medicion del 26-08 la desmiente: la tasa afirmativa
individual cae de 78,5% a 50,4%. Se espera **theta < 0**.

SESGO DE SELECCION, dicho de frente: lo que llega a votarse sobre tablas ya es material
disputado — muchas veces una moción de la oposicion que el oficialismo bloquea. Entonces
theta NO es "el costo de tratar sobre tablas" en abstracto: es el corrimiento condicional
a que alguien haya PEDIDO el tratamiento. Para el nowcast eso alcanza (se aplica en el
mismo escenario en que se midio), pero no es un parametro causal.

Uso:
    python modelo/ensemble/src/estimar_theta_sobre_tablas.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("estimar_theta")

VENTANA_DIAS = 730
K_SHRINK = 5.0


def _hallar_repo() -> Path:
    p = Path(__file__).resolve()
    for cand in [p, *p.parents]:
        if (cand / "coordinacion").is_dir() and (cand / "variables").is_dir():
            return cand
    raise FileNotFoundError("no encontre la raiz del repo")


REPO = _hallar_repo()
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))


def _logit(p, eps=1e-4):
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return np.log(p / (1 - p))


def panel(camara: str = "") -> pd.DataFrame:
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta
    from baseline_voto_individual import _norm_cond, _ContadorAvisos

    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)

    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                if cond is not None and len(cond) else {})

    # marcar las actas de tratamiento sobre tablas por el titulo del acta
    ac = pd.read_parquet(REPO / "datos/canonica/data/clean/actas_canonico.parquet")
    ac["tab"] = ac["titulo"].fillna("").str.lower().str.contains("sobre tablas")
    tab = dict(zip(ac["acta_id"], ac["tab"]))

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara:
        v = v[v["camara"] == camara]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v["tab"] = v["acta_id"].map(tab).fillna(False)
    v = v.sort_values("fecha")

    # desvio individual walk-forward (hace falta para la rama de bloque)
    lin = (v.groupby(["acta_id", "bloque_linaje"])["af"].agg(["mean", "size"]).reset_index())
    lin = lin[lin["size"] >= 3]
    lin["linea_lin"] = (lin["mean"] >= 0.5).astype(int)
    v = v.merge(lin[["acta_id", "bloque_linaje", "linea_lin"]],
                on=["acta_id", "bloque_linaje"], how="left")
    v["_dev"] = (v["af"] != v["linea_lin"]).astype(float)
    v.loc[v["linea_lin"].isna(), "_dev"] = np.nan
    v["d_i"] = v.groupby("legislador_id")["_dev"].transform(
        lambda s: s.shift(1).expanding().mean())

    actas = (v[["acta_id", "fecha", "camara", "tab"]].drop_duplicates("acta_id")
             .sort_values("fecha"))
    actas = actas[actas["fecha"] >= votos["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)]
    # todas las de sobre tablas + una COMPARACION del mismo mes y camara, para que theta
    # no confunda "sobre tablas" con "epoca". Se toman todas las normales de los meses en
    # que hubo alguna sobre tablas.
    meses_tab = set(actas.loc[actas.tab].apply(
        lambda r: (r.camara, r.fecha.year, r.fecha.month), axis=1))
    keep = actas.apply(
        lambda r: bool(r.tab) or (r.camara, r.fecha.year, r.fecha.month) in meses_tab, axis=1)
    actas = actas[keep]
    logger.info("actas: %d (sobre tablas: %d)", len(actas), int(actas.tab.sum()))

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cache: dict = {}
    filas = []
    for a in actas.itertuples():
        info = cond_map.get(str(a.acta_id), {})
        tema, origen = _norm_cond(info.get("tema_area")), _norm_cond(info.get("origen"))
        clave = (a.camara, a.fecha.year, a.fecha.month, tema, origen)
        if clave not in cache:
            try:
                post = proyectar_postura(votos, a.fecha, a.camara,
                                         ventana_dias=VENTANA_DIAS, tema=tema,
                                         origen=origen, cond_por_acta=cond,
                                         k_shrink=K_SHRINK)
                cache[clave] = {p["bloque"]: p for p in post}
            except (ValueError, KeyError):
                cache[clave] = None
        by_lin = cache[clave]
        if by_lin is None:
            continue
        sub = por_acta.get(a.acta_id)
        if sub is None:
            continue
        for r in sub.itertuples():
            p = by_lin.get(str(r.bloque_linaje))
            if p is None:
                continue
            s = float(min(max(p["_share_afirm"], 0.0), 1.0))
            d = float(r.d_i) if not pd.isna(r.d_i) else float(p["desvio"])
            d = min(max(d, 0.0), 1.0)
            # RAMA DE BLOQUE, sin atajo al record: es lo que dice §III.A.5
            p_bloque = s * (1 - d) + (1 - s) * (d / 2)
            filas.append({"acta_id": a.acta_id, "camara": a.camara, "fecha": a.fecha,
                          "y": int(r.af), "p_bloque": p_bloque, "tab": int(bool(a.tab)),
                          "d_i": d})
    d = pd.DataFrame(filas)
    d.attrs["avisos"] = dict(cont.tally)
    return d


def estimar(d: pd.DataFrame) -> dict:
    import statsmodels.api as sm

    d = d.copy()
    d["offset"] = _logit(d["p_bloque"])

    def ajustar(X, sub):
        X = sm.add_constant(X.astype(float), has_constant="add")
        try:
            r = sm.GLM(sub["y"].astype(float), X, family=sm.families.Binomial(),
                       offset=sub["offset"].astype(float)).fit(
                cov_type="cluster", cov_kwds={"groups": sub["acta_id"]})
        except Exception as e:  # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}
        return {"n": int(r.nobs),
                "coef": {k: round(float(v), 4) for k, v in r.params.items()},
                "se_cluster_acta": {k: round(float(v), 4) for k, v in r.bse.items()},
                "p": {k: round(float(v), 5) for k, v in r.pvalues.items()}}

    res = {}
    # A) theta como diferencia entre sobre tablas y el resto del mismo mes/camara
    res["A_theta_vs_resto"] = ajustar(d[["tab"]], d)
    # B) solo las actas sobre tablas: la constante es theta directo
    sub = d[d.tab == 1]
    res["B_solo_sobre_tablas"] = ajustar(pd.DataFrame(index=sub.index), sub)
    # C) por camara
    res["C_por_camara"] = {c: ajustar(g[["tab"]], g) for c, g in d.groupby("camara")}

    res["_descriptivos"] = {
        "n_votos": int(len(d)), "n_actas": int(d.acta_id.nunique()),
        "n_actas_sobre_tablas": int(d[d.tab == 1].acta_id.nunique()),
        "n_votos_sobre_tablas": int((d.tab == 1).sum()),
        "tasa_afirm_sobre_tablas": round(float(d[d.tab == 1].y.mean()), 4),
        "tasa_afirm_resto": round(float(d[d.tab == 0].y.mean()), 4),
        "p_bloque_medio_sobre_tablas": round(float(d[d.tab == 1].p_bloque.mean()), 4),
        "p_bloque_medio_resto": round(float(d[d.tab == 0].p_bloque.mean()), 4),
    }
    return res


def _exigir_statsmodels() -> None:
    """Falla en el segundo 1, no en el minuto 9.

    El 06-09-2026 este script murio con `ModuleNotFoundError: No module named
    'statsmodels'` DESPUES de procesar 1.556 actas (9,2 min), porque el import esta
    adentro de `estimar()`, que es la ultima cosa util que hace el programa. La regla
    que dejo: lo que puede fallar en el segundo 1 no puede fallar en el minuto 9.
    """
    import importlib.util
    if importlib.util.find_spec("statsmodels") is None:
        raise SystemExit(
            "falta statsmodels, y este script no sirve sin el.\n"
            "    python -m pip install statsmodels\n"
            "Chequeo completo de dependencias:  python verificar_dependencias.py")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--camara", default="")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    _exigir_statsmodels()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    d = panel(args.camara)
    if d.empty or d.tab.sum() == 0:
        raise SystemExit("no hay votos de sobre tablas en el panel")
    res = estimar(d)
    res["_avisos"] = d.attrs.get("avisos", {})
    out = Path(args.salida) if args.salida else (
        REPO / "modelo/ensemble/outputs/theta_sobre_tablas.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
