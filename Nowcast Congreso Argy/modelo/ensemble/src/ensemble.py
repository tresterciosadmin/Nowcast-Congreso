"""modelo/ensemble - la maquinaria compartida del roster y la simulación.

⚠️ LA FORMULACIÓN v1 DE ESTE ARCHIVO ESTÁ DADA DE BAJA (2026-08-22, ADR-0012).
   Era: P(aprobación) = P(llega al recinto) × P(mayoría | recinto).
   `componer`, `_p_llega_de_embudo`, `nowcast_proyecto`, `nowcast_auto`,
   `imprimir_tarjeta` y la CLI **levantan SystemExit con el motivo**. No se borraron a
   propósito: quien las llame recibe una explicación y a dónde ir, en vez de un
   ImportError sin contexto. El punto de entrada vivo es `nowcast_puertas.nowcast(...)`.

LO QUE SIGUE VIVO Y ES DE ACÁ: `roster_nominal` (el roster point-in-time, con la
escalera de desvío y la foto completa de la cámara) y `simular_con_guardas` (el
agregador con el piso de desvío y el techo de confianza). Los consumen la Puerta B, la
Puerta D y `casos/`.

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
_BAJA_V1 = (
    "La formulacion v1 -P(aprobacion) = P(llega al recinto) x P(mayoria | recinto)- se "
    "dio de BAJA el 2026-08-22 (ADR-0012). `p_llega_recinto` media la mortandad en el "
    "cajon: agenda politica, y se decidio no modelarla. El punto de entrada vivo es "
    "`modelo/ensemble/src/nowcast_puertas.py` (funcion `nowcast`), que corre la cadena "
    "de puertas y devuelve un numero CONDICIONAL a que las camaras voten, con el "
    "desagregado por legislador. El codigo viejo quedo entero en "
    "Archivos_Borrar/BORRAR_modelo-ensemble-src-ensemble-v1.py")


def componer(*args, **kwargs):
    """DADA DE BAJA (2026-08-22) - era el corazon de la v1. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


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
                   min_votos: int = MIN_VOTOS_FICHA, padron_file=None):
    """Construye el roster NOMINAL para simular: (lineas, desvios, detalle).

    camara  : 'diputados' | 'senado'
    fecha   : fecha de la votación (filtra el mandato desde<=F<=hasta del padrón)
    bloques : salida de proyectar_postura ([{bloque, linea, desvio, ...}]) — aporta
              la LÍNEA por linaje y el desvío promedio del bloque como fallback.
    padron_file : ruta explícita al padrón. Si se pasa, IGNORA el nombre por defecto
              `padron_<camara>.csv`. Lo usa la Puerta D para apuntar al padrón
              HISTÓRICO del Senado (`padron_senado_historico.csv`), que tiene los
              mandatos 2017→2031 en vez de sólo los 72 vigentes. Backward-compatible:
              sin este argumento, todo se comporta como antes.

    Devuelve:
      lineas  : np.ndarray de str, una por legislador
      desvios : np.ndarray de float, una por legislador (escalera individual→bloque)
      detalle : dict con la trazabilidad (n por fuente de desvío, sin_linea, filas)
    """
    import pandas as pd

    F = pd.to_datetime(fecha)
    if pd.isna(F):
        raise ValueError(f"fecha inválida para el roster: {fecha}")

    if padron_file or padron_dir:
        # Ruta EXPLÍCITA: un solo archivo, tal cual se pidió. La usan los tests con
        # padrones sintéticos y cualquiera que quiera fijar la fuente a mano.
        pcsv = Path(padron_file) if padron_file else _padron_csv(camara, padron_dir)
        if not pcsv.exists():
            raise FileNotFoundError(f"falta el padrón oficial: {pcsv}")
        pad = pd.read_csv(pcsv, dtype=str, encoding="utf-8-sig")
        need = {"legislador_id", "bloque_linaje", "desde", "hasta"}
        faltan = need - set(pad.columns)
        if faltan:
            raise KeyError(f"padrón sin columnas {faltan}; hay {list(pad.columns)}")
        d0 = pd.to_datetime(pad["desde"], errors="coerce")
        d1 = pd.to_datetime(pad["hasta"], errors="coerce")
        vig = pad[(d0 <= F) & (F <= d1)].copy()
        origen_padron = pcsv.name
    else:
        # Por DEFECTO: la foto completa de la cámara (oficial + histórico, sin
        # duplicados). Antes se leía un solo archivo y el oficial cubre 81 de 257
        # bancas en 2008 y 203 en 2019: todo cálculo sobre fechas viejas corría
        # sobre una cámara agujereada. Ver datos/padron/src/padron_vigente.py, que
        # es el único lugar donde vive la regla de fusión.
        sys.path.insert(0, str(_root() / "datos" / "padron" / "src"))
        from padron_vigente import padron_vigente  # type: ignore
        vig = padron_vigente(camara, F).copy()
        origen_padron = "oficial+histórico"
        need = {"legislador_id", "bloque_linaje", "desde", "hasta"}
        faltan = need - set(vig.columns)
        if faltan:
            raise KeyError(f"padrón sin columnas {faltan}; hay {list(vig.columns)}")
    if vig.empty:
        raise ValueError(f"padrón {origen_padron}: ningún mandato vigente al {F.date()}")

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
        for c in ("n_votos", "n_reciente", "n_presente", "tasa_desvio", "tasa_desvio_reciente",
                  "tasa_desvio_conducta", "tasa_desvio_reciente_conducta"):
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
        # Desvío de CONDUCTA (votó distinto ESTANDO PRESENTE), con fallback a la
        # mezclada si la planilla es vieja. Evita que un ausente crónico entre como
        # bisagra en la proyección (URGENTE 1, 2026-08-13).
        d_rec = f.get("tasa_desvio_reciente_conducta")
        if d_rec is None or pd.isna(d_rec):
            d_rec = f.get("tasa_desvio_reciente")
        d_gl = f.get("tasa_desvio_conducta")
        if d_gl is None or pd.isna(d_gl):
            d_gl = f.get("tasa_desvio")
        n_r, n_v = f.get("n_reciente"), f.get("n_votos")
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
    detalle = {"n": len(lineas), "padron": origen_padron,
               "ficha_reciente": n_rec, "ficha_global": n_glob,
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


def _p_llega_de_embudo(*args, **kwargs):
    """DADA DE BAJA (2026-08-22) - leia p_llega_recinto del contrato del embudo. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


# --------------------------------------------------------------------------- #
# Nowcast                                                                      #
# --------------------------------------------------------------------------- #
# Incertidumbre IRREDUCIBLE (2026-08-14, pedido de Valle). Dos topes contra la
# sobreconfianza del agregado, que bajo votos independientes daba P(mayoría)=100% exacto:
#  - DESVIO_MIN_INDIVIDUAL: ni el legislador más leal es un 100% seguro. Se le pone un
#    piso de desvío a CADA legislador antes de simular (un 0% medido sobre historia
#    finita no es un 0 real: siempre hay ausencia/enfermedad/sorpresa).
#  - P_INCERTIDUMBRE: ninguna votación es 0%/100% segura — hay riesgo SISTÉMICO
#    (ausencias masivas, un sacudón político, una sorpresa de bloque) que el supuesto
#    de votos INDEPENDIENTES no capta. P(mayoría) se reporta en [ε, 1-ε].
DESVIO_MIN_INDIVIDUAL = 0.02
P_INCERTIDUMBRE = 0.01


def simular_con_guardas(lineas, desvios, tipo_mayoria: str, camara: str, *,
                        n_sims: int = 2000, seed: int | None = 0,
                        desvio_min: float = DESVIO_MIN_INDIVIDUAL,
                        p_incertidumbre: float = P_INCERTIDUMBRE,
                        p_presente=None, reparto_desvio: float = 0.5) -> dict:
    """Corre el agregador CON las dos guardas contra la sobreconfianza.

    ÚNICO lugar donde viven esas dos guardas (2026-08-22). Antes estaban sólo dentro
    de `nowcast_proyecto` —o sea, sólo en el camino de la formulación v1—, mientras
    que `puerta_d.p_voto_revisora` tomaba `sim["p_aprobacion"]` crudo y
    `casos/proyeccion_hipotetica_bicameral.py` tenía su PROPIA copia del clamp. Tres
    lugares, dos definiciones y una ausencia: al dar de baja v1, la producción se
    quedaba sin el techo de confianza justo en la puerta que sobrevive.

    Las dos guardas (pedido de Valle, 2026-08-14):
      - `desvio_min`: piso de desvío POR LEGISLADOR. Un 0% medido sobre historia
        finita no es un 0 real: siempre hay ausencia, enfermedad o sorpresa.
      - `p_incertidumbre`: ε de riesgo SISTÉMICO que el supuesto de votos
        independientes no capta. P(mayoría) se reporta en [ε, 1-ε], nunca 0%/100%.

    Poner las dos en 0 devuelve el comportamiento crudo del agregador.

    Devuelve el dict de `simular_votacion` con `p_aprobacion` YA acotada, más la
    trazabilidad de lo que se aplicó (`p_aprobacion_cruda`, `desvio_min_aplicado`,
    `p_incertidumbre_aplicada`) para que el clamp nunca sea invisible.
    """
    simular = _cargar_simulador()
    desv = np.maximum(np.asarray(desvios, dtype=float), float(max(desvio_min, 0.0)))
    # `p_presente` es el modo ASISTENCIA del agregador: la línea es la dirección del
    # voto y cada legislador la emite SÓLO si está presente. Sin esto, alguien que casi
    # nunca vota entra igual como un voto entero — que es lo que pasaba con el
    # presidente de la Cámara, contado como afirmativo casi seguro.
    extra = {} if p_presente is None else {"p_presente": np.asarray(p_presente, dtype=float)}
    sim = simular(np.asarray(lineas), desv, tipo_mayoria=tipo_mayoria,
                  camara=str(camara).strip().lower(), n_sims=n_sims, seed=seed,
                  reparto_desvio=float(reparto_desvio), **extra)
    cruda = float(sim["p_aprobacion"])
    eps = float(np.clip(p_incertidumbre, 0.0, 0.5))
    sim = dict(sim)
    sim["p_aprobacion"] = float(np.clip(cruda, eps, 1.0 - eps))
    sim["p_aprobacion_cruda"] = cruda
    sim["desvio_min_aplicado"] = float(max(desvio_min, 0.0))
    sim["p_incertidumbre_aplicada"] = eps
    return sim


def nowcast_proyecto(*args, **kwargs):
    """DADA DE BAJA (2026-08-22) - exigia p_llega_recinto y sin el tiraba ValueError. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


def nowcast_auto(*args, **kwargs):
    """DADA DE BAJA (2026-08-22) - componia la cadena v1 con roster automatico. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


def imprimir_tarjeta(*args, **kwargs):
    """DADA DE BAJA (2026-08-22) - imprimia la tarjeta de la v1. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _p_embudo_path() -> Path:
    return Path(os.environ.get(
        "P_EMBUDO", _root() / "variables" / "embudo" / "outputs" / "p_embudo.parquet"))


def main(argv: list[str]) -> None:
    """DADA DE BAJA (2026-08-22) - la CLI corria nowcast_auto. Ver `_BAJA_V1`."""
    raise SystemExit(_BAJA_V1)


if __name__ == "__main__":
    main(sys.argv)
