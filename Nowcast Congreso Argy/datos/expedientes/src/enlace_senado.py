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
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip().upper()
    if not s or s in {"NAN", "NONE", "-"}:
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


def prefijo(clave: Optional[str]) -> Optional[str]:
    """Letra del denominador ya normalizado ('0038-CD-2022' -> 'CD')."""
    if not clave:
        return None
    partes = clave.split("-")
    return partes[1] if len(partes) == 3 else None


def _leer(path: Path, que: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"falta {que}: {path}\n"
            "  ¿corriste la ingesta del módulo correspondiente? "
            "(datos/canonica/src/run_pipeline.py · datos/expedientes/src/ingesta_ckan.py)"
        )
    return pd.read_parquet(path)


def construir_enlace(
    actas: pd.DataFrame, expedientes: pd.DataFrame
) -> pd.DataFrame:
    """Une cada acta con su proyecto de HCDN. Una fila por acta con expediente."""
    faltan = {"acta_id", "camara", "expediente"} - set(actas.columns)
    if faltan:
        raise ValueError(f"actas_canonico sin columnas esperadas: {sorted(faltan)}")

    a = actas.loc[actas["expediente"].notna(), :].copy()
    a["clave"] = a["expediente"].map(normalizar_expediente)
    a["prefijo"] = a["clave"].map(prefijo)

    sin_parsear = int(a["clave"].isna().sum())
    if sin_parsear:
        logger.warning(
            "%d actas con expediente que no se pudo normalizar (quedan sin enlace)",
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
        if not clave:
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
    else:
        # `.apply` sobre un DataFrame vacío no devuelve las columnas expandidas.
        # Sin este caso el módulo rompe cuando la canónica todavía no tiene
        # actas con expediente, que es exactamente el estado inicial.
        a["proyecto_id"] = pd.Series(dtype="object")
        a["metodo"] = pd.Series(dtype="object")
    a["es_cruce"] = a["prefijo"].isin(PREFIJOS_CRUCE)

    cols = ["acta_id", "camara", "expediente", "clave", "prefijo",
            "proyecto_id", "metodo", "es_cruce"]
    extra = [c for c in ("fecha", "resultado", "tipo_mayoria") if c in a.columns]
    return a[cols + extra].reset_index(drop=True)


def construir_cadena(enlace: pd.DataFrame, expedientes: pd.DataFrame) -> pd.DataFrame:
    """Un proyecto por fila, con su votación en cada cámara. `n_camaras`==2 es
    la cadena completa observada: el insumo de P(revisora | aprobó origen)."""
    e = enlace.dropna(subset=["proyecto_id"]).copy()
    if "fecha" not in e.columns:
        e["fecha"] = pd.NaT
    if "resultado" not in e.columns:
        e["resultado"] = None

    partes = []
    for cam, sufijo in (("diputados", "dip"), ("senado", "sen")):
        sub = e[e["camara"].astype(str).str.lower() == cam]
        # Si un proyecto se votó varias veces en la misma cámara nos quedamos
        # con la ÚLTIMA: es la que define el desenlace en esa cámara.
        sub = sub.sort_values("fecha").groupby("proyecto_id").last()
        partes.append(
            sub[["acta_id", "fecha", "resultado"]].rename(
                columns={
                    "acta_id": f"acta_{sufijo}",
                    "fecha": f"fecha_{sufijo}",
                    "resultado": f"resultado_{sufijo}",
                }
            )
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

    enlace = construir_enlace(actas, expedientes)
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
