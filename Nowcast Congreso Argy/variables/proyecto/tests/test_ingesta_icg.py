"""Tests offline de ingesta_icg (sin red): normalización de layouts y controles."""
# sync-check: 2026-07-11
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import ingesta_icg as icg  # noqa: E402

OK = 0


def check(cond, msg):
    global OK
    assert cond, msg
    OK += 1
    print(f"  ok: {msg}")


def _excel_bytes(df, header_offset=0):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, startrow=header_offset)
    buf.seek(0)
    return buf.read()


def test_layout_largo():
    n = 300
    fechas = pd.date_range("2001-11-01", periods=n, freq="MS")
    df = pd.DataFrame({"Año": fechas.year, "Mes": fechas.month, "ICG": 2.5})
    out = icg.parsear_excel(_excel_bytes(df))
    check(len(out) == n, "largo: conserva los 300 meses")
    check(list(out.columns) == ["fecha", "anio", "mes", "icg"], "largo: contrato de columnas")
    check(out["fecha"].is_monotonic_increasing, "largo: orden temporal")


def test_layout_largo_meses_texto():
    df = pd.DataFrame({
        "año": [2001] * 2 + [2002] * 12 + [2003] * 12 + list(range(2004, 2026)) * 12,
        "mes": (["noviembre", "diciembre"] + list(icg.MESES)[:12] * 2
                + [m for m in list(icg.MESES)[:12] for _ in range(22)]),
        "ICG (0-5)": 3.1,
    })
    out = icg.parsear_excel(_excel_bytes(df))
    check(len(out) > 250, f"texto: meses en castellano parseados ({len(out)})")
    check(set(out["mes"]) <= set(range(1, 13)), "texto: mes numérico 1-12")


def test_layout_ancho():
    anios = list(range(2001, 2027))
    data = {"Año": anios}
    for m in ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
              "agosto", "septiembre", "octubre", "noviembre", "diciembre"]:
        data[m] = [2.0] * len(anios)
    out = icg.parsear_excel(_excel_bytes(pd.DataFrame(data)))
    check(len(out) == len(anios) * 12, "ancho: filas año x columnas mes")


def test_limpieza_defensiva():
    df = pd.DataFrame({
        "anio": [2005, 2005, 1990, 2005, 2005],
        "mes": [1, 1, 2, 3, 4],           # duplicado ene-2005
        "icg": [2.0, 2.0, 2.0, 9.9, None],  # fuera de escala y nulo
    })
    out = icg._limpiar(df)
    check(len(out) == 1, "limpieza: descarta dup/fuera de rango/nulo/año inválido")
    check(out["icg"].iloc[0] == 2.0, "limpieza: conserva el válido")


def test_layout_transpuesto_utdt():
    """Regresión: layout REAL del Excel de UTDT (visto 2026-07-11) — fechas en una
    fila, valores 'ICG' abajo, fila 'Variación ICG' a ignorar, etiquetas de año
    como texto arriba (que NO deben elegirse como fila de fechas), 2 hojas."""
    import numpy as np
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for nombre, inicio, n in [("Evolución ICG 2001-2022", "2001-11-01", 254),
                                  ("Evolución ICG a partir de 2023", "2023-01-01", 42)]:
            fechas = pd.date_range(inicio, periods=n, freq="MS")
            filas = [
                [None, None, "Índice de Confianza en el Gobierno"] + [None] * (n - 1),
                [None] * (n + 2),
                [None, None] + [str(f.year) if f.month == 1 else None for f in fechas],
                [None] * (n + 2),
                [None, None] + list(fechas),                      # fila de fechas
                [None, "ICG "] + [2.2] * n,                        # fila de valores
                [None, "Variación ICG"] + [0.01] * n,              # a ignorar
                [None] * (n + 2),
                [None, None, "Cómo citar: ..."] + [None] * (n - 1),
            ]
            pd.DataFrame(filas).to_excel(w, sheet_name=nombre, index=False, header=False)
    buf.seek(0)
    out = icg.parsear_excel(buf.read())
    check(len(out) == 296, f"transpuesto: 296 meses en 2 hojas ({len(out)})")
    check(out["fecha"].min() == pd.Timestamp("2001-11-01"), "transpuesto: arranca nov-2001")
    check((out["icg"] == 2.2).all(), "transpuesto: toma la fila ICG, no la variación")


