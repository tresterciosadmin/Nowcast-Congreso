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


# --- version FINA: factor de la 2a camara (revisora) --------------------- #
def test_revisora_memoizacion():
    llamadas = []

    def fake(camara, mes):
        llamadas.append((camara, mes))
        return 0.6

    c = _cohorte_sintetica()
    prev = B.construir_p_revisora_por_mes(c, fake)
    chk(len(prev) == 4, "revisora: 4 (origen,mes) unicos memoizados")
    chk(len(llamadas) == 4, "revisora: se calculo una vez por mes-origen")


def test_componer_con_revisora_triple():
    c = _cohorte_sintetica()
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.8}
    prev = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.5, ("Senado", "2023-06"): 0.5}
    out = B.componer_backtest(c, pmay, p_revisora_map=prev)
    fila = out[out["proyecto_id"] == "P0"].iloc[0]
    chk(abs(fila["p_aprob"] - fila["p_llega"] * 0.5 * 0.5) < 1e-9,
        "p_aprob = p_llega x p_mayoria x p_revisora (segunda camara)")
    chk((out["p_aprob"] <= 1.0).all(), "p_aprob clip en 1 con la 2a camara")


def test_componer_revisora_descarta_mes_faltante():
    c = _cohorte_sintetica()
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.8}
    prev = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5}  # falta junio
    out = B.componer_backtest(c, pmay, p_revisora_map=prev)
    chk((out["mes"] == "2023-05").all(),
        "sin p_revisora del mes -> esas filas se descartan (cohorte 2018+ honesta)")


def test_revisora_backend_faltante_pdNA():
    base = _cohorte_sintetica()
    base.loc[0, "p_llega"] = np.nan
    pmay = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.8, ("Senado", "2023-06"): 0.8}
    prev = {("Diputados", "2023-05"): 0.5, ("Senado", "2023-05"): 0.5,
            ("Diputados", "2023-06"): 0.5, ("Senado", "2023-06"): 0.5}
    for backend in ("numpy_nullable", "pyarrow"):
        try:
            c = base.convert_dtypes(dtype_backend=backend)
        except Exception:
            continue
        out = B.componer_backtest(c, pmay, p_revisora_map=prev)
        chk(pd.isna(out.loc[out['proyecto_id'] == 'P0', 'p_aprob']).all(),
            f"revisora backend {backend}: p_llega NA -> p_aprob NA, sin excepcion")


# --- factor empirico de 2a camara (walk-forward, sin fuga) --------------- #
def _cohorte_multianio():
    filas = []
    # 2020: 40 llegan al recinto, 20 sancionados (tasa 0.5)
    for i in range(40):
        filas.append({"proyecto_id": f"A{i}", "anio": 2020, "llega_recinto": True,
                      "sancionado": 1 if i < 20 else 0})
    # 2021: 40 llegan, 10 sancionados (tasa 0.25) — no debe afectar al factor de 2021
    for i in range(40):
        filas.append({"proyecto_id": f"B{i}", "anio": 2021, "llega_recinto": True,
                      "sancionado": 1 if i < 10 else 0})
    # 2022: un proyecto cualquiera
    filas.append({"proyecto_id": "C0", "anio": 2022, "llega_recinto": False, "sancionado": 0})
    return pd.DataFrame(filas)


def test_factor_empirico_walkforward():
    c = _cohorte_multianio()
    k = B.factor_revisora_empirico(c, min_prev=10)
    c = c.assign(k=k)
    chk(c[c["anio"] == 2020]["k"].isna().all(),
        "2020 sin años previos -> factor NaN (no inventa)")
    k2021 = c[c["anio"] == 2021]["k"].iloc[0]
    chk(abs(k2021 - 0.5) < 1e-9,
        "2021 usa SOLO 2020 (tasa 0.5), no su propio año -> sin fuga")
    k2022 = c[c["anio"] == 2022]["k"].iloc[0]
    # 2022 usa 2020+2021 = (20+10)/(40+40) = 0.375
    chk(abs(k2022 - 0.375) < 1e-9, "2022 acumula 2020+2021 = 0.375 (walk-forward)")


