"""Tests offline de modelo/ensemble/src/composicion_capitulos.py (FASE 2,
PROMPT-MULTITEMA-V2.md). Sin datos reales ni red: rosters sintéticos.

El test que más importa (pedido EXPLÍCITO del prompt): con capítulos
PERFECTAMENTE correlacionados, P_todo tiene que dar ≈ min_k P_k y NO el
producto — es el que atrapa el error de independencia si alguien lo
reintroduce.

    python modelo/ensemble/tests/test_composicion_capitulos.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import composicion_capitulos as C  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


N = 100  # roster chico, alcanza para el test que no necesita escala real


def _roster(p_afirm: float) -> tuple[np.ndarray, np.ndarray]:
    """Roster sintético cuya línea agregada da aproximadamente p_afirm cuando
    se simula sin desvío (línea AFIRMATIVO para la fracción p_afirm del roster,
    NEGATIVO para el resto, desvío 0 -> determinístico sin el shock)."""
    n_afirm = int(round(N * p_afirm))
    lineas = np.array(["AFIRMATIVO"] * n_afirm + ["NEGATIVO"] * (N - n_afirm))
    desvios = np.zeros(N)
    return lineas, desvios


def _roster_referencia() -> tuple[np.ndarray, np.ndarray]:
    """El ESCENARIO DE REFERENCIA de FORMULA-COMPLETA.md §III.A.3 / ADR-0025
    (el mismo que usa `test_agregador.py`: 140 a favor con desvío 0,03 ->
    P_i≈0,97, 117 en contra con desvío 0,04 -> P_i≈0,04): con tipo_mayoria
    ABSOLUTA pasa de P≈1,0 (sin shock) a P≈0,73 con tau=1,2 — SENSIBLE al
    shock, a diferencia de un roster con desvío 0 (los P_i quedan tan pegados
    a 0/1 tras el encogimiento afín que hace falta un eta extremo para mover
    el voto). Reusar el escenario ya validado, no inventar uno nuevo sin
    verificar."""
    lineas = np.array(["AFIRMATIVO"] * 140 + ["NEGATIVO"] * 117)
    desvios = np.array([0.03] * 140 + [0.04] * 117)
    return lineas, desvios


print("capítulos perfectamente correlacionados (mismo roster, mismo shock): "
      "P_todo == min_k P_k, NO el producto")
lin, dv = _roster_referencia()
caps_iguales = {
    "I": {"lineas": lin, "desvios": dv, "tipo_mayoria": "ABSOLUTA", "camara": "diputados", "n_articulos": 10},
    "II": {"lineas": lin, "desvios": dv, "tipo_mayoria": "ABSOLUTA", "camara": "diputados", "n_articulos": 5},
    "III": {"lineas": lin, "desvios": dv, "tipo_mayoria": "ABSOLUTA", "camara": "diputados", "n_articulos": 20},
}
r_iguales = C.simular_capitulos(caps_iguales, n_sims=20000, seed=1, epsilon0=0.02, tau=1.2)
check(abs(r_iguales["P_todo"] - r_iguales["min_P_k"]) < 0.01,
      f"capítulos idénticos: P_todo={r_iguales['P_todo']:.4f} tiene que ser "
      f"~= min_P_k={r_iguales['min_P_k']:.4f}")
producto_ingenuo = 1.0
for k in r_iguales["P_por_capitulo"]:
    producto_ingenuo *= r_iguales["P_por_capitulo"][k]
check(r_iguales["P_todo"] > producto_ingenuo * 1.3,
      f"P_todo real ({r_iguales['P_todo']:.4f}) tiene que ser MUCHO mayor que el "
      f"producto ingenuo bajo independencia falsa ({producto_ingenuo:.4f})")
print(f"  OK P_todo={r_iguales['P_todo']:.4f}  min_P_k={r_iguales['min_P_k']:.4f}  "
     f"producto_ingenuo={producto_ingenuo:.4f}")


print("\nsin shock compartido (epsilon0=tau=0): rompe claro, no simula en silencio")
try:
    C.simular_capitulos(caps_iguales, n_sims=500, seed=1, epsilon0=0.0, tau=0.0)
    check(False, "tenía que levantar ValueError sin epsilon0/tau")
except ValueError:
    pass
print("  OK")


print("\ncapítulos DISTINTOS: P_algo >= P_todo y P_algo >= cualquier P_k (cotas lógicas)")
lin_bajo, dv_bajo = _roster(0.20)
lin_alto, dv_alto = _roster(0.90)
caps_dist = {
    "LABORAL": {"lineas": lin_bajo, "desvios": dv_bajo, "tipo_mayoria": "SIMPLE",
               "camara": "diputados", "n_articulos": 15},
    "ECON": {"lineas": lin_alto, "desvios": dv_alto, "tipo_mayoria": "SIMPLE",
            "camara": "diputados", "n_articulos": 8},
}
r_dist = C.simular_capitulos(caps_dist, n_sims=5000, seed=2, epsilon0=0.03, tau=1.0)
check(r_dist["P_algo"] >= r_dist["P_todo"] - 1e-9, "P_algo tiene que ser >= P_todo")
for k, p in r_dist["P_por_capitulo"].items():
    check(r_dist["P_algo"] >= p - 1e-9, f"P_algo tiene que ser >= P_{k}")
    check(r_dist["P_todo"] <= p + 1e-9, f"P_todo tiene que ser <= P_{k}")
print(f"  OK P_todo={r_dist['P_todo']:.4f}  P_algo={r_dist['P_algo']:.4f}  "
     f"P_por_capitulo={r_dist['P_por_capitulo']}")


print("\nE[supervivencia] pondera por n_articulos (caso determinístico)")
lin_pasa, dv_pasa = _roster(0.99)   # prácticamente siempre pasa
lin_cae, dv_cae = _roster(0.01)     # prácticamente nunca pasa
caps_pesos = {
    "GRANDE": {"lineas": lin_pasa, "desvios": dv_pasa, "tipo_mayoria": "SIMPLE",
              "camara": "diputados", "n_articulos": 90},
    "CHICO": {"lineas": lin_cae, "desvios": dv_cae, "tipo_mayoria": "SIMPLE",
             "camara": "diputados", "n_articulos": 10},
}
r_pesos = C.simular_capitulos(caps_pesos, n_sims=5000, seed=3, epsilon0=0.02, tau=0.3)
# el capítulo GRANDE (90 artículos) casi siempre pasa y el CHICO (10) casi nunca:
# la supervivencia esperada tiene que quedar cerca de 90/100 = 0.90, no de 0.50
check(0.75 < r_pesos["E_supervivencia"] < 0.99,
      f"E[supervivencia] ponderada por artículos tiene que acercarse a 0.90 "
      f"(90 de 100 artículos en el capítulo que casi siempre pasa): "
      f"{r_pesos['E_supervivencia']:.4f}")
print(f"  OK E[supervivencia]={r_pesos['E_supervivencia']:.4f} (esperado ~0.90)")


print("\ndeterminismo: mismo seed -> mismo resultado")
r_a = C.simular_capitulos(caps_dist, n_sims=2000, seed=7, epsilon0=0.03, tau=1.0)
r_b = C.simular_capitulos(caps_dist, n_sims=2000, seed=7, epsilon0=0.03, tau=1.0)
check(r_a["P_todo"] == r_b["P_todo"] and r_a["P_algo"] == r_b["P_algo"],
      "mismo seed tiene que dar EXACTAMENTE el mismo resultado")
print("  OK")


print("\nsin capítulos: rompe claro")
try:
    C.simular_capitulos({}, epsilon0=0.02)
    check(False, "tenía que levantar ValueError con capitulos vacío")
except ValueError:
    pass
print("  OK")


print("\ncapítulo sin un campo obligatorio: rompe claro, con el nombre del campo")
try:
    C.simular_capitulos({"I": {"lineas": lin, "desvios": dv, "tipo_mayoria": "SIMPLE"}},
                        epsilon0=0.02)
    check(False, "tenía que levantar KeyError sin 'camara'")
except KeyError as e:
    check("camara" in str(e), f"el error tiene que nombrar el campo faltante: {e}")
print("  OK")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
