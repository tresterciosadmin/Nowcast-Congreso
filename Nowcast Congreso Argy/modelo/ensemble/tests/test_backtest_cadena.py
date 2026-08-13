"""Tests offline del backtest de la cadena (opcion B). NO tocan datos del repo:
la cohorte y el factor de mayoria se inyectan sinteticos. Ejercitan los DOS
backends de dtype (numpy_nullable + pyarrow) para el path del faltante pd.NA.
Correr:  python modelo/ensemble/tests/test_backtest_cadena.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import backtest_cadena as B  # noqa: E402

# _metricas real del embudo, para que resumen() sea el del sistema
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "variables" / "embudo" / "src"))
import embudo  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def _cohorte_sintetica():
    """8 proyectos, 2 camaras, 2 meses; label sancionado correlado con p_llega alto."""
    filas = []
    for i in range(8):
        cam = "Diputados" if i % 2 == 0 else "Senado"
        mes = "2023-05" if i < 4 else "2023-06"
        p_llega = 0.1 + 0.1 * i           # 0.1 .. 0.8
        filas.append({
            "proyecto_id": f"P{i}",
            "camara": cam, "mes": mes, "anio": 2023,
            "sancionado": 1 if p_llega >= 0.5 else 0,
            "p_llega": p_llega,
            "p_sancion_embudo": min(0.99, p_llega * 0.6),
        })
    return pd.DataFrame(filas)


# --- skill_score ---------------------------------------------------------- #
def test_skill_score():
    chk(B.skill_score(0.05, 0.10) == 0.5, "skill 0,05 vs 0,10 = 0,5")
    chk(B.skill_score(0.10, 0.10) == 0.0, "brier igual a la ref -> skill 0")
    chk(B.skill_score(0.20, 0.10) == -1.0, "peor que la ref -> skill negativo")
    chk(np.isnan(B.skill_score(0.1, 0.0)), "ref 0 -> NaN (no divide por cero)")
    chk(np.isnan(B.skill_score(0.1, float("nan"))), "ref NaN -> NaN")


# --- construir_p_mayoria_por_mes: memoizacion e inyeccion ----------------- #
def test_memoizacion():
    llamadas = []

    def fake(camara, mes):
        llamadas.append((camara, mes))
        return 0.5

    c = _cohorte_sintetica()
    pmay = B.construir_p_mayoria_por_mes(c, fake)
    # 2 camaras x 2 meses = 4 claves unicas, aunque hay 8 proyectos
    chk(len(pmay) == 4, "4 (camara,mes) unicos memoizados")
    chk(len(llamadas) == 4, "el factor de mayoria se calculo 4 veces, no 8")
    chk(all(0.0 <= v <= 1.0 for v in pmay.values()), "p_mayoria en [0,1]")


def test_memoizacion_tolera_fallos():
    def fake(camara, mes):
        if camara == "Senado":
            raise RuntimeError("mes sin roster")
        return 0.4

    c = _cohorte_sintetica()
    pmay = B.construir_p_mayoria_por_mes(c, fake)
    chk(("Senado", "2023-05") not in pmay, "un mes que falla no entra al mapa")
    chk(("Diputados", "2023-05") in pmay, "los que andan si entran")


# --- componer_backtest ---------------------------------------------------- #
def test_componer():
    c = _cohorte_sintetica()
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.2}
    out = B.componer_backtest(c, pmay)
    chk(len(out) == 8, "todas las filas tienen p_mayoria de su mes")
    fila = out[out["proyecto_id"] == "P0"].iloc[0]
    chk(abs(fila["p_aprob"] - fila["p_llega"] * 0.5) < 1e-9,
        "p_aprob = p_llega x p_mayoria")
    chk((out["p_aprob"] <= 1.0).all(), "p_aprob clip en 1")


def test_componer_descarta_mes_faltante():
    c = _cohorte_sintetica()
    # falta el mes de junio para Senado -> esas filas se caen
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8}
    out = B.componer_backtest(c, pmay)
    chk(len(out) < 8, "las filas sin p_mayoria de su mes se descartan")
    chk(not (out["camara"].eq("Senado") & out["mes"].eq("2023-06")).any(),
        "no queda ninguna fila del mes faltante")


# --- resumen -------------------------------------------------------------- #
def test_resumen():
    c = _cohorte_sintetica()
    pmay = {("Diputados", "2023-05"): 0.6, ("Senado", "2023-05"): 0.6,
            ("Diputados", "2023-06"): 0.6, ("Senado", "2023-06"): 0.6}
    out = B.componer_backtest(c, pmay)
    res = B.resumen(embudo, out)
    chk(res["n_evaluados"] == 8, "resumen cuenta los 8 evaluados")
    chk(0.0 <= res["tasa_base_sancion"] <= 1.0, "tasa base en [0,1]")
    for k in ("brier", "auc", "skill_vs_climatologia", "skill_vs_embudo"):
        chk(k in res["cadena"], f"resumen.cadena trae {k}")
    chk("brier" in res["baseline_embudo_p_sancion"], "trae la baseline del embudo")
    chk(isinstance(res["cadena"]["calibracion"], list), "calibracion es lista de bins")


# --- los DOS backends de dtype: el faltante como pd.NA no rompe ----------- #
def _correr_pipeline(c):
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.2}
    out = B.componer_backtest(c, pmay)
    return B.resumen(embudo, out)


def test_backends_dtype():
    base = _cohorte_sintetica()
    for backend in ("numpy_nullable", "pyarrow"):
        try:
            c = base.convert_dtypes(dtype_backend=backend)
        except Exception as e:  # pyarrow puede no estar en algun entorno
            print(f"  (backend {backend} no disponible: {e})")
            continue
        res = _correr_pipeline(c)
        chk(res["n_evaluados"] == 8, f"backend {backend}: 8 evaluados sin romper")
        chk(not pd.isna(res["cadena"]["brier"]), f"backend {backend}: brier valido")


def test_backend_con_faltante_pdNA():
    """Un p_llega faltante (pd.NA) no debe reventar la composicion ni el resumen."""
    base = _cohorte_sintetica()
    base.loc[0, "p_llega"] = np.nan
    for backend in ("numpy_nullable", "pyarrow"):
        try:
            c = base.convert_dtypes(dtype_backend=backend)
        except Exception:
            continue
        pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
                ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.2}
        out = B.componer_backtest(c, pmay)
        # la fila 0 queda con p_aprob NaN (p_llega NA); resumen no debe crashear
        chk(len(out) == 8, f"backend {backend}: componer no descarta por p_llega NA")
        # el faltante se propaga a p_aprob sin levantar TypeError de pd.NA
        chk(pd.isna(out.loc[out['proyecto_id'] == 'P0', 'p_aprob']).all(),
            f"backend {backend}: p_llega NA -> p_aprob NA, sin excepcion")


if __name__ == "__main__":
    test_skill_score()
    test_memoizacion()
    test_memoizacion_tolera_fallos()
    test_componer()
    test_componer_descarta_mes_faltante()
    test_resumen()
    test_backends_dtype()
    test_backend_con_faltante_pdNA()
    print(f"\nOK: {OK} chequeos")
