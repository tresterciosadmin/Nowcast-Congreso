"""DIAGNOSTICO DEL SENADO — por que el motor rinde la mitad que en Diputados.

El censo del 03-09 (730.574 votos) dio:

    Diputados   skill 0,1302   Brier 0,1491   accuracy 0,785
    Senado      skill 0,0721   Brier 0,0997   accuracy 0,877   <- la mitad de skill

Ojo con la lectura facil: el Brier del Senado es MEJOR (0,0997 vs 0,1491). No es que el
motor prediga peor en numero absoluto — es que **la tasa base del Senado es 87,8% y ya
predice casi todo sola**, asi que el margen que queda para aportar es chico. La pregunta
correcta no es "por que erra mas" sino **"por que aporta menos sobre lo trivial"**.

QUE SE MIDE. Cinco hipotesis, cada una con su corte:

  H1  CALIBRACION      el motor esta sesgado o sobreconfiado en el Senado
  H2  ERA              el problema esta concentrado en algun periodo (como en Diputados)
  H3  TAMANO DE BLOQUE 72 bancas repartidas en muchos linajes -> bloques chicos, y la
                       linea de bloque se calcula con un minimo de 3 emisores por acta.
                       Si muchos linajes no llegan, la postura sale de ruido.
  H4  DESVIO           d_i del Senado es la mitad que el de Diputados (0,0080 vs 0,0131):
                       con desvio casi nulo, P_i se pega a 0 o 1 y no discrimina
  H5  DISTRITO         en el Senado la representacion es PROVINCIAL (3 por provincia).
                       Si el distrito predice mejor que el linaje, el modelo esta usando
                       el eje equivocado.

NO TOCA EL REPO: solo lee. Escribe el diagnostico en outputs/.

Uso:
    python evaluacion/baseline/src/diagnostico_senado.py
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("diag_senado")

VENTANA_DIAS = 730
K_SHRINK = 5.0
MIN_HIST = 8


def _hallar_repo() -> Path:
    p = Path(__file__).resolve()
    for cand in [p, *p.parents]:
        if (cand / "coordinacion").is_dir() and (cand / "variables").is_dir():
            return cand
    raise FileNotFoundError("no encontre la raiz del repo")


REPO = _hallar_repo()
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))


def _met(p, y):
    if len(p) == 0:
        return {}
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    b = float(((p - y) ** 2).mean())
    bb = float(((y.mean() - y) ** 2).mean())
    return {"n": int(len(y)), "tasa_base": round(float(y.mean()), 4),
            "brier": round(b, 5), "skill": round(1 - b / bb, 4) if bb > 0 else None,
            "accuracy": round(float(((p >= .5).astype(int) == y).mean()), 4)}


def construir(camara: str, muestra: int, seed: int = 7) -> pd.DataFrame:
    from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta
    sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))
    from baseline_voto_individual import perfil, _norm_cond, _ContadorAvisos

    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)
    votos = cargar_bloque()
    cond = cargar_tema_por_acta()
    cond_map = (cond.set_index(cond.columns[0]).to_dict("index")
                if cond is not None and len(cond) else {})

    v = votos[(votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"]))
              & (votos["camara"] == camara)].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha")
    gp = v.groupby("legislador_id")["af"]
    v["record"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_prev"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    # cuantos EMISORES tiene cada linaje en cada acta (H3)
    tam = v.groupby(["acta_id", "bloque_linaje"])["af"].size().rename("emisores")

    actas = (v[["acta_id", "fecha", "camara"]].drop_duplicates("acta_id").sort_values("fecha"))
    actas = actas[actas["fecha"] >= votos["fecha"].min() + pd.Timedelta(days=VENTANA_DIAS)]
    if muestra:
        actas = actas.sample(min(muestra, len(actas)), random_state=seed).sort_values("fecha")
    logger.info("%s: %d actas", camara, len(actas))

    por_acta = {k: g for k, g in v.groupby("acta_id", sort=False)}
    cache, filas = {}, []
    for a in actas.itertuples():
        info = cond_map.get(str(a.acta_id), {})
        tema, origen = _norm_cond(info.get("tema_area")), _norm_cond(info.get("origen"))
        clave = (a.camara, a.fecha.year, a.fecha.month, tema, origen)
        if clave not in cache:
            try:
                post = proyectar_postura(votos, a.fecha, a.camara, ventana_dias=VENTANA_DIAS,
                                         tema=tema, origen=origen, cond_por_acta=cond,
                                         k_shrink=K_SHRINK)
                cache[clave] = {p["bloque"]: p for p in post}
            except (ValueError, KeyError):
                cache[clave] = None
        by = cache[clave]
        if by is None:
            continue
        sub = por_acta.get(a.acta_id)
        if sub is None:
            continue
        for r in sub.itertuples():
            p = by.get(str(r.bloque_linaje))
            if p is None:
                continue
            filas.append({
                "acta_id": a.acta_id, "fecha": a.fecha, "camara": a.camara,
                "legislador_id": r.legislador_id, "linaje": str(r.bloque_linaje),
                "y": int(r.af),
                "p": perfil(p["_share_afirm"], p["desvio"], r.record, r.n_prev),
                "share": float(p["_share_afirm"]), "desvio": float(p["desvio"]),
                "n_actas_postura": int(p.get("_n_actas", 0)),
                "emisores_linaje": int(tam.get((a.acta_id, str(r.bloque_linaje)), 0)),
                "fuente": "record" if (not pd.isna(r.record) and r.n_prev >= MIN_HIST) else "bloque",
            })
    d = pd.DataFrame(filas)
    d.attrs["avisos"] = dict(cont.tally)
    return d


def diagnosticar(d: pd.DataFrame) -> dict:
    out = {"global": _met(d.p, d.y)}

    # H1 calibracion
    dd = d.assign(bin=np.clip((d.p * 10).astype(int), 0, 9))
    g = dd.groupby("bin").agg(n=("y", "size"), pred=("p", "mean"), real=("y", "mean"))
    out["H1_calibracion"] = [{"bin": int(b), "n": int(r.n), "pred": round(float(r.pred), 4),
                              "real": round(float(r.real), 4),
                              "gap": round(float(r.real - r.pred), 4)} for b, r in g.iterrows()]

    # H2 era
    eras = pd.cut(d.fecha, bins=[pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"),
                                 pd.Timestamp("2015-12-10"), pd.Timestamp("2019-12-10"),
                                 pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")],
                  labels=["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"])
    out["H2_era"] = {str(k): _met(g.p, g.y)
                     for k, g in d.assign(era=eras).groupby("era", observed=True)}

    # H3 tamano del linaje en el acta
    tr = pd.cut(d.emisores_linaje, bins=[-1, 2, 4, 9, 19, 1000],
                labels=["1-2", "3-4", "5-9", "10-19", "20+"])
    out["H3_tamano_linaje"] = {str(k): _met(g.p, g.y)
                               for k, g in d.assign(t=tr).groupby("t", observed=True)}
    out["H3_reparto_emisores"] = {
        "media": round(float(d.emisores_linaje.mean()), 2),
        "mediana": float(d.emisores_linaje.median()),
        "pct_en_linaje_de_menos_de_3": round(float((d.emisores_linaje < 3).mean()), 4),
        "linajes_distintos_por_acta": round(
            float(d.groupby("acta_id")["linaje"].nunique().mean()), 2),
    }

    # H4 desvio
    td = pd.cut(d.desvio, bins=[-0.001, 0.021, 0.05, 0.10, 0.20, 1.0],
                labels=["<=0,02 (piso)", "0,02-0,05", "0,05-0,10", "0,10-0,20", ">0,20"])
    out["H4_desvio"] = {str(k): _met(g.p, g.y)
                        for k, g in d.assign(t=td).groupby("t", observed=True)}
    out["H4_reparto_desvio"] = {
        "media": round(float(d.desvio.mean()), 4),
        "pct_en_el_piso_0_02": round(float((d.desvio <= 0.021).mean()), 4),
        "p_extrema_pct": round(float(((d.p < 0.05) | (d.p > 0.95)).mean()), 4),
        "p_media": round(float(d.p.mean()), 4),
    }

    # fuente de la direccion
    out["fuente_direccion"] = {k: _met(g.p, g.y) for k, g in d.groupby("fuente")}

    # skill por linaje (los grandes)
    out["por_linaje"] = {k: _met(g.p, g.y) for k, g in d.groupby("linaje") if len(g) >= 2000}
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--muestra", type=int, default=0)
    ap.add_argument("--comparar-diputados", action="store_true")
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")

    res = {}
    ds = construir("senado", args.muestra)
    res["senado"] = diagnosticar(ds)
    res["senado"]["_avisos"] = ds.attrs.get("avisos", {})
    if args.comparar_diputados:
        dd = construir("diputados", args.muestra)
        res["diputados"] = diagnosticar(dd)

    out = Path(args.salida) if args.salida else (
        REPO / "evaluacion/baseline/outputs/diagnostico_senado.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
