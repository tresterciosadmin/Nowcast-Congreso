# -*- coding: utf-8 -*-
"""De una Orden del Día a la URL de su PDF en el sitio de HCDN.

## Por qué existe

Los firmantes del dictamen no están en el CKAN de Diputados: sólo están en el
PDF de la Orden del Día. Nuestro `expedientes_resultados.parquet` trae el número
de OD y su fecha de publicación, así que lo único que falta para llegar al PDF
es armar la URL. Toda la ingesta cuelga de esta regla, y es lo único del módulo
que se puede probar sin red — por eso vive en su propio archivo con su test.

## La regla (verificada el 21-08-2026 contra 7 PDF reales, 2008 a 2026)

    periodo = anio_parlamentario - 1882
    anio_parlamentario = anio(fecha) - (1 si el mes es enero o febrero)
    URL = https://www3.hcdn.gob.ar/dependencias/dcomisiones/periodo-<P>/<P>-<N>.pdf

El **período parlamentario va del 1 de marzo al 28/29 de febrero** — lo dice el
selector oficial del buscador de HCDN: *"Período 142 (01/03/2024 - 28/02/2025)"*.
Por eso una OD impresa en enero o febrero cae en el período del año ANTERIOR, y
viene rotulada "Sesiones Extraordinarias <año-1>".

Comprobaciones exactas (número + fecha impresa en el PDF contra nuestro parquet):

    141-1     26-ene-2024 (Extraordinarias 2023)    144-7      7-abr-2026
    142-362   29-ago-2024                           126-886   19-sep-2008
    143-4     11-feb-2026 (Extraordinarias 2025)    133-2360   7-sep-2015
                                                    137-1491  19-nov-2019

## Las tres trampas

1. **El número de OD NO reinicia con el período.** Reinicia con la renovación de
   la Cámara (10-dic de años impares) y sigue corriendo a través de DOS períodos:
   la serie va 1 (ene-2024) → 1264 (nov-2025) y recién ahí vuelve a 1. Si el
   período se dedujera del número, dos años enteros de OD irían a la carpeta
   equivocada. **Se deduce de la FECHA, siempre.**
2. **Los ceros a la izquierda se sacan.** `od_numero` viene del parquet como
   `"0356"`; la URL es `.../126-356.pdf`. Probado con 1, 7, 886, 1491 y 2360.
3. **`www3` y `www4` son espejos del mismo archivo**, no períodos distintos.
   No hay que elegir host por período: se usa uno y se cae al otro ante error.

## Uso

    from od_url import periodo_de, url_od, urls_od
    url_od("0886", "2008-09-19")
    # 'https://www3.hcdn.gob.ar/dependencias/dcomisiones/periodo-126/126-886.pdf'

Un faltante (None, NaN, NaT, pd.NA, cadena vacía) levanta `ValueError` con el
valor adentro del mensaje. Este módulo **falla ruidoso a propósito**: una fecha
vacía que se cuela devolvería una URL plausible pero falsa, y eso se descubriría
recién al mirar el contenido de 2.500 PDF.
"""
from __future__ import annotations

import datetime as _dt
import re

# El período 1 arranca en 1883, así que el año parlamentario N+1882 es el período N.
PERIODO_BASE = 1882

# El buscador oficial de HCDN ofrece desde el período 121 (01/03/2003 - 28/02/2004).
# Más atrás no está publicado en esta ruta; nuestra base arranca en 2008 igual.
PERIODO_MIN = 121

HOSTS = ("www3.hcdn.gob.ar", "www4.hcdn.gob.ar")

_RUTA = "/dependencias/dcomisiones/periodo-{p}/{p}-{n}.pdf"

_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})")
_DMA = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_SOLO_DIGITOS = re.compile(r"^\d+$")


def _es_faltante(valor: object) -> bool:
    """True para None, NaN, NaT, pd.NA y cadenas vacías.

    Escrito sin importar pandas a propósito: este módulo tiene que poder correr
    (y testearse) sin él. Y cubre los tres sabores de faltante que ya rompieron
    código en este repo — `None`, `float('nan')` y `pd.NA` —, incluido el caso
    en que la comparación misma levanta TypeError en vez de devolver un bool.
    """
    if valor is None:
        return True
    if type(valor).__name__ in ("NaTType", "NAType"):
        return True
    try:
        if bool(valor != valor):          # NaN es el único que no es igual a sí mismo
            return True
    except (TypeError, ValueError):       # pd.NA levanta al pedirle un bool
        return True
    if isinstance(valor, str) and not valor.strip():
        return True
    return False


