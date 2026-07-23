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
# Carga (contrato de la canónica)                                             #
# --------------------------------------------------------------------------- #
def cargar(canon_dir: Path = DEFAULT_CANON) -> pd.DataFrame:
    """Lee votos_resuelto + actas_canonico y devuelve el detalle voto-a-voto con
    fecha y cámara resueltas. Parsing defensivo: si falta una columna esperada,
    error específico; filas sin fecha/bloque/linaje se descartan con aviso."""
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
    n0 = len(df)
    df = df[df["fecha"].notna() & df["bloque_linaje"].notna() & df["conducta"].notna()]
    df = df[df["bloque_linaje"].astype(str).str.strip().ne("")]
    if len(df) < n0:
        logger.warning("descarté %d/%d filas sin fecha/linaje/conducta", n0 - len(df), n0)
    if df.empty:
        raise ValueError("no quedaron votos utilizables tras el filtrado")
    df["camara"] = df["camara"].fillna("desconocida").astype(str)
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


def _cond_map(cond_por_acta) -> dict:
    """Normaliza el insumo tema/origen por acta a dict acta_id -> {'tema_area', 'origen'}.
    Acepta un dict ya armado o un DataFrame con columna acta_id + tema_area/origen
    (el contrato de variables/proyecto/data/tema_por_acta.parquet)."""
    if cond_por_acta is None:
        return {}
    if isinstance(cond_por_acta, dict):
        return {str(k): v for k, v in cond_por_acta.items()}
    df = cond_por_acta
    if "acta_id" not in getattr(df, "columns", []):
        logger.warning("cond_por_acta sin columna acta_id; ignoro condicionamiento")
        return {}
    campos = [c for c in ("tema_area", "origen") if c in df.columns]
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
    if not p.exists():
        logger.info("sin tema_por_acta (%s): dirección incondicional (v1)", p)
        return None
    try:
        return pd.read_parquet(p)
    except (OSError, ValueError) as e:
        logger.warning("no pude leer tema_por_acta %s: %s", p, e)
        return None


def proyectar_postura(votos: pd.DataFrame, fecha, camara: str,
                      ventana_dias: int = 730, min_actas: int = 3,
                      padron_path=None, tema=None, origen=None,
                      cond_por_acta=None, k_shrink: float = 5.0) -> list[dict]:
    """Escenario por bloque para una votacion en `fecha`/`camara`.

    COMPOSICION (bancas) = padron OFICIAL vigente a la fecha (datos/padron): la camara
    real (257 Dip / 72 Sen). COMPORTAMIENTO (linea, desvio) = historia ANTERIOR a la
    fecha dentro de una ventana movil (walk-forward, sin leakage).

    v2 — DIRECCION CONDICIONADA POR TEMA/ORIGEN (2026-07-22): si se pasa `tema` (area,
    ej. 'TRAB') y/o `origen` (ej. 'OPOSICION') del proyecto objetivo, MAS un mapa
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
    comp = mab.groupby("bloque_linaje", observed=True).agg(
        share_afirm=("dir_afirm", "mean"),
        desvio=("desvio", "mean"),
        n_actas=("acta_id", "nunique"),
    )

    # v2: subconjunto de la ventana que comparte tema/origen con el proyecto objetivo
    cond_map = _cond_map(cond_por_acta)
    condicionar = (tema is not None or origen is not None) and len(cond_map) > 0
    cond_share: dict = {}
    if condicionar:
        tgt_t = str(tema).upper() if tema is not None else None
        tgt_o = str(origen).upper() if origen is not None else None

        def _match(aid) -> bool:
            info = cond_map.get(str(aid))
            if not info:
                return False
            if tgt_t is not None and str(info.get("tema_area", "")).upper() != tgt_t:
                return False
            if tgt_o is not None and str(info.get("origen", "")).upper() != tgt_o:
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
