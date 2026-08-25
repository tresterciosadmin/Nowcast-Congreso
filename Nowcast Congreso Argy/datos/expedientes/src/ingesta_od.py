# -*- coding: utf-8 -*-
"""Baja los PDF de las Órdenes del Día de DIPUTADOS que contienen dictámenes de LEY.

## Por qué existe

Los firmantes del dictamen —quién lo firmó, quién firmó en disidencia— no están
en el CKAN de Diputados. Están sólo en el PDF de la Orden del Día. Este script
arma la lista de trabajo desde nuestros propios parquet, baja cada PDF a un caché
en disco y deja un manifiesto de qué entró y qué falló. **No parsea nada**: eso
es `parser_od.py`, para que un cambio en el parser no obligue a volver a bajar.

## Qué baja y qué no

Sólo proyectos de **LEY** (incluye "MENSAJE Y PROYECTO DE LEY"). Medido el
21-08-2026: de 18.087 Órdenes del Día únicas, **2.523 son de proyectos de ley** y
cubren 3.176 proyectos. Las otras ~15.500 son resoluciones (2.988) y
declaraciones (2.254) — homenajes, beneplácitos, pedidos de informe — que no son
insumo de ninguna puerta. Con `--tipos` se puede pedir el resto.

## Régimen de descartables

El PDF crudo es **regenerable**: va a `Archivos_Borrar/od_pdf/` y nadie lo trata
como fuente de verdad. Lo que sí es contrato es la salida del parser.

## Cómo se corre (PC con internet, PowerShell — es una corrida larga)

    python datos/expedientes/src/ingesta_od.py                # las 2.523 de ley
    python datos/expedientes/src/ingesta_od.py --solo-lista   # arma la lista y no baja nada
    python datos/expedientes/src/ingesta_od.py --limite 20    # prueba corta
    python datos/expedientes/src/ingesta_od.py --desde 2023   # sólo la ventana viva

Es **reanudable**: lo ya bajado y válido se saltea, así que se puede cortar con
Ctrl-C y volver a lanzar. `REFRESH=1` fuerza a bajar de nuevo todo.
Variables: `OD_CACHE=/dir`  `EXP_CLEAN=/dir`  `REFRESH=1`.

## Las 4 directivas de resiliencia

Errores específicos (un 404 no se reintenta en el espejo: significa que esa OD no
existe con ese número y período), backoff en red, parsing defensivo (columnas por
nombre, guardas con `pd.isna()`), y logging estructurado con un manifiesto por
archivo. **Falla ruidoso:** lo que no se pudo bajar queda listado con su motivo,
no desaparece del conteo.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import EXPEDIENTES_CLEAN, RAIZ  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from od_url import nombre_pdf, numero_od, periodo_de, urls_od  # noqa: E402

logger = logging.getLogger("expedientes.ingesta_od")

TIPOS_LEY = ("LEY", "MENSAJE Y PROYECTO DE LEY")
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/expedientes; ingesta_od)"}
TIMEOUT = 120
REINTENTOS = 3
PAUSA = 0.35          # segundos entre descargas; no hay apuro y el sitio es del Estado
MINIMO_PDF = 1500     # bytes: por debajo de esto no es una OD, es una página de error


def cache_dir() -> Path:
    return Path(os.environ.get("OD_CACHE", RAIZ / "Archivos_Borrar" / "od_pdf"))


# ───────────────────────────── lista de trabajo ─────────────────────────────

def construir_lista(clean: Path, tipos: tuple[str, ...] = TIPOS_LEY) -> pd.DataFrame:
    """Una fila por Orden del Día a bajar, con los proyectos que cubre.

    El grano es (od_numero, od_publicacion): el mismo número de OD se repite
    entre legislaturas —el numerador reinicia con la renovación de la Cámara—,
    así que el número solo NO identifica una Orden del Día.
    """
    res = pd.read_parquet(clean / "expedientes_resultados.parquet")
    exp = pd.read_parquet(clean / "expedientes.parquet")

    for col in ("proyecto_id", "od_numero", "od_publicacion"):
        if col not in res.columns:
            raise KeyError(f"expedientes_resultados.parquet no tiene la columna {col!r}")
    if "tipo" not in exp.columns:
        raise KeyError("expedientes.parquet no tiene la columna 'tipo'")

    res = res[["proyecto_id", "od_numero", "od_publicacion"]].copy()
    res["od_publicacion"] = pd.to_datetime(res["od_publicacion"], errors="coerce")
    res = res[res["od_numero"].notna() & res["od_publicacion"].notna()]

    tipos_norm = {t.upper() for t in tipos}
    exp = exp[["proyecto_id", "tipo"]].copy()
    exp["tipo"] = exp["tipo"].map(lambda v: "" if pd.isna(v) else str(v).strip().upper())
    exp = exp[exp["tipo"].isin(tipos_norm)]

    m = res.merge(exp, on="proyecto_id", how="inner")
    if m.empty:
        raise SystemExit(f"la lista quedó vacía: ningún proyecto con tipo en {sorted(tipos_norm)}")

    # el número viene como texto con ceros ("0356"); se normaliza una sola vez acá
    m["od_num"] = m["od_numero"].map(numero_od)
    m["periodo"] = m["od_publicacion"].map(periodo_de)
    m["archivo"] = [nombre_pdf(n, f) for n, f in zip(m["od_numero"], m["od_publicacion"])]

    # El archivo es UNO solo por (periodo, numero): esa pareja es lo que arma la URL.
    # En 6 casos de 2.523 el parquet trae DOS fechas de publicación para el mismo
    # (periodo, numero) — p. ej. 132-671 figura el 10-sep-2014 y el 10-oct-2014.
    # Las dos fechas caen en el mismo período, así que apuntan al MISMO PDF: se
    # unen en una fila (fecha mínima, unión de proyectos) y queda `n_fechas` > 1
    # como marca. No se descarta ninguno de los dos juegos de proyectos: cuál
    # corresponde de verdad lo dirime el parser, que lee los expedientes del PDF.
    lista = (m.groupby(["periodo", "od_num", "archivo"], as_index=False)
               .agg(od_publicacion=("od_publicacion", "min"),
                    n_fechas=("od_publicacion", "nunique"),
                    n_proyectos=("proyecto_id", "nunique"),
                    proyecto_ids=("proyecto_id", lambda s: ";".join(sorted(set(s))))))
    lista["url"] = [urls_od(n, f)[0] for n, f in zip(lista["od_num"], lista["od_publicacion"])]
    lista = lista.sort_values(["od_publicacion", "od_num"]).reset_index(drop=True)

    if lista["archivo"].duplicated().any():   # no debería poder pasar; si pasa, se corta
        repes = sorted(lista.loc[lista["archivo"].duplicated(keep=False), "archivo"])
        raise SystemExit(f"dos filas apuntan al mismo archivo, la lista está mal: {repes}")
    ambiguas = int((lista["n_fechas"] > 1).sum())
    if ambiguas:
        logger.warning("%d Órdenes del Día con más de una fecha de publicación en el "
                       "parquet; se toma la mínima y se unen los proyectos", ambiguas)
    return lista


# ───────────────────────────── descarga ─────────────────────────────

def _bajar_una(url: str, destino: Path) -> tuple[bool, str]:
    """Devuelve (ok, detalle). Escribe el archivo sólo si es un PDF de verdad."""
    ultimo = "sin intentos"
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        except requests.RequestException as exc:
            ultimo = f"{type(exc).__name__}: {exc}"
            time.sleep(min(2 ** intento, 10))
            continue
        if r.status_code == 404:
            return False, "404"          # no existe; reintentar sólo esconde el problema
        if r.status_code != 200:
            ultimo = f"HTTP {r.status_code}"
            time.sleep(min(2 ** intento, 10))
            continue
        cuerpo = r.content
        if not cuerpo.startswith(b"%PDF-"):
            return False, f"no es PDF (cabecera {cuerpo[:8]!r}, {len(cuerpo)} bytes)"
        if len(cuerpo) < MINIMO_PDF:
            return False, f"PDF sospechosamente chico ({len(cuerpo)} bytes)"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(cuerpo)
        return True, "ok"
    return False, ultimo


def bajar(lista: pd.DataFrame, destino: Path, refresh: bool = False) -> pd.DataFrame:
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    total = len(lista)
    for i, fila in enumerate(lista.itertuples(index=False), start=1):
        ruta = destino / fila.archivo
        if ruta.exists() and ruta.stat().st_size >= MINIMO_PDF and not refresh:
            estado, detalle = "cache", "ya estaba"
        else:
            ok = False
            detalle = ""
            for url in urls_od(fila.od_num, fila.od_publicacion):
                ok, detalle = _bajar_una(url, ruta)
                if ok or detalle == "404":
                    break            # el 404 no se reintenta en el espejo
                logger.warning("espejo falló (%s) para %s: %s", url, fila.archivo, detalle)
            estado = "ok" if ok else "FALLA"
            time.sleep(PAUSA)
        bytes_ = ruta.stat().st_size if ruta.exists() else 0
        sha = (hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]
               if estado in ("ok", "cache") and ruta.exists() else "")
        filas.append({"archivo": fila.archivo, "periodo": fila.periodo,
                      "od_numero": fila.od_num, "od_publicacion": fila.od_publicacion,
                      "url": fila.url, "estado": estado, "detalle": detalle,
                      "bytes": bytes_, "sha256_16": sha,
                      "n_fechas": fila.n_fechas,
                      "n_proyectos": fila.n_proyectos, "proyecto_ids": fila.proyecto_ids})
        if i % 50 == 0 or i == total:
            hechos = sum(1 for f in filas if f["estado"] in ("ok", "cache"))
            logger.info("%d/%d  ok+cache=%d  fallas=%d", i, total, hechos, len(filas) - hechos)
    return pd.DataFrame(filas)


# ───────────────────────────── CLI ─────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tipos", default=",".join(TIPOS_LEY),
                    help="tipos de proyecto separados por coma (por defecto, sólo LEY)")
    ap.add_argument("--desde", type=int, default=None, help="año parlamentario mínimo")
    ap.add_argument("--hasta", type=int, default=None, help="año parlamentario máximo")
    ap.add_argument("--limite", type=int, default=None, help="bajar sólo las primeras N")
    ap.add_argument("--solo-lista", action="store_true", help="arma la lista y no baja nada")
    args = ap.parse_args(argv)

    # stream=sys.stdout a propósito: por defecto logging escribe en stderr, y
    # PowerShell pinta de ROJO todo lo que un proceso manda por stderr —incluido
    # un INFO de avance— y encima lo envuelve en un NativeCommandError. Una
    # corrida sana parecía estar fallando. Con stdout, `| Tee-Object` alcanza y
    # no hace falta el `2>&1`.
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    clean = Path(os.environ.get("EXP_CLEAN", EXPEDIENTES_CLEAN))
    destino = cache_dir()

    tipos = tuple(t.strip().upper() for t in args.tipos.split(",") if t.strip())
    lista = construir_lista(clean, tipos)

    if args.desde:
        lista = lista[lista["periodo"] >= args.desde - 1882]
    if args.hasta:
        lista = lista[lista["periodo"] <= args.hasta - 1882]
    if args.limite:
        lista = lista.head(args.limite)

    destino.mkdir(parents=True, exist_ok=True)
    ruta_lista = destino / "od_trabajo.csv"
    lista.to_csv(ruta_lista, index=False, encoding="utf-8")
    logger.info("lista de trabajo: %d Órdenes del Día, %d proyectos -> %s",
                len(lista), int(lista["n_proyectos"].sum()), ruta_lista)
    logger.info("períodos %d a %d (%d a %d)", lista["periodo"].min(), lista["periodo"].max(),
                lista["periodo"].min() + 1882, lista["periodo"].max() + 1882)
    if args.solo_lista:
        return 0

    manifiesto = bajar(lista, destino, refresh=bool(os.environ.get("REFRESH")))
    ruta_man = destino / "od_descargas.csv"
    manifiesto.to_csv(ruta_man, index=False, encoding="utf-8")

    por_estado = manifiesto["estado"].value_counts().to_dict()
    logger.info("RESULTADO %s -> %s", por_estado, ruta_man)
    fallas = manifiesto[manifiesto["estado"] == "FALLA"]
    if len(fallas):
        logger.warning("%d Órdenes del Día NO se pudieron bajar. Motivos:", len(fallas))
        for motivo, n in fallas["detalle"].value_counts().items():
            logger.warning("  %4d  %s", n, motivo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
