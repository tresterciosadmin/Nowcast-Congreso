"""variables/embudo - supervivencia del proyecto de ley (el diferencial del nowcast).

Mide el EMBUDO por etapas (presentado -> giro -> dictamen -> recinto -> sancion)
y entrena un modelo de supervivencia v1 que estima, para cada proyecto de LEY,
P(llega al recinto) y P(sancion) con rasgos conocidos AL MOMENTO DE PRESENTACION
(sin leakage), validado con backtesting temporal walk-forward.

Insumo: contrato de datos/expedientes (data/clean/*.parquet).
Salida (contrato estable, outputs/):
  embudo_etapas.csv        tasas de transicion por etapa (global y por anio/camara)
  embudo_por_comision.csv  tasa de supervivencia por comision (cementerios vs. rapidas)
  p_embudo.parquet         proyecto_id, etapa_actual, p_llega_recinto, p_sancion
  backtest_embudo.json     Brier/AUC/calibracion walk-forward vs baseline (tasa base)

CLI:
  python embudo.py funnel        # caracterizacion por etapas (no requiere sklearn)
  python embudo.py modelo        # survival v1 + backtest temporal (requiere sklearn)
  python embudo.py all

CADUCIDAD: los proyectos de ley caducan si no avanzan (Ley 13.640: ~1-2 anios
parlamentarios). Por eso el modelo entrena/backtestea sobre COHORTES MADURAS
(presentadas hasta MADUREZ_ANIOS antes del ultimo anio con datos) para no contar
como "muerto" lo que todavia sigue vivo. Los proyectos inmaduros SI se scorean
(es el uso real: predecir el futuro), pero no entran al entrenamiento/backtest.

HOOKS variables/proyecto (cuando esten): el TEMA (taxonomias) y el ORIGEN
oficialismo/oposicion son los rasgos mas predictivos del embudo. Si existe
`variables/proyecto/data/features_proyecto.parquet` con columnas `origen` y/o
`tema_*`, el modelo las incorpora automaticamente. Hoy corre solo con rasgos
de expedientes.

4 directivas: errores especificos, backoff (n/a: I/O local), parsing defensivo
(columnas por nombre, tolerante a NA), logging estructurado.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("embudo")

MADUREZ_ANIOS = 2          # cohorte madura = presentada <= (ultimo_anio - MADUREZ_ANIOS)
TOP_COMISIONES = 25        # cuantas comisiones entran como rasgo one-hot
MIN_TRAIN = 500            # minimo de proyectos de train para intentar un fold


# --------------------------------------------------------------------------- #
# Carga (parsing defensivo)                                                    #
# --------------------------------------------------------------------------- #
def cargar(clean_dir: Path) -> dict[str, pd.DataFrame]:
    """Lee el contrato de datos/expedientes. Tolerante a archivos faltantes."""
    archivos = {
        "expedientes": "expedientes.parquet",
        "giros": "expedientes_giros.parquet",
        "dictamenes": "expedientes_dictamenes.parquet",
        "movimientos": "expedientes_movimientos.parquet",
        "resultados": "expedientes_resultados.parquet",
        "leyes": "expedientes_leyes.parquet",
    }
    dfs: dict[str, pd.DataFrame] = {}
    for k, nombre in archivos.items():
        p = clean_dir / nombre
        if not p.exists():
            logger.warning("falta %s (sigo)", nombre)
            continue
        try:
            dfs[k] = pd.read_parquet(p)
        except (OSError, ValueError) as e:
            logger.error("no pude leer %s: %s", nombre, e)
    if "expedientes" not in dfs:
        raise FileNotFoundError(
            f"no encontre expedientes.parquet en {clean_dir}. "
            "Corre antes: python datos/expedientes/src/ingesta_ckan.py")
    return dfs


def _ids(df: pd.DataFrame | None, col: str = "proyecto_id") -> set:
    if df is None or col not in df.columns:
        return set()
    return set(df[col].dropna().astype(str))


# --------------------------------------------------------------------------- #
# Cohorte a nivel proyecto (una fila por proyecto de LEY)                       #
# --------------------------------------------------------------------------- #
def construir_cohorte(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Una fila por proyecto de LEY con sus etapas y rasgos de presentacion."""
    exp = dfs["expedientes"].copy()
    exp["proyecto_id"] = exp["proyecto_id"].astype(str)
    if "tipo" in exp.columns:
        exp = exp[exp["tipo"].str.contains("LEY", case=False, na=False)]
    exp = exp.drop_duplicates("proyecto_id")

    giros = dfs.get("giros")
    id_giro = _ids(giros)
    id_dict = _ids(dfs.get("dictamenes"))
    id_ley = _ids(dfs.get("leyes"))

    # resultado NO nulo = el proyecto tuvo tratamiento en el recinto
    res = dfs.get("resultados")
    id_res = set()
    if res is not None and "proyecto_id" in res.columns:
        rc = res.copy()
        rc["proyecto_id"] = rc["proyecto_id"].astype(str)
        col_res = "resultado" if "resultado" in rc.columns else None
        if col_res:
            rc = rc[rc[col_res].notna() & (rc[col_res].astype(str).str.strip() != "")]
        id_res = set(rc["proyecto_id"])

    # n de comisiones giradas (conocido al ingresar, sin leakage)
    n_giros = pd.Series(0, index=exp["proyecto_id"], dtype="int64")
    comis_por_proy: dict[str, list] = {}
    if giros is not None and "proyecto_id" in giros.columns:
        g = giros.copy()
        g["proyecto_id"] = g["proyecto_id"].astype(str)
        cnt = g.groupby("proyecto_id").size()
        n_giros = cnt.reindex(exp["proyecto_id"]).fillna(0).astype("int64")
        if "comision" in g.columns:
            comis_por_proy = (g.dropna(subset=["comision"])
                              .groupby("proyecto_id")["comision"]
                              .apply(lambda s: sorted(set(s.astype(str)))).to_dict())

    c = pd.DataFrame({"proyecto_id": exp["proyecto_id"].values})
    c["fecha_publicacion"] = pd.to_datetime(
        exp["fecha_publicacion"].values, errors="coerce")
    c["anio"] = c["fecha_publicacion"].dt.year
    c["mes"] = c["fecha_publicacion"].dt.month
    c["camara_origen"] = (exp["camara_origen"].astype(str).str.strip().str.upper().values
                          if "camara_origen" in exp.columns else "NA")
    c["autor"] = (exp["autor"].astype(str).str.strip().values
                  if "autor" in exp.columns else "NA")
    c["n_giros"] = c["proyecto_id"].map(n_giros).fillna(0).astype("int64").values
    c["comisiones"] = c["proyecto_id"].map(comis_por_proy)

    ids = c["proyecto_id"]
    c["con_giro"] = ids.isin(id_giro)
    c["con_dictamen"] = ids.isin(id_dict)
    c["sancionado"] = ids.isin(id_ley)
    c["llega_recinto"] = ids.isin(id_res) | c["sancionado"]

    def etapa(r):
        if r["sancionado"]:
            return "5_sancionado"
        if r["llega_recinto"]:
            return "4_recinto"
        if r["con_dictamen"]:
            return "3_dictamen"
        if r["con_giro"]:
            return "2_comision"
        return "1_presentado"
    c["etapa_actual"] = c.apply(etapa, axis=1)
    return c


