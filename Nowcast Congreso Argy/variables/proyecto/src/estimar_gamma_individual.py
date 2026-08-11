"""estimar_gamma_individual.py — ¿el ICG mueve a las BISAGRAS?

El test a nivel acta dio cero, pero estaba mal apuntado: la hipótesis de Valle es
que el clima mueve a 10-20 legisladores, y con ~69 votos emitidos por acta eso es
4% del share contra un ruido de fondo del 18%. **El promedio de cámara no tiene
resolución para verlo.** Acá se mide donde sí la hay.

## Diseño

- **Unidad:** legislador × acta. Resultado: acompañó (afirmativo) o no.
- **Efectos fijos por LEGISLADOR.** Es el corazón del test: cada legislador se
  compara consigo mismo. La pregunta deja de ser "¿los oficialistas acompañan
  más?" (trivialmente sí) y pasa a ser **"¿este mismo legislador acompaña más
  cuando el clima de su gobierno está por encima del propio promedio?"**.
- **Modelo de probabilidad lineal con doble demeaning** (legislador + gobierno).
  Con ~1.500 legisladores, un logit con dummies no entra en el presupuesto de
  cómputo; el LPM demeaneado da el efecto marginal en probabilidad, que después
  se pasa a escala logit dividiendo por p(1-p). Para responder "¿existe y cuánto
  vale?" alcanza y sobra.
- **Bisagras:** se restringe a legisladores con tasa de desvío alta
  (`disciplina_individual.csv`). Un disciplinado no puede moverse por definición
  — incluirlo sólo agrega ceros y diluye.
- **Bootstrap de bloque por mes:** el ICG es mensual y las actas del mes
  comparten valor.

## Lo que este test NO puede responder
Que γ no aparezca no prueba que el clima no exista. Hay causalidades políticas
que no dejan huella estadística con 25 años de datos y seis gobiernos. Ver la
nota de Valle en ESTADO: si el efecto no se puede estimar, la alternativa es
declararlo como escenario, no fingir que se midió.

Uso:
    python variables/proyecto/src/estimar_gamma_individual.py
    python variables/proyecto/src/estimar_gamma_individual.py --umbral 0.25 --boot 200
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("icg.gamma.ind")
_HERE = Path(__file__).resolve()
RAIZ = _HERE.parents[3]
DATA = _HERE.parents[1] / "data"
OUT = _HERE.parents[1] / "outputs"


def cargar(umbral_desvio: float) -> pd.DataFrame:
    ctx = pd.read_parquet(DATA / "icg_contexto.parquet")
    ctx["mes_key"] = ctx["fecha"].values.astype("datetime64[M]")
    ctx = ctx[ctx["apto_ajuste"]][["mes_key", "log_rel", "z_fondo", "z_corto",
                                   "vol6_z", "gobierno"]]

    ori = pd.read_parquet(DATA / "origen_por_acta.parquet")
    ori = ori[ori["origen_lado"].isin(["GOBIERNO", "OPOSICION"])][["acta_id", "origen_lado"]]
    ori = ori.drop_duplicates("acta_id")

    act = pd.read_parquet(RAIZ / "datos/canonica/data/clean/actas_canonico.parquet")[
        ["acta_id", "fecha", "camara"]]
    act["f"] = pd.to_datetime(act["fecha"], errors="coerce")
    act = act.dropna(subset=["f"])
    act["mes_key"] = act["f"].values.astype("datetime64[M]")
    act = act.merge(ori, on="acta_id").merge(ctx, on="mes_key")

    v = pd.read_parquet(RAIZ / "datos/canonica/data/clean/votos_resuelto.parquet")[
        ["acta_id", "legislador_id", "voto", "bloque_linaje"]]
    d = v.merge(act, on="acta_id", how="inner")
    d = d[d["voto"].notna()]
    d["acompana"] = d["voto"].astype(str).str.upper().str.startswith("AFIRMATIVO").astype(float)
    d["s"] = np.where(d["origen_lado"] == "GOBIERNO", 1.0, -1.0)

    disc = pd.read_csv(RAIZ / "modelo/voto_individual/outputs/disciplina_individual.csv")
    col = "tasa_desvio_disputadas" if "tasa_desvio_disputadas" in disc.columns else "tasa_desvio"
    disc = disc[disc["n_votos"] >= 50][["legislador_id", col]].rename(columns={col: "desvio"})
    d = d.merge(disc, on="legislador_id", how="left")
    d["es_pivote"] = d["desvio"].fillna(0) >= umbral_desvio
    return d


def lpm_fe(d: pd.DataFrame, con_vol: bool = False, modelo: str = "crudo") -> dict:
    """LPM con doble demeaning (legislador y gobierno).

    modelo='crudo'     -> regresor s*log_rel (el ICG mensual crudo; +vol opcional).
    modelo='dos_capas' -> DOS regresores: s*z_fondo (humor de fondo, 6m) y
                          s*z_corto (sacudón reciente, 3m). Ver icg_contexto.py.
    """
    y = d["acompana"].values
    if modelo == "dos_capas":
        X = {"s_fondo": (d["s"] * d["z_fondo"]).values,
             "s_corto": (d["s"] * d["z_corto"]).values}
    else:
        X = {"s_logrel": (d["s"] * d["log_rel"]).values}
        if con_vol:
            X["s_logrel_vol"] = X["s_logrel"] * d["vol6_z"].values
    X["s"] = d["s"].values
    M = pd.DataFrame(X, index=d.index)
    ys = pd.Series(y, index=d.index)
    for g in ("legislador_id", "gobierno"):          # demean iterativo (Frisch-Waugh)
        key = d[g]
        ys = ys - ys.groupby(key).transform("mean")
        M = M - M.groupby(key).transform("mean")
    A = M.values
    beta, *_ = np.linalg.lstsq(A, ys.values, rcond=None)
    p = float(y.mean())
    esc = max(p * (1 - p), 1e-6)                     # LPM -> escala logit
    return {k: float(b) / esc for k, b in zip(M.columns, beta)} | {"_p": p, "_n": len(d)}


def boot(d: pd.DataFrame, con_vol: bool, n: int, semilla=7, modelo: str = "crudo") -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    meses = d["mes_key"].unique()
    idx_por_mes = {m: d.index[d.mes_key == m] for m in meses}
    filas = []
    for _ in range(n):
        el = rng.choice(meses, size=len(meses), replace=True)
        idx = np.concatenate([idx_por_mes[m] for m in el])
        try:
            filas.append(lpm_fe(d.loc[idx].reset_index(drop=True), con_vol, modelo))
        except (ValueError, np.linalg.LinAlgError):
            continue
    return pd.DataFrame(filas)


# los tramos de desvío del ADR-0008 (dose-response): a cada uno le corresponde un
# gamma por capa. El tramo del NÚCLEO DURO se mide SOLO sobre los disciplinados
# (<0.10), no sobre TODOS: si se mezclan las bisagras, el número deja de ser el del
# núcleo duro (2026-08-11, a pedido de Valle). Los demás son acumulados (>=x).
TRAMOS_DOSIS = [0.0, 0.10, 0.20, 0.30, 0.40]


def _estimar_crudo(d, a) -> dict:
    res = {}
    for etq, sub in [("TODOS", d), ("BISAGRAS", d[d.es_pivote])]:
        if len(sub) < 5000:
            print(f"  {etq}: muestra chica ({len(sub)}), no se estima"); continue
        c = lpm_fe(sub.reset_index(drop=True), a.con_vol)
        b = boot(sub.reset_index(drop=True), a.con_vol, a.boot)
        print(f"\n=== {etq} — n={c['_n']:,} votos, {sub.legislador_id.nunique()} legisladores, "
              f"p(acompaña)={c['_p']:.3f} ===")
        res[etq] = {"n": c["_n"], "p": round(c["_p"], 4)}
        for k, nom in [("s_logrel", "gamma_0"), ("s_logrel_vol", "gamma_0*lambda")]:
            if k not in c:
                continue
            lo, hi = b[k].quantile(.025), b[k].quantile(.975)
            sig = "SI" if (lo > 0 or hi < 0) else "no"
            print(f"  {nom:16s} = {c[k]:+.4f}   IC95% [{lo:+.4f}, {hi:+.4f}]   distinto de cero: {sig}")
            res[etq][nom] = {"punto": round(c[k], 4), "ic95": [round(float(lo), 4), round(float(hi), 4)],
                             "significativo": sig == "SI"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gamma_icg_individual.json").write_text(
        json.dumps({"umbral_pivote": a.umbral, "con_vol": a.con_vol, "resultado": res},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    return res


def _estimar_dos_capas(d, a) -> dict:
    """Dose-response de las DOS capas (fondo 6m + sacudón 3m) a través de los
    tramos de desvío. Escribe gamma_icg_dos_capas.json, que consume modulador_icg.
    """
    tramos = {}
    for thr in TRAMOS_DOSIS:
        if thr == 0.0:                                   # núcleo duro: SOLO <0.10
            sub = d[d["desvio"].fillna(0) < 0.10]; etq = "<0.10"
        else:                                            # bisagras: acumulado >=x
            sub = d[d["desvio"].fillna(0) >= thr]; etq = f">={thr:.2f}"
        if len(sub) < 5000:
            print(f"  {etq}: muestra chica ({len(sub)}), no se estima"); continue
        c = lpm_fe(sub.reset_index(drop=True), modelo="dos_capas")
        b = boot(sub.reset_index(drop=True), a.con_vol, a.boot, modelo="dos_capas")
        print(f"\n=== desvío {etq} — n={c['_n']:,} votos, {sub.legislador_id.nunique()} legisladores, "
              f"p(acompaña)={c['_p']:.3f} ===")
        fila = {"umbral": thr, "n": c["_n"], "n_legisladores": int(sub.legislador_id.nunique()),
                "p": round(c["_p"], 4)}
        for k, nom in [("s_fondo", "gamma_fondo"), ("s_corto", "gamma_corto")]:
            lo, hi = b[k].quantile(.025), b[k].quantile(.975)
            sig = "SI" if (lo > 0 or hi < 0) else "no"
            print(f"  {nom:12s} = {c[k]:+.4f}   IC95% [{lo:+.4f}, {hi:+.4f}]   distinto de cero: {sig}")
            fila[nom] = {"punto": round(c[k], 4), "ic95": [round(float(lo), 4), round(float(hi), 4)],
                         "significativo": sig == "SI"}
        tramos[etq] = fila
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "gamma_icg_dos_capas.json").write_text(
        json.dumps({"modelo": "dos_capas", "ma_fondo": 6, "ma_corto": 3,
                    "nota": "gamma en escala logit por capa y por tramo de desvío. "
                            "El modulador arma sus tramos desde acá.",
                    "tramos": tramos}, ensure_ascii=False, indent=2), encoding="utf-8")
    return tramos


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=float, default=0.25, help="tasa de desvio minima para ser bisagra (modelo crudo)")
    ap.add_argument("--boot", type=int, default=120)
    ap.add_argument("--con-vol", action="store_true")
    ap.add_argument("--modelo", choices=["crudo", "dos_capas"], default="crudo",
                    help="crudo = ICG mensual (compat); dos_capas = fondo 6m + sacudón 3m (ADR-0008 rev 2026-08-11)")
    a = ap.parse_args(argv)

    # dos_capas recorre tramos por su cuenta -> cargar sin filtrar (umbral 0.0)
    d = cargar(0.0 if a.modelo == "dos_capas" else a.umbral)
    logger.info("votos individuales utilizables: %d (%d legisladores, %d meses)",
                len(d), d.legislador_id.nunique(), d.mes_key.nunique())
    if a.modelo == "dos_capas":
        _estimar_dos_capas(d, a)
    else:
        _estimar_crudo(d, a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
