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
`tema_*`, el modelo las incorpora automaticamente.

ICG (contexto politico, 2026-08-04): si existe `variables/proyecto/data/
icg_mensual.csv` entran `icg`, `icg_delta_3m` e `icg_sin_dato`, REZAGADOS un mes
(el proyecto presentado en M ve el ICG de M-1: anti-leakage duro). Es la unica
variable no procedimental del modelo. `cmd_modelo` imprime la ablacion de tres
escalones (procedimental / +origen-lider / +ICG) para que el aporte del ICG sea
atribuible y no un numero de fe.

4 directivas: errores especificos, backoff (n/a: I/O local), parsing defensivo
(columnas por nombre, tolerante a NA), logging estructurado.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import tempfile
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("embudo")

MADUREZ_ANIOS = 2          # cohorte madura = presentada <= (ultimo_anio - MADUREZ_ANIOS)
TOP_COMISIONES = 25        # cuantas comisiones entran como rasgo one-hot
MIN_TRAIN = 500            # minimo de proyectos de train para intentar un fold
ICG_LAG_MESES = 1          # el ICG entra REZAGADO: el del mes ANTERIOR (anti-leakage)
ICG_DELTA_MESES = 3        # ventana de la variacion (icg_delta_3m)


# --------------------------------------------------------------------------- #
# ICG - Indice de Confianza en el Gobierno (UTDT). Unica variable de CONTEXTO  #
# POLITICO del modelo; el resto de los rasgos son procedimentales.             #
#                                                                             #
# ANTI-LEAKAGE (regla dura): un proyecto presentado en el mes M ve el ICG de   #
# M-1, nunca el de M. El ICG de M se publica DESPUES de que el mes termino, y  #
# ademas el clima del propio mes ya esta contaminado por lo que pasa con el    #
# proyecto. Se usa el nivel (icg) y la variacion a 3 meses (icg_delta_3m): la  #
# hipotesis de Franco es que la DERIVA importa mas que el NIVEL (un gobierno   #
# en 2,0 subiendo no es lo mismo que uno en 2,0 cayendo).                      #
# --------------------------------------------------------------------------- #
def cargar_icg(path: Path | None) -> dict | None:
    """Lee icg_mensual.csv -> {(anio, mes): {"icg": x, "icg_delta_3m": y}}.

    Devuelve None si el archivo no existe (el modelo corre igual, sin la
    variable). Parsing defensivo: exige las columnas anio/mes/icg y descarta
    filas rotas en vez de explotar.
    """
    if path is None or not Path(path).exists():
        logger.warning("no encontre icg_mensual.csv - el modelo corre SIN contexto politico")
        return None
    try:
        d = pd.read_csv(path)
    except (OSError, ValueError) as e:
        logger.error("no pude leer el ICG (%s): %s", path, e)
        return None
    faltan = {"anio", "mes", "icg"} - set(d.columns)
    if faltan:
        logger.error("icg_mensual.csv sin columnas %s - lo ignoro", sorted(faltan))
        return None
    d = d.dropna(subset=["anio", "mes", "icg"]).copy()
    d["anio"] = d["anio"].astype(int)
    d["mes"] = d["mes"].astype(int)
    d["icg"] = d["icg"].astype(float)
    d = d.sort_values(["anio", "mes"]).drop_duplicates(["anio", "mes"], keep="last")
    # la variacion se calcula sobre la serie mensual ORDENADA y continua
    d["icg_delta_3m"] = d["icg"].diff(ICG_DELTA_MESES)
    tabla = {(int(r.anio), int(r.mes)): {"icg": float(r.icg),
                                         "icg_delta_3m": (float(r.icg_delta_3m)
                                                          if pd.notna(r.icg_delta_3m) else None)}
             for r in d.itertuples()}
    logger.info("ICG cargado: %d meses (%d-%02d -> %d-%02d)", len(tabla),
                d["anio"].iloc[0], d["mes"].iloc[0], d["anio"].iloc[-1], d["mes"].iloc[-1])
    return tabla


