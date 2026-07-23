"""variables/proyecto - ORIGEN POR ACTA VOTADA (el lever que endereza el 1167).

Etiqueta cada acta de la canónica con QUIÉN impulsa el proyecto votado, leído
contra el gobierno de turno A LA FECHA DEL ACTA (no de la presentación):

  origen      ∈ {EJECUTIVO, OFICIALISMO, OPOSICION, DESCONOCIDO}
  origen_lado ∈ {GOBIERNO, OPOSICION, None}   (EJECUTIVO+OFICIALISMO -> GOBIERNO)
  gobierno    ∈ {KIRCHNER, MACRI, AF, MILEI}  (quién gobernaba a la fecha del acta)

POR QUÉ: condicionar la dirección del bloque sólo por TEMA da el signo político
invertido (hallazgo 2026-07-22 con el 1167: las votaciones "TRAB" 2024-25 eran
proyectos opositores → el modelo puso a LLA en NEGATIVO en una reforma DEL gobierno).
La misma materia tiene signo opuesto según quién la impulsa. Además el MISMO autor
cambia de lado con el recambio (ej. PRO: oficialista 2016-19, opositor 2020-23),
por eso la etiqueta va contra el gobierno del día del acta y se guarda `gobierno`
para que el proyector no mezcle eras al condicionar.

TRES VÍAS DETERMINÍSTICAS (sin API key, sin PDFs), en orden:
  1. codigo : el código de expediente del acta (canónica o puente CKAN acta_expediente).
              Letra PE/JGM -> EJECUTIVO directo; D/S -> autor vía expedientes.parquet.
  2. od     : títulos "O.D. N - ..." (argentinadatos 2024+) -> expedientes_resultados
              (od_numero + od_publicacion <= fecha del acta, la más cercana).
  3. titulo : match EXACTO del título normalizado contra los 112k títulos de
              expedientes.parquet (misma fuente HCDN; se elige la publicación previa
              más cercana a la fecha del acta).
Con el proyecto resuelto: tipo MENSAJE -> EJECUTIVO; si no, linaje del autor
(variables/legislador) evaluado con oficialista_por_fecha a la FECHA DEL ACTA.

CONSUME (contratos): datos/canonica actas_canonico.parquet · datos/expedientes
{acta_expediente, expedientes, expedientes_resultados}.parquet · variables/legislador
{legisladores.csv, legislador_bloques.parquet} · helpers de origen_lider (mismo módulo).
PRODUCE (contrato estable): variables/proyecto/data/origen_por_acta.parquet
  acta_id, expediente, proyecto_id, origen, origen_lado, autor_linaje, gobierno,
  via, etiquetado_en

CLI:  python variables/proyecto/src/origen_por_acta.py
4 directivas: errores específicos, parsing defensivo, logging estructurado.
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

logger = logging.getLogger("proyecto.origen_por_acta")

_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
from origen_lider import (_norm, _linaje_autor, _mapa_autor_linaje,  # noqa: E402
                          oficialista_por_fecha, GOBIERNOS)

_RAIZ = Path(__file__).resolve().parents[3]
DEFAULT_ACTAS = _RAIZ / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet"
DEFAULT_EXP_CLEAN = _RAIZ / "datos" / "expedientes" / "data" / "clean"
DEFAULT_LEG_DATA = _RAIZ / "variables" / "legislador" / "data"
OUT_DEFAULT = _RAIZ / "variables" / "proyecto" / "data" / "origen_por_acta.parquet"

# nombres de los gobiernos, ALINEADOS 1:1 con las ventanas de GOBIERNOS (origen_lider)
GOBIERNO_NOMBRES = ("KIRCHNER", "MACRI", "AF", "MILEI")

_RE_CODE = re.compile(r"(\d+)-([A-Z]+)-(\d{2,4})")
# Formato EMBEBIDO en títulos del Senado viejo (semilla decada_votada): "PE-608/03",
# "S-1234/05", "CD-45/11" (LETRA-NUMERO/AÑO, con barra). Distinto del estándar
# N-LETRA-AÑO (con guiones): por eso no colisiona con _RE_CODE ni con Diputados.
_RE_CODE_EMB = re.compile(r"\b([A-Z]{1,4})\s*-\s*(\d+)\s*/\s*(\d{2,4})\b")
_RE_OD = re.compile(r"\bO\.?\s*D\.?\s*(\d+)\b", re.IGNORECASE)
LETRAS_EJECUTIVO = {"PE", "JGM"}


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gobierno_por_fecha(fecha) -> str | None:
    """KIRCHNER | MACRI | AF | MILEI según la fecha (ventanas de origen_lider)."""
    f = pd.to_datetime(fecha, errors="coerce")
    if pd.isna(f):
        return None
    for (desde, hasta, _ofi), nombre in zip(GOBIERNOS, GOBIERNO_NOMBRES):
        if pd.Timestamp(desde) <= f < pd.Timestamp(hasta):
            return nombre
    return None


def _norm_code(s) -> str | None:
    """'0010-pe-15' -> '0010-PE-2015' (clave estable para joins)."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    m = _RE_CODE.search(str(s).upper())
    if not m:
        return None
    n, letra, anio = m.groups()
    if len(anio) == 2:
        anio = "20" + anio
    return f"{int(n):04d}-{letra}-{anio}"


