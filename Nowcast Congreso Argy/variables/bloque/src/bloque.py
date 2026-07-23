"""variables/bloque - serie temporal por bloque + proyector de postura.

Produce, para cada bloque (linaje) a lo largo del tiempo:
  - TAMAÑO (bancas activas),
  - POSTURA: reparto de dirección AFIRMATIVO/NEGATIVO entre los que EMITIERON,
  - COHESIÓN (índice de Rice) y su complemento, el DESVÍO interno,
  - FRACTURAS: actas donde el bloque se parte (cohesión baja).

Y un PROYECTOR point-in-time que, dada una fecha y cámara, devuelve el escenario
por bloque {bloque, bancas, linea, desvio} que consume el ensemble/agregador —
hoy ese escenario se pone A MANO. Walk-forward: solo usa historia ANTERIOR a la
fecha (sin leakage).

Contrato de entrada : datos/canonica/data/clean/{votos_resuelto,actas_canonico}.parquet
Contrato de salida  : variables/bloque/outputs/serie_bloque.parquet

SEMÁNTICA (idéntica al agregador, para que el escenario encaje sin traducir):
  linea  in {AFIRMATIVO, NEGATIVO, NO_ACOMPANA}  -> dirección esperada del bloque.
  desvio in [0,1]                                -> tasa de ruptura interna (cohesión inversa).
El agregador reparte ese desvío entre las otras conductas (reparto_desvio).

v2 (2026-07-22): la DIRECCIÓN puede CONDICIONARSE por TEMA/ORIGEN del proyecto
(parámetros tema/origen/cond_por_acta de proyectar_postura), consumiendo el contrato
variables/proyecto/data/tema_por_acta.parquet. Sin tema/origen la dirección es la
INCONDICIONAL del v1 (tendencia reciente) -> retrocompatible. El DESVÍO/cohesión ya
salía bien en v1: es lo que el ensemble necesita para calibrar su banda.

4 directivas: errores específicos, parsing defensivo, logging estructurado.
(No hay I/O de red en este módulo; por eso no hay backoff de red.)
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("bloque")

# --- conductas (mismo vocabulario que modelo/agregador_institucional) ---------
CONDUCTA_MAP = {
    "AFIRMATIVO": "AFIRMATIVO",
    "NEGATIVO": "NEGATIVO",
    "ABSTENCION": "NO_ACOMPANA",
    "AUSENTE": "NO_ACOMPANA",
}
SUSTANTIVAS = ("AFIRMATIVO", "NEGATIVO")  # las que "emiten" dirección

DEFAULT_CANON = Path("datos/canonica/data/clean")
OUT_DEFAULT = Path("variables/bloque/outputs/serie_bloque.parquet")
DEFAULT_PADRON_DIR = Path(__file__).resolve().parents[3] / "datos" / "padron" / "data"

# --------------------------------------------------------------------------- #
# Enriquecimiento de LINAJE del Senado (contribución al entity_resolution).    #
# Los votos del Senado 2024+ (fuente argentinadatos) llegan con bloque="SIN    #
# BLOQUE" -> linaje "OTRO / PROVINCIAL" para TODOS: la ingesta no resolvió el   #
# bloque. Acá se recupera el linaje real por NOMBRE contra el padrón oficial    #
# (datos/padron, contrato que ya consumimos), RESPETANDO EL MANDATO (la fecha   #
# del voto cae en [desde,hasta] del senador) para no anacronizar. Los que ya no #
# están en el padrón (dejaron banca en un recambio) se completan a mano en      #
# senado_linaje_manual.csv (curado). NO edita datos/canonica; es una capa de    #
# consumo. Propuesta: que datos/canonica/entity_resolution (Franco) lo absorba. #
_LINAJE_GENERICO = {"", "OTRO / PROVINCIAL", "SIN BLOQUE", "OTRO", "NONE", "NAN"}

# Linajes canónicos (los strings EXACTOS que usa datos/canonica). El override manual
# del Senado se completa a mano, así que toleramos variantes (ej. "FdT-UxP" sin el
# sufijo) y las llevamos al canónico para no partir un bloque en dos al agregar.
_LINAJES_CANON = {
    "FdT-UxP (kirchnerismo)", "OTRO / PROVINCIAL", "RADICALISMO", "PERONISMO FEDERAL",
    "PRO", "COALICION CIVICA", "PROGRESISMO", "FRENTE RENOVADOR (massismo)",
    "LA LIBERTAD AVANZA", "IZQUIERDA",
}


def _canon_linaje(v):
    """Lleva una etiqueta de linaje escrita a mano a su forma canónica. Devuelve el
    string tal cual si ya es canónico; None si viene vacío/genérico."""
    if v is None:
        return None
    t = " ".join(str(v).strip().split())
    if not t or t.upper() in _LINAJE_GENERICO:
        return None
    if t in _LINAJES_CANON:
        return t
    u = t.upper()
    if "KIRCHner".upper() in u or u.startswith("FDT") or "UXP" in u or "UNION POR LA PATRIA" in u:
        return "FdT-UxP (kirchnerismo)"
    if "LIBERTAD AVANZA" in u or u == "LLA":
        return "LA LIBERTAD AVANZA"
    if "RADICAL" in u or u == "UCR":
        return "RADICALISMO"
    if "PERONISMO FEDERAL" in u:
        return "PERONISMO FEDERAL"
    if "COALICION CIVICA" in u or u == "CC":
        return "COALICION CIVICA"
    if "PROGRESISMO" in u:
        return "PROGRESISMO"
    if "RENOVADOR" in u or "MASSISMO" in u:
        return "FRENTE RENOVADOR (massismo)"
    if u == "PRO" or "PROPUESTA REPUBLICANA" in u:
        return "PRO"
    if "IZQUIERDA" in u:
        return "IZQUIERDA"
    return t  # desconocido: se respeta tal cual (mejor no perder el dato)


def _norm_nombre(s) -> str:
    """APELLIDO NOMBRE sin acentos/puntuación (misma convención que origen_lider)."""
    import unicodedata
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    t = str(s).strip()
    if "," in t:
        ap, _, no = t.partition(",")
        t = f"{ap} {no}"
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = "".join(c if c.isalnum() or c.isspace() else " " for c in t)
    return " ".join(t.upper().split())


def _cargar_padron_linaje_senado(padron_dir=None):
    """Devuelve (tramos, manual): tramos = lista (nn, desde, hasta, linaje) del padrón
    del Senado; manual = dict nn->linaje del override curado (senadores que ya no están
    en el padrón). Ambos vacíos si faltan los archivos (degradación limpia)."""
    base = Path(padron_dir or DEFAULT_PADRON_DIR)
    tramos, manual = [], {}
    pcsv = base / "padron_senado.csv"
    if pcsv.exists():
        pad = pd.read_csv(pcsv, dtype=str, encoding="utf-8-sig")
        if {"legislador", "bloque_linaje"} <= set(pad.columns):
            for _, r in pad.iterrows():
                tramos.append((_norm_nombre(r["legislador"]),
                               pd.to_datetime(r.get("desde"), errors="coerce"),
                               pd.to_datetime(r.get("hasta"), errors="coerce"),
                               r.get("bloque_linaje")))
    mcsv = base / "senado_linaje_manual.csv"
    if mcsv.exists():
        man = pd.read_csv(mcsv, dtype=str, encoding="utf-8-sig", comment="#")
        col_clave = "clave_norm" if "clave_norm" in man.columns else man.columns[0]
        if "linaje" in man.columns:
            for _, r in man.iterrows():
                lin = _canon_linaje(r.get("linaje"))
                if lin:
                    manual[_norm_nombre(r[col_clave])] = lin
    return tramos, manual


def _enriquecer_linaje_senado(df, padron_dir=None):
    """Reasigna bloque_linaje de las filas del SENADO cuyo linaje es genérico
    (OTRO/PROVINCIAL, SIN BLOQUE, vacío) usando el nombre del legislador contra el
    padrón (mandate-aware) y el override manual. Solo mueve hacia un linaje ESPECÍFICO:
    si el padrón también dice OTRO/PROVINCIAL, no cambia nada. Requiere columnas
    'camara', 'bloque_linaje', 'legislador_nombre', 'fecha'. Devuelve (df, n_cambiadas)."""
    if df.empty or "legislador_nombre" not in df.columns:
        return df, 0
    tramos, manual = _cargar_padron_linaje_senado(padron_dir)
    if not tramos and not manual:
        return df, 0
    from collections import defaultdict
    def _k2(nn):  # apellido + primer nombre (fallback robusto: el padrón abrevia)
        t = nn.split(); return " ".join(t[:2])
    por_nn = defaultdict(list)
    por_k2 = defaultdict(list)
    for nn, desde, hasta, lin in tramos:
        por_nn[nn].append((desde, hasta, lin))
        por_k2[_k2(nn)].append((desde, hasta, lin))

    es_sen = df["camara"].astype(str).str.lower().eq("senado")
    generico = df["bloque_linaje"].astype(str).str.strip().str.upper().isin(_LINAJE_GENERICO)
    objetivo = es_sen & generico
    if not objetivo.any():
        return df, 0
    nn_col = df["legislador_nombre"].map(_norm_nombre)
    fechas = pd.to_datetime(df["fecha"], errors="coerce")

    def _en_ventana(f, desde, hasta):
        return ((pd.isna(desde) or (pd.notna(f) and f >= desde)) and
                (pd.isna(hasta) or (pd.notna(f) and f <= hasta)))

    def _resolver(nn, f):
        for desde, hasta, lin in por_nn.get(nn, ()):
            if _en_ventana(f, desde, hasta) and str(lin).strip().upper() not in _LINAJE_GENERICO:
                return lin
        # fallback: apellido + primer nombre (el padrón suele abreviar el 2º nombre)
        cand = por_k2.get(_k2(nn), ())
        if len(cand) == 1 or len({l for _, _, l in cand}) == 1:  # sin ambigüedad
            for desde, hasta, lin in cand:
                if _en_ventana(f, desde, hasta) and str(lin).strip().upper() not in _LINAJE_GENERICO:
                    return lin
        m = manual.get(nn)
        if m and str(m).strip().upper() not in _LINAJE_GENERICO:
            return m
        return None

    nuevos = df["bloque_linaje"].copy()
    n = 0
    for i in df.index[objetivo]:
        r = _resolver(nn_col.at[i], fechas.at[i])
        if r is not None:
            nuevos.at[i] = r
            n += 1
    df = df.copy()
    df["bloque_linaje"] = nuevos
    if n:
        logger.info("enriquecí linaje del Senado: %d votos reasignados desde el padrón/override", n)
    return df, n



# --------------------------------------------------------------------------- #
# Carga (contrato de la canónica)                                             #
# --------------------------------------------------------------------------- #
def cargar(canon_dir: Path = DEFAULT_CANON, enriquecer_senado: bool = True,
           padron_dir=None) -> pd.DataFrame:
    """Lee votos_resuelto + actas_canonico y devuelve el detalle voto-a-voto con
    fecha y cámara resueltas. Parsing defensivo: si falta una columna esperada,
    error específico; filas sin fecha/bloque/linaje se descartan con aviso.

    enriquecer_senado (default True): recupera el linaje real de los votos del Senado
    que llegan con bloque genérico (SIN BLOQUE -> OTRO/PROVINCIAL) uniendo por nombre
    al padrón oficial, mandate-aware (ver _enriquecer_linaje_senado). Ponelo en False
    para reproducir el comportamiento crudo de la canónica."""
    canon_dir = Path(canon_dir)
    fv = canon_dir / "votos_resuelto.parquet"
    fa = canon_dir / "actas_canonico.parquet"
    for f in (fv, fa):
        if not f.exists():
            raise FileNotFoundError(f"falta contrato de la canónica: {f}")

    votos = pd.read_parquet(fv)
    actas = pd.read_parquet(fa)

    need_v = {"acta_id", "legislador_id", "bloque_linaje", "voto"}
    faltan = need_v - set(votos.columns)
    if faltan:
        raise KeyError(f"votos_resuelto sin columnas {faltan}; hay {list(votos.columns)}")
    need_a = {"acta_id", "fecha", "camara"}
    faltan = need_a - set(actas.columns)
    if faltan:
        raise KeyError(f"actas_canonico sin columnas {faltan}; hay {list(actas.columns)}")

    a = actas[["acta_id", "fecha", "camara"]].copy()
    a["fecha"] = pd.to_datetime(a["fecha"], errors="coerce")
    df = votos.merge(a, on="acta_id", how="left", suffixes=("", "_acta"))
    # fecha: preferimos la del acta; si votos ya trae fecha usable, fallback
    if "fecha_acta" in df.columns:
        df["fecha"] = df["fecha_acta"].fillna(pd.to_datetime(df.get("fecha"), errors="coerce"))
    else:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    df["conducta"] = df["voto"].map(CONDUCTA_MAP)
    df["camara"] = df["camara"].fillna("desconocida").astype(str)
    # enriquecimiento de linaje del Senado (recupera bloque desde el padrón antes de
    # filtrar/agrupar; ver _enriquecer_linaje_senado). Requiere legislador_nombre, que
    # votos_resuelto trae; si no está, es no-op.
    if enriquecer_senado:
        df, _ = _enriquecer_linaje_senado(df, padron_dir=padron_dir)
    n0 = len(df)
    df = df[df["fecha"].notna() & df["bloque_linaje"].notna() & df["conducta"].notna()]
    df = df[df["bloque_linaje"].astype(str).str.strip().ne("")]
    if len(df) < n0:
        logger.warning("descarté %d/%d filas sin fecha/linaje/conducta", n0 - len(df), n0)
    if df.empty:
        raise ValueError("no quedaron votos utilizables tras el filtrado")
    return df[["acta_id", "fecha", "camara", "bloque_linaje",
               "legislador_id", "conducta"]].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Métricas por (acta, bloque): dirección, cohesión, desvío                     #
# --------------------------------------------------------------------------- #
def metricas_acta_bloque(votos: pd.DataFrame, min_emit: int = 3) -> pd.DataFrame:
    """Una fila por (acta, bloque) con dirección (mayoría A/N entre EMITIDOS),
    cohesión de Rice y desvío interno. Solo bloques con >= min_emit emisores."""
    v = votos.copy()
    v["es_afirm"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v["es_neg"] = (v["conducta"] == "NEGATIVO").astype(int)
    g = v.groupby(["acta_id", "fecha", "camara", "bloque_linaje"], observed=True).agg(
        n_afirm=("es_afirm", "sum"),
        n_neg=("es_neg", "sum"),
        n_filas=("conducta", "size"),
    ).reset_index()
    g["n_emit"] = g["n_afirm"] + g["n_neg"]
    g = g[g["n_emit"] >= int(min_emit)].copy()
    if g.empty:
        raise ValueError(f"ningún (acta,bloque) alcanza min_emit={min_emit}")
    g["direccion"] = np.where(g["n_afirm"] >= g["n_neg"], "AFIRMATIVO", "NEGATIVO")
    tot = g["n_emit"].astype(float)
    g["rice"] = (g["n_afirm"] - g["n_neg"]).abs() / tot         # 1 = unánime, 0 = 50/50
    g["desvio"] = g[["n_afirm", "n_neg"]].min(axis=1) / tot      # fracción minoritaria
    g["bancas_acta"] = g["n_filas"]                             # presentes+ausentes del bloque
    return g[["acta_id", "fecha", "camara", "bloque_linaje", "direccion",
              "n_afirm", "n_neg", "n_emit", "rice", "desvio", "bancas_acta"]]


def _periodo_parlamentario(fecha: pd.Series) -> pd.Series:
    """Año legislativo: el recambio es el 10-dic; diciembre cuenta para el año
    siguiente. Devuelve el año de inicio del período."""
    f = pd.to_datetime(fecha)
    return np.where(f.dt.month == 12, f.dt.year + 1, f.dt.year)


def serie_bloque(mab: pd.DataFrame) -> pd.DataFrame:
    """Agrega las métricas por (período, cámara, bloque): tamaño, postura,
    cohesión y fracturas. Es el contrato de salida serie_bloque.parquet."""
    m = mab.copy()
    m["periodo"] = _periodo_parlamentario(m["fecha"])
    m["dir_afirm"] = (m["direccion"] == "AFIRMATIVO").astype(int)
    m["fractura"] = (m["rice"] < 0.5).astype(int)   # bloque partido: <75/25
    s = m.groupby(["periodo", "camara", "bloque_linaje"], observed=True).agg(
        n_actas=("acta_id", "nunique"),
        bancas_medias=("bancas_acta", "mean"),
        share_afirmativo=("dir_afirm", "mean"),
        cohesion_media=("rice", "mean"),
        desvio_medio=("desvio", "mean"),
        tasa_fractura=("fractura", "mean"),
    ).reset_index()
    s["bancas_medias"] = s["bancas_medias"].round(1)
    for c in ("share_afirmativo", "cohesion_media", "desvio_medio", "tasa_fractura"):
        s[c] = s[c].round(4)
    return s.sort_values(["periodo", "camara", "bancas_medias"],
                         ascending=[True, True, False]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Proyector point-in-time (lo que consume el escenario del ensemble)          #
# --------------------------------------------------------------------------- #
def _bancas_padron(camara: str, fecha, padron_path=None):
    """Composicion REAL a la fecha desde datos/padron: {bloque_linaje: bancas}.
    Cuenta legisladores con mandato vigente (desde <= fecha <= hasta). None si no hay
    padron (entonces el proyector cae al conteo por ventana, con aviso)."""
    p = Path(padron_path) if padron_path else DEFAULT_PADRON_DIR / f"padron_{camara}.csv"
    if not p.exists():
        logger.warning("sin padron %s (%s): uso conteo por ventana (roster inflado)", camara, p)
        return None
    pad = pd.read_csv(p, dtype=str)
    if "bloque_linaje" not in pad.columns:
        logger.warning("padron %s sin columna bloque_linaje; ignoro", p)
        return None
    fecha = pd.to_datetime(fecha)
    d = pd.to_datetime(pad.get("desde"), errors="coerce")
    h = pd.to_datetime(pad.get("hasta"), errors="coerce")
    vig = pad[(d <= fecha) & (h.isna() | (h >= fecha))]
    if vig.empty:
        logger.warning("padron %s sin bancas vigentes a %s; uso ventana", camara, fecha.date())
        return None
    return vig.groupby("bloque_linaje").size().astype(int).to_dict()


# Recambios presidenciales (10-dic). MANTENER SINCRONIZADAS con
# variables/proyecto/src/origen_lider.py (GOBIERNOS) y origen_por_acta (nombres).
_GOBIERNOS = [
    ("1900-01-01", "2015-12-10", "KIRCHNER"),
    ("2015-12-10", "2019-12-10", "MACRI"),
    ("2019-12-10", "2023-12-10", "AF"),
    ("2023-12-10", "2100-01-01", "MILEI"),
]


def _gobierno_por_fecha(fecha):
    f = pd.to_datetime(fecha, errors="coerce")
    if pd.isna(f):
        return None
    for desde, hasta, nombre in _GOBIERNOS:
        if pd.Timestamp(desde) <= f < pd.Timestamp(hasta):
            return nombre
    return None


def _cond_map(cond_por_acta) -> dict:
    """Normaliza el insumo tema/origen por acta a dict acta_id ->
    {'tema_area','origen','origen_lado','gobierno'}. Acepta un dict ya armado o un
    DataFrame con acta_id + esas columnas (contratos tema_por_acta y origen_por_acta
    de variables/proyecto, ya fusionados por cargar_tema_por_acta)."""
    if cond_por_acta is None:
        return {}
    if isinstance(cond_por_acta, dict):
        return {str(k): v for k, v in cond_por_acta.items()}
    df = cond_por_acta
    if "acta_id" not in getattr(df, "columns", []):
        logger.warning("cond_por_acta sin columna acta_id; ignoro condicionamiento")
        return {}
    campos = [c for c in ("tema_area", "origen", "origen_lado", "gobierno") if c in df.columns]
    m = {}
    for _, r in df.iterrows():
        info = {c: r[c] for c in campos if pd.notna(r.get(c))}
        if info:
            m[str(r["acta_id"])] = info
    return m


def cargar_tema_por_acta(path=None):
    """Lee el contrato tema_por_acta.parquet (variables/proyecto). None si no está
    todavía (entonces el proyector cae a la dirección INCONDICIONAL = v1)."""
    p = Path(path) if path else (Path(__file__).resolve().parents[3] /
                                 "variables" / "proyecto" / "data" / "tema_por_acta.parquet")
    df = None
    if p.exists():
        try:
            df = pd.read_parquet(p)
        except (OSError, ValueError) as e:
            logger.warning("no pude leer tema_por_acta %s: %s", p, e)
    # v2b (2026-07-22): fusionar el contrato ORIGEN por acta (quién impulsa + gobierno)
    po = p.parent / "origen_por_acta.parquet"
    if po.exists():
        try:
            ori = pd.read_parquet(po)
            cols = [c for c in ("acta_id", "origen", "origen_lado", "gobierno")
                    if c in ori.columns]
            ori = ori[cols].drop_duplicates("acta_id")
            if df is None:
                df = ori
            else:
                df = df.drop(columns=[c for c in ("origen", "origen_lado", "gobierno")
                                      if c in df.columns], errors="ignore")
                df = df.merge(ori, on="acta_id", how="outer")
        except (OSError, ValueError, KeyError) as e:
            logger.warning("no pude fusionar origen_por_acta %s: %s", po, e)
    if df is None:
        logger.info("sin tema_por_acta ni origen_por_acta (%s): dirección incondicional (v1)", p)
    return df


def proyectar_postura(votos: pd.DataFrame, fecha, camara: str,
                      ventana_dias: int = 730, min_actas: int = 3,
                      padron_path=None, tema=None, origen=None,
                      cond_por_acta=None, k_shrink: float = 5.0,
                      excluir_aux: bool = True) -> list[dict]:
    """Escenario por bloque para una votacion en `fecha`/`camara`.

    COMPOSICION (bancas) = padron OFICIAL vigente a la fecha (datos/padron): la camara
    real (257 Dip / 72 Sen). COMPORTAMIENTO (linea, desvio) = historia ANTERIOR a la
    fecha dentro de una ventana movil (walk-forward, sin leakage).

    v2 — DIRECCION CONDICIONADA POR TEMA/ORIGEN (2026-07-22): si se pasa `tema` (area,
    ej. 'TRAB') y/o `origen` del proyecto objetivo — fino (EJECUTIVO/OFICIALISMO/
    OPOSICION) o por LADO (GOBIERNO/OPOSICION, recomendado: agrupa EJECUTIVO+
    OFICIALISMO y junta mas actas) —, MAS un mapa. Al condicionar por origen solo
    cuentan actas del MISMO gobierno que `fecha` (guard del recambio del 10-dic),
    `cond_por_acta` (acta_id -> {tema_area, origen}; el contrato tema_por_acta de
    variables/proyecto), la direccion de cada bloque se calcula sobre las actas de la
    ventana que comparten ese tema/origen, y se mezcla con la incondicional por
    ENCOGIMIENTO (shrinkage empirico-bayesiano, pseudo-conteo k_shrink) para no dar
    vuelta la direccion con 2-3 actas. Sin `tema`/`origen` (o sin mapa), el resultado
    es IDENTICO al v1 incondicional -> no rompe el contrato ni el ensemble.

    Devuelve [{bloque, bancas, linea, desvio, ...}], listo para el ensemble.
    """
    fecha = pd.to_datetime(fecha)
    if pd.isna(fecha):
        raise ValueError("fecha invalida para proyectar")
    desde = fecha - pd.Timedelta(days=int(ventana_dias))

    hist = votos[(votos["camara"] == camara) &
                 (votos["fecha"] < fecha) & (votos["fecha"] >= desde)]
    if hist.empty:
        raise ValueError(f"sin historia para camara={camara} en "
                         f"[{desde.date()}, {fecha.date()})")
    mab = metricas_acta_bloque(hist, min_emit=1)  # ventana chica: no exigir 3
    mab["dir_afirm"] = (mab["direccion"] == "AFIRMATIVO").astype(int)

    # v2b (2026-07-23): las actas AUX (homenajes, trámite, declaraciones de interés,
    # y en la práctica tratados/pliegos que se aprueban por consenso) NO informan la
    # postura política de ningún bloque: todos votan que sí. Se excluyen del cálculo de
    # postura (condicional E incondicional) para que ese consenso no infle el share
    # afirmativo. Requiere el tema por acta (cond_map); sin él no se puede filtrar.
    cond_map = _cond_map(cond_por_acta)
    if excluir_aux and cond_map:
        es_aux = mab["acta_id"].map(
            lambda a: str(cond_map.get(str(a), {}).get("tema_area", "")).upper() == "AUX")
        if es_aux.any() and (~es_aux).any():  # no vaciar la ventana entera
            logger.info("excluí %d actas AUX (consenso) del cálculo de postura", int(es_aux.sum()))
            mab = mab[~es_aux]

    comp = mab.groupby("bloque_linaje", observed=True).agg(
        share_afirm=("dir_afirm", "mean"),
        desvio=("desvio", "mean"),
        n_actas=("acta_id", "nunique"),
    )

    # v2: subconjunto de la ventana que comparte tema/origen con el proyecto objetivo
    condicionar = (tema is not None or origen is not None) and len(cond_map) > 0
    cond_share: dict = {}
    if condicionar:
        tgt_t = str(tema).upper() if tema is not None else None
        tgt_o = str(origen).upper() if origen is not None else None
        # al condicionar por ORIGEN, solo actas del MISMO gobierno que la fecha
        # objetivo (un bloque cambia de lado con el recambio del 10-dic; decision
        # de Valle 2026-07-22: no mezclar eras dentro de la ventana)
        gob_objetivo = _gobierno_por_fecha(fecha) if tgt_o is not None else None

        def _match(aid) -> bool:
            info = cond_map.get(str(aid))
            if not info:
                return False
            if tgt_t is not None and str(info.get("tema_area", "")).upper() != tgt_t:
                return False
            if tgt_o is not None:
                fino = str(info.get("origen", "")).upper()
                lado = str(info.get("origen_lado", "")).upper()
                if tgt_o not in (fino, lado):
                    return False
                if gob_objetivo is not None and info.get("gobierno") is not None \
                        and str(info.get("gobierno")).upper() != gob_objetivo:
                    return False
            return True

        sel = mab[mab["acta_id"].map(_match)]
        if sel.empty:
            logger.warning("condicionamiento tema=%s origen=%s: 0 actas en ventana; "
                           "caigo a incondicional", tema, origen)
            condicionar = False
        else:
            cg = sel.groupby("bloque_linaje", observed=True).agg(
                share_cond=("dir_afirm", "mean"),
                n_cond=("acta_id", "nunique"),
            )
            cond_share = cg.to_dict("index")
            logger.info("v2: %d actas condicionadas (tema=%s origen=%s) sobre %d de la ventana",
                        sel["acta_id"].nunique(), tema, origen, mab["acta_id"].nunique())

    # composicion a la fecha: padron oficial si esta; si no, conteo por ventana
    base = _bancas_padron(camara, fecha, padron_path)
    fuente_bancas = "padron"
    if base is None:
        base = (hist.groupby("bloque_linaje")["legislador_id"].nunique().to_dict())
        fuente_bancas = "ventana"

    out = []
    for linaje, nb in base.items():
        nb = int(nb)
        if nb <= 0:
            continue
        n_cond_used = 0
        if linaje in comp.index:
            r = comp.loc[linaje]
            share_u = float(r["share_afirm"])
            desvio = float(np.clip(r["desvio"], 0.0, 1.0))
            nact = int(r["n_actas"])
            share = share_u
            cs = cond_share.get(linaje)
            if cs is not None:
                n_c = float(cs["n_cond"])
                s_c = float(cs["share_cond"])
                # encogimiento hacia la incondicional: pocas actas del tema -> confia
                # menos en el condicionado; muchas -> lo domina.
                share = (n_c * s_c + float(k_shrink) * share_u) / (n_c + float(k_shrink))
                n_cond_used = int(n_c)
        else:
            share_u, share, desvio, nact = 0.5, 0.5, 0.15, 0  # sin historia: neutro
        linea = "AFIRMATIVO" if share >= 0.5 else "NEGATIVO"
        out.append({"bloque": str(linaje), "bancas": nb, "linea": linea,
                    "desvio": round(desvio, 4),
                    "_share_afirm": round(share, 4),
                    "_share_incond": round(share_u, 4),
                    "_n_actas": nact, "_n_cond": n_cond_used,
                    "_cond": (f"tema={tema};origen={origen}" if condicionar else None),
                    "_bancas_de": fuente_bancas})
    if not out:
        raise ValueError("ningun bloque con bancas para proyectar")
    return sorted(out, key=lambda d: d["bancas"], reverse=True)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _cli_serie(canon_dir: Path, out: Path) -> None:
    votos = cargar(canon_dir)
    mab = metricas_acta_bloque(votos)
    s = serie_bloque(mab)
    out.parent.mkdir(parents=True, exist_ok=True)
    s.to_parquet(out, index=False)
    logger.info("serie_bloque: %d filas -> %s", len(s), out)
    print(s.tail(20).to_string(index=False))


def _cli_proyectar(fecha: str, camara: str, canon_dir: Path,
                   tema=None, origen=None) -> None:
    votos = cargar(canon_dir)
    cpa = cargar_tema_por_acta() if (tema or origen) else None
    esc = proyectar_postura(votos, fecha, camara, tema=tema, origen=origen,
                            cond_por_acta=cpa)
    print(json.dumps({"fecha": fecha, "camara": camara, "tema": tema,
                      "origen": origen, "bloques": esc},
                     ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("uso: bloque.py serie [canon_dir] | "
              "bloque.py proyectar <YYYY-MM-DD> <camara> [canon_dir]")
        return 2
    cmd = argv[0]
    try:
        if cmd == "serie":
            canon = Path(argv[1]) if len(argv) > 1 else DEFAULT_CANON
            _cli_serie(canon, OUT_DEFAULT)
        elif cmd == "proyectar":
            if len(argv) < 3:
                print("uso: bloque.py proyectar <YYYY-MM-DD> <camara> "
                      "[--tema AREA] [--origen ORIGEN] [canon_dir]")
                return 2
            tema = origen = None
            rest = argv[3:]
            pos = []
            i = 0
            while i < len(rest):
                if rest[i] == "--tema" and i + 1 < len(rest):
                    tema = rest[i + 1]; i += 2
                elif rest[i] == "--origen" and i + 1 < len(rest):
                    origen = rest[i + 1]; i += 2
                else:
                    pos.append(rest[i]); i += 1
            canon = Path(pos[0]) if pos else DEFAULT_CANON
            _cli_proyectar(argv[1], argv[2], canon, tema=tema, origen=origen)
        else:
            print(f"comando desconocido: {cmd}")
            return 2
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error("%s: %s", type(e).__name__, e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