def _mes_rezagado(anio, mes, lag: int = ICG_LAG_MESES):
    """(anio, mes) - lag meses. Devuelve None si la fecha no es utilizable."""
    try:
        a, m = int(anio), int(mes)
    except (TypeError, ValueError):
        return None
    if not (1 <= m <= 12) or a < 1900:
        return None
    total = a * 12 + (m - 1) - lag
    return total // 12, total % 12 + 1


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
        # opcional: giro AL INGRESAR (ver datos/expedientes/src/giros_iniciales.py)
        "giros_iniciales": "giros_iniciales.parquet",
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


def cargar_sqlite(db_path: Path) -> dict[str, pd.DataFrame]:
    """Mismo contrato que `cargar()`, pero leido de `proyectos.db` (ADR-0009).

    Devuelve EXACTAMENTE las mismas claves y columnas que la ruta de parquet, y
    sigue usando `proyecto_id` como llave. Eso es a proposito: la etapa 1 del
    ADR-0009 es una MUDANZA, no un cambio de modelo. Si esta funcion devolviera
    algo distinto, el test de aceptacion (mismo skill por las dos rutas) no
    podria distinguir un error de carga de una mejora real.

    El cambio de llave a `denominador` es de una etapa posterior, y se hara
    cuando esta ruta ya este validada.
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"no existe {db_path}. Corre antes: "
            "python datos/proyectos/src/migrar_ckan.py")

    # El mount de la carpeta del proyecto no soporta el file locking de SQLite
    # (`disk I/O error`, comprobado 07-08-2026). Se lee una copia local. En
    # Windows no hace falta, pero copiar 88 MB es barato y no rompe nada.
    tmp = Path(tempfile.gettempdir()) / "proyectos_lectura.db"
    try:
        shutil.copyfile(db_path, tmp)
        origen = tmp
    except OSError as e:
        logger.warning("no pude copiar la base a local (%s); la leo en su lugar", e)
        origen = Path(db_path)

    con = sqlite3.connect(str(origen))
    try:
        q = lambda sql: pd.read_sql_query(sql, con)  # noqa: E731
        dfs = {
            # COALESCE, no `proyecto_id` a secas: las altas del bot NO tienen id de
            # CKAN (todavia no lo publico), y `construir_cohorte` hace
            # `astype(str)` + `drop_duplicates("proyecto_id")` — con lo cual TODOS
            # los nulos se vuelven el string "None" y colapsan a UNA fila. Sin
            # esto, cargar 671 leyes nuevas sumaba +1 proyecto a la cohorte, sin
            # error y sin warning. Para los de CKAN el COALESCE devuelve lo mismo,
            # asi que la equivalencia entre las dos rutas se mantiene.
            "expedientes": q("""
                SELECT COALESCE(proyecto_id, denominador) AS proyecto_id,
                       sumario AS titulo, fecha_ingreso AS fecha_publicacion,
                       camara AS camara_origen, denominador AS exp_diputados,
                       exp_senado, tipo,
                       (SELECT nombre FROM proyecto_autores a
                         WHERE a.denominador = p.denominador AND a.orden = 0) AS autor
                  FROM proyectos p"""),
            "giros": q("""
                SELECT COALESCE(pr.proyecto_id, pr.denominador) AS proyecto_id, g.comision
                  FROM proyecto_giros g JOIN proyectos pr USING (denominador)"""),
            "dictamenes": q("""
                SELECT COALESCE(pr.proyecto_id, pr.denominador) AS proyecto_id FROM proyecto_hitos h
                  JOIN proyectos pr USING (denominador) WHERE h.hito = 'dictamen'"""),
            "movimientos": q("""
                SELECT COALESCE(pr.proyecto_id, pr.denominador) AS proyecto_id, t.movimiento, t.fecha
                  FROM proyecto_tramite t JOIN proyectos pr USING (denominador)"""),
            "resultados": q("""
                SELECT COALESCE(pr.proyecto_id, pr.denominador) AS proyecto_id, h.detalle AS resultado, h.fecha
                  FROM proyecto_hitos h JOIN proyectos pr USING (denominador)
                 WHERE h.hito = 'resultado'"""),
            "leyes": q("""
                SELECT COALESCE(pr.proyecto_id, pr.denominador) AS proyecto_id FROM proyecto_hitos h
                  JOIN proyectos pr USING (denominador) WHERE h.hito = 'ley'"""),
        }
        gi = q("""SELECT COALESCE(proyecto_id, denominador) AS proyecto_id,
                          n_giros_inicial, n_giros_inicial_fuente AS fuente
                    FROM proyectos WHERE n_giros_inicial IS NOT NULL""")
        if len(gi):
            dfs["giros_iniciales"] = gi
    finally:
        con.close()

    # `camara_origen` viaja en minuscula en la base y en capitalizado en el
    # parquet. `construir_cohorte` hace .upper(), asi que da igual — pero se
    # normaliza igual para que un diff de las dos rutas no muestre ruido.
    if "camara_origen" in dfs["expedientes"].columns:
        dfs["expedientes"]["camara_origen"] = (
            dfs["expedientes"]["camara_origen"].astype(str).str.capitalize())

    logger.info("SQLite: %s", {k: len(v) for k, v in dfs.items()})
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

    # HOOK: giro AL INGRESAR (contrato de datos/expedientes, 2026-08-07).
    # `expedientes_giros` es el acumulado de HOY; una parte de los proyectos recibe
    # ampliación de giro despues de presentado y esos avanzan 1,6x mas, o sea que
    # para ellos el rasgo miraba un pedazo del futuro. Si existe el parquet, se usa
    # el giro medido/reconstruido al ingresar; si no, sigue el acumulado (contrato
    # intacto). Auditoria completa en ESTADO 07-08: el efecto es acotado (91,8% de
    # los proyectos no cambia) pero corregirlo SUBE el skill.
    gi = dfs.get("giros_iniciales")
    if gi is not None and {"proyecto_id", "n_giros_inicial"} <= set(gi.columns):
        serie = gi.drop_duplicates("proyecto_id").set_index("proyecto_id")["n_giros_inicial"]
        m = c["proyecto_id"].map(serie)
        cambian = int((m.notna() & (m != c["n_giros"])).sum())
        c["n_giros"] = m.fillna(c["n_giros"]).astype("int64")
        logger.info("giros_iniciales enchufado: %d proyectos con el giro corregido", cambian)

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


def _como_lista(v) -> list:
    """Normaliza el campo `comisiones` a lista, venga de donde venga.

    Tolera list/tuple (cohorte en memoria), numpy.ndarray (cohorte leida de
    parquet) y NA. Cualquier cosa que no sea iterable o sea texto -> [].
    """
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, str):
        return []
    try:
        if pd.isna(v):
            return []
    except (TypeError, ValueError):
        pass                      # arrays: pd.isna devuelve un array, no un bool
    try:
        return list(v)
    except TypeError:
        return []


def construir_features(df: pd.DataFrame, top_com: list, tasa_autor: dict,
                       base_autor: float, feats_proy: pd.DataFrame | None = None,
                       icg: dict | None = None) -> pd.DataFrame:
    """Matriz de rasgos. `top_com` / `tasa_autor` se derivan del TRAIN (sin leakage)."""
    X = pd.DataFrame(index=df.index)
    X["n_giros"] = df["n_giros"].fillna(0).astype(float)
    X["multi_comision"] = (df["n_giros"].fillna(0) > 1).astype(float)
    X["mes"] = df["mes"].fillna(0).astype(float)
    X["anio_electoral"] = (df["anio"].fillna(0).astype(int) % 2 == 1).astype(float)
    X["camara_senado"] = df["camara_origen"].astype(str).str.contains(
        "SENADO", case=False, na=False).astype(float)
    X["autor_tasa_hist"] = df["autor"].map(tasa_autor).fillna(base_autor).astype(float)
    # one-hot de las comisiones mas frecuentes.
    # VECTORIZADO (2026-08-04): antes eran 25 `.apply` sobre 41k filas POR FOLD,
    # y con la ablacion de 3 escalones x 2 targets x ~15 folds el backtest no
    # terminaba en media hora. Un explode + pivot hace lo mismo en una pasada.
    # El resultado es identico (lo verifica test_embudo); cambia solo el costo.
    cols_com = ["com__" + str(c)[:40] for c in top_com]
    for c_ in cols_com:
        X[c_] = 0.0
    if top_com:
        listas = df["comisiones"]
        # PARSING DEFENSIVO (2026-08-04): NO usar isinstance(v, (list, tuple)).
        # Al persistir la cohorte en parquet, pandas devuelve las listas como
        # numpy.ndarray, y ese isinstance las rechaza EN SILENCIO: las 25
        # columnas de comisiones quedan todas en cero y el modelo pierde su
        # segundo bloque de rasgos sin que nada falle ni avise. Pasó de verdad
        # el 04-08 y contaminó una medición entera del aporte del ICG.
        # Se acepta cualquier iterable que no sea texto.
        listas = listas.map(_como_lista)
        mask = listas.map(len) > 0
        if bool(mask.any()):
            ex = listas[mask].explode()
            ex = ex[ex.isin(set(top_com))]
            if len(ex):
                pres = pd.crosstab(ex.index, ex).clip(upper=1).astype(float)
                pres.columns = ["com__" + str(c)[:40] for c in pres.columns]
                pres = pres.reindex(index=df.index, columns=cols_com,
                                    fill_value=0.0).fillna(0.0)
                X[cols_com] = pres[cols_com].values
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
    # contexto politico: ICG del mes ANTERIOR a la presentacion (nunca el del mes)
    if icg:
        clave = [_mes_rezagado(a, m) for a, m in zip(df["anio"], df["mes"])]
        vals = [icg.get(k) if k else None for k in clave]
        nivel = [v["icg"] if v else None for v in vals]
        delta = [v["icg_delta_3m"] if v else None for v in vals]
        s_niv = pd.Series(nivel, index=df.index, dtype="float64")
        s_del = pd.Series(delta, index=df.index, dtype="float64")
        # los faltantes (proyecto anterior a nov-2001, o mes sin dato) van a la
        # MEDIA de la propia serie: neutro, no inventa un clima que no se midio
        media = float(pd.Series([v["icg"] for v in icg.values()]).mean())
        X["icg"] = s_niv.fillna(media).astype(float)
        X["icg_delta_3m"] = s_del.fillna(0.0).astype(float)
        X["icg_sin_dato"] = s_niv.isna().astype(float)   # el modelo sabe cuando no vio nada
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
                      feats_proy: pd.DataFrame | None = None,
                      icg: dict | None = None) -> dict:
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
        Xtr = construir_features(train, top_com, tasa_autor, base_autor, feats_proy, icg)
        Xte = construir_features(test, top_com, tasa_autor, base_autor, feats_proy, icg).reindex(
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
            "con_icg": bool(icg), "con_origen_lider": feats_proy is not None,
            "global": glob, "brier_baseline_tasabase": round(brier_base, 5),
            "skill_score": round(skill, 4), "folds": folds}


def entrenar_y_scorear(c: pd.DataFrame, target: str,
                       feats_proy: pd.DataFrame | None, madurez: int = MADUREZ_ANIOS,
                       icg: dict | None = None) -> pd.Series:
    """Modelo final sobre toda la cohorte madura; scorea TODOS los proyectos."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    train = cohorte_madura(c, madurez)
    top_com = _top_comisiones(train)
    tasa_autor, base_autor = _tasa_autor(train, target)
    Xtr = construir_features(train, top_com, tasa_autor, base_autor, feats_proy, icg)
    ytr = train[target].astype(int).values
    modelo = make_pipeline(StandardScaler(with_mean=False),
                           LogisticRegression(max_iter=1000))
    modelo.fit(Xtr, ytr)
    Xall = construir_features(c, top_com, tasa_autor, base_autor, feats_proy, icg).reindex(
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
    icg = Path(os.environ.get(
        "ICG_CSV", root.parents[3] / "variables" / "proyecto" / "data" / "icg_mensual.csv"))
    # ADR-0009: si existe proyectos.db se lee de ahi. `EMBUDO_FUENTE=parquet`
    # fuerza la ruta vieja — es lo que permite correr las dos y compararlas.
    db = Path(os.environ.get(
        "PROYECTOS_DB", root.parents[3] / "datos" / "proyectos" / "data" / "proyectos.db"))
    return (clean, out, (feats if feats.exists() else None),
            (icg if icg.exists() else None), (db if db.exists() else None))


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


def cmd_modelo(c: pd.DataFrame, out: Path, feats_proy, icg: dict | None = None) -> None:
    """Backtest con ABLACION explicita: cada rasgo nuevo tiene que ganarse el lugar.

    Tres escalones acumulativos, para poder atribuir el aporte de cada bloque:
      (1) solo procedimental (giros, comisiones, autor, calendario)
      (2) + origen/lider (variables/proyecto)      -> aporto +0,020 el 12-jul
      (3) + ICG (contexto politico)                -> lo que se mide aca
    El delta que importa es (3)-(2): que agrega el clima politico POR ENCIMA de
    lo que ya explican el tramite y quien firma.
    """
    resumen = {}
    for target in ("sancionado", "llega_recinto"):
        bt_base = backtest_temporal(c, target=target, feats_proy=None, icg=None)
        bt = (backtest_temporal(c, target=target, feats_proy=feats_proy, icg=None)
              if feats_proy is not None else bt_base)
        bt_icg = (backtest_temporal(c, target=target, feats_proy=feats_proy, icg=icg)
                  if icg else None)
        resumen[target] = bt_icg or bt
        resumen[target + "_sin_origen_lider"] = bt_base
        resumen[target + "_sin_icg"] = bt
        g, gb = bt.get("global", {}), bt_base.get("global", {})
        print(f"\n=== BACKTEST target={target} ===")
        print(f"  (1) solo procedimental:   skill {bt_base.get('skill_score')} | AUC {gb.get('auc')} | Brier {gb.get('brier')}")
        print(f"  (2) + origen/líder:       skill {bt.get('skill_score')} | AUC {g.get('auc')} | Brier {g.get('brier')} | n {g.get('n')}")
        if bt_icg:
            gi = bt_icg.get("global", {})
            d = (bt_icg.get("skill_score") or 0) - (bt.get("skill_score") or 0)
            resumen[target + "_delta_icg"] = round(d, 4)
            print(f"  (3) + ICG (contexto):     skill {bt_icg.get('skill_score')} | AUC {gi.get('auc')} | Brier {gi.get('brier')}")
            print(f"      -> APORTE DEL ICG: {d:+.4f} de skill  "
                  f"({'SUMA' if d > 0.002 else 'NEUTRO' if d > -0.002 else 'RESTA'})")
        else:
            print("  (3) ICG: NO disponible (falta icg_mensual.csv)")
    (out / "backtest_embudo.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    # contrato de salida: P por proyecto (el modelo de produccion usa TODO lo que suma)
    p_rec = entrenar_y_scorear(c, "llega_recinto", feats_proy, icg=icg)
    p_san = entrenar_y_scorear(c, "sancionado", feats_proy, icg=icg)
    salida = c[["proyecto_id", "anio", "etapa_actual"]].copy()
    salida["p_llega_recinto"] = p_rec.round(4).values
    salida["p_sancion"] = p_san.round(4).values
    salida.to_parquet(out / "p_embudo.parquet", index=False)
    print(f"\n  -> outputs: backtest_embudo.json, p_embudo.parquet ({len(salida):,} proyectos)")


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cmd = argv[1] if len(argv) > 1 else "all"
    clean, out, feats_path, icg_path, db = _rutas()
    icg = cargar_icg(icg_path)
    fuente = os.environ.get("EMBUDO_FUENTE", "auto").lower()
    if fuente == "parquet" or db is None:
        logger.info("FUENTE: parquet (%s)", clean)
        dfs = cargar(clean)
    else:
        logger.info("FUENTE: sqlite (%s)", db)
        dfs = cargar_sqlite(db)
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
        cmd_modelo(c, out, feats_proy, icg)


if __name__ == "__main__":
    main(sys.argv)