def _code_embebido(titulo) -> str | None:
    """Extrae el código EMBEBIDO en el título ('PE-608/03') y lo lleva al estándar
    'NNNN-LETRA-YYYY'. Devuelve None si no hay. Año de 2 dígitos: <50 -> 20xx, si no 19xx
    (la semilla del Senado es 2004-2014, así que en la práctica siempre 20xx)."""
    if not isinstance(titulo, str):
        return None
    m = _RE_CODE_EMB.search(titulo.upper())
    if not m:
        return None
    letra, num, anio = m.groups()
    if len(anio) == 2:
        anio = ("20" + anio) if int(anio) < 50 else ("19" + anio)
    return f"{int(num):04d}-{letra}-{anio}"


def _norm_titulo(s) -> str:
    """Título normalizado para match exacto: sin 'O.D. N -', sin acentos/puntuación."""
    t = str(s or "")
    t = _RE_OD.sub(" ", t)
    return _norm(t)


# --------------------------------------------------------------------------- #
# Carga de insumos (contratos de otros módulos)                                #
# --------------------------------------------------------------------------- #
def cargar_insumos(actas_path: Path = DEFAULT_ACTAS,
                   exp_clean: Path = DEFAULT_EXP_CLEAN,
                   leg_data: Path = DEFAULT_LEG_DATA) -> dict:
    actas_path = Path(actas_path)
    if not actas_path.exists():
        raise FileNotFoundError(f"falta la canónica: {actas_path}")
    actas = pd.read_parquet(actas_path)
    need = {"acta_id", "fecha", "titulo"}
    faltan = need - set(actas.columns)
    if faltan:
        raise KeyError(f"actas_canonico sin columnas {faltan}")

    def _pq(nombre):
        p = Path(exp_clean) / nombre
        if not p.exists():
            logger.warning("insumo opcional ausente: %s", p)
            return None
        return pd.read_parquet(p)

    leg_data = Path(leg_data)
    legis = (pd.read_csv(leg_data / "legisladores.csv", dtype=str, encoding="utf-8-sig")
             if (leg_data / "legisladores.csv").exists() else None)
    lb_path = leg_data / "legislador_bloques.parquet"
    lb = pd.read_parquet(lb_path) if lb_path.exists() else None
    return {
        "actas": actas,
        "acta_exp": _pq("acta_expediente.parquet"),
        "expedientes": _pq("expedientes.parquet"),
        "resultados": _pq("expedientes_resultados.parquet"),
        "legis": legis,
        "leg_bloques": lb,
    }


# --------------------------------------------------------------------------- #
# Índices auxiliares                                                           #
# --------------------------------------------------------------------------- #
def _idx_codigo_por_acta(acta_exp: pd.DataFrame | None) -> dict:
    """acta_id -> código normalizado del puente CKAN. Si el acta cruza varios
    expedientes, gana el PE/JGM (el mensaje es la cabecera política); si no,
    el del título más largo (mismo criterio que tema_por_acta)."""
    if acta_exp is None or "acta_id" not in acta_exp.columns:
        return {}
    df = acta_exp.copy()
    df["code"] = df.get("expediente").map(_norm_code)
    df = df[df["code"].notna()]
    df["_pe"] = df["code"].str.split("-").str[1].isin(LETRAS_EJECUTIVO)
    df["_len"] = df.get("titulo", "").astype(str).str.len()
    df = df.sort_values(["_pe", "_len"], ascending=False)
    return df.drop_duplicates("acta_id").set_index("acta_id")["code"].to_dict()