def test_encabezado_desplazado():
    n = 300
    fechas = pd.date_range("2001-11-01", periods=n, freq="MS")
    df = pd.DataFrame({"AÑO": fechas.year, "MES": fechas.month, "icg": 1.5})
    out = icg.parsear_excel(_excel_bytes(df, header_offset=3))
    check(len(out) == n, "encabezado en fila 4: lo encuentra igual")


FIXTURE_INFORMES = """
<h1>ICG</h1><h2>Resultados</h2>
<p><strong><a href="/download.php?fname=_178216301375542900.pdf">Junio 2026</a></strong></p>
<p>El ICG de junio fue de 2,07 puntos, nivel que representa un aumento de 3,9% respecto del mes anterior.</p>
<p><strong><a href="/download.php?fname=_177973789336894400.pdf">Mayo 2026</a></strong></p>
<p>El ICG de mayo fue de 1,99 puntos, nivel que representa una disminución de 1,6% respecto del mes anterior.</p>
<p><strong><a href="#">Febrero 202</a></strong><strong><a href="#">6</a></strong></p>
<p>El ICG de febrero fue de 2,38 puntos, nivel que representa una leve caída de 0,6%.</p>
<p><strong><a href="#">Diciembre</a></strong><strong><a href="#">2025</a></strong></p>
<p>El ICG de diciembre fue de 2,46 puntos, nivel que representa una leve disminución de 0,1%.</p>
<p><a href="#"><strong>Julio 2025</strong></a></p>
<p>La medición de julio del ICG fue de 2,45 puntos, indicando un crecimiento del 4,9%.</p>
"""


def test_scrapear_informes_fixture():
    out = icg.scrapear_informes(html=FIXTURE_INFORMES)
    check(len(out) == 5, f"informes: 5 entradas parseadas ({len(out)})")
    d = {f.strftime("%Y-%m"): v for f, v in zip(out["fecha"], out["icg"])}
    check(d.get("2026-06") == 2.07, "informes: junio 2026 = 2,07 (redacción nueva)")
    check(d.get("2025-07") == 2.45, "informes: julio 2025 = 2,45 (redacción vieja 'La medición')")
    check(d.get("2026-02") == 2.38, "informes: febrero 2026 con año partido por negritas")
    check(d.get("2025-12") == 2.46, "informes: diciembre con 'Diciembre'+'2025' en links separados")


def test_actualizar_ultimo_merge(tmp_path=None):
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    csv = tmp / "icg_mensual.csv"
    base = pd.DataFrame({
        "fecha": pd.date_range("2026-01-01", periods=4, freq="MS"),
        "anio": [2026] * 4, "mes": [1, 2, 3, 4],
        "icg": [2.396878, 2.383406, 2.300890, 2.023031],
    })
    base.to_csv(csv, index=False)
    original = icg.scrapear_informes
    icg.scrapear_informes = lambda html=None: original(html=FIXTURE_INFORMES)
    try:
        out = icg.actualizar_ultimo(csv)
        out2 = icg.actualizar_ultimo(csv)  # segunda corrida
    finally:
        icg.scrapear_informes = original
    check(len(out) == 6, f"ultimo: agrega mayo y junio ({len(out)} filas)")
    releido = pd.read_csv(csv, parse_dates=["fecha"])
    check(releido["fecha"].max() == pd.Timestamp("2026-06-01"), "ultimo: CSV extendido a jun-2026")
    check(abs(releido[releido.mes == 2].icg.iloc[0] - 2.383406) < 1e-6,
          "ultimo: NO pisa el valor preciso existente (feb) con el redondeado del informe")
    check(len(out2) == 6, "ultimo: idempotente (segunda corrida no duplica)")


