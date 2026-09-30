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

EL OFFSET (28-09-2026, ADR-0034). tau mide lo que el motor NO explica, asi que depende de
que P_i se le pase. Hasta el 28-09 el panel lo armaba `panel()`, una copia vieja del
harness: `shift(1)` por fila (cuenta los articulos anteriores de la MISMA ley del mismo
dia), sin guard de era, sin encoger, sin origen. Un offset que conoce la respuesta deja
menos residuo: tau salia SUBESTIMADO. Ahora el default es `--panel censo`: el P_i del
MOTOR voto a voto, tal como lo deja `censo_detalle_paralelo.py` (historia estricta).
`--panel harness_viejo` queda solo para reproducir el 1,197 / 1,190 anteriores.

DE DONDE LEE EL CENSO (auditoria 2026-09, A2). El detalle voto a voto (37 MB) esta
ignorado por git: vive en un solo disco. Por defecto este script lee
`censo_estadisticos_*.json` (`evaluacion/baseline/src/censo_estadisticos.py`), que SI
viaja por git y trae, por acta, n, A, Σp y Σp² (alcanzan para tau con cualquier eps0) y
la curva de Brier y log-loss sobre la grilla de eps0. Da lo mismo que el detalle
(`tests/test_censo_estadisticos.py` lo fija). `--detalle X.parquet` fuerza el camino
voto a voto; es el que verifica al otro. Otra grilla u otra perdida piden el detalle.

Uso:
    python modelo/ensemble/src/estimar_epsilon_tau.py                      # censo limpio (JSON)
    python modelo/ensemble/src/estimar_epsilon_tau.py --columna estricta__general
    python modelo/ensemble/src/estimar_epsilon_tau.py --detalle <censo_detalle.parquet>
    python modelo/ensemble/src/estimar_epsilon_tau.py --panel harness_viejo --muestra 2500
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


# La raiz del repo sale de `rutas.py`: hay UNA sola copia del criterio
# (ver tests/test_raiz_del_repo_una_sola_copia.py). Buscar `coordinacion/` +
# `variables/` daba lo mismo -- esta medido -- pero se apoyaba en que esas dos
# carpetas no cambiaran de nombre ni de lugar.
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))
import censo_estadisticos as CE  # noqa: E402


def panel(muestra: int = 0, seed: int = 7, camara: str = "") -> pd.DataFrame:
    """(acta_id, camara, fecha, p_motor, y) para cada voto emitido — con el HARNESS VIEJO.

    ⚠️ ESPEJO VIEJO DEL MOTOR (ADR-0034): shift(1) por fila, sin guard, sin encoger, sin
    origen. Sólo para reproducir las estimaciones anteriores al 28-09 (`--panel
    harness_viejo`). El default es `panel_censo`."""
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


def panel_censo(ruta, columna: str = "p", camara: str = "") -> pd.DataFrame:
    """(acta_id, camara, fecha, p_motor, y) desde el detalle voto a voto del censo: el P_i
    que calcula el MOTOR (`baseline_voto_individual`, que lo importa), no una copia.
    `ruta` es obligatoria: el detalle no viaja por git (ver el docstring del modulo)."""
    d = pd.read_parquet(Path(ruta))
    if columna not in d.columns:
        raise KeyError(f"el censo no tiene la columna {columna!r}; hay "
                       f"{[c for c in d.columns if c.startswith('p')]}")
    if camara:
        d = d[d["camara"] == camara]
    out = d[["acta_id", "camara", "fecha", "y"]].copy()
    out["p_motor"] = d[columna].astype(float).to_numpy()
    out.attrs["avisos"] = {"panel": "censo", "columna": columna}
    return out


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
    grid = CE.GRILLA_EPS
    brier = [_brier(e + (1 - 2 * e) * p, y) for e in grid]
    logloss = [_logloss(e + (1 - 2 * e) * p, y) for e in grid]
    return estimar_epsilon_curvas(grid, brier, logloss)