def cohorte_madura(c: pd.DataFrame, madurez: int = MADUREZ_ANIOS) -> pd.DataFrame:
    """Proyectos con anio valido y con tiempo suficiente para resolverse."""
    valido = c.dropna(subset=["anio"]).copy()
    if valido.empty:
        return valido
    corte = int(valido["anio"].max()) - madurez
    return valido[valido["anio"] <= corte]


# --------------------------------------------------------------------------- #
# Caracterizacion del embudo (descriptivo, no requiere sklearn)                #
# --------------------------------------------------------------------------- #
def medir_embudo(c: pd.DataFrame) -> dict:
    n = len(c)
    if n == 0:
        return {"n_presentados": 0}
    con_giro = int(c["con_giro"].sum())
    con_dict = int(c["con_dictamen"].sum())
    recinto = int(c["llega_recinto"].sum())
    sanc = int(c["sancionado"].sum())

    def pct(a, b):
        return round(100 * a / b, 2) if b else 0.0

    return {
        "n_presentados": n,
        "con_giro": con_giro,
        "con_dictamen": con_dict,
        "llega_recinto": recinto,
        "sancionado": sanc,
        # tasas absolutas (sobre presentados)
        "pct_con_dictamen": pct(con_dict, n),
        "pct_llega_recinto": pct(recinto, n),
        "pct_sancionado": pct(sanc, n),
        # transiciones condicionales (donde muere el embudo)
        "trans_dictamen_dado_giro": pct(con_dict, con_giro),
        "trans_recinto_dado_dictamen": pct(recinto, con_dict),
        "trans_sancion_dado_recinto": pct(sanc, recinto),
    }