def test_escritura_estable():
    """El CSV reescrito sin cambios tiene que quedar BYTE A BYTE igual.

    Sin `float_format` fijo, pandas devuelve algunos floats con un dígito menos
    en la última posición (2.8727293059654078 -> 2.872729305965408): el mismo
    número, pero el `git diff` marca decenas de líneas como cambiadas. La
    primera corrida del workflow del ICG ensució **59 líneas para agregar una**.
    Un diff que siempre trae ruido deja de servir para revisar, y un cambio real
    de la UTDT quedaría enterrado ahí.
    """
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "icg.csv"
    serie = pd.DataFrame({
        "fecha": pd.to_datetime(["2003-09-01", "2007-07-01", "2026-06-01"]),
        "anio": [2003, 2007, 2026], "mes": [9, 7, 6],
        # los dos primeros son los que oscilaban en la serie real
        "icg": [2.8727293059654078, 1.9988101264971851, 2.07],
    })
    icg._escribir(icg._con_fuente(serie, icg.FUENTE_EXCEL), tmp)
    primera = tmp.read_bytes()
    releida = icg._con_fuente(pd.read_csv(tmp, parse_dates=["fecha"]), icg.FUENTE_EXCEL)
    icg._escribir(releida, tmp)
    check(tmp.read_bytes() == primera, "escritura: leer y reescribir no cambia un byte")
    check("fuente" in pd.read_csv(tmp).columns, "escritura: la columna `fuente` viaja")


def test_excel_pisa_pero_no_borra():
    """Regla de Valle (06-08): **siempre gana el valor del Excel oficial.**

    Pero el Excel no puede BORRAR: si la serie en disco tiene un mes que el
    Excel todavía no publicó —el que entró por el informe—, se conserva. Sin
    esto, correr el modo `serie` para refinar la precisión haría desaparecer el
    mes más nuevo, que es justo el que mira el nowcast.
    """
    previa = pd.DataFrame({
        "fecha": pd.to_datetime(["2026-06-01", "2026-07-01"]),
        "anio": [2026, 2026], "mes": [6, 7], "icg": [2.07, 1.94],
        "fuente": [icg.FUENTE_INFORME, icg.FUENTE_INFORME],
    })
    # el Excel trae junio con precisión completa, pero NO julio
    excel = icg._con_fuente(pd.DataFrame({
        "fecha": pd.to_datetime(["2026-06-01"]), "anio": [2026], "mes": [6],
        "icg": [2.0712345678901],
    }), icg.FUENTE_EXCEL)

    out = icg._fundir(excel, previa[icg.COLUMNAS])
    junio = out[out.mes == 6].iloc[0]
    check(abs(junio["icg"] - 2.0712345678901) < 1e-12,
          "precedencia: el Excel PISA el valor redondeado del informe")
    check(junio["fuente"] == icg.FUENTE_EXCEL, "precedencia: junio queda marcado como `excel`")
    julio = out[out.mes == 7]
    check(len(julio) == 1, "precedencia: julio NO se borra aunque el Excel no lo traiga")
    check(julio["fuente"].iloc[0] == icg.FUENTE_INFORME,
          "precedencia: julio queda marcado `informe` (provisional)")
    check(list(out["fecha"]) == sorted(out["fecha"]), "precedencia: la serie queda ordenada")


if __name__ == "__main__":
    for fn in [test_layout_largo, test_layout_largo_meses_texto, test_layout_ancho,
               test_limpieza_defensiva, test_layout_transpuesto_utdt,
               test_encabezado_desplazado, test_scrapear_informes_fixture,
               test_actualizar_ultimo_merge,
               test_escritura_estable, test_excel_pisa_pero_no_borra]:
        print(fn.__name__)
        fn()
    print(f"\n{OK} chequeos OK")
