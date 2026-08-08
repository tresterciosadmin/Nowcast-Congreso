"""Enlace acta -> expediente para el SENADO (y la cadena entre cámaras).

PROBLEMA QUE RESUELVE
---------------------
Para modelar la cadena `cámara de origen -> cámara revisora` hace falta saber
QUÉ PROYECTO se votó en cada acta. En Diputados el acta ya trae el denominador
de HCDN (`1623-D-2018`). En el Senado el acta trae la numeración INTERNA del
Senado (`CD-38/22-PL`, `S-2234/22-PD`, `PE-184/21-AC`), que no es el mismo
identificador, y por eso el cruce directo daba ~0 coincidencias.

LA CLAVE (hallazgo 2026-08-08): el puente ya está en nuestros datos.
`expedientes.parquet` trae la columna `exp_senado` con EXACTAMENTE esa
numeración del Senado, ya normalizada al formato de HCDN:

    acta del Senado      'CD-38/22-PL'   --normalizar-->  '0038-CD-2022'
    expedientes.parquet   exp_senado  =  '0038-CD-2022'   --> proyecto_id

No hace falta scrapear senado.gob.ar para armar el crosswalk. La ficha del
Senado (`datos/seguimiento`) sigue siendo útil para los casos sueltos que no
matchean, pero no es el camino principal.

QUÉ SIGNIFICA CADA PREFIJO (numeración del Senado)
    CD-  el expediente ENTRÓ desde Diputados con media sanción -> es un cruce
    S-   proyecto con origen en el Senado
    PE-  mensaje del Poder Ejecutivo
    OV-  oficiales varios / particulares

CONTRATO DE SALIDA  (datos/expedientes/data/clean/)
    acta_expediente_senado.parquet
        acta_id       id canónico del acta
        camara        'senado' | 'diputados'
        expediente    lo que traía el acta, tal cual
        clave         denominador normalizado NNNN-XX-AAAA
        prefijo       CD | S | PE | OV | D | ...
        proyecto_id   id de HCDN, o nulo si no matcheó
        metodo        'exp_senado' | 'exp_diputados' | None
        es_cruce      True si el acta corresponde a un expediente que entró
                      desde la otra cámara (prefijo CD)

    cadena_camaras.parquet   (el que consume el modelo)
        proyecto_id, camara_origen, exp_diputados, exp_senado, titulo,
        acta_dip, fecha_dip, resultado_dip,
        acta_sen, fecha_sen, resultado_sen,
        n_camaras   (1 o 2)

LÍMITE CONOCIDO Y DÓNDE ESTÁ EL CUELLO DE BOTELLA
    Sólo 250 de las 3.078 actas del Senado traen expediente (8,1%). De esas
    matchea el 80%. O sea: el problema NO es el crosswalk (resuelto acá), es
    que la ingesta del Senado no guarda el expediente en el 92% de las actas.
    Eso se arregla en `datos/senado/src/scrape_votaciones.py` y en la ingesta
    de argentinadatos, no acá.

CÓMO CORRER
    python datos/expedientes/src/enlace_senado.py            # construye y reporta
    python datos/expedientes/src/enlace_senado.py --reporte  # sólo diagnóstico
    python datos/expedientes/tests/test_enlace_senado.py     # tests sin red

Módulo: datos/expedientes · creado 2026-08-08 (línea Revisión de Comisiones)
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s enlace_senado: %(message)s"
)
logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
CANONICA = RAIZ / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet"
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"

# Prefijos que en la numeración del Senado indican que el expediente ENTRÓ
# desde la otra cámara con media sanción.
PREFIJOS_CRUCE = {"CD"}

# 'CD-38/22-PL' · 'S-2234/22-PD' · 'PE-184/21-AC'  -> letra, número, año(2)
_RE_SENADO = re.compile(r"^\s*([A-Z]{1,4})\s*[-\.]\s*(\d{1,5})\s*/\s*(\d{2})\b")
# '1623-D-2018' y también '5094-D-18': la canónica mezcla año de 4 y de 2
# dígitos según la fuente. Exigir 4 dejaba 1.628 actas de Diputados sin
# enlazar (el 82%), que fue el primer resultado de la corrida del 08-08.
_RE_HCDN = re.compile(r"^\s*(\d{1,5})\s*-\s*([A-Z]{1,4})\s*-\s*(\d{4}|\d{2})\b")

# El expediente EMBEBIDO EN EL TÍTULO. Hallazgo del 08-08: la columna
# `expediente` de la canónica está vacía en el 92% de las actas del Senado, pero
# el título lo trae escrito adentro en 2.229 de ellas:
#   "...Reforma Laboral. PE-608/03. Votacion en general"
#   "Presupuesto General... Artículo 67. CD-30/25-PL"
# O sea que NO hace falta re-scrapear el Senado para recuperar la historia: el
# dato ya está en disco. Se busca en cualquier posición del título, no al
# principio, y por eso este patrón es aparte del de arriba.
_RE_EN_TITULO = re.compile(
    r"\b(CD|S|PE|OV|OVD|JGM)\s*[-\.\s]\s*(\d{1,5})\s*/\s*(\d{2})\b", re.I
)

# La ORDEN DEL DÍA en el título. Es el puente del lado de DIPUTADOS: desde 2020
# sus actas no traen expediente (0 de 369 entre 2024 y 2026) y el título tampoco
# lo nombra, pero sí trae la O.D.: "O. D. 759 - DNU 179/2025, QUE APRUEBA...".
# `expedientes_resultados.parquet` tiene `od_numero` + `od_publicacion`, así que
# el par (año, O.D.) lleva al proyecto.
_RE_OD = re.compile(r"\bO\.?\s*D\.?\s*N?[ºo°]?\s*(\d{1,4})\b", re.I)


def _vacio(valor: object) -> bool:
    """¿Es un faltante, en cualquiera de sus disfraces?

    ⚠️ NO alcanza con `if not valor`. Según la versión de pandas y el backend de
    la columna (object vs. Arrow), un faltante llega como `None`, como
    `float('nan')` o como `pd.NA` — y **`not float('nan')` es False**, así que
    un `if not valor` deja pasar el NaN y explota más abajo. Pasó de verdad el
    2026-08-08: los tests daban 83/83 en el sandbox (columnas object) y
    reventaban en la PC de Valle (pandas más nuevo, columnas Arrow) con
    `'float' object has no attribute 'split'`.
    """
    if valor is None:
        return True
    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        pass
    return str(valor).strip() == ""


def normalizar_expediente(valor: object) -> Optional[str]:
    """Lleva cualquiera de los dos formatos al denominador canónico NNNN-XX-AAAA.

    Devuelve None ante cualquier cosa que no encaje: parsing defensivo, no
    adivinamos. Un None acá es "no sé", nunca un match dudoso.

    >>> normalizar_expediente('CD-38/22-PL')
    '0038-CD-2022'
    >>> normalizar_expediente('1623-D-2018')
    '1623-D-2018'
    >>> normalizar_expediente('sin datos') is None
    True
    """
    if _vacio(valor):
        return None
    s = str(valor).strip().upper()
    if not s or s in {"NAN", "NONE", "-", "<NA>"}:
        return None

    m = _RE_HCDN.match(s)
    if m:
        nro, letra, anio = m.groups()
        if len(anio) == 2:
            # La ventana del proyecto es 2001-2026: dos dígitos nunca son 19xx.
            anio = f"20{anio}"
        return f"{int(nro):04d}-{letra}-{anio}"

    m = _RE_SENADO.match(s)
    if m:
        letra, nro, aa = m.groups()
        anio = int(aa)
        # Ventana del proyecto: 2001-2026. Dos dígitos nunca son 19xx acá.
        siglo = 2000 + anio
        return f"{int(nro):04d}-{letra}-{siglo}"

    return None


def expediente_en_titulo(titulo: object) -> Optional[str]:
    """Rescata el expediente escrito dentro del título del acta.

    Se usa SÓLO como respaldo cuando la columna `expediente` viene vacía. El
    campo propio siempre manda: donde existen los dos coinciden en el **98,8%**
    (246 de 249), y las discrepancias son casos en que el título nombra un
    expediente REFERENCIADO —un proyecto que se reproduce, o el proyecto de
    fondo de un dictamen de comisión bicameral— y no el que se está votando.

    >>> expediente_en_titulo('Reforma Laboral. PE-608/03. Votacion en general')
    '0608-PE-2003'
    >>> expediente_en_titulo('Presupuesto 2026') is None
    True
    """
    if _vacio(titulo):
        return None
    m = _RE_EN_TITULO.search(str(titulo))
    if not m:
        return None
    letra, nro, aa = m.groups()
    return f"{int(nro):04d}-{letra.upper()}-20{aa}"


def od_en_titulo(titulo: object) -> Optional[str]:
    """Número de Orden del Día escrito en el título, sin ceros a la izquierda.

    >>> od_en_titulo('O. D. 759 - DNU 179/2025, QUE APRUEBA...')
    '759'
    >>> od_en_titulo('PLAN DE LABOR') is None
    True
    """
    if _vacio(titulo):
        return None
    m = _RE_OD.search(str(titulo))
    return m.group(1).lstrip("0") or None if m else None


def mapa_od(resultados: pd.DataFrame) -> dict[tuple[int, str], str]:
    """(año de publicación, nº de O.D.) -> proyecto_id, **sólo claves unívocas**.

    Las O.D. se renumeran cada año, así que la clave tiene que llevar el año. Y
    hay 292 pares que apuntan a más de un proyecto (una O.D. puede contener
    varios dictámenes): esas se descartan. Preferimos no enlazar antes que
    adjudicarle a una votación el proyecto equivocado.
    """
    faltan = {"od_numero", "od_publicacion", "proyecto_id"} - set(resultados.columns)
    if faltan:
        logger.warning("expedientes_resultados sin columnas %s: sin puente por O.D.",
                       sorted(faltan))
        return {}
    r = resultados.dropna(subset=["od_numero", "od_publicacion"]).copy()
    r["anio_od"] = pd.to_datetime(r["od_publicacion"], errors="coerce").dt.year
    r["od"] = r["od_numero"].astype(str).str.strip().str.lstrip("0")
    r = r.dropna(subset=["anio_od"])
    r = r[r["od"] != ""]

    conteo = r.groupby(["anio_od", "od"])["proyecto_id"].nunique()
    ambiguas = set(conteo[conteo > 1].index)
    if ambiguas:
        logger.info("O.D.: %d claves (año, nº) ambiguas descartadas", len(ambiguas))
    r = r[~r.set_index(["anio_od", "od"]).index.isin(ambiguas)]
    r = r.drop_duplicates(["anio_od", "od"])
    return {(int(a), o): p for a, o, p in zip(r["anio_od"], r["od"], r["proyecto_id"])}


def prefijo(clave: Optional[str]) -> Optional[str]:
    """Letra del denominador ya normalizado ('0038-CD-2022' -> 'CD').

    Tolera faltantes de cualquier backend: ver `_vacio`. Esta función es la que
    reventó en la PC de Valle el 08-08 con `'float' object has no attribute
    'split'` mientras el sandbox daba 83/83.
    """
    if _vacio(clave):
        return None
    partes = str(clave).split("-")
    return partes[1] if len(partes) == 3 else None


def _leer(path: Path, que: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"falta {que}: {path}\n"
            "  ¿corriste la ingesta del módulo correspondiente? "
            "(datos/canonica/src/run_pipeline.py · datos/expedientes/src/ingesta_ckan.py)"
        )
    return pd.read_parquet(path)


def _puente_od(a: pd.DataFrame, resultados: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Tercer nivel de respaldo: la O.D. del título, **sólo para DIPUTADOS**.

    ⛔ NO se aplica al Senado a propósito. El Senado numera sus propias Órdenes
    del Día, así que buscar "O.D. 206/2023" de un acta del Senado en la tabla de
    HCDN devolvería un proyecto ajeno con toda naturalidad. Un falso positivo
    acá mete la votación equivocada en la cadena entre cámaras, que es
    exactamente lo que el módulo existe para medir bien.
    """
    if resultados is None or "titulo" not in a.columns or "fecha" not in a.columns:
        return a
    mapa = mapa_od(resultados)
    if not mapa:
        return a

    es_dip = a["camara"].astype(str).str.lower() == "diputados"
    od = a["titulo"].map(od_en_titulo)
    anio = pd.to_datetime(a["fecha"], errors="coerce").dt.year

    def buscar(y, o):
        if pd.isna(y) or not o:
            return None
        # Una O.D. publicada a fin de año se vota al año siguiente.
        for cand in (int(y), int(y) - 1):
            pid = mapa.get((cand, o))
            if pid:
                return pid
        return None

    pid_od = pd.Series([buscar(y, o) for y, o in zip(anio, od)], index=a.index)

    # Control de salud contra lo ya resuelto por expediente.
    ya = a["proyecto_id"].notna() & pid_od.notna() & es_dip
    if int(ya.sum()):
        iguales = int((a.loc[ya, "proyecto_id"] == pid_od[ya]).sum())
        logger.info("O.D. vs expediente: coinciden %d/%d (%.1f%%) — manda el expediente",
                    iguales, int(ya.sum()), 100 * iguales / int(ya.sum()))

    falta = es_dip & a["proyecto_id"].isna() & pid_od.notna()
    if int(falta.sum()):
        a.loc[falta, "proyecto_id"] = pid_od[falta]
        a.loc[falta, "metodo"] = "od_titulo"
        a.loc[falta, "origen_clave"] = a.loc[falta, "origen_clave"].fillna("od")
        logger.info("enlazadas por O.D. del título (Diputados): %d actas", int(falta.sum()))
    return a


