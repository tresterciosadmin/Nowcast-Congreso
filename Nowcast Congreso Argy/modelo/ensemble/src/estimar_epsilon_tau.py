"""PASO 2 — Estima las dos piezas que reemplazan al clip: epsilon_0 y tau.

§III.A.3 de FORMULA-COMPLETA.md:

    P_i~      = eps0 + (1-2*eps0) * P_i                      <- encogimiento afin
    P_i^(j)   = sigma( logit(P_i~) + tau * eta_j )           <- shock comun, eta_j ~ N(0,1)

Las dos piezas arreglan cosas DISTINTAS y por eso se estiman distinto:

  * `eps0` arregla la AFIRMACION INDIVIDUAL (nadie es una certeza). Se estima donde vive el
    problema: minimizando el error sobre los votos individuales. Es un parametro de
    calibracion y sale por busqueda directa.

  * `tau` arregla la CONCENTRACION AGREGADA. No se puede estimar mirando votos sueltos:
    por definicion es la parte de la incertidumbre que mueve a TODOS a la vez. Se estima
    por SOBREDISPERSION del recuento por acta.

EL ESTIMADOR DE TAU (momentos, sin simular)
-------------------------------------------
Si los votos fueran independientes dado P_i, el recuento A de un acta tendria

    E[A] = S1 = sum_i p_i          Var(A) = S = sum_i p_i (1-p_i)

Con el shock comun, un corrimiento eta mueve cada p_i en p_i(1-p_i)*tau*eta, asi que

    Var(A) ~= S + S^2 * tau^2

Entonces se regresa el residuo al cuadrado observado, (A_obs - S1)^2, sobre S y S^2 sin
constante: el coeficiente de S^2 es tau^2. Es una regresion de momentos, no hace falta
correr Monte Carlo para calibrarla.

QUE MIDE TAU EN LA PRACTICA — y hay que decirlo. El residuo (A_obs - S1)^2 mezcla dos
cosas: la correlacion real entre legisladores, y el ERROR DEL MODELO (cuando el motor se
equivoca, se equivoca para toda el acta a la vez). Este estimador no las separa, asi que
`tau` sale como COTA SUPERIOR: es "toda la incertidumbre que el motor no explica", que es
justamente lo que las bandas tienen que reflejar. Pero no es "el mundo se movio junto";
parte es "el motor no sabia". Bajar el sesgo del motor deberia bajar tau.

Uso:
    python modelo/ensemble/src/estimar_epsilon_tau.py --muestra 600
    python modelo/ensemble/src/estimar_epsilon_tau.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("estimar_eps_tau")

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


def panel(muestra: int = 0, seed: int = 7, camara: str = "") -> pd.DataFrame:
    """(acta_id, camara, fecha, p_motor, y) para cada voto emitido."""
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta
    from baseline_voto_individual import perfil, _norm_cond, _ContadorAvisos, MIN_HIST_INDIVIDUAL

    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)

    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                if cond is not None and len(cond) else {})

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara:
        v = v[v["camara"] == camara]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")
    gp = v.groupby("legislador_id")["af"]
    v["record"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_prev"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    actas = (v[["acta_id", "fecha", "camara"]].drop_duplicates("acta_id")
             .sort_values("fecha"))
    actas = actas[actas["fecha"] >= votos["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)]
    if muestra:
        actas = actas.sample(min(muestra, len(actas)), random_state=seed).sort_values("fecha")
    logger.info("actas: %d", len(actas))

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cache: dict = {}
    filas = []
    for k, a in enumerate(actas.itertuples(), 1):
        if k % 300 == 0:
            logger.info("  %d/%d", k, len(actas))
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
            filas.append({"acta_id": a.acta_id, "camara": a.camara, "fecha": a.fecha,
                          "p_motor": perfil(p["_share_afirm"], p["desvio"],
                                            r.record, r.n_prev),
                          "y": int(r.af)})
    d = pd.DataFrame(filas)
    d.attrs["avisos"] = dict(cont.tally)
    return d


def _brier(p, y):
    return float(((np.asarray(p, float) - np.asarray(y, float)) ** 2).mean())


def _logloss(p, y):
    p = np.clip(np.asarray(p, float), 1e-9, 1 - 1e-9)
    y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def estimar_epsilon(d: pd.DataFrame) -> dict:
    """Busca el eps0 que minimiza Brier y el que minimiza log-loss.

    Se reportan los dos a proposito: **no tienen por que coincidir**. Brier castiga el
    error cuadratico y log-loss castiga la CONFIANZA equivocada, que es justo el problema
    que se quiere arreglar. Si el optimo de log-loss es bastante mayor, la lectura es que
    el motor no esta tan lejos en promedio pero si demasiado seguro.
    """
    p, y = d["p_motor"].values, d["y"].values
    grid = np.round(np.arange(0.0, 0.301, 0.005), 3)
    filas = []
    for e in grid:
        pe = e + (1 - 2 * e) * p
        filas.append({"eps0": float(e), "brier": _brier(pe, y), "logloss": _logloss(pe, y)})
    g = pd.DataFrame(filas)
    mb = g.loc[g.brier.idxmin()]
    ml = g.loc[g.logloss.idxmin()]
    base = g[g.eps0 == 0.0].iloc[0]
    return {
        "eps0_optimo_brier": float(mb.eps0),
        "eps0_optimo_logloss": float(ml.eps0),
        "brier_sin": round(float(base.brier), 5),
        "brier_con_optimo": round(float(mb.brier), 5),
        "mejora_brier_pct": round(100 * (base.brier - mb.brier) / base.brier, 2),
        "logloss_sin": round(float(base.logloss), 5),
        "logloss_con_optimo": round(float(ml.logloss), 5),
        "mejora_logloss_pct": round(100 * (base.logloss - ml.logloss) / base.logloss, 2),
        "curva": [{"eps0": float(r.eps0), "brier": round(float(r.brier), 5),
                   "logloss": round(float(r.logloss), 5)}
                  for r in g.itertuples() if round(r.eps0 * 200) % 10 == 0],
    }


def estimar_tau(d: pd.DataFrame, eps0: float = 0.0) -> dict:
    """tau^2 por sobredispersion del recuento por acta (ver docstring del modulo)."""
    p = eps0 + (1 - 2 * eps0) * d["p_motor"].values
    dd = d.assign(_p=p, _v=p * (1 - p))
    g = dd.groupby("acta_id").agg(A=("y", "sum"), S1=("_p", "sum"),
                                  S=("_v", "sum"), n=("y", "size"))
    g = g[g.n >= 20]
    if len(g) < 30:
        return {"error": f"muestra chica para tau: {len(g)} actas"}
    res = (g.A - g.S1)
    res2 = res ** 2

    # POR QUE NO ALCANZA CON MINIMOS CUADRADOS. La regresion res2 ~ a*S + b*S^2 sin
    # constante esta mal condicionada: S y S^2 estan casi perfectamente correlacionadas
    # entre actas (todas tienen ~el mismo n), asi que el ajuste manda todo al termino
    # lineal y `b` sale con signo arbitrario. En la corrida del 03-09 daba b<0 en
    # Diputados y 2,62 en Senado: ruido, no estimacion.
    #
    # El despeje directo por acta es robusto a eso: de Var(A) ~= S + S^2*tau^2,
    #     tau_acta^2 = (res^2 - S) / S^2
    # y se toma la MEDIANA, que no se deja arrastrar por las actas donde el motor
    # simplemente se equivoco de lado.
    tau2_acta = (res2 - g.S) / (g.S ** 2)
    tau_mediana = float(np.sqrt(max(float(tau2_acta.median()), 0.0)))
    tau_q25 = float(np.sqrt(max(float(tau2_acta.quantile(0.25)), 0.0)))
    tau_q75 = float(np.sqrt(max(float(tau2_acta.quantile(0.75)), 0.0)))

    X = np.column_stack([g.S.values, (g.S.values ** 2)])
    coef, *_ = np.linalg.lstsq(X, res2.values, rcond=None)
    a, b = float(coef[0]), float(coef[1])

    # Cuanto del error es SESGO (el motor apunta al lado equivocado en promedio) y
    # cuanto es DISPERSION. Si domina el sesgo, tau esta capturando error del modelo y
    # bajaria al corregirlo; si domina la dispersion, es incertidumbre genuina.
    sesgo = float(res.mean())
    parte_sesgo = float(sesgo ** 2 / res2.mean()) if res2.mean() > 0 else None

    ratio = float(res2.mean() / g.S.mean())
    return {
        "tau_mediana": round(tau_mediana, 4),
        "tau_IQR": [round(tau_q25, 4), round(tau_q75, 4)],
        "tau_lstsq_NO_USAR": round(float(np.sqrt(max(b, 0.0))), 4),
        "coef_S_lstsq": round(a, 4),
        "n_actas": int(len(g)),
        "sobredispersion_observada": round(ratio, 2),
        "sesgo_medio_votos": round(sesgo, 2),
        "fraccion_del_error_que_es_sesgo": (round(parte_sesgo, 4)
                                            if parte_sesgo is not None else None),
        "lectura": ("la varianza real del recuento es ~%.0f veces la que produce suponer "
                    "votos independientes" % ratio),
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--muestra", type=int, default=0)
    ap.add_argument("--camara", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    d = panel(args.muestra, args.seed, args.camara)
    if d.empty:
        raise SystemExit("panel vacio")
    eps = estimar_epsilon(d)
    res = {
        "n_votos": int(len(d)), "n_actas": int(d.acta_id.nunique()),
        "epsilon": eps,
        "tau_sin_epsilon": estimar_tau(d, 0.0),
        "tau_con_epsilon": estimar_tau(d, eps["eps0_optimo_logloss"]),
        "por_camara": {c: {"epsilon": estimar_epsilon(g), "tau": estimar_tau(g, 0.0)}
                       for c, g in d.groupby("camara")},
        "_avisos": d.attrs.get("avisos", {}), "_args": vars(args),
    }
    out = Path(args.salida) if args.salida else (
        REPO / "modelo/ensemble/outputs/epsilon_tau.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
