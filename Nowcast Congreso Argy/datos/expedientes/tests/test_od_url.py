# -*- coding: utf-8 -*-
"""Tests offline de datos/expedientes/src/od_url.py — sin red, sin datos reales.

Cada test fija una forma REAL en que la regla de la URL se puede romper. Acá el
falso positivo es más caro que el error: una fecha mal interpretada no devuelve
error, devuelve una URL **plausible** que apunta al período equivocado, y eso se
descubriría recién al leer el contenido de 2.500 PDF.

Los 7 casos de `VERIFICADOS` no son inventados: se bajó cada PDF y se comparó su
número y su fecha de impresión contra nuestro `expedientes_resultados.parquet`
el 21-08-2026. Si alguno falla, cambió la regla, no el test.

    python datos/expedientes/tests/test_od_url.py
    python -m pytest datos/expedientes/tests/test_od_url.py -q
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from od_url import (  # noqa: E402
    HOSTS,
    anio_parlamentario,
    nombre_pdf,
    numero_od,
    periodo_de,
    url_od,
    urls_od,
)

# (od_numero tal como viene del parquet, fecha de publicación, URL verificada)
VERIFICADOS = [
    ("0001", "2024-01-26", "periodo-141/141-1.pdf"),      # Extraordinarias 2023
    ("0362", "2024-08-29", "periodo-142/142-362.pdf"),
    ("0004", "2026-02-11", "periodo-143/143-4.pdf"),      # Extraordinarias 2025
    ("0007", "2026-04-07", "periodo-144/144-7.pdf"),
    ("0886", "2008-09-19", "periodo-126/126-886.pdf"),
    ("2360", "2015-09-07", "periodo-133/133-2360.pdf"),
    ("1491", "2019-11-19", "periodo-137/137-1491.pdf"),
]


def _correr() -> int:
    fallos: list[str] = []
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    # ─────────────────── los 7 PDF verificados contra la fuente ───────────────────
    print("URL contra PDF reales")
    for numero, fecha, cola in VERIFICADOS:
        u = url_od(numero, fecha)
        check(u.endswith(cola), f"{numero} del {fecha} debería terminar en {cola}, dio {u}")

    # ─────────────────── el borde marzo/febrero, que es TODO el riesgo ───────────────────
    print("borde del período parlamentario (1-mar)")
    check(periodo_de("2025-02-28") == 142, "28-feb-2025 sigue siendo período 142")
    check(periodo_de("2025-03-01") == 143, "1-mar-2025 ya es período 143")
    check(periodo_de("2024-12-31") == 142, "diciembre no cambia de período")
    check(periodo_de("2025-01-01") == 142, "1-ene-2025 todavía es período 142")
    check(anio_parlamentario("2026-02-11") == 2025, "febrero pertenece al año parlamentario anterior")
    check(anio_parlamentario("2026-03-01") == 2026, "marzo abre el año parlamentario")
    check(periodo_de(dt.date(2004, 2, 29)) == 121, "29-feb de bisiesto cae en el período anterior")

    # ─────────────────── el número: ceros a la izquierda y basura ───────────────────
    print("normalización del número de OD")
    check(numero_od("0356") == 356, "se sacan los ceros a la izquierda")
    check(numero_od("1641") == 1641, "un número sin ceros queda igual")
    check(numero_od(7) == 7, "acepta int")
    check(nombre_pdf("0356", "2008-09-19") == "126-356.pdf", "nombre de archivo del caché")
    for malo in ("", "  ", "12a", "OD 4", "-3", "0", 0, -1, True):
        try:
            numero_od(malo)
            check(False, f"numero_od({malo!r}) tendría que haber levantado ValueError")
        except ValueError:
            check(True, "")
            corridos -= 1  # no infla la cuenta: lo importante es que no pase de largo

    # ─────────────────── faltantes: los tres sabores que ya rompieron este repo ───────────────────
    print("faltantes (None / NaN / NaT / pd.NA)")
    faltantes: list[object] = [None, float("nan"), "", "   "]
    try:
        import pandas as pd

        faltantes += [pd.NA, pd.NaT]
    except ImportError:
        print("  (sin pandas: se saltean pd.NA y pd.NaT)")
    for f in faltantes:
        try:
            url_od("0004", f)
            check(False, f"una fecha {f!r} tendría que levantar ValueError, no devolver una URL")
        except ValueError:
            check(True, f"fecha {f!r} rechazada")
        try:
            url_od(f, "2026-02-11")
            check(False, f"un número {f!r} tendría que levantar ValueError")
        except ValueError:
            check(True, f"número {f!r} rechazado")

    # ─────────────────── formatos de fecha que llegan de distintos lados ───────────────────
    print("formatos de fecha")
    esperado = url_od("0362", "2024-08-29")
    check(url_od("0362", dt.date(2024, 8, 29)) == esperado, "acepta datetime.date")
    check(url_od("0362", dt.datetime(2024, 8, 29, 13, 5)) == esperado, "acepta datetime")
    check(url_od("0362", "29/08/2024") == esperado, "acepta dd/mm/aaaa")
    check(url_od("0362", "2024-08-29 00:00:00") == esperado, "acepta ISO con hora")
    for mala in ("agosto de 2024", "2024-13-01", "2024-02-30", "29-08-2024"):
        try:
            url_od("0362", mala)
            check(False, f"la fecha {mala!r} tendría que levantar ValueError")
        except ValueError:
            check(True, f"fecha {mala!r} rechazada")

    # ─────────────────── espejos ───────────────────
    print("espejos www3 / www4")
    us = urls_od("0362", "2024-08-29")
    check(len(us) == len(HOSTS), "hay una URL por espejo")
    check(us[0].startswith("https://www3."), "el primero es www3")
    check(len({u.split("/dependencias/")[1] for u in us}) == 1, "los espejos comparten la ruta")

    # ─────────────────── los dos backends de dtype ───────────────────
    print("valores que vienen de pandas, con los dos backends")
    try:
        import pandas as pd

        df = pd.DataFrame({"od_numero": ["0362"], "od_publicacion": ["2024-08-29"]})
        for etiqueta, d in [("object", df), ("pyarrow", None)]:
            if d is None:
                try:
                    import pyarrow  # noqa: F401  - sin esto convert_dtypes revienta feo
                    d = df.convert_dtypes(dtype_backend="pyarrow")
                except Exception as exc:  # noqa: BLE001 - pandas viejo levanta cosas raras
                    # OJO: sin pyarrow instalado, pandas 2.3 no levanta ImportError sino
                    # NameError('ArrowDtype'). Por eso acá se atrapa ancho a propósito.
                    print(f"  (sin backend pyarrow, se saltea: {type(exc).__name__})")
                    continue
            fila = d.iloc[0]
            check(url_od(fila["od_numero"], fila["od_publicacion"]) == esperado,
                  f"misma URL leyendo del backend {etiqueta}")
        # y con la fecha ya parseada a Timestamp, que es como sale del parquet
        ts = pd.to_datetime(df["od_publicacion"]).iloc[0]
        check(url_od("0362", ts) == esperado, "acepta pandas.Timestamp")
    except ImportError:
        print("  (sin pandas: se saltea)")

    # ─────────────────── períodos que no están publicados en esta ruta ───────────────────
    print("períodos fuera de rango")
    try:
        periodo_de("1999-05-10")
        check(False, "un período anterior al 121 tendría que levantar ValueError")
    except ValueError:
        check(True, "período viejo rechazado")

    print(f"\n{corridos - len(fallos)}/{corridos} OK")
    if fallos:
        print(f"\n{len(fallos)} FALLAS:")
        for f in fallos:
            print(f"  - {f}")
    return len(fallos)


def test_od_url() -> None:
    """Entrada para pytest. El cuerpo vive en `_correr()` para que el archivo
    siga andando como script sin abortar la corrida de pytest con SystemExit."""
    assert _correr() == 0


if __name__ == "__main__":
    sys.exit(1 if _correr() else 0)
