# -*- coding: utf-8 -*-
"""PRUEBA 2 de `coordinacion/PROMPT-DECIDIR-CAPITULOS.md` — ¿se puede
reconstruir el resultado real por capítulo cruzando el número de artículo
que declara el acta de votación contra el rango de artículos de cada
capítulo en el PDF de la Orden del Día? (ADR-0029 la dejó como camino
abierto y nadie la exploró.)

QUÉ MIDE
--------
1. Cuántas actas de votación en particular declaran un número de artículo
   parseable en su propio título (`votacion_por_articulo.parquet::titulo`) —
   `extraer_titulo_capitulo` sólo saca título/capítulo, NUNCA el número de
   artículo: hay que parsearlo acá.
2. Si el PDF de la Orden del Día permite mapear CAPÍTULO -> RANGO DE
   ARTÍCULOS: el primer artículo que sigue a cada encabezado "CAPÍTULO X"
   en el texto (antes del próximo encabezado) es el artículo con el que
   arranca ese capítulo -- se probó a mano sobre Ley Bases y funciona
   (Capítulo III -> Art. 9, IV -> Art. 14, V -> Art. 20, VI -> Art. 22:
   secuencia creciente y consistente). Usa el caché local de PDFs
   (`Archivos_Borrar/od_pdf/`), gratis.
3. Cruza (1) contra (2): para cada tramo con artículo parseable, busca en
   qué capítulo cae ese número -- eso da RESULTADO REAL POR CAPÍTULO sin
   depender de que el acta declare el capítulo explícitamente (el techo que
   encontró `validar_piloto_capitulos.py`: sólo 1 proyecto de 160 lo
   declaraba).

CERO GASTO DE API. NO TOCA EL MOTOR: sólo lee, parsea y cruza.

    python evaluacion/baseline/src/prueba2_reconstruccion_por_rango.py
"""
from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger("prueba2_reconstruccion_por_rango")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "datos" / "expedientes" / "src"))
from capitulos_nombre import (texto_completo_pdf, _RE_CAPITULO_TEXTO,  # noqa: E402
                              _RE_TITULO_TEXTO, OD_CACHE_DEFAULT)

_RE_ART_NUM = re.compile(r"ART[IÍ]?CULOS?\.?\s*(\d+)", re.IGNORECASE)
_RE_AL = re.compile(r"\bAL\s+(\d+)", re.IGNORECASE)
_RE_ART_INICIO_LINEA = re.compile(r"(?:^|\n)\s*Art[IÍ]?\.?\s*(\d+)", re.IGNORECASE)


def articulo_de_titulo_acta(titulo: str) -> tuple[int | None, int | None]:
    """(articulo_desde, articulo_hasta) declarado en el TÍTULO DEL ACTA (no
    el PDF). Un solo número -> (n, n); con "AL m" -> (n, m); nada -> (None,None)."""
    if not isinstance(titulo, str):
        return None, None
    m = _RE_ART_NUM.search(titulo)
    if not m:
        return None, None
    desde = int(m.group(1))
    m2 = _RE_AL.search(titulo[m.end():m.end() + 60])
    hasta = int(m2.group(1)) if m2 else desde
    return desde, hasta