def _idx_expedientes(expedientes: pd.DataFrame | None):
    """(code -> fila, titulo_norm -> [filas], proyecto_id -> fila) de expedientes."""
    por_code: dict = {}
    por_titulo: dict = {}
    por_pid: dict = {}
    if expedientes is None:
        return por_code, por_titulo, por_pid
    exp = expedientes.copy()
    exp["fecha_pub"] = pd.to_datetime(exp.get("fecha_publicacion"), errors="coerce")
    for r in exp.itertuples(index=False):
        d = r._asdict()
        por_pid[str(d.get("proyecto_id"))] = d
        for col in ("exp_diputados", "exp_senado"):
            c = _norm_code(d.get(col))
            if c and c not in por_code:
                por_code[c] = d
        tn = _norm_titulo(d.get("titulo"))
        if len(tn) >= 25:  # títulos cortos son ambiguos: no sirven para match exacto
            por_titulo.setdefault(tn, []).append(d)
    return por_code, por_titulo, por_pid


def _idx_od(resultados: pd.DataFrame | None) -> dict:
    """od_numero (int) -> [(od_publicacion, proyecto_id)] ordenado por fecha."""
    if resultados is None or "od_numero" not in resultados.columns:
        return {}
    df = resultados.copy()
    df["od_n"] = pd.to_numeric(df["od_numero"], errors="coerce")
    df["od_pub"] = pd.to_datetime(df.get("od_publicacion"), errors="coerce")
    df = df.dropna(subset=["od_n", "od_pub"])
    out: dict = {}
    for r in df.itertuples(index=False):
        out.setdefault(int(r.od_n), []).append((r.od_pub, str(r.proyecto_id)))
    for k in out:
        out[k].sort()
    return out


def _pid_por_od(titulo: str, fecha, idx_od: dict) -> str | None:
    """'O.D. 1 - ...' + fecha del acta -> proyecto_id de la publicación previa más cercana."""
    m = _RE_OD.search(str(titulo or ""))
    if not m or not idx_od:
        return None
    f = pd.to_datetime(fecha, errors="coerce")
    candidatos = idx_od.get(int(m.group(1)))
    if not candidatos or pd.isna(f):
        return None
    previos = [(pub, pid) for pub, pid in candidatos if pub <= f]
    return previos[-1][1] if previos else None


def _pid_por_titulo(titulo: str, fecha, por_titulo: dict) -> str | None:
    """Match exacto del título normalizado -> proyecto de publicación previa más cercana."""
    tn = _norm_titulo(titulo)
    filas = por_titulo.get(tn)
    if not filas:
        return None
    f = pd.to_datetime(fecha, errors="coerce")
    if pd.isna(f):
        return None
    previos = sorted((d["fecha_pub"], str(d["proyecto_id"])) for d in filas
                     if pd.notna(d.get("fecha_pub")) and d["fecha_pub"] <= f)
    return previos[-1][1] if previos else None


# --------------------------------------------------------------------------- #
# Etiquetado                                                                   #
# --------------------------------------------------------------------------- #
def _resolver_origen(fila_exp: dict | None, code: str | None, fecha_acta,
                     mapa_autor: dict):
    """(origen, autor_linaje) para un acta, contra el gobierno a la FECHA DEL ACTA."""
    # 1) Ejecutivo por letra del código o por tipo MENSAJE del expediente
    letra = code.split("-")[1] if code and "-" in code else None
    if letra in LETRAS_EJECUTIVO:
        return "EJECUTIVO", None
    if fila_exp is not None:
        tipo = str(fila_exp.get("tipo") or "")
        if "MENSAJE" in tipo.upper():
            return "EJECUTIVO", None
        autor_nn = _norm(fila_exp.get("autor"))
        anio_pres = fila_exp.get("fecha_pub")
        anio_pres = anio_pres.year if pd.notna(anio_pres) else None
        linaje = _linaje_autor(autor_nn, anio_pres, mapa_autor) if autor_nn else None
        if linaje is not None:
            ofi = oficialista_por_fecha(linaje, pd.to_datetime(fecha_acta, errors="coerce"))
            if ofi is True:
                return "OFICIALISMO", linaje
            if ofi is False:
                return "OPOSICION", linaje
            return "DESCONOCIDO", linaje
    return "DESCONOCIDO", None