# --- condicionar por ORIGEN FINO (camara, mes, origen) ------------------- #
def _cohorte_con_origen():
    """Cohorte con origen_fino: mismos (camara,mes) pero DISTINTO origen -> deben
    ser claves separadas."""
    filas = []
    origenes = ["EJECUTIVO", "OFICIALISMO", "OPOSICION", None]
    for i in range(8):
        filas.append({
            "proyecto_id": f"P{i}", "camara": "Diputados", "mes": "2023-05", "anio": 2023,
            "sancionado": 1 if i % 2 == 0 else 0, "p_llega": 0.5,
            "p_sancion_embudo": 0.3, "origen_fino": origenes[i % 4],
        })
    return pd.DataFrame(filas)


def test_norm_origen():
    chk(B._norm_origen(None) is None, "None -> None")
    chk(B._norm_origen(float("nan")) is None, "nan -> None (pyarrow pd.NA cubierto)")
    chk(B._norm_origen("EJECUTIVO") == "EJECUTIVO", "str se conserva")


def test_grupo_memoizacion():
    llamadas = []

    def fake(camara, mes, origen):
        llamadas.append((camara, mes, origen))
        return 0.5

    c = _cohorte_con_origen()
    pmay = B.construir_p_mayoria_por_grupo(c, fake)
    # 1 camara x 1 mes x 4 origenes (incl. None) = 4 claves, aunque hay 8 proyectos
    chk(len(pmay) == 4, "4 (camara,mes,origen) unicos memoizados")
    chk(len(llamadas) == 4, "el factor se calculo 4 veces (una por origen), no 8")
    chk(("Diputados", "2023-05", "EJECUTIVO") in pmay, "clave con origen EJECUTIVO")
    chk(("Diputados", "2023-05", None) in pmay, "clave con origen None (incondicional)")


def test_componer_por_origen():
    c = _cohorte_con_origen()
    pmay = {("Diputados", "2023-05", "EJECUTIVO"): 0.9,
            ("Diputados", "2023-05", "OFICIALISMO"): 0.4,
            ("Diputados", "2023-05", "OPOSICION"): 0.2,
            ("Diputados", "2023-05", None): 0.5}
    out = B.componer_backtest(c, pmay, por_origen=True)
    chk(len(out) == 8, "todas las filas encuentran su p_mayoria por origen")
    fila_pe = out[out["proyecto_id"] == "P0"].iloc[0]   # EJECUTIVO
    chk(abs(fila_pe["p_mayoria"] - 0.9) < 1e-9, "P0 (EJECUTIVO) toma 0.9, no el incondicional")
    fila_ofi = out[out["proyecto_id"] == "P1"].iloc[0]  # OFICIALISMO
    chk(abs(fila_ofi["p_mayoria"] - 0.4) < 1e-9, "P1 (OFICIALISMO) toma 0.4 (distinto del PE)")


def test_por_origen_dos_backends():
    base = _cohorte_con_origen()
    pmay = {("Diputados", "2023-05", "EJECUTIVO"): 0.9,
            ("Diputados", "2023-05", "OFICIALISMO"): 0.4,
            ("Diputados", "2023-05", "OPOSICION"): 0.2,
            ("Diputados", "2023-05", None): 0.5}
    for backend in ("numpy_nullable", "pyarrow"):
        try:
            c = base.convert_dtypes(dtype_backend=backend)
        except Exception:
            continue
        out = B.componer_backtest(c, pmay, por_origen=True)
        chk(len(out) == 8, f"backend {backend}: por_origen no rompe (pd.NA en origen cubierto)")


if __name__ == "__main__":
    test_norm_origen()
    test_grupo_memoizacion()
    test_componer_por_origen()
    test_por_origen_dos_backends()
    test_factor_empirico_walkforward()
    test_skill_score()
    test_memoizacion()
    test_memoizacion_tolera_fallos()
    test_componer()
    test_componer_descarta_mes_faltante()
    test_resumen()
    test_backends_dtype()
    test_backend_con_faltante_pdNA()
    test_revisora_memoizacion()
    test_componer_con_revisora_triple()
    test_componer_revisora_descarta_mes_faltante()
    test_revisora_backend_faltante_pdNA()
    print(f"\nOK: {OK} chequeos")
