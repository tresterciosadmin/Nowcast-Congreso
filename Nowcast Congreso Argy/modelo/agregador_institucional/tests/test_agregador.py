"""Tests del motor de agregación — sin datos externos (rosters sintéticos)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import agregador as ag  # noqa: E402

ok = 0


def check(cond, msg):
    global ok
    assert cond, "FALLA: " + msg
    ok += 1


# --- normalización de mayorías ---
check(ag.normalizar_mayoria(None) == "SIMPLE", "None -> SIMPLE")
check(ag.normalizar_mayoria("Dos tercios") == "DOS_TERCIOS", "dos tercios")
check(ag.normalizar_mayoria("Dos tercios de los presentes en el cuerpo") == "DOS_TERCIOS_CUERPO", "cuerpo")
check(ag.normalizar_mayoria("Absoluta") == "ABSOLUTA", "absoluta")
check(ag.normalizar_mayoria("Tres cuartos") == "TRES_CUARTOS", "tres cuartos")

# --- umbrales ---
check(ag.umbral_aprobacion("SIMPLE", 200, "diputados") == 100.0, "simple = emitidos/2")
check(ag.umbral_aprobacion("ABSOLUTA", 200, "diputados") == 129.0, "absoluta dip = 129")
check(ag.umbral_aprobacion("ABSOLUTA", 60, "senado") == 37.0, "absoluta sen = 37")
check(ag.umbral_aprobacion("DOS_TERCIOS", 90, "diputados") == 60.0, "2/3 de 90 = 60")

# --- probabilidades por conducta ---
p = ag._prob_conductas("AFIRMATIVO", 0.0)
check(abs(p[0] - 1.0) < 1e-9, "desvío 0 y línea afirm -> p(afirm)=1")
p = ag._prob_conductas("AFIRMATIVO", 0.2)
check(abs(p[0] - 0.8) < 1e-9 and abs(p[1] - 0.1) < 1e-9 and abs(p[2] - 0.1) < 1e-9, "desvío 0.2 reparte 0.1/0.1")
check(abs(p.sum() - 1.0) < 1e-9, "probabilidades suman 1")

# --- simulación: bloque unánime y disciplinado aprueba con certeza ---
n = 150
lineas = np.array(["AFIRMATIVO"] * n)
desvios = np.zeros(n)
r = ag.simular_votacion(lineas, desvios, "SIMPLE", "diputados", n_sims=200, seed=1)
check(r["p_aprobacion"] == 1.0, "150 afirmativos disciplinados -> P=1")
check(r["afirm_medio"] == 150.0, "afirm medio = 150")

# --- rechazo unánime: P=0 ---
lineas = np.array(["NEGATIVO"] * n)
r = ag.simular_votacion(lineas, desvios, "SIMPLE", "diputados", n_sims=200, seed=1)
check(r["p_aprobacion"] == 0.0, "150 negativos -> P=0")

# --- votación al filo: mitad afirm / mitad neg, con desvío -> P intermedia y banda ancha ---
# (roster ~realista: 250 escaños, alcanza el quórum de 129 de Diputados)
lineas = np.array(["AFIRMATIVO"] * 125 + ["NEGATIVO"] * 125)
desvios = np.full(250, 0.15)
r = ag.simular_votacion(lineas, desvios, "SIMPLE", "diputados", n_sims=1000, seed=2)
check(0.2 < r["p_aprobacion"] < 0.8, f"votación al filo -> P intermedia (fue {r['p_aprobacion']})")
check(r["afirm_std"] > 2.0, "al filo la banda no es degenerada (std>2)")

# --- mayoría agravada endurece: mismos afirmativos, 2/3 baja la P ---
lineas = np.array(["AFIRMATIVO"] * 140 + ["NEGATIVO"] * 100)
desvios = np.full(240, 0.05)
simple = ag.simular_votacion(lineas, desvios, "SIMPLE", "diputados", n_sims=500, seed=3)
dost = ag.simular_votacion(lineas, desvios, "DOS_TERCIOS", "diputados", n_sims=500, seed=3)
check(simple["p_aprobacion"] >= dost["p_aprobacion"], "2/3 nunca aprueba más fácil que simple")

# --- errores defensivos ---
try:
    ag.simular_votacion(np.array([]), np.array([]), "SIMPLE", "diputados")
    check(False, "roster vacío debe fallar")
except ValueError:
    check(True, "roster vacío lanza ValueError")

print(f"OK — {ok} chequeos pasaron")
