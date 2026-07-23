"""modelo/ensemble - composición final del Nowcast.

    P(aprobación) = P(llega al recinto) × P(mayoría | recinto)

Conecta las dos piezas ya validadas:
  - P(llega al recinto): `variables/embudo/outputs/p_embudo.parquet` (col p_llega_recinto),
    modelo de supervivencia del proyecto (embudo).
  - P(mayoría | recinto): `modelo/agregador_institucional` (función reutilizable
    `simular_votacion`), que simula el recuento como distribución con reglas de
    quórum y tipo de mayoría.

Entrega el **nowcast de un proyecto**: dado su `proyecto_id` (para el embudo) y un
escenario de votación (postura esperada de cada bloque, para el agregador), devuelve
P(aprobación) descompuesta en sus dos factores + la banda de votos.

El `proyecto_id` puede venir como DENOMINADOR humano (ej. 1167-D-2025) o como id
interno del embudo (HCDN...). Si es denominador, se traduce con el contrato de
datos/expedientes antes de buscar el p_llega.

SIMPLIFICACIÓN v1 (documentada, heredada del agregador): la POSTURA de cada bloque es
un dato de entrada (elegida a mano / observada). En el sistema final la proyecta un
módulo de posición de bloque por tema. Por eso la calibración de la cadena COMPLETA
sobre proyectos no votados espera esa proyección; hoy cada factor está validado por
separado (embudo: skill 0,34-0,39; agregador: Brier 0,0089).

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

# Denominador parlamentario, ej. "1167-D-2025" / "45-S-2024" (nro-letra-anio).
# Es como lo escribe el humano; el embudo indexa por proyecto_id interno (HCDN...).
_RE_DENOMINADOR = re.compile(r"^\s*\d+\s*-\s*[A-Za-z]+\s*-\s*\d{4}\s*$")


# --------------------------------------------------------------------------- #
# Import de la función reutilizable del agregador (contrato público de ese módulo)
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


# --------------------------------------------------------------------------- #
# Composición (el corazón del ensemble)                                        #
# --------------------------------------------------------------------------- #
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


def componer(p_llega: float, p_mayoria: float) -> float:
    """P(aprobación) = P(llega al recinto) × P(mayoría | recinto)."""
    if not (0.0 <= p_llega <= 1.0):
        raise ValueError(f"p_llega fuera de [0,1]: {p_llega}")
    if not (0.0 <= p_mayoria <= 1.0):
        raise ValueError(f"p_mayoria fuera de [0,1]: {p_mayoria}")
    return float(p_llega * p_mayoria)


def _expandir_roster(bloques: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Escenario por bloque -> arrays por legislador (lineas, desvios) para el agregador."""
    lineas, desvios = [], []
    for b in bloques:
        linea = str(b.get("linea", "NO_ACOMPANA")).upper().strip()
        if linea not in CONDUCTAS:
            raise ValueError(f"linea inválida '{linea}' en bloque {b.get('bloque')}; "
                             f"usar una de {sorted(CONDUCTAS)}")
        bancas = int(b.get("bancas", 0))
        if bancas <= 0:
            raise ValueError(f"bancas inválidas en bloque {b.get('bloque')}: {bancas}")
        desvio = float(b.get("desvio", 0.0))
        lineas += [linea] * bancas
        desvios += [np.clip(desvio, 0.0, 1.0)] * bancas
    if not lineas:
        raise ValueError("escenario sin bancas: no hay roster para simular")
    return np.array(lineas), np.array(desvios, dtype=float)


def _expedientes_path() -> Path:
    """Ruta del contrato de datos/expedientes (mapa denominador -> proyecto_id interno)."""
    root = Path(__file__).resolve().parents[3]
    return Path(os.environ.get(
        "EXPEDIENTES",
        root / "datos" / "expedientes" / "data" / "clean" / "expedientes.parquet"))


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