def _a_fecha(fecha: object) -> _dt.date:
    """Normaliza a `datetime.date`. Acepta date, datetime, Timestamp o texto."""
    if _es_faltante(fecha):
        raise ValueError(f"fecha de publicación faltante o vacía: {fecha!r}")

    # datetime.datetime y pandas.Timestamp entran por acá (Timestamp hereda de datetime).
    if isinstance(fecha, _dt.datetime):
        return fecha.date()
    if isinstance(fecha, _dt.date):
        return fecha

    # Cualquier otra cosa (numpy.datetime64, objetos raros) se pasa por texto.
    texto = str(fecha).strip()
    m = _ISO.match(texto)
    if m:
        anio, mes, dia = (int(g) for g in m.groups())
    else:
        m = _DMA.match(texto)
        if not m:
            raise ValueError(f"no sé leer esta fecha de publicación: {fecha!r}")
        dia, mes, anio = (int(g) for g in m.groups())
    try:
        return _dt.date(anio, mes, dia)
    except ValueError as exc:
        raise ValueError(f"fecha de publicación inválida {fecha!r}: {exc}") from exc


def anio_parlamentario(fecha: object) -> int:
    """Año del período parlamentario al que pertenece una fecha.

    El período va del 1-mar al 28/29-feb, así que enero y febrero pertenecen al
    año anterior. Ahí es donde caen las Órdenes del Día de sesiones
    extraordinarias, que son ~4% del total y el 100% de los errores si se toma
    el año calendario.
    """
    f = _a_fecha(fecha)
    return f.year - 1 if f.month < 3 else f.year


def periodo_de(fecha: object) -> int:
    """Número de período parlamentario (el `<NNN>` de la URL) para una fecha."""
    periodo = anio_parlamentario(fecha) - PERIODO_BASE
    if periodo < PERIODO_MIN:
        raise ValueError(
            f"período {periodo} (fecha {fecha!r}) por debajo del mínimo publicado "
            f"en esta ruta ({PERIODO_MIN}); esa OD hay que buscarla por otro lado"
        )
    return periodo


def numero_od(od_numero: object) -> int:
    """Normaliza el número de OD a entero, sacando los ceros a la izquierda."""
    if _es_faltante(od_numero):
        raise ValueError(f"número de Orden del Día faltante o vacío: {od_numero!r}")
    if isinstance(od_numero, bool):       # bool es int en Python; acá no es un número válido
        raise ValueError(f"número de Orden del Día inválido: {od_numero!r}")
    if isinstance(od_numero, int):
        n = od_numero
    else:
        texto = str(od_numero).strip()
        if not _SOLO_DIGITOS.match(texto):
            raise ValueError(f"número de Orden del Día no numérico: {od_numero!r}")
        n = int(texto)
    if n <= 0:
        raise ValueError(f"número de Orden del Día fuera de rango: {od_numero!r}")
    return n


def ruta_od(od_numero: object, fecha: object) -> str:
    """Ruta del PDF dentro del sitio, sin esquema ni host."""
    return _RUTA.format(p=periodo_de(fecha), n=numero_od(od_numero))


def url_od(od_numero: object, fecha: object, host: str = HOSTS[0]) -> str:
    """URL completa del PDF de una Orden del Día."""
    return f"https://{host}{ruta_od(od_numero, fecha)}"


def urls_od(od_numero: object, fecha: object) -> tuple[str, ...]:
    """Las URL de todos los espejos, en orden de preferencia.

    Se usan para reintentar: si `www3` devuelve 5xx o corta la conexión, el mismo
    archivo suele estar en `www4`. Un 404 en el primero NO se reintenta en el
    segundo — un 404 significa que esa OD no existe con ese número y período, y
    reintentarlo sólo esconde el problema.
    """
    ruta = ruta_od(od_numero, fecha)
    return tuple(f"https://{h}{ruta}" for h in HOSTS)


def nombre_pdf(od_numero: object, fecha: object) -> str:
    """Nombre de archivo para el caché en disco: `<periodo>-<numero>.pdf`."""
    return f"{periodo_de(fecha)}-{numero_od(od_numero)}.pdf"


if __name__ == "__main__":  # pragma: no cover - ayuda de línea de comandos
    import sys

    if len(sys.argv) != 3:
        print("uso: python od_url.py <od_numero> <fecha AAAA-MM-DD>")
        raise SystemExit(2)
    print(url_od(sys.argv[1], sys.argv[2]))
