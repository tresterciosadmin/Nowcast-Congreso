# -*- coding: utf-8 -*-
"""datos/expedientes — NOMBRE de cada capítulo, leído del PDF de la Orden del Día
(B2, addendum de ADR-0023: "es la vía para conseguir el NOMBRE de cada capítulo
—útil para presentar el número, no para calcularlo—").

PROBLEMA QUE RESUELVE
----------------------
`votacion_por_articulo.py::extraer_titulo_capitulo` ya saca el NUMERAL romano
del capítulo ("VIII") leyendo el título de cada acta — barato, sin red, sin
bajar nada. Pero un numeral solo no dice nada a un lector humano: "Capítulo
VIII" no es tan útil como "Capítulo VIII — Disposiciones transitorias". Ese
nombre sólo está en el TEXTO del articulado, que sólo trae el PDF de la Orden
del Día.

Este módulo NO agranda la cobertura de qué tramo pertenece a qué capítulo
—eso ya lo decide `extraer_titulo_capitulo` sobre el título del acta—. Sólo
busca, en el texto de cada PDF ya descargado, los encabezados de capítulo
("CAPÍTULO II — Declaración de emergencia pública...") y arma la tabla
numeral -> nombre para poder mostrarla junto al numeral que ya se tenía.

CONSUME
  Archivos_Borrar/od_pdf/od_descargas.csv (manifiesto de `ingesta_od.py`,
    columnas archivo/estado/proyecto_ids) + los PDF ahí listados.
PRODUCE (contrato nuevo)
  datos/expedientes/data/clean/capitulos_nombre.parquet
    archivo, proyecto_ids, capitulo_num, nombre_capitulo

Por qué no reusa `parser_od.texto_de_pdf` tal cual: esa función existe para
sacar FIRMANTES, que viven cerca del principio del PDF, y por eso corta en
cuanto encuentra el ancla dentro de las primeras `tope_paginas` (20 por
defecto) — para un articulado largo, los capítulos finales quedan afuera.
Acá hace falta el documento COMPLETO, así que se usa directo el mismo
"rescate" con pypdf que `parser_od.py` ya usa como fallback (medido: 2
segundos incluso en el PDF más pesado del corpus, 72 páginas/58 fuentes) —
mismo extractor, sin el corte anticipado que no aplica a este caso de uso.

    python datos/expedientes/src/capitulos_nombre.py
    python datos/expedientes/src/capitulos_nombre.py --limite 5   # prueba corta
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("expedientes.capitulos_nombre")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

OD_CACHE_DEFAULT = RAIZ / "Archivos_Borrar" / "od_pdf"
OUT_DEFAULT = RAIZ / "datos" / "expedientes" / "data" / "clean" / "capitulos_nombre.parquet"
TOPE_PAGINAS_DEFAULT = 150   # generoso: el rescate con pypdf es rápido (ver docstring)

# Encabezado de capítulo dentro del articulado. Dos formas reales, verificadas
# sobre Ley Bases (141-1.pdf): con guión largo en la misma línea, en Título
# Oración ("Capítulo II — Declaración de emergencia pública y bases...") y con
# el nombre en la línea siguiente, en MAYÚSCULA, sin separador explícito
# (forma común en textos legales: "CAPÍTULO I\nDISPOSICIONES GENERALES"). Se
# exige que el nombre no esté vacío y no pase de una línea: un capítulo real
# tiene un título corto, no un párrafo — así se evita matchear texto de cuerpo
# que mencione la palabra "capítulo" de pasada ("...conforme al capítulo II
# de esta ley..."). La palabra "Capítulo"/"CAPÍTULO" exige su C inicial en
# MAYÚSCULA (las dos formas reales la tienen así); una referencia de cuerpo
# ("el capítulo II") empieza en minúscula y por eso no matchea, sin necesidad
# de mirar el contexto alrededor.
_RE_CAPITULO_TEXTO = re.compile(
    r"C[Aa][Pp][IiÍí][Tt][Uu][Ll][Oo]\s+([IVXLCDM]+)\.?\s*[—\-:]?\s*\n?\s*([A-ZÁÉÍÓÚÑ][^\n]{2,110})",
)


def texto_completo_pdf(ruta: Path, tope_paginas: int = TOPE_PAGINAS_DEFAULT) -> str:
    """Todo el texto del PDF, sin el corte anticipado de `parser_od.texto_de_pdf`
    (ver docstring del módulo: ese corte es correcto para firmantes, no para
    capítulos que pueden estar al final del articulado)."""
    from pypdf import PdfReader
    paginas = PdfReader(str(ruta)).pages
    return "\n".join((p.extract_text() or "") for p in paginas[:tope_paginas])


# Medido sobre el corpus real de B2 (16-09): 10/322 candidatos (3,1%, en 5 de
# 163 ODs) eran falsos positivos de una forma concreta — un capítulo SIN
# nombre propio ("CAPÍTULO V" y a la línea siguiente arranca derecho el
# articulado, sin título), donde el regex agarraba el texto del primer
# artículo como si fuera el nombre ("ARTÍCULO 91.- Las disposiciones..."). Un
# capítulo real puede no tener nombre (es válido, no es un error de parseo);
# lo que no es válido es INVENTARLE uno con el texto del artículo que sigue.
_RE_ES_ARTICULO = re.compile(r"^ART[IÍ]CULO\b|^ART\.?\s*\d", re.I)
# Mismo problema, otra forma: el encabezado/pie de página se repite en cada
# hoja del PDF ("CÁMARA DE DIPUTADOS DE LA NACIÓN O.D. Nº 7") y a veces cae
# justo después de un "CAPÍTULO N" que sí era real pero sin nombre — el
# regex principal lo agarra como si fuera el título. Detectado sobre el
# corpus real de B2 (HCDN272347, capítulos II y III).
_RE_ES_ENCABEZADO_PAGINA = re.compile(r"C[ÁA]MARA\s+DE\s+(DIPUTADOS|SENADORES)|O\.?\s*D\.?\s*N", re.I)


def extraer_capitulos(texto: str) -> list[dict]:
    """[{capitulo_num, nombre_capitulo}, ...] — un capítulo puede repetirse si
    el PDF lo menciona dos veces (encabezado real + índice/sumario); se
    deduplica por numeral, quedándose con el nombre más largo (más informativo,
    normalmente el del encabezado real y no una referencia de pasada). Un
    capítulo sin nombre propio (el "nombre" capturado es en realidad el
    arranque del articulado, ver `_RE_ES_ARTICULO`) se descarta: mejor
    ausente que con un nombre inventado."""
    candidatos: dict[str, str] = {}
    for m in _RE_CAPITULO_TEXTO.finditer(texto):
        num = m.group(1).upper()
        nombre = " ".join(m.group(2).split()).strip(" .-—:")
        if not nombre or _RE_ES_ARTICULO.match(nombre) or _RE_ES_ENCABEZADO_PAGINA.search(nombre):
            continue
        if num not in candidatos or len(nombre) > len(candidatos[num]):
            candidatos[num] = nombre
    return [{"capitulo_num": n, "nombre_capitulo": t} for n, t in sorted(candidatos.items())]


def correr(od_cache: Path = OD_CACHE_DEFAULT, out: Path = OUT_DEFAULT,
           limite: int | None = None) -> pd.DataFrame:
    manifiesto = od_cache / "od_descargas.csv"
    if not manifiesto.exists():
        raise FileNotFoundError(
            f"no está {manifiesto} — corré primero ingesta_od.py (ver --solo-proyectos "
            "para bajar sólo un subconjunto)")
    man = pd.read_csv(manifiesto, dtype=str)
    man = man[man["estado"].isin(["ok", "cache"])]
    if limite:
        man = man.head(limite)

    filas: list[dict] = []
    sin_capitulos = []
    for i, fila in enumerate(man.itertuples(index=False), start=1):
        ruta = od_cache / fila.archivo
        if not ruta.exists():
            logger.warning("manifiesto dice %s pero el archivo no está en disco", fila.archivo)
            continue
        try:
            texto = texto_completo_pdf(ruta)
        except Exception as exc:  # noqa: BLE001 - un PDF roto no puede tumbar la corrida
            logger.warning("no pude leer %s: %s: %s", fila.archivo, type(exc).__name__, exc)
            continue
        capitulos = extraer_capitulos(texto)
        if not capitulos:
            sin_capitulos.append(fila.archivo)
            continue
        for c in capitulos:
            filas.append({"archivo": fila.archivo, "proyecto_ids": fila.proyecto_ids, **c})
        if i % 25 == 0 or i == len(man):
            logger.info("%d/%d PDF leídos, %d capítulos con nombre encontrados hasta ahora",
                        i, len(man), len(filas))

    df = pd.DataFrame(filas, columns=["archivo", "proyecto_ids", "capitulo_num", "nombre_capitulo"])
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    logger.info("RESULTADO: %d Órdenes del Día leídas, %d SIN un capítulo reconocible, "
                "%d filas (capítulo con nombre) -> %s",
                len(man), len(sin_capitulos), len(df), out)
    if sin_capitulos:
        logger.info("sin capítulos reconocibles (puede ser una ley de un solo bloque, sin "
                    "títulos/capítulos formales — no necesariamente un error de parseo): %s",
                    ", ".join(sin_capitulos[:10]) + (" ..." if len(sin_capitulos) > 10 else ""))
    return df


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--od-cache", default=str(OD_CACHE_DEFAULT))
    ap.add_argument("--salida", default=str(OUT_DEFAULT))
    ap.add_argument("--limite", type=int, default=None, help="procesar sólo las primeras N ODs")
    args = ap.parse_args(argv)
    correr(Path(args.od_cache), Path(args.salida), args.limite)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