def nowcast_proyecto(proyecto_id: str, escenario: dict, p_embudo_path: Path,
                     n_sims: int = 2000) -> dict:
    """Nowcast end-to-end de un proyecto: P(aprobación) descompuesta."""
    simular = _cargar_simulador()

    # factor 1: P(llega al recinto) — del embudo (o del escenario como override).
    # El embudo indexa por proyecto_id interno; si vino un denominador (1167-D-2025)
    # lo traducimos antes de buscar. Guardamos ambos para la tarjeta y la trazabilidad.
    proyecto_id_interno = _resolver_proyecto_id(proyecto_id)
    p_llega = escenario.get("p_llega_recinto")
    if p_llega is None:
        p_llega = _p_llega_de_embudo(proyecto_id_interno, p_embudo_path)
    if p_llega is None:
        raise ValueError(
            f"sin p_llega_recinto para {proyecto_id} (interno {proyecto_id_interno}): no "
            "está en p_embudo y no vino en el escenario. Corré variables/embudo, verificá "
            "el denominador, o pasá 'p_llega_recinto' en el JSON.")
    p_llega = float(np.clip(p_llega, 0.0, 1.0))

    # factor 2: P(mayoría | recinto) — del agregador sobre el escenario de bloques
    lineas, desvios = _expandir_roster(escenario["bloques"])
    sim = simular(lineas, desvios,
                  tipo_mayoria=escenario.get("tipo_mayoria", "SIMPLE"),
                  camara=escenario.get("camara", "Diputados"),
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
    """Nowcast end-to-end con el escenario ARMADO por variables/bloque (proyector
    point-in-time) en vez de a mano: bancas = padron oficial vigente a la fecha
    (257/72), postura/desvio = historia. p_llega del embudo (o override).

    v2: si se pasa `tema` (area, ej. 'TRAB') y/o `origen` del proyecto, la DIRECCIÓN
    de cada bloque se condiciona a las votaciones del mismo tema/origen (consumiendo
    variables/proyecto/data/tema_por_acta.parquet). Sin tema/origen = incondicional (v1)."""
    cargar_bloque, proyectar_postura, cargar_tema_por_acta = _cargar_proyector()
    root = Path(__file__).resolve().parents[3]
    canon = Path(canon_dir) if canon_dir else root / "datos" / "canonica" / "data" / "clean"
    votos = cargar_bloque(canon)
    cond = cargar_tema_por_acta() if (tema or origen) else None
    bloques = proyectar_postura(votos, fecha, camara, tema=tema, origen=origen,
                                cond_por_acta=cond)
    n_bancas = sum(int(b["bancas"]) for b in bloques)
    logger.info("escenario auto: %d bloques, %d bancas (%s)%s", len(bloques), n_bancas,
                bloques[0].get("_bancas_de", "?"),
                f" | condicionado tema={tema} origen={origen}" if (tema or origen) else "")
    escenario = {"tipo_mayoria": tipo_mayoria, "camara": camara, "bloques": bloques,
                 "tema": tema, "origen": origen}
    if p_llega is not None:
        escenario["p_llega_recinto"] = float(p_llega)
    nc = nowcast_proyecto(proyecto_id, escenario, p_embudo_path, n_sims=n_sims)
    nc["fecha_escenario"] = fecha
    nc["bancas_totales"] = n_bancas
    nc["escenario_auto"] = True
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
    print("=" * 56)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _p_embudo_path() -> Path:
    root = Path(__file__).resolve().parents[3]
    return Path(os.environ.get(
        "P_EMBUDO", root / "variables" / "embudo" / "outputs" / "p_embudo.parquet"))


def _demo() -> dict:
    """Ejemplo end-to-end autocontenido (sin depender de archivos): Diputados,
    mayoría simple, un reparto peleado; p_llega del embudo puesto a mano."""
    escenario = {
        "tipo_mayoria": "SIMPLE", "camara": "Diputados",
        "p_llega_recinto": 0.12,
        "bloques": [
            {"bloque": "UxP", "bancas": 99, "linea": "NEGATIVO", "desvio": 0.03},
            {"bloque": "LLA", "bancas": 39, "linea": "AFIRMATIVO", "desvio": 0.02},
            {"bloque": "PRO", "bancas": 37, "linea": "AFIRMATIVO", "desvio": 0.05},
            {"bloque": "UCR", "bancas": 34, "linea": "AFIRMATIVO", "desvio": 0.12},
            {"bloque": "Federales", "bancas": 23, "linea": "NO_ACOMPANA", "desvio": 0.20},
            {"bloque": "Izquierda", "bancas": 5, "linea": "NEGATIVO", "desvio": 0.0},
            {"bloque": "Otros", "bancas": 20, "linea": "NO_ACOMPANA", "desvio": 0.25},
        ],
    }
    return nowcast_proyecto("DEMO-0000-D-2026", escenario, Path("/no/existe"))


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cmd = argv[1] if len(argv) > 1 else "demo"
    if cmd == "demo":
        imprimir_tarjeta(_demo())
        return
    if cmd == "nowcast":
        if len(argv) < 4:
            raise SystemExit("uso: python ensemble.py nowcast <proyecto_id> <escenario.json>")
        proyecto_id, ruta = argv[2], Path(argv[3])
        escenario = json.loads(ruta.read_text(encoding="utf-8"))
        nc = nowcast_proyecto(proyecto_id, escenario, _p_embudo_path())
        imprimir_tarjeta(nc)
        out = Path(__file__).resolve().parents[1] / "outputs"
        out.mkdir(exist_ok=True)
        (out / f"nowcast_{proyecto_id}.json").write_text(
            json.dumps(nc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  -> outputs/nowcast_{proyecto_id}.json")
        return
    if cmd == "nowcast_auto":
        if len(argv) < 5:
            raise SystemExit("uso: python ensemble.py nowcast_auto <proyecto_id> <YYYY-MM-DD> <camara> [tipo_mayoria] [p_llega] [--tema AREA] [--origen ORIGEN]")
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
    raise SystemExit(f"comando desconocido: {cmd} (usá demo | nowcast | nowcast_auto)")


if __name__ == "__main__":
    main(sys.argv)