def embudo_por_dimension(c: pd.DataFrame, dim: str) -> pd.DataFrame:
    filas = []
    for val, g in c.groupby(dim, dropna=False):
        m = medir_embudo(g)
        m[dim] = val
        filas.append(m)
    cols = [dim, "n_presentados", "pct_con_dictamen",
            "pct_llega_recinto", "pct_sancionado"]
    out = pd.DataFrame(filas)
    return out[[x for x in cols if x in out.columns]].sort_values("n_presentados",
                                                                  ascending=False)


def embudo_por_comision(c: pd.DataFrame) -> pd.DataFrame:
    """Tasa de supervivencia por comision: cementerios vs. comisiones rapidas."""
    filas = []
    exploded = c.explode("comisiones")
    exploded = exploded[exploded["comisiones"].notna()]
    for com, g in exploded.groupby("comisiones"):
        n = len(g)
        filas.append({
            "comision": com,
            "n_proyectos": n,
            "pct_con_dictamen": round(100 * g["con_dictamen"].mean(), 2),
            "pct_sancionado": round(100 * g["sancionado"].mean(), 2),
        })
    out = pd.DataFrame(filas)
    if out.empty:
        return out
    return out[out["n_proyectos"] >= 30].sort_values("pct_sancionado")


# --------------------------------------------------------------------------- #
# Rasgos para el modelo (sin leakage: solo lo conocido al presentar)           #
# --------------------------------------------------------------------------- #
def _top_comisiones(train: pd.DataFrame, k: int = TOP_COMISIONES) -> list:
    cont = (train.explode("comisiones")["comisiones"].dropna().value_counts())
    return list(cont.head(k).index)


def _tasa_autor(train: pd.DataFrame, target: str) -> tuple[dict, float]:
    """Tasa historica de exito por autor, calculada SOLO sobre train."""
    base = float(train[target].mean()) if len(train) else 0.0
    if "autor" not in train.columns:
        return {}, base
    g = train.groupby("autor")[target].agg(["mean", "size"])
    g = g[g["size"] >= 5]           # autores con historia suficiente
    return g["mean"].to_dict(), base


def construir_features(df: pd.DataFrame, top_com: list, tasa_autor: dict,
                       base_autor: float, feats_proy: pd.DataFrame | None = None
                       ) -> pd.DataFrame:
    """Matriz de rasgos. `top_com` / `tasa_autor` se derivan del TRAIN (sin leakage)."""
    X = pd.DataFrame(index=df.index)
    X["n_giros"] = df["n_giros"].fillna(0).astype(float)
    X["multi_comision"] = (df["n_giros"].fillna(0) > 1).astype(float)
    X["mes"] = df["mes"].fillna(0).astype(float)
    X["anio_electoral"] = (df["anio"].fillna(0).astype(int) % 2 == 1).astype(float)
    X["camara_senado"] = df["camara_origen"].astype(str).str.contains(
        "SENADO", case=False, na=False).astype(float)
    X["autor_tasa_hist"] = df["autor"].map(tasa_autor).fillna(base_autor).astype(float)
    # one-hot de las comisiones mas frecuentes
    coms = df["comisiones"]
    for com in top_com:
        X["com__" + str(com)[:40]] = coms.apply(
            lambda lst, cc=com: 1.0 if isinstance(lst, (list, tuple)) and cc in lst else 0.0)
    # hooks variables/proyecto (origen, lider, tema_*) - features_proyecto.parquet
    if feats_proy is not None and "proyecto_id" in feats_proy.columns:
        fp = feats_proy.drop_duplicates("proyecto_id").set_index(
            feats_proy.drop_duplicates("proyecto_id")["proyecto_id"].astype(str))
        idx = df["proyecto_id"].astype(str)
        if "origen" in fp.columns:
            og = idx.map(fp["origen"].astype(str).to_dict())
            for cat in ("EJECUTIVO", "OFICIALISMO", "OPOSICION"):
                X["origen_" + cat.lower()] = (og == cat).fillna(False).astype(float).values
        if "lider" in fp.columns:
            X["lider"] = idx.map(fp["lider"].astype(float).to_dict()).fillna(0.0).astype(float).values
        for col in [c for c in fp.columns if c.startswith("tema_")]:
            X["proy_" + col] = idx.map(fp[col].to_dict()).fillna(0).astype(float).values
    return X.fillna(0.0)


