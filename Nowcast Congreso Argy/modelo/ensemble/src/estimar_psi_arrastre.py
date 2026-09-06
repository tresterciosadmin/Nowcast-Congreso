"""PASO 5 — Estima psi: cuanto arrastra el margen de la camara de ORIGEN sobre la REVISORA.

§III.A.4 de FORMULA-COMPLETA.md (ADR-0016):

    logit(P_i^rev) = logit(P_i) + psi_l(i) * ( A_origen/E_origen - 1/2 )

LO QUE HAY QUE PROBAR, Y ES LO INTERESANTE. La version agregada del 25-08 ponia un psi
UNICO para toda la camara revisora. Al bajarlo al legislador (doctrina ADR-0016) aparecio
la prediccion de que **psi depende del bloque**: un senador del espacio que impulso el
proyecto lee una media sancion holgada como RESPALDO; uno de la oposicion la lee como
AMENAZA. Con un psi unico los dos se mueven igual, que es falso.

Este script contrasta las dos versiones:

    P1  psi unico          -> la version agregada, escrita por legislador
    P2  psi por LADO       -> interactuado con si el linaje acompano en la camara de origen
    P3  psi por LINAJE     -> un coeficiente por familia politica

Si P2/P3 no mejoran sobre P1, la prediccion de la doctrina no se sostiene y hay que
decirlo: bajar un termino al legislador es correcto por construccion, pero **que ademas
revele heterogeneidad es una hipotesis empirica, no un teorema**.

El "lado" del linaje se mide con el DATO, no con una etiqueta: la tasa afirmativa de ese
linaje en la votacion de origen. Asi no hace falta clasificar bloques a mano.

Uso:
    python modelo/ensemble/src/estimar_psi_arrastre.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("estimar_psi")

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


def panel() -> pd.DataFrame:
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta
    from baseline_voto_individual import perfil, _norm_cond, _ContadorAvisos

    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)

    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                if cond is not None and len(cond) else {})
    cad = pd.read_parquet(REPO / "datos/expedientes/data/clean/cadena_camaras.parquet")

    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")
    gp = v.groupby("legislador_id")["af"]
    v["record"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_prev"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    # margen y tasa por linaje en cada acta (para la camara de origen)
    marg = v.groupby("acta_id")["af"].agg(["mean", "size"]).rename(
        columns={"mean": "margen", "size": "emitidos"})
    lin_af = v.groupby(["acta_id", "bloque_linaje"])["af"].mean().rename("af_lin")

    cad = cad.dropna(subset=["acta_dip", "acta_sen", "fecha_dip", "fecha_sen"])
    cad["fecha_dip"] = pd.to_datetime(cad["fecha_dip"], errors="coerce")
    cad["fecha_sen"] = pd.to_datetime(cad["fecha_sen"], errors="coerce")
    cad = cad.dropna(subset=["fecha_dip", "fecha_sen"])

    filas, cache = [], {}
    for r in cad.itertuples():
        # quien es origen y quien revisora sale de la FECHA, no de la etiqueta: hay
        # proyectos donde `camara_origen` y el orden real no coinciden.
        if r.fecha_dip < r.fecha_sen:
            acta_o, acta_r = r.acta_dip, r.acta_sen
            fecha_r, cam_r = r.fecha_sen, "senado"
        elif r.fecha_sen < r.fecha_dip:
            acta_o, acta_r = r.acta_sen, r.acta_dip
            fecha_r, cam_r = r.fecha_dip, "diputados"
        else:
            continue
        if acta_o not in marg.index or acta_r not in por_acta:
            continue
        m = float(marg.loc[acta_o, "margen"]) - 0.5

        info = cond_map.get(str(acta_r), {})
        tema, origen = _norm_cond(info.get("tema_area")), _norm_cond(info.get("origen"))
        clave = (cam_r, fecha_r.year, fecha_r.month, tema, origen)
        if clave not in cache:
            try:
                post = proyectar_postura(votos, fecha_r, cam_r, ventana_dias=VENTANA_DIAS,
                                         tema=tema, origen=origen, cond_por_acta=cond,
                                         k_shrink=K_SHRINK)
                cache[clave] = {p["bloque"]: p for p in post}
            except (ValueError, KeyError):
                cache[clave] = None
        by_lin = cache[clave]
        if by_lin is None:
            continue

        for w in por_acta[acta_r].itertuples():
            p = by_lin.get(str(w.bloque_linaje))
            if p is None:
                continue
            # el LADO del linaje, medido con el dato: como voto esa familia en origen
            k = (acta_o, str(w.bloque_linaje))
            lado = float(lin_af.loc[k]) - 0.5 if k in lin_af.index else np.nan
            filas.append({
                "proyecto_id": r.proyecto_id, "acta_rev": acta_r, "camara_rev": cam_r,
                "linaje": str(w.bloque_linaje), "y": int(w.af),
                "p_motor": perfil(p["_share_afirm"], p["desvio"], w.record, w.n_prev),
                "margen_origen": m,
                "lado_linaje": lado,
                "tema": tema or "SIN_TEMA", "origen": origen or "SIN_ORIGEN",
            })
    d = pd.DataFrame(filas)
    d.attrs["avisos"] = dict(cont.tally)
    return d


def estimar(d: pd.DataFrame) -> dict:
    import statsmodels.api as sm

    d = d.copy()
    d["offset"] = _logit(d["p_motor"])

    def ajustar(X, sub, etiqueta=""):
        X = sm.add_constant(X.astype(float), has_constant="add")
        try:
            r = sm.GLM(sub["y"].astype(float), X, family=sm.families.Binomial(),
                       offset=sub["offset"].astype(float)).fit(
                cov_type="cluster", cov_kwds={"groups": sub["acta_rev"]})
        except Exception as e:  # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}
        return {"n": int(r.nobs), "llf": round(float(r.llf), 1),
                "coef": {k: round(float(v), 4) for k, v in r.params.items()},
                "se_cluster_acta": {k: round(float(v), 4) for k, v in r.bse.items()},
                "p": {k: round(float(v), 5) for k, v in r.pvalues.items()}}

    res = {}
    res["P1_psi_unico"] = ajustar(d[["margen_origen"]], d)
    # P1b: MISMA muestra, + tema y origen del proyecto. Es la capa que separa "el margen
    # arrastra" de "los proyectos de consenso pasan holgado en las dos camaras". Sin
    # esto psi no es interpretable.
    ctrl = pd.concat([d[["margen_origen"]],
                      pd.get_dummies(d["tema"], prefix="t", drop_first=True),
                      pd.get_dummies(d["origen"], prefix="o", drop_first=True)], axis=1)
    res["P1b_psi_con_tema_origen"] = ajustar(ctrl, d)

    dd = d.dropna(subset=["lado_linaje"]).copy()
    dd["margen_x_lado"] = dd["margen_origen"] * dd["lado_linaje"]
    res["P2_psi_por_lado"] = ajustar(
        dd[["margen_origen", "lado_linaje", "margen_x_lado"]], dd)

    # P3: un psi por linaje, solo para los linajes con muestra suficiente
    grandes = [l for l, g in d.groupby("linaje") if len(g) >= 2000]
    d3 = d[d.linaje.isin(grandes)].copy()
    if len(grandes) >= 2 and len(d3) > 1000:
        X = pd.DataFrame(index=d3.index)
        for l in grandes:
            X[f"psi__{l[:18]}"] = d3["margen_origen"] * (d3["linaje"] == l).astype(float)
        res["P3_psi_por_linaje"] = ajustar(X, d3)
    else:
        res["P3_psi_por_linaje"] = {"error": "sin linajes con muestra suficiente"}

    res["_descriptivos"] = {
        "n_votos": int(len(d)), "n_proyectos": int(d.proyecto_id.nunique()),
        "n_actas_revisoras": int(d.acta_rev.nunique()),
        "reparto_camara_revisora": {k: int(v) for k, v in d.camara_rev.value_counts().items()},
        "margen_origen_medio": round(float(d.margen_origen.mean()), 4),
        "margen_origen_p10_p90": [round(float(d.margen_origen.quantile(.1)), 4),
                                  round(float(d.margen_origen.quantile(.9)), 4)],
        "cobertura_lado_linaje": round(float(d.lado_linaje.notna().mean()), 4),
        "linajes_en_P3": grandes,
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
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    _exigir_statsmodels()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    d = panel()
    if d.empty:
        raise SystemExit("panel vacio: revisa cadena_camaras")
    res = estimar(d)
    res["_avisos"] = d.attrs.get("avisos", {})
    out = Path(args.salida) if args.salida else (
        REPO / "modelo/ensemble/outputs/psi_arrastre.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