def etiquetar(dfs: dict) -> pd.DataFrame:
    actas = dfs["actas"].copy()
    actas["fecha"] = pd.to_datetime(actas["fecha"], errors="coerce")
    idx_ckan = _idx_codigo_por_acta(dfs.get("acta_exp"))
    por_code, por_titulo, por_pid = _idx_expedientes(dfs.get("expedientes"))
    idx_od = _idx_od(dfs.get("resultados"))
    mapa_autor = _mapa_autor_linaje(dfs.get("legis"), dfs.get("leg_bloques"))

    filas = []
    vias = {"codigo": 0, "titulo_codigo": 0, "od": 0, "titulo": 0, "sin_via": 0}
    for r in actas.itertuples(index=False):
        aid = str(r.acta_id)
        fecha = r.fecha
        titulo = getattr(r, "titulo", "") or ""
        # el código estándar (columna expediente o puente CKAN) manda; si no hay,
        # se prueba el código EMBEBIDO en el título (Senado viejo: 'PE-608/03').
        code = _norm_code(getattr(r, "expediente", None)) or idx_ckan.get(aid)
        code_via = "codigo"
        if not code:
            emb = _code_embebido(titulo)
            if emb:
                code, code_via = emb, "titulo_codigo"
        pid = None
        via = None
        if code:
            via = code_via
            fila = por_code.get(code)
            pid = str(fila["proyecto_id"]) if fila else None
        else:
            pid = _pid_por_od(titulo, fecha, idx_od)
            if pid:
                via = "od"
            else:
                pid = _pid_por_titulo(titulo, fecha, por_titulo)
                if pid:
                    via = "titulo"
        fila_exp = por_pid.get(pid) if pid else (por_code.get(code) if code else None)
        origen, linaje = _resolver_origen(fila_exp, code, fecha, mapa_autor)
        lado = ("GOBIERNO" if origen in ("EJECUTIVO", "OFICIALISMO")
                else "OPOSICION" if origen == "OPOSICION" else None)
        vias[via or "sin_via"] += 1
        filas.append({
            "acta_id": aid,
            "expediente": code,
            "proyecto_id": pid,
            "origen": origen,
            "origen_lado": lado,
            "autor_linaje": linaje,
            "gobierno": gobierno_por_fecha(fecha),
            "via": via,
            "etiquetado_en": _ahora(),
        })
    out = pd.DataFrame(filas)
    n = len(out)
    con = (out["origen"] != "DESCONOCIDO").sum()
    logger.info("origen_por_acta: %d actas | etiquetadas %d (%.1f%%) | vías %s | origen %s",
                n, con, 100 * con / max(n, 1), vias,
                out["origen"].value_counts().to_dict())
    return out


def correr(actas_path: Path = DEFAULT_ACTAS, exp_clean: Path = DEFAULT_EXP_CLEAN,
           leg_data: Path = DEFAULT_LEG_DATA, out: Path = OUT_DEFAULT) -> pd.DataFrame:
    dfs = cargar_insumos(actas_path, exp_clean, leg_data)
    res = etiquetar(dfs)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out, index=False)
    logger.info("-> %s (%d filas)", out, len(res))
    return res


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Etiqueta origen (quién impulsa) + gobierno por acta votada.")
    p.add_argument("--actas", default=str(DEFAULT_ACTAS))
    p.add_argument("--exp-clean", default=str(DEFAULT_EXP_CLEAN))
    p.add_argument("--leg-data", default=str(DEFAULT_LEG_DATA))
    p.add_argument("--out", default=str(OUT_DEFAULT))
    args = p.parse_args(argv)
    try:
        res = correr(Path(args.actas), Path(args.exp_clean), Path(args.leg_data), Path(args.out))
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error("%s: %s", type(e).__name__, e)
        return 1
    print(res.groupby(["gobierno", "origen"], dropna=False).size().unstack(fill_value=0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