# --------------------------------------------------------------------------- #
# Backtest temporal walk-forward (sin leakage)                                 #
# --------------------------------------------------------------------------- #
def _metricas(y_true, y_pred) -> dict:
    import numpy as np
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    brier = float(((p - y) ** 2).mean())
    # AUC (Mann-Whitney), robusto a clases desbalanceadas
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) and len(neg):
        allr = pd.Series(p).rank().values
        auc = float((allr[y == 1].sum() - len(pos) * (len(pos) + 1) / 2)
                    / (len(pos) * len(neg)))
    else:
        auc = float("nan")
    # calibracion en 10 bins
    bins = np.clip((p * 10).astype(int), 0, 9)
    calib = []
    for b in range(10):
        m = bins == b
        if m.sum():
            calib.append({"bin": b, "n": int(m.sum()),
                          "pred": round(float(p[m].mean()), 4),
                          "real": round(float(y[m].mean()), 4)})
    return {"brier": round(brier, 5), "auc": round(auc, 4),
            "n": int(len(y)), "tasa_real": round(float(y.mean()), 4),
            "calibracion": calib}


def backtest_temporal(c: pd.DataFrame, target: str = "sancionado",
                      madurez: int = MADUREZ_ANIOS, min_train: int = MIN_TRAIN,
                      feats_proy: pd.DataFrame | None = None) -> dict:
    """Walk-forward: entrena con anios < T (maduros), predice el anio T."""
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
    except ImportError as e:
        raise RuntimeError("backtest requiere scikit-learn (pip install scikit-learn)") from e

    mad = cohorte_madura(c, madurez)
    anios = sorted(int(a) for a in mad["anio"].dropna().unique())
    y_true, y_pred, y_base = [], [], []
    folds = []
    for T in anios:
        train = mad[mad["anio"] < T]
        test = mad[mad["anio"] == T]
        if len(train) < min_train or test.empty:
            continue
        top_com = _top_comisiones(train)
        tasa_autor, base_autor = _tasa_autor(train, target)
        Xtr = construir_features(train, top_com, tasa_autor, base_autor, feats_proy)
        Xte = construir_features(test, top_com, tasa_autor, base_autor, feats_proy).reindex(
            columns=Xtr.columns, fill_value=0.0)
        ytr = train[target].astype(int).values
        if ytr.sum() == 0 or ytr.sum() == len(ytr):
            continue
        modelo = make_pipeline(StandardScaler(with_mean=False),
                               LogisticRegression(max_iter=1000))
        modelo.fit(Xtr, ytr)
        p = modelo.predict_proba(Xte)[:, 1]
        base = float(ytr.mean())
        yte = test[target].astype(int).values
        y_true += list(yte); y_pred += list(p); y_base += [base] * len(yte)
        folds.append({"anio": T, "n_train": len(train), "n_test": len(test),
                      **_metricas(yte, p), "brier_base": round(
                          float(((base - yte) ** 2).mean()), 5)})
    if not y_true:
        return {"error": "sin folds suficientes", "target": target}
    glob = _metricas(y_true, y_pred)
    import numpy as np
    brier_base = float(((np.asarray(y_base) - np.asarray(y_true)) ** 2).mean())
    skill = 1 - glob["brier"] / brier_base if brier_base else float("nan")
    return {"target": target, "madurez_anios": madurez,
            "global": glob, "brier_baseline_tasabase": round(brier_base, 5),
            "skill_score": round(skill, 4), "folds": folds}


