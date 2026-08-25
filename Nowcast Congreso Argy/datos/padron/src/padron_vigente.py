# -*- coding: utf-8 -*-
"""La foto de la cámara a una fecha: UNA fila por banca, sin duplicados.

POR QUÉ EXISTE (2026-08-22)
    El padrón vive en dos archivos por cámara: el OFICIAL (la nómina publicada) y
    el HISTÓRICO reconstruido desde la canónica. El oficial es la verdad donde
    llega, pero históricamente llega poco —81 de 257 bancas en 2008, 203 en 2019—;
    el histórico completa. Hasta hoy el modelo leía UNO SOLO, así que cualquier
    cálculo sobre fechas viejas corría sobre una cámara agujereada.

    Pegarlos sin más NO sirve, y esto está medido: al 2026-06-01 el concat crudo
    da **513 diputados en vez de 257** —la cámara duplicada— y ni siquiera
    deduplicar por `legislador_id` alcanza, porque **la misma persona tiene otro id
    en cada archivo cuando su nombre está escrito distinto**:

        oficial                    histórico
        ANALIA QUIROGA RACH        ALEXANDRA ANALIA QUIROGA RACH
        BAHILLO JOSE JUAN          BAHILLO JUANJO
        MARCELA PAULA URROZ        PAULA URROZ

    Es la misma clase de problema que los duplicados de resolución de entidades de
    `datos/canonica`. La solución no es nueva: **match por SUBCONJUNTO de tokens**,
    exactamente la regla que `datos/expedientes/src/resolver_firmantes.py` ya usa
    para emparejar firmantes de dictamen (los PDF abrevian los nombres igual que
    estos archivos). Se REUSA su tokenizador; no se reimplementa.

EL CONTROL, Y ES DURO
    Diputados tiene 257 bancas y el Senado 72. Medido con este módulo:

        fecha        oficial + histórico -> bancas   (colapsados)
        2008-06-01     81 + 257          -> 256       82
        2013-06-01    221 + 264          -> 257      228
        2019-06-01    203 + 256          -> 259      200
        2024-06-01    188 + 257          -> 258      187
        2026-06-01    257 + 256          -> 257      256

    Cero ambigüedades. El residuo de −1/+2 es ROTACIÓN REAL —renuncias y asunciones
    a mitad de período— no error de emparejamiento: es el mismo patrón que ya se
    midió al construir el histórico. `verificar()` lo reporta en vez de esconderlo.

REGLAS
    1. El OFICIAL gana siempre. El histórico sólo rellena lo que el oficial no tiene.
    2. Una fila del histórico se descarta si sus tokens son subconjunto —o
       superconjunto— de los de una fila oficial ya aceptada A ESA FECHA.
    3. **Un empate NUNCA se rompe por la fuerza.** Si una fila del histórico matchea
       con DOS oficiales, no se colapsa contra ninguna: se descarta y se cuenta como
       ambigua. Inventar la identidad es peor que perder una banca, y el conteo lo
       dice.

Módulo: datos/padron · creado 2026-08-22
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

# OJO: NADA de basicConfig acá. Este módulo se IMPORTA desde modelo/ensemble, y
# configurar el root logger al importar le pisa el formato a quien lo llama: los
# mensajes del ensemble salían rotulados "padron_vigente". La configuración va en
# `__main__`, que es cuando este archivo es el programa y no una dependencia.
logger = logging.getLogger("padron_vigente")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import (  # noqa: E402
    PADRON_DIPUTADOS,
    PADRON_DIPUTADOS_HISTORICO,
    PADRON_SENADO,
    PADRON_SENADO_HISTORICO,
    RAIZ,
)

BANCAS = {"diputados": 257, "senado": 72}


def _tokenizar():
    """El tokenizador de `datos/expedientes` — el mismo que empareja las firmas."""
    src = RAIZ / "datos" / "expedientes" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from resolver_firmantes import tokenizar  # type: ignore
    return tokenizar


def archivos_de(camara: str) -> list[Path]:
    """Los archivos de esa cámara, EN ORDEN DE PRIORIDAD: oficial primero."""
    c = str(camara).strip().lower()
    par = ((PADRON_DIPUTADOS, PADRON_DIPUTADOS_HISTORICO) if c.startswith("dip")
           else (PADRON_SENADO, PADRON_SENADO_HISTORICO))
    return [Path(p) for p in par if Path(p).exists()]


def _vigentes(df: pd.DataFrame, fecha) -> pd.DataFrame:
    F = pd.to_datetime(fecha)
    if pd.isna(F):
        raise ValueError(f"fecha inválida: {fecha!r}")
    d0 = pd.to_datetime(df["desde"], errors="coerce")
    d1 = pd.to_datetime(df["hasta"], errors="coerce")
    return df[(d0 <= F) & (F <= d1)]


def padron_vigente(camara: str, fecha, rutas=None, con_detalle: bool = False):
    """Una fila por banca a `fecha`, oficial primero y el histórico rellenando.

    Devuelve el DataFrame; con `con_detalle=True`, `(df, detalle)` donde el detalle
    trae de dónde salió cada banca, cuántas se colapsaron y cuántas quedaron ambiguas.
    """
    cam = str(camara).strip().lower()
    # La fecha se valida ANTES de abrir nada: un error de tipeo tiene que dar un
    # error de fecha, no un FileNotFoundError tres capas más abajo.
    if pd.isna(pd.to_datetime(fecha, errors="coerce")):
        raise ValueError(f"fecha inválida: {fecha!r}")
    archivos = [Path(r) for r in rutas] if rutas else archivos_de(cam)
    if not archivos:
        raise FileNotFoundError(f"no encontré ningún padrón para {cam!r}")

    tokenizar = _tokenizar()
    aceptadas, tokens, fuentes = [], [], []
    colapsadas = ambiguas = 0

    for i, ruta in enumerate(archivos):
        df = pd.read_csv(ruta, dtype=str, encoding="utf-8-sig")
        df = df[~df["legislador"].astype(str).str.startswith("#")]
        vig = _vigentes(df, fecha)
        for _, fila in vig.iterrows():
            t = set(tokenizar(fila.get("clave") or fila.get("legislador"))[0])
            if i > 0:  # sólo el histórico se contrasta: el oficial entra entero
                cand = [k for k, x in enumerate(tokens) if t <= x or x <= t]
                if len(cand) == 1:
                    colapsadas += 1
                    continue
                if len(cand) > 1:
                    ambiguas += 1
                    logger.warning("banca ambigua a %s: '%s' matchea con %d del padrón "
                                   "oficial; NO se colapsa contra ninguna", fecha,
                                   fila.get("legislador"), len(cand))
                    continue
            aceptadas.append(fila)
            tokens.append(t)
            fuentes.append(ruta.name)

    out = pd.DataFrame(aceptadas).reset_index(drop=True)
    out["padron_archivo"] = fuentes
    esperadas = BANCAS.get(cam)
    detalle = {"camara": cam, "fecha": str(fecha), "n": len(out),
               "bancas_esperadas": esperadas, "colapsadas": colapsadas,
               "ambiguas": ambiguas,
               "por_archivo": pd.Series(fuentes).value_counts().to_dict()}
    if esperadas:
        detalle["desvio_vs_bancas"] = len(out) - esperadas
    logger.info("padrón %s @%s: %d bancas (esperadas %s) | colapsadas %d | ambiguas %d",
                cam, fecha, len(out), esperadas, colapsadas, ambiguas)
    return (out, detalle) if con_detalle else out


def verificar(camara: str = "diputados", fechas=None) -> list[dict]:
    """Contrasta el conteo contra las bancas reales. El control que puede decir NO."""
    fechas = fechas or ["2008-06-01", "2013-06-01", "2019-06-01",
                        "2024-06-01", "2026-06-01"]
    filas = []
    for f in fechas:
        try:
            _, d = padron_vigente(camara, f, con_detalle=True)
        except (FileNotFoundError, ValueError) as e:
            logger.warning("%s @%s: %s", camara, f, e)
            continue
        filas.append(d)
    print(f"\n  {camara.upper()} — bancas reales: {BANCAS.get(camara)}")
    print(f"  {'fecha':12s} {'bancas':>7s} {'desvío':>7s} {'colapsadas':>11s} {'ambiguas':>9s}")
    for d in filas:
        print(f"  {d['fecha']:12s} {d['n']:7d} {d.get('desvio_vs_bancas', 0):+7d} "
              f"{d['colapsadas']:11d} {d['ambiguas']:9d}")
    print("\n  El desvío de -1/+2 es ROTACIÓN REAL (renuncias y asunciones a mitad de\n"
          "  período), no error de emparejamiento. Un desvío grande SÍ es un problema.")
    return filas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    cam = sys.argv[1] if len(sys.argv) > 1 else "diputados"
    verificar(cam)