def estimar_epsilon_curvas(grid, brier, logloss) -> dict:
    """El optimo de eps0 a partir de las CURVAS (Brier y log-loss medios por cada eps0 de la
    grilla). Es lo que comparten el camino voto a voto y el de los estadisticos por git."""
    g = pd.DataFrame({"eps0": np.asarray(grid, float), "brier": np.asarray(brier, float),
                      "logloss": np.asarray(logloss, float)})
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
    return _tau_desde_actas(g)


def estimar_tau_actas(a: pd.DataFrame, eps0: float = 0.0) -> dict:
    """tau^2 a partir de los agregados POR ACTA (n, A = Σy, Σp, Σp²), sin voto a voto.

    Con p~ = e + (1-2e)p (afin), Σp~ = e·n + (1-2e)·Σp y Σp~² = n·e² + 2e(1-2e)·Σp +
    (1-2e)²·Σp²; y S = Σp~(1-p~) = Σp~ - Σp~². Da lo mismo que `estimar_tau` sobre el
    detalle (`tests/test_censo_estadisticos.py`) porque comparten `_tau_desde_actas`."""
    e, c = float(eps0), 1.0 - 2.0 * float(eps0)
    n, sp, sp2 = (a[k].to_numpy(float) for k in ("n", "sp", "sp2"))
    s1 = e * n + c * sp
    s = s1 - (n * e * e + 2 * e * c * sp + c * c * sp2)
    g = pd.DataFrame({"A": a["A"].to_numpy(float), "S1": s1, "S": s, "n": a["n"].to_numpy()},
                     index=pd.Index(a["acta_id"].to_numpy(), name="acta_id"))
    return _tau_desde_actas(g)


def _tau_desde_actas(g: pd.DataFrame) -> dict:
    """El estimador, sobre el agregado por acta g (A, S1, S, n)."""
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


def _resultado_desde_estadisticos(est: dict, columna: str, camara: str) -> dict:
    """Lo mismo que arma `main` desde el detalle, pero desde los estadisticos versionados."""
    a = CE.tabla_actas(est)
    en_corte = a["camara"].eq(camara) if camara else a["camara"].notna()

    def eps(cam):
        return estimar_epsilon_curvas(*CE.curvas_epsilon(est, columna, cam or None)[:3])

    def tau(e0, cam):
        return estimar_tau_actas(CE.panel_actas(est, columna, cam or None, a), e0)

    e = eps(camara)
    return {
        "n_votos": int(a.loc[en_corte, "n"].sum()),
        "n_actas": int(en_corte.sum()),
        "epsilon": e,
        "tau_sin_epsilon": tau(0.0, camara),
        "tau_con_epsilon": tau(e["eps0_optimo_logloss"], camara),
        "por_camara": {c: {"epsilon": eps(c), "tau": tau(0.0, c)}
                       for c in sorted(a["camara"].unique()) if not camara or c == camara},
        "_avisos": {"panel": "censo_estadisticos", "variante": CE.variante(est, columna),
                    "generado": est.get("generado"), "fuente": est.get("fuente")},
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--muestra", type=int, default=0)
    ap.add_argument("--camara", default="")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--panel", choices=["censo", "harness_viejo"], default="censo",
                    help="censo (default) = P_i del motor, historia estricta; "
                         "harness_viejo = la copia con fuga que se usó hasta el 28-09")
    ap.add_argument("--detalle", default=None,
                    help="parquet del censo voto a voto: fuerza ese camino en vez del JSON "
                         "de estadisticos versionado")
    ap.add_argument("--estadisticos", default=None,
                    help="JSON de estadisticos (default: el del censo del 28-09)")
    ap.add_argument("--columna", default="p",
                    help="que variante del censo usar como offset: `p` (= estricta__tema, "
                         "RECORD_POR_TEMA prendido al generarse el censo), estricta__general "
                         "(el motor de hoy) o, con --detalle, cualquier columna del parquet")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    if args.panel == "censo" and not args.detalle:
        res = _resultado_desde_estadisticos(CE.cargar(args.estadisticos), args.columna,
                                            args.camara)
        res["_args"] = vars(args)
    else:
        d = (panel_censo(args.detalle, args.columna, args.camara) if args.panel == "censo"
             else panel(args.muestra, args.seed, args.camara))
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