def entrenar_y_scorear(c: pd.DataFrame, target: str,
                       feats_proy: pd.DataFrame | None, madurez: int = MADUREZ_ANIOS
                       ) -> pd.Series:
    """Modelo final sobre toda la cohorte madura; scorea TODOS los proyectos."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    train = cohorte_madura(c, madurez)
    top_com = _top_comisiones(train)
    tasa_autor, base_autor = _tasa_autor(train, target)
    Xtr = construir_features(train, top_com, tasa_autor, base_autor, feats_proy)
    ytr = train[target].astype(int).values
    modelo = make_pipeline(StandardScaler(with_mean=False),
                           LogisticRegression(max_iter=1000))
    modelo.fit(Xtr, ytr)
    Xall = construir_features(c, top_com, tasa_autor, base_autor, feats_proy).reindex(
        columns=Xtr.columns, fill_value=0.0)
    return pd.Series(modelo.predict_proba(Xall)[:, 1], index=c.index)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _rutas():
    root = Path(__file__).resolve()
    clean = Path(os.environ.get(
        "EXP_CLEAN", root.parents[3] / "datos" / "expedientes" / "data" / "clean"))
    out = Path(os.environ.get("OUT", root.parents[1] / "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    feats = root.parents[3] / "variables" / "proyecto" / "data" / "features_proyecto.parquet"
    return clean, out, (feats if feats.exists() else None)


def cmd_funnel(c: pd.DataFrame, out: Path) -> None:
    glob = medir_embudo(c)
    logger.info("EMBUDO global: %s", glob)
    por_anio = embudo_por_dimension(c, "anio")
    por_cam = embudo_por_dimension(c, "camara_origen")
    etapas = pd.DataFrame([{"nivel": "global", **glob}])
    etapas.to_csv(out / "embudo_etapas.csv", index=False)
    por_anio.to_csv(out / "embudo_por_anio.csv", index=False)
    por_cam.to_csv(out / "embudo_por_camara.csv", index=False)
    embudo_por_comision(c).to_csv(out / "embudo_por_comision.csv", index=False)
    extra = []
    for dim in ("origen", "lider"):
        if dim in c.columns:
            embudo_por_dimension(c, dim).to_csv(out / f"embudo_por_{dim}.csv", index=False)
            extra.append(f"embudo_por_{dim}.csv")
    print("\n=== EMBUDO (global, proyectos de LEY) ===")
    for k, v in glob.items():
        print(f"  {k:32s} {v}")
    print(f"\n  -> outputs: embudo_etapas.csv, embudo_por_anio.csv, "
          f"embudo_por_camara.csv, embudo_por_comision.csv"
          + (", " + ", ".join(extra) if extra else ""))


def cmd_modelo(c: pd.DataFrame, out: Path, feats_proy) -> None:
    resumen = {}
    for target in ("sancionado", "llega_recinto"):
        bt_base = backtest_temporal(c, target=target, feats_proy=None)
        bt = backtest_temporal(c, target=target, feats_proy=feats_proy) if feats_proy is not None else bt_base
        resumen[target] = bt
        resumen[target + "_sin_origen_lider"] = bt_base
        g, gb = bt.get("global", {}), bt_base.get("global", {})
        print(f"\n=== BACKTEST target={target} ===")
        print(f"  SIN origen/líder:  skill {bt_base.get('skill_score')} | AUC {gb.get('auc')} | Brier {gb.get('brier')}")
        print(f"  CON origen/líder:  skill {bt.get('skill_score')} | AUC {g.get('auc')} | Brier {g.get('brier')} | n {g.get('n')}")
    (out / "backtest_embudo.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    # contrato de salida: P por proyecto
    p_rec = entrenar_y_scorear(c, "llega_recinto", feats_proy)
    p_san = entrenar_y_scorear(c, "sancionado", feats_proy)
    salida = c[["proyecto_id", "anio", "etapa_actual"]].copy()
    salida["p_llega_recinto"] = p_rec.round(4).values
    salida["p_sancion"] = p_san.round(4).values
    salida.to_parquet(out / "p_embudo.parquet", index=False)
    print(f"\n  -> outputs: backtest_embudo.json, p_embudo.parquet ({len(salida):,} proyectos)")


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cmd = argv[1] if len(argv) > 1 else "all"
    clean, out, feats_path = _rutas()
    dfs = cargar(clean)
    c = construir_cohorte(dfs)
    logger.info("cohorte: %d proyectos de LEY", len(c))
    feats_proy = pd.read_parquet(feats_path) if feats_path else None
    if feats_proy is not None:
        cols_seg = [x for x in ("proyecto_id", "origen", "lider") if x in feats_proy.columns]
        c = c.merge(feats_proy[cols_seg].drop_duplicates("proyecto_id"), on="proyecto_id", how="left")
        logger.info("features_proyecto enchufado: %s", [x for x in cols_seg if x != "proyecto_id"])
    if cmd in ("funnel", "all"):
        cmd_funnel(c, out)
    if cmd in ("modelo", "all"):
        cmd_modelo(c, out, feats_proy)


if __name__ == "__main__":
    main(sys.argv)