def construir_enlace(
    actas: pd.DataFrame,
    expedientes: pd.DataFrame,
    resultados: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Une cada acta con su proyecto de HCDN. Una fila por acta con expediente."""
    faltan = {"acta_id", "camara", "expediente"} - set(actas.columns)
    if faltan:
        raise ValueError(f"actas_canonico sin columnas esperadas: {sorted(faltan)}")

    # Se parte de TODAS las actas, no sólo de las que traen la columna
    # `expediente`: el rescate desde el título recupera 2.229 actas del Senado
    # que la traían vacía (el 92% de esa cámara).
    a = actas.copy()
    a["clave"] = a["expediente"].map(normalizar_expediente)
    a["origen_clave"] = a["clave"].notna().map({True: "campo", False: None})

    if "titulo" in a.columns:
        rescate = a["titulo"].map(expediente_en_titulo)
        # Control de salud: dónde hay las dos, ¿coinciden? Si esta tasa se cae,
        # el formato del título cambió y el respaldo dejó de ser confiable.
        ambos = a["clave"].notna() & rescate.notna()
        if int(ambos.sum()):
            iguales = int((a.loc[ambos, "clave"] == rescate[ambos]).sum())
            logger.info(
                "campo vs título: coinciden %d/%d (%.1f%%) — manda el campo",
                iguales, int(ambos.sum()), 100 * iguales / int(ambos.sum()),
            )
        falta = a["clave"].isna() & rescate.notna()
        a.loc[falta, "clave"] = rescate[falta]
        a.loc[falta, "origen_clave"] = "titulo"
        if int(falta.sum()):
            logger.info("rescatadas del título: %d actas", int(falta.sum()))

    # Se conservan también las actas que sólo traen una O.D. en el título: son
    # las de Diputados desde 2020, que no tienen expediente por ningún lado.
    tiene_od = (a["titulo"].map(od_en_titulo).notna()
                if "titulo" in a.columns else pd.Series(False, index=a.index))
    a = a.loc[a["clave"].notna() | a["expediente"].notna() | tiene_od, :].copy()
    a["prefijo"] = a["clave"].map(prefijo)

    sin_parsear = int(a["clave"].isna().sum())
    if sin_parsear:
        logger.warning(
            "%d actas con expediente que no se pudo normalizar ni rescatar",
            sin_parsear,
        )

    # Dos diccionarios de búsqueda: la numeración del Senado y la de HCDN.
    # Se descartan las claves ambiguas (una misma numeración apuntando a dos
    # proyectos): preferimos no enlazar antes que enlazar mal.
    mapas = {}
    for metodo, col in (("exp_senado", "exp_senado"), ("exp_diputados", "exp_diputados")):
        if col not in expedientes.columns:
            logger.warning("expedientes.parquet sin columna %s", col)
            mapas[metodo] = {}
            continue
        sub = expedientes.loc[expedientes[col].notna(), [col, "proyecto_id"]].copy()
        sub["clave"] = sub[col].map(normalizar_expediente)
        sub = sub.dropna(subset=["clave"])
        conteo = sub.groupby("clave")["proyecto_id"].nunique()
        ambiguas = set(conteo[conteo > 1].index)
        if ambiguas:
            logger.warning(
                "%s: %d claves ambiguas descartadas (apuntan a >1 proyecto)",
                metodo, len(ambiguas),
            )
        sub = sub[~sub["clave"].isin(ambiguas)]
        mapas[metodo] = dict(zip(sub["clave"], sub["proyecto_id"]))

    def resolver(fila) -> tuple[Optional[str], Optional[str]]:
        clave = fila["clave"]
        if _vacio(clave):
            return None, None
        # El acta del Senado se resuelve por la numeración del Senado; la de
        # Diputados por la de HCDN. Se prueba primero la de su propia cámara.
        orden = (
            ("exp_senado", "exp_diputados")
            if str(fila["camara"]).lower() == "senado"
            else ("exp_diputados", "exp_senado")
        )
        for metodo in orden:
            pid = mapas[metodo].get(clave)
            if pid is not None:
                return pid, metodo
        return None, None

    if len(a):
        resuelto = a.apply(resolver, axis=1, result_type="expand")
        a["proyecto_id"] = resuelto[0]
        a["metodo"] = resuelto[1]
        a = _puente_od(a, resultados)
    else:
        # `.apply` sobre un DataFrame vacío no devuelve las columnas expandidas.
        # Sin este caso el módulo rompe cuando la canónica todavía no tiene
        # actas con expediente, que es exactamente el estado inicial.
        a["proyecto_id"] = pd.Series(dtype="object")
        a["metodo"] = pd.Series(dtype="object")
    a["es_cruce"] = a["prefijo"].isin(PREFIJOS_CRUCE)

    cols = ["acta_id", "camara", "expediente", "clave", "origen_clave", "prefijo",
            "proyecto_id", "metodo", "es_cruce"]
    extra = [c for c in ("fecha", "resultado", "tipo_mayoria", "titulo") if c in a.columns]
    return a[cols + extra].reset_index(drop=True)


# Una ley se vota EN GENERAL (¿se aprueba?) y después EN PARTICULAR, artículo
# por artículo. La decisiva es la general: un artículo puede caerse y la ley
# sancionarse igual.
_RE_GENERAL = re.compile(r"EN GENERAL", re.I)
_RE_PARTICULAR = re.compile(
    r"EN PARTICULAR|ART[IÍ]CULOS?\b|ARTS?\.|CAP[IÍ]TULO\s+[IVXLC0-9]|T[IÍ]TULO\s+[IVXLC]+\b",
    re.I,
)


def elegir_votacion(sub: pd.DataFrame) -> pd.Series:
    """De todas las votaciones de un proyecto en una cámara, la DECISIVA.

    POR QUÉ EXISTE: la primera versión se quedaba con la última votación, y para
    la Ley Bases —**50 votaciones** del mismo proyecto en Diputados— eso devolvía
    el último artículo en vez de la votación en general. El 15,2% de los pares
    (proyecto, cámara) tiene más de una votación, así que no es un caso raro.

    Orden de preferencia:
      1. la que dice EN GENERAL en el título;
      2. si ninguna lo dice, la PRIMERA en el tiempo — la general va antes que
         el articulado;
      3. entre las que empatan, la que NO parezca "en particular".
    """
    if len(sub) == 1:
        f = sub.iloc[0].copy()
        f["tipo_votacion"] = "unica"
        return f

    tit = sub["titulo"].astype(str) if "titulo" in sub.columns else pd.Series("", index=sub.index)
    general = sub[tit.str.contains(_RE_GENERAL, na=False)]
    if len(general):
        f = general.sort_values("fecha").iloc[0].copy()
        f["tipo_votacion"] = "general"
        return f

    no_part = sub[~tit.str.contains(_RE_PARTICULAR, na=False)]
    candidatas = no_part if len(no_part) else sub
    f = candidatas.sort_values("fecha").iloc[0].copy()
    f["tipo_votacion"] = "primera" if len(no_part) else "primera_particular"
    return f


def construir_cadena(enlace: pd.DataFrame, expedientes: pd.DataFrame) -> pd.DataFrame:
    """Un proyecto por fila, con su votación DECISIVA en cada cámara.

    `n_camaras`==2 es la cadena completa observada: el insumo de
    P(revisora | aprobó origen)."""
    e = enlace.dropna(subset=["proyecto_id"]).copy()
    if "fecha" not in e.columns:
        e["fecha"] = pd.NaT
    if "resultado" not in e.columns:
        e["resultado"] = None

    partes = []
    for cam, sufijo in (("diputados", "dip"), ("senado", "sen")):
        sub = e[e["camara"].astype(str).str.lower() == cam]
        if sub.empty:
            partes.append(pd.DataFrame(
                columns=[f"acta_{sufijo}", f"fecha_{sufijo}", f"resultado_{sufijo}",
                         f"tipo_votacion_{sufijo}", f"n_actas_{sufijo}"]
            ).rename_axis("proyecto_id"))
            continue
        n = sub.groupby("proyecto_id").size().rename(f"n_actas_{sufijo}")
        elegidas = (sub.groupby("proyecto_id", group_keys=True)
                       .apply(elegir_votacion, include_groups=False))
        partes.append(
            elegidas[["acta_id", "fecha", "resultado", "tipo_votacion"]].rename(
                columns={
                    "acta_id": f"acta_{sufijo}",
                    "fecha": f"fecha_{sufijo}",
                    "resultado": f"resultado_{sufijo}",
                    "tipo_votacion": f"tipo_votacion_{sufijo}",
                }
            ).join(n)
        )

    cadena = partes[0].join(partes[1], how="outer")
    cadena["n_camaras"] = (
        cadena["acta_dip"].notna().astype(int) + cadena["acta_sen"].notna().astype(int)
    )

    cols_exp = [c for c in ("proyecto_id", "camara_origen", "exp_diputados",
                            "exp_senado", "tipo", "titulo")
                if c in expedientes.columns]
    return (
        expedientes[cols_exp]
        .merge(cadena.reset_index(), on="proyecto_id", how="right")
        .sort_values(["n_camaras", "fecha_dip"], ascending=[False, True])
        .reset_index(drop=True)
    )


def reportar(enlace: pd.DataFrame, cadena: pd.DataFrame) -> None:
    tot = len(enlace)
    ok = int(enlace["proyecto_id"].notna().sum())
    logger.info("actas con expediente: %d | enlazadas: %d (%.1f%%)",
                tot, ok, 100 * ok / tot if tot else 0)

    for cam, sub in enlace.groupby("camara"):
        n, m = len(sub), int(sub["proyecto_id"].notna().sum())
        logger.info("  %-10s %5d actas -> %4d enlazadas (%.1f%%)",
                    cam, n, m, 100 * m / n if n else 0)

    if "origen_clave" in enlace.columns:
        t = enlace.groupby("origen_clave")["proyecto_id"].agg(actas="size", enlazadas="count")
        t["pct"] = (100 * t["enlazadas"] / t["actas"]).round(1)
        logger.info("  según de dónde salió el expediente:\n%s", t.to_string())

    sen = enlace[enlace["camara"].astype(str).str.lower() == "senado"]
    if len(sen):
        t = sen.groupby("prefijo")["proyecto_id"].agg(actas="size", enlazadas="count")
        t["pct"] = (100 * t["enlazadas"] / t["actas"]).round(1)
        logger.info("  por prefijo del Senado:\n%s", t.to_string())

    dos = int((cadena["n_camaras"] == 2).sum())
    logger.info("proyectos con votación en LAS DOS cámaras: %d (de %d con alguna)",
                dos, len(cadena))
    if dos:
        cruces = cadena[cadena["n_camaras"] == 2]
        logger.info("  por cámara de origen:\n%s",
                    cruces["camara_origen"].value_counts().to_string())


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reporte", action="store_true",
                    help="sólo diagnostica, no escribe los parquet")
    ap.add_argument("--out", type=Path, default=CLEAN,
                    help="directorio de salida (default: data/clean del módulo)")
    args = ap.parse_args(argv)

    try:
        actas = _leer(CANONICA, "la canónica de actas")
        expedientes = _leer(CLEAN / "expedientes.parquet", "el maestro de expedientes")
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 2

    try:
        resultados = _leer(CLEAN / "expedientes_resultados.parquet", "los resultados")
    except FileNotFoundError:
        logger.warning("sin expedientes_resultados.parquet: se corre sin el puente por O.D.")
        resultados = None

    enlace = construir_enlace(actas, expedientes, resultados)
    cadena = construir_cadena(enlace, expedientes)
    reportar(enlace, cadena)

    if args.reporte:
        logger.info("--reporte: no se escribió nada")
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    p1 = args.out / "acta_expediente_senado.parquet"
    p2 = args.out / "cadena_camaras.parquet"
    enlace.to_parquet(p1, index=False)
    cadena.to_parquet(p2, index=False)
    logger.info("escrito: %s (%d filas)", p1.name, len(enlace))
    logger.info("escrito: %s (%d filas)", p2.name, len(cadena))
    return 0


if __name__ == "__main__":
    sys.exit(main())
