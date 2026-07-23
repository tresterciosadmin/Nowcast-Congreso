"""modelo/ensemble - composición final del Nowcast.

    P(aprobación) = P(llega al recinto) × P(mayoría | recinto)

Conecta las piezas ya validadas:
  - P(llega al recinto): `variables/embudo/outputs/p_embudo.parquet` (col p_llega_recinto).
  - P(mayoría | recinto): `modelo/agregador_institucional` (`simular_votacion`), que
    simula el recuento como distribución con reglas de quórum y tipo de mayoría.

ROSTER NOMINAL (v3, 2026-07-22 — cimiento "las partes hacen al todo"):
El escenario que entra al simulador es UNA FILA POR LEGISLADOR del padrón oficial
vigente a la fecha (datos/padron), no bancas anónimas por bloque. Cada legislador
lleva SU tasa de desvío individual (modelo/voto_individual), con esta escalera:
  1. tasa_desvio_reciente  si su muestra reciente alcanza (n_reciente >= MIN_VOTOS_FICHA)
  2. tasa_desvio global    si su historia total alcanza  (n_votos    >= MIN_VOTOS_FICHA)
  3. desvío promedio de su bloque (proyectar_postura)  — SOLO para quien no tiene
     historial suficiente (p. ej. camada nueva). Es la única excepción admitida.
La LÍNEA de cada legislador es la de su bloque proyectada por variables/bloque
(condicionable por tema/origen, walk-forward). El desvío individual es la puerta por
la que cada legislador se aparta de esa línea en la simulación (las bisagras pesan).

El v2 (_expandir_roster: clonar el desvío promedio del bloque `bancas` veces) se
ELIMINÓ 2026-07-22 por decisión de Valle: aplicaba el promedio a todos, incluidos los
753 legisladores con desvío individual medido. También se eliminó el comando `demo` y
el `nowcast` con escenario JSON a mano (eran de la puesta en marcha del 10-jul).

El `proyecto_id` puede venir como DENOMINADOR humano (ej. 1167-D-2025) o como id
interno del embudo (HCDN...).

4 directivas: errores específicos, parsing defensivo, logging estructurado.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

import numpy as np

logger = logging.getLogger("ensemble")

CONDUCTAS = {"AFIRMATIVO", "NEGATIVO", "NO_ACOMPANA"}

# Muestra mínima de votos para confiar en la tasa de desvío individual (escalera).
MIN_VOTOS_FICHA = int(os.environ.get("MIN_VOTOS_FICHA", "20"))
# Desvío neutro si el legislador no tiene ficha NI su bloque tiene historia.
DESVIO_NEUTRO = 0.15

# Denominador parlamentario, ej. "1167-D-2025" / "45-S-2024" (nro-letra-anio).
_RE_DENOMINADOR = re.compile(r"^\s*\d+\s*-\s*[A-Za-z]+\s*-\s*\d{4}\s*$")


# --------------------------------------------------------------------------- #
# Imports de contratos públicos de otros módulos (no se toca su código)        #
# --------------------------------------------------------------------------- #
def _cargar_simulador():
    """Importa simular_votacion del agregador sin tocar su código."""
    agg = Path(__file__).resolve().parents[2] / "agregador_institucional" / "src"
    if str(agg) not in sys.path:
        sys.path.insert(0, str(agg))
    try:
        from agregador import simular_votacion  # type: ignore
        return simular_votacion
    except ImportError as e:
        raise RuntimeError(
            f"no pude importar simular_votacion desde {agg}: {e}") from e


def _cargar_proyector():
    """Importa cargar + proyectar_postura de variables/bloque (contrato publico)."""
    blo = Path(__file__).resolve().parents[3] / "variables" / "bloque" / "src"
    if str(blo) not in sys.path:
        sys.path.insert(0, str(blo))
    try:
        from bloque import (cargar as cargar_bloque, proyectar_postura,  # type: ignore
                            cargar_tema_por_acta)
        return cargar_bloque, proyectar_postura, cargar_tema_por_acta
    except ImportError as e:
        raise RuntimeError(f"no pude importar proyectar_postura desde {blo}: {e}") from e


# --------------------------------------------------------------------------- #
# Composición (el corazón del ensemble)                                        #
# --------------------------------------------------------------------------- #
def componer(p_llega: float, p_mayoria: float) -> float:
    """P(aprobación) = P(llega al recinto) × P(mayoría | recinto)."""
    if not (0.0 <= p_llega <= 1.0):
        raise ValueError(f"p_llega fuera de [0,1]: {p_llega}")
    if not (0.0 <= p_mayoria <= 1.0):
        raise ValueError(f"p_mayoria fuera de [0,1]: {p_mayoria}")
    return float(p_llega * p_mayoria)


# --------------------------------------------------------------------------- #
# Roster nominal: una fila por legislador del padrón, con SU desvío            #
# --------------------------------------------------------------------------- #
def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _padron_csv(camara: str, padron_dir=None) -> Path:
    cam = str(camara).strip().lower()
    base = Path(padron_dir or os.environ.get(
        "PADRON_DIR", _root() / "datos" / "padron" / "data"))
    return base / f"padron_{cam}.csv"


def _disciplina_csv(disciplina_path=None) -> Path:
    return Path(disciplina_path or os.environ.get(
        "DISCIPLINA", _root() / "modelo" / "voto_individual" / "outputs"
        / "disciplina_individual.csv"))


def roster_nominal(camara: str, fecha, bloques: list[dict],
                   padron_dir=None, disciplina_path=None,
                   min_votos: int = MIN_VOTOS_FICHA):
    """Construye el roster NOMINAL para simular: (lineas, desvios, detalle).

    camara  : 'diputados' | 'senado'
    fecha   : fecha de la votación (filtra el mandato desde<=F<=hasta del padrón)
    bloques : salida de proyectar_postura ([{bloque, linea, desvio, ...}]) — aporta
              la LÍNEA por linaje y el desvío promedio del bloque como fallback.

    Devuelve:
      lineas  : np.ndarray de str, una por legislador
      desvios : np.ndarray de float, una por legislador (escalera individual→bloque)
      detalle : dict con la trazabilidad (n por fuente de desvío, sin_linea, filas)
    """
    import pandas as pd

    pcsv = _padron_csv(camara, padron_dir)
    if not pcsv.exists():
        raise FileNotFoundError(f"falta el padrón oficial: {pcsv}")
    pad = pd.read_csv(pcsv, dtype=str, encoding="utf-8-sig")
    need = {"legislador_id", "bloque_linaje", "desde", "hasta"}
    faltan = need - set(pad.columns)
    if faltan:
        raise KeyError(f"padrón sin columnas {faltan}; hay {list(pad.columns)}")

    F = pd.to_datetime(fecha)
    if pd.isna(F):
        raise ValueError(f"fecha inválida para el roster: {fecha}")
    d0 = pd.to_datetime(pad["desde"], errors="coerce")
    d1 = pd.to_datetime(pad["hasta"], errors="coerce")
    vig = pad[(d0 <= F) & (F <= d1)].copy()
    if vig.empty:
        raise ValueError(f"padrón {pcsv.name}: ningún mandato vigente al {F.date()}")

    # línea y desvío-fallback por linaje (del proyector de bloque)
    por_linaje: dict[str, dict] = {}
    for b in bloques or []:
        linea = str(b.get("linea", "NO_ACOMPANA")).upper().strip()
        if linea not in CONDUCTAS:
            raise ValueError(f"linea inválida '{linea}' en bloque {b.get('bloque')}; "
                             f"usar una de {sorted(CONDUCTAS)}")
        por_linaje[str(b.get("bloque"))] = {
            "linea": linea, "desvio": float(b.get("desvio", DESVIO_NEUTRO))}

    # ficha individual (contrato de modelo/voto_individual)
    fichas = {}
    dcsv = _disciplina_csv(disciplina_path)
    if dcsv.exists():
        di = pd.read_csv(dcsv, encoding="utf-8-sig")
        for c in ("n_votos", "n_reciente", "tasa_desvio", "tasa_desvio_reciente"):
            if c in di.columns:
                di[c] = pd.to_numeric(di[c], errors="coerce")
        fichas = di.set_index("legislador_id").to_dict("index")
    else:
        logger.warning("sin disciplina_individual (%s): todos al fallback de bloque", dcsv)

    lineas, desvios, filas = [], [], []
    n_rec = n_glob = n_blo = n_sin_linea = 0
    for _, r in vig.iterrows():
        lid = r["legislador_id"]
        linaje = str(r["bloque_linaje"])
        info = por_linaje.get(linaje)
        if info is None:
            linea, d_blo = "NO_ACOMPANA", DESVIO_NEUTRO
            n_sin_linea += 1
        else:
            linea, d_blo = info["linea"], info["desvio"]

        f = fichas.get(lid) or {}
        d_rec, n_r = f.get("tasa_desvio_reciente"), f.get("n_reciente")
        d_gl, n_v = f.get("tasa_desvio"), f.get("n_votos")
        if d_rec is not None and pd.notna(d_rec) and (n_r or 0) >= min_votos:
            desvio, fuente = float(d_rec), "ficha_reciente"
            n_rec += 1
        elif d_gl is not None and pd.notna(d_gl) and (n_v or 0) >= min_votos:
            desvio, fuente = float(d_gl), "ficha_global"
            n_glob += 1
        else:
            desvio, fuente = float(d_blo), "bloque"
            n_blo += 1
        desvio = float(np.clip(desvio, 0.0, 1.0))
        lineas.append(linea)
        desvios.append(desvio)
        filas.append({"legislador_id": lid, "legislador": r.get("legislador"),
                      "bloque_linaje": linaje, "linea": linea,
                      "desvio": round(desvio, 4), "desvio_de": fuente})
    if n_sin_linea:
        logger.warning("roster nominal: %d legisladores con linaje sin línea proyectada "
                       "(entran NO_ACOMPANA, desvío neutro)", n_sin_linea)
    detalle = {"n": len(lineas), "ficha_reciente": n_rec, "ficha_global": n_glob,
               "fallback_bloque": n_blo, "sin_linea_proyectada": n_sin_linea,
               "min_votos_ficha": int(min_votos), "filas": filas}
    logger.info("roster nominal %s @%s: %d legisladores (ficha reciente %d, ficha "
                "global %d, fallback bloque %d)", camara, F.date(), len(lineas),
                n_rec, n_glob, n_blo)
    return np.array(lineas), np.array(desvios, dtype=float), detalle


# --------------------------------------------------------------------------- #
# Embudo: P(llega) + resolución del denominador                                #
# --------------------------------------------------------------------------- #
def _expedientes_path() -> Path:
    """Ruta del contrato de datos/expedientes (mapa denominador -> proyecto_id interno)."""
    return Path(os.environ.get(
        "EXPEDIENTES",
        _root() / "datos" / "expedientes" / "data" / "clean" / "expedientes.parquet"))


def _resolver_proyecto_id(entrada: str, expedientes_path: Path | None = None) -> str:
    """Traduce un denominador humano (1167-D-2025) al proyecto_id interno del embudo
    (HCDN...). Si ya es un id interno, o no se puede resolver, devuelve la entrada
    sin tocar (el embudo hará su propio fallback y logueará el faltante)."""
    pid = str(entrada).strip()
    if not _RE_DENOMINADOR.match(pid):
        return pid  # ya es id interno (o algo no-denominador): no hay nada que mapear
    deno = re.sub(r"\s+", "", pid).upper()
    ruta = expedientes_path or _expedientes_path()
    if not ruta.exists():
        logger.warning("no encontré %s: no puedo resolver el denominador %s (uso tal cual)",
                       ruta, deno)
        return pid
    import pandas as pd
    df = pd.read_parquet(ruta, columns=["proyecto_id", "exp_diputados", "exp_senado"])
    for col in ("exp_diputados", "exp_senado"):
        fila = df[df[col].astype(str).str.strip().str.upper() == deno]
        if not fila.empty:
            interno = str(fila["proyecto_id"].iloc[0])
            logger.info("denominador %s -> proyecto_id interno %s (%s)", deno, interno, col)
            return interno
    logger.warning("denominador %s no está en expedientes (uso tal cual; el embudo dirá si falta)",
                   deno)
    return pid


def _p_llega_de_embudo(proyecto_id: str, p_embudo_path: Path) -> float | None:
    """Busca p_llega_recinto del proyecto en el contrato del embudo."""
    if not p_embudo_path.exists():
        logger.warning("no encontré %s (paso p_llega por escenario)", p_embudo_path)
        return None
    import pandas as pd
    df = pd.read_parquet(p_embudo_path, columns=["proyecto_id", "p_llega_recinto"])
    fila = df[df["proyecto_id"].astype(str) == str(proyecto_id)]
    if fila.empty:
        logger.warning("proyecto %s no está en p_embudo (paso p_llega por escenario)",
                       proyecto_id)
        return None
    return float(fila["p_llega_recinto"].iloc[0])


# --------------------------------------------------------------------------- #
# Nowcast                                                                      #
# --------------------------------------------------------------------------- #
def nowcast_proyecto(proyecto_id: str, lineas: np.ndarray, desvios: np.ndarray,
                     tipo_mayoria: str, camara: str, p_embudo_path: Path,
                     p_llega=None, n_sims: int = 2000) -> dict:
    """Nowcast end-to-end de un proyecto sobre un roster NOMINAL ya armado
    (una línea y un desvío POR LEGISLADOR). P(aprobación) descompuesta."""
    simular = _cargar_simulador()

    # factor 1: P(llega al recinto) — del embudo (o override explícito).
    proyecto_id_interno = _resolver_proyecto_id(proyecto_id)
    if p_llega is None:
        p_llega = _p_llega_de_embudo(proyecto_id_interno, p_embudo_path)
    if p_llega is None:
        raise ValueError(
            f"sin p_llega_recinto para {proyecto_id} (interno {proyecto_id_interno}): no "
            "está en p_embudo y no vino como override. Corré variables/embudo, verificá "
            "el denominador, o pasá p_llega explícito.")
    p_llega = float(np.clip(p_llega, 0.0, 1.0))

    # factor 2: P(mayoría | recinto) — simulación legislador por legislador
    sim = simular(np.asarray(lineas), np.asarray(desvios, dtype=float),
                  tipo_mayoria=tipo_mayoria, camara=str(camara).strip().lower(),
                  n_sims=n_sims)
    p_mayoria = float(sim["p_aprobacion"])

    p_aprob = componer(p_llega, p_mayoria)
    return {
        "proyecto_id": proyecto_id,
        "proyecto_id_interno": proyecto_id_interno,
        "camara": sim["camara"],
        "tipo_mayoria": sim["tipo_mayoria"],
        "n_roster": sim["n_roster"],
        "p_llega_recinto": round(p_llega, 4),
        "p_mayoria_recinto": round(p_mayoria, 4),
        "p_aprobacion": round(p_aprob, 4),
        "afirmativos_medio": round(sim["afirm_medio"], 1),
        "afirmativos_banda_5_95": [round(sim["afirm_p5"], 1), round(sim["afirm_p95"], 1)],
        "umbral_medio": round(sim["umbral_medio"], 1),
    }


def nowcast_auto(proyecto_id: str, fecha: str, camara: str, tipo_mayoria: str,
                 p_embudo_path: Path, p_llega=None, canon_dir=None,
                 n_sims: int = 2000, tema=None, origen=None) -> dict:
    """Nowcast end-to-end con roster NOMINAL automático: padrón oficial vigente a la
    fecha (una fila por legislador, desvío individual de su ficha con escalera
    reciente→global→bloque) + línea de bloque proyectada por variables/bloque
    (walk-forward; condicionable por tema/origen vía tema_por_acta)."""
    cargar_bloque, proyectar_postura, cargar_tema_por_acta = _cargar_proyector()
    canon = Path(canon_dir) if canon_dir else _root() / "datos" / "canonica" / "data" / "clean"
    votos = cargar_bloque(canon)
    cond = cargar_tema_por_acta() if (tema or origen) else None
    bloques = proyectar_postura(votos, fecha, camara, tema=tema, origen=origen,
                                cond_por_acta=cond)
    lineas, desvios, detalle = roster_nominal(camara, fecha, bloques)
    logger.info("escenario auto NOMINAL: %d legisladores%s", detalle["n"],
                f" | condicionado tema={tema} origen={origen}" if (tema or origen) else "")
    nc = nowcast_proyecto(proyecto_id, lineas, desvios, tipo_mayoria, camara,
                          p_embudo_path, p_llega=p_llega, n_sims=n_sims)
    nc["fecha_escenario"] = fecha
    nc["bancas_totales"] = detalle["n"]
    nc["escenario_auto"] = True
    nc["roster_nominal"] = {k: v for k, v in detalle.items() if k != "filas"}
    nc["tema"] = tema
    nc["origen"] = origen
    nc["bloques_proyectados"] = bloques
    return nc


def imprimir_tarjeta(nc: dict) -> None:
    print("\n" + "=" * 56)
    print(f"  NOWCAST — proyecto {nc['proyecto_id']}  ({nc['camara']}, mayoría {nc['tipo_mayoria']})")
    if nc.get("proyecto_id_interno") and nc["proyecto_id_interno"] != nc["proyecto_id"]:
        print(f"  (id interno embudo: {nc['proyecto_id_interno']})")
    print("=" * 56)
    print(f"  P(llega al recinto)   {nc['p_llega_recinto']*100:6.1f}%   (embudo)")
    print(f"  P(mayoría | recinto)  {nc['p_mayoria_recinto']*100:6.1f}%   (agregador)")
    print(f"  {'-'*40}")
    print(f"  P(APROBACIÓN)         {nc['p_aprobacion']*100:6.1f}%   = producto")
    print(f"\n  Afirmativos esperados: {nc['afirmativos_medio']} "
          f"(banda 5-95%: {nc['afirmativos_banda_5_95'][0]}–{nc['afirmativos_banda_5_95'][1]}) "
          f"| umbral {nc['umbral_medio']}")
    rn = nc.get("roster_nominal")
    if rn:
        print(f"  Roster nominal: {rn['n']} legisladores "
              f"(ficha reciente {rn['ficha_reciente']} · ficha global {rn['ficha_global']} "
              f"· fallback bloque {rn['fallback_bloque']})")
    print("=" * 56)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _p_embudo_path() -> Path:
    return Path(os.environ.get(
        "P_EMBUDO", _root() / "variables" / "embudo" / "outputs" / "p_embudo.parquet"))


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd in ("demo", "nowcast"):
        raise SystemExit(f"'{cmd}' se eliminó 2026-07-22 (era de la puesta en marcha; "
                         "clonaba promedios de bloque). Usá nowcast_auto.")
    if cmd == "nowcast_auto":
        if len(argv) < 5:
            raise SystemExit("uso: python ensemble.py nowcast_auto <proyecto_id> "
                             "<YYYY-MM-DD> <camara> [tipo_mayoria] [p_llega] "
                             "[--tema AREA] [--origen ORIGEN]")
        tema = origen = None
        rest = list(argv[2:])
        pos = []
        i = 0
        while i < len(rest):
            if rest[i] == "--tema" and i + 1 < len(rest):
                tema = rest[i + 1]; i += 2
            elif rest[i] == "--origen" and i + 1 < len(rest):
                origen = rest[i + 1]; i += 2
            else:
                pos.append(rest[i]); i += 1
        proyecto_id, fecha, camara = pos[0], pos[1], pos[2]
        tipo = pos[3] if len(pos) > 3 else "SIMPLE"
        p_llega = float(pos[4]) if len(pos) > 4 else None
        nc = nowcast_auto(proyecto_id, fecha, camara, tipo, _p_embudo_path(),
                          p_llega=p_llega, tema=tema, origen=origen)
        imprimir_tarjeta(nc)
        out = Path(__file__).resolve().parents[1] / "outputs"
        out.mkdir(exist_ok=True)
        (out / f"nowcast_{proyecto_id}.json").write_text(
            json.dumps(nc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  -> outputs/nowcast_{proyecto_id}.json")
        return
    raise SystemExit(f"comando desconocido: {cmd!r} (usá nowcast_auto)")


if __name__ == "__main__":
    main(sys.argv)