def rangos_de_capitulos_pdf(archivo: str) -> list[dict]:
    """Para un PDF de la Orden del Día ya en caché: [{titulo_num,
    capitulo_num, nombre, articulo_inicio}, ...], en el ORDEN en que
    aparecen los capítulos en el texto -- el artículo con el que arranca
    cada uno es el primer 'Art. N' que sigue a su encabezado (antes del
    próximo encabezado de capítulo o título). El RANGO de cada capítulo es
    [su articulo_inicio, el articulo_inicio del SIGUIENTE encabezado - 1]."""
    ruta = OD_CACHE_DEFAULT / archivo
    if not ruta.exists():
        return []
    try:
        texto = texto_completo_pdf(ruta)
    except (OSError, ValueError) as e:
        logger.warning("no pude leer %s: %s", archivo, e)
        return []

    marcas = [(m.start(), "titulo", m.group(1).upper(), None) for m in _RE_TITULO_TEXTO.finditer(texto)]
    marcas += [(m.start(), "capitulo", m.group(1).upper(), m.group(2)) for m in _RE_CAPITULO_TEXTO.finditer(texto)]
    marcas.sort(key=lambda t: t[0])

    filas = []
    titulo_actual = None
    for i, (pos, tipo, num, nombre) in enumerate(marcas):
        if tipo == "titulo":
            titulo_actual = num
            continue
        fin_bloque = marcas[i + 1][0] if i + 1 < len(marcas) else len(texto)
        bloque = texto[pos:fin_bloque]
        m_art = _RE_ART_INICIO_LINEA.search(bloque)
        art_inicio = int(m_art.group(1)) if m_art else None
        filas.append({"titulo_num": titulo_actual, "capitulo_num": num,
                      "nombre": (nombre or "").strip()[:60], "articulo_inicio": art_inicio,
                      "_pos": pos})

    # rango = [articulo_inicio propio, articulo_inicio del PRÓXIMO capítulo - 1]
    filas_con_art = [f for f in filas if f["articulo_inicio"] is not None]
    filas_con_art.sort(key=lambda f: f["_pos"])
    for i, f in enumerate(filas_con_art):
        siguiente = filas_con_art[i + 1]["articulo_inicio"] if i + 1 < len(filas_con_art) else None
        f["articulo_fin"] = (siguiente - 1) if (siguiente and siguiente > f["articulo_inicio"]) else f["articulo_inicio"]
    return filas_con_art


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

    v = pd.read_parquet(REPO / "datos/expedientes/data/clean/votacion_por_articulo.parquet")
    p = v[v["es_particular"]].copy()
    p["art_desde"], p["art_hasta"] = zip(*p["titulo"].map(articulo_de_titulo_acta))
    con_articulo = p[p["art_desde"].notna()]
    logger.info("PASO 1 -- tramos es_particular con artículo parseable en el título del acta: "
               "%d/%d (%d proyectos distintos)", len(con_articulo), len(p),
               con_articulo["proyecto_id"].nunique())

    cn = pd.read_parquet(REPO / "datos/expedientes/data/clean/capitulos_nombre.parquet")
    proyectos_con_articulo = set(con_articulo["proyecto_id"].unique())
    # sólo vale la pena parsear el PDF de proyectos que YA tienen chance de cruzar
    cn_relevante = cn[cn["proyecto_ids"].map(
        lambda ids: bool(set(str(ids).split(";")) & proyectos_con_articulo))]
    archivos = sorted(cn_relevante["archivo"].unique())
    logger.info("PASO 2 -- PDFs a parsear (de proyectos con artículo en el acta): %d", len(archivos))

    rangos_por_archivo = {}
    for archivo in archivos:
        rangos_por_archivo[archivo] = rangos_de_capitulos_pdf(archivo)
    con_rango = sum(1 for r in rangos_por_archivo.values() if r)
    logger.info("PDFs con al menos un capítulo con artículo_inicio parseado: %d/%d",
               con_rango, len(archivos))

    # archivo -> proyecto_ids (para saber qué archivo(s) mirar por proyecto)
    archivo_a_proyectos = {a: set(str(cn_relevante[cn_relevante["archivo"] == a]["proyecto_ids"].iloc[0]).split(";"))
                           for a in archivos}

    filas_cruzadas = []
    for r in con_articulo.itertuples():
        pid = r.proyecto_id
        archivos_del_pid = [a for a, pids in archivo_a_proyectos.items() if pid in pids]
        encontrado = None
        for a in archivos_del_pid:
            for cap in rangos_por_archivo.get(a, []):
                lo, hi = cap["articulo_inicio"], cap["articulo_fin"]
                if lo is None:
                    continue
                if lo <= r.art_desde <= hi:
                    encontrado = {"proyecto_id": pid, "titulo_acta": r.titulo_num,
                                 "capitulo_acta": r.capitulo_num,
                                 "articulo_acta": r.art_desde,
                                 "titulo_pdf": cap["titulo_num"], "capitulo_pdf": cap["capitulo_num"],
                                 "nombre_pdf": cap["nombre"], "archivo": a,
                                 "resultado_clase": r.resultado_clase, "fecha": str(r.fecha)}
                    break
            if encontrado:
                break
        if encontrado:
            filas_cruzadas.append(encontrado)

    tabla = pd.DataFrame(filas_cruzadas)
    n_proyectos_con_resultado = tabla["proyecto_id"].nunique() if not tabla.empty else 0
    logger.info("PASO 3 -- tramos cruzados con éxito a un capítulo del PDF: %d/%d, "
               "en %d proyectos distintos", len(tabla), len(con_articulo), n_proyectos_con_resultado)

    if n_proyectos_con_resultado >= 5:
        veredicto = "PASA"
    elif n_proyectos_con_resultado >= 2:
        veredicto = "PARCIAL"
    else:
        veredicto = "FALLA"

    reporte = {
        "paso1_tramos_con_articulo_en_acta": int(len(con_articulo)),
        "paso1_tramos_es_particular_total": int(len(p)),
        "paso1_proyectos_con_articulo_en_acta": int(con_articulo["proyecto_id"].nunique()),
        "paso2_pdfs_evaluados": len(archivos),
        "paso2_pdfs_con_rango_parseado": con_rango,
        "paso3_tramos_cruzados_ok": int(len(tabla)),
        "paso3_proyectos_con_resultado_real_por_capitulo": int(n_proyectos_con_resultado),
        "proyectos_con_resultado": sorted(tabla["proyecto_id"].unique().tolist()) if not tabla.empty else [],
        "UMBRAL_pasa": 5, "UMBRAL_parcial_min": 2,
        "VEREDICTO": veredicto,
        "muestra_cruces": tabla.head(30).to_dict("records") if not tabla.empty else [],
    }

    print("\n" + json.dumps({k: v_ for k, v_ in reporte.items() if k != "muestra_cruces"},
                            indent=1, ensure_ascii=False))
    print(f"\n=== VEREDICTO PRUEBA 2: {veredicto} ===")

    out = REPO / "evaluacion/baseline/outputs/prueba2_reconstruccion_por_rango_2026-09-17.json"
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
