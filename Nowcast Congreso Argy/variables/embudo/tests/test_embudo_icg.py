"""Tests del ICG dentro del embudo (offline, sin red ni disco de datos).

Lo que se protege acá es UNA cosa sobre todo: **que el ICG no mire el futuro.**
El propio URGENTE.md abrió por sospechar leakage en `n_giros`; meter una serie
temporal como rasgo sin candado es la forma más fácil de repetir ese problema a
lo grande. Un proyecto presentado en el mes M tiene que ver el ICG de M-1 y
nunca el de M.

Correr:  python variables/embudo/tests/test_embudo_icg.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import embudo as E  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def serie_icg(tmp: Path) -> Path:
    """24 meses de 2020-2021 con un valor por mes fácil de reconocer:
    icg = anio_offset + mes/100, así el test puede leer de qué mes salió."""
    filas = []
    for anio in (2020, 2021):
        for mes in range(1, 13):
            filas.append({"fecha": f"{anio}-{mes:02d}-01", "anio": anio,
                          "mes": mes, "icg": (anio - 2020) * 10 + mes})
    p = tmp / "icg_test.csv"
    pd.DataFrame(filas).to_csv(p, index=False)
    return p


def cohorte(anios_meses):
    return pd.DataFrame({
        "proyecto_id": [f"{i}-D" for i in range(len(anios_meses))],
        "anio": [a for a, _ in anios_meses],
        "mes": [m for _, m in anios_meses],
        "n_giros": 1, "camara_origen": "DIPUTADOS", "autor": "A0",
        "comisiones": [["PRESUPUESTO"]] * len(anios_meses),
    })


def main():
    import tempfile
    tmp = Path(tempfile.mkdtemp())

    # ---------- cargar_icg ----------
    icg = E.cargar_icg(serie_icg(tmp))
    chk(icg is not None and len(icg) == 24, "cargar_icg lee los 24 meses")
    chk(icg[(2020, 6)]["icg"] == 6, "el nivel del mes es el que dice la serie")
    chk(icg[(2020, 6)]["icg_delta_3m"] == 3, "delta_3m = junio(6) - marzo(3)")
    chk(icg[(2020, 1)]["icg_delta_3m"] is None,
        "los primeros 3 meses no tienen delta (no se inventa)")
    chk(E.cargar_icg(tmp / "no_existe.csv") is None,
        "sin archivo devuelve None y el modelo corre igual")

    # ---------- el rezago ----------
    chk(E._mes_rezagado(2021, 3) == (2021, 2), "rezago simple: marzo ve febrero")
    chk(E._mes_rezagado(2021, 1) == (2020, 12),
        "rezago cruzando el año: enero ve diciembre del año anterior")
    chk(E._mes_rezagado(None, 5) is None, "fecha ilegible no rompe, devuelve None")
    chk(E._mes_rezagado(2021, 13) is None, "mes fuera de rango se descarta")

    # ---------- ANTI-LEAKAGE: el rasgo es el del mes ANTERIOR ----------
    c = cohorte([(2020, 6), (2021, 1), (2020, 2)])
    X = E.construir_features(c, [], {}, 0.1, None, icg)
    chk(X["icg"].iloc[0] == 5,
        "proyecto de junio-2020 ve el ICG de MAYO (5), no el de junio (6)")
    chk(X["icg"].iloc[1] == 12,
        "proyecto de enero-2021 ve diciembre-2020 (12), cruzando el año")
    chk(X["icg_delta_3m"].iloc[0] == 3, "el delta también viene del mes anterior")

    # ---------- faltantes ----------
    c2 = cohorte([(1998, 5), (2020, 6)])       # 1998 es anterior a la serie
    X2 = E.construir_features(c2, [], {}, 0.1, None, icg)
    media = sum(v["icg"] for v in icg.values()) / len(icg)
    chk(abs(X2["icg"].iloc[0] - media) < 1e-9,
        "sin dato, el nivel va a la media de la serie (neutro, no cero)")
    chk(X2["icg_sin_dato"].iloc[0] == 1.0 and X2["icg_sin_dato"].iloc[1] == 0.0,
        "la bandera icg_sin_dato marca exactamente a quien no tuvo dato")
    chk(not X2.isna().any().any(), "la matriz de rasgos no queda con NaN")

    # ---------- el ICG es OPCIONAL ----------
    X3 = E.construir_features(c, [], {}, 0.1, None, None)
    chk(not any(col.startswith("icg") for col in X3.columns),
        "sin ICG el modelo queda idéntico al anterior (no rompe nada)")

    # ---------- el rasgo no puede ser constante (seria inutil) ----------
    chk(X["icg"].nunique() > 1, "el ICG varía entre proyectos de distintos meses")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
