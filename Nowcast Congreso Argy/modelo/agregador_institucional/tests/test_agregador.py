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

# --- modo asistencia: p_presente escala la emisión ---
li = np.array(["AFIRMATIVO"] * 200); dv = np.zeros(200)
full = ag.simular_votacion(li, dv, "SIMPLE", "diputados", n_sims=800, seed=1, p_presente=np.ones(200))
half = ag.simular_votacion(li, dv, "SIMPLE", "diputados", n_sims=800, seed=1, p_presente=np.full(200, 0.5))
check(full["afirm_medio"] > 195, "presentismo 1.0 -> casi todos emiten (~200)")
check(90 < half["afirm_medio"] < 110, f"presentismo 0.5 -> ~mitad emite (fue {half['afirm_medio']:.0f})")

# --- el arreglo del sesgo: bloque con ausentismo mayoritario cuyos presentes votan SÍ ---
rows = ([("acta:x", "A", f"leg:a{i}", "AFIRMATIVO") for i in range(70)] +
        [("acta:x", "A", f"leg:a{200+i}", "AUSENTE") for i in range(80)] +
        [("acta:x", "B", f"leg:b{i}", "NEGATIVO") for i in range(60)] +
        [("acta:x", "B", f"leg:b{200+i}", "AUSENTE") for i in range(47)])
import pandas as pd  # noqa: E402
vv = pd.DataFrame(rows, columns=["acta_id", "bloque_norm", "legislador_id", "voto"])
lv = ag._linea_bloque_por_acta(vv).set_index("bloque_norm")["linea"].to_dict()
dr = ag._direccion_bloque_por_acta(vv).set_index("bloque_norm")["linea"].to_dict()
check(lv["A"] == "NO_ACOMPANA", "línea VIEJA cuenta ausentes -> bloque A 'no acompaña' (el bug)")
check(dr["A"] == "AFIRMATIVO", "DIRECCIÓN nueva entre presentes -> bloque A 'afirmativo'")
p_viejo = ag.simular_votacion(vv["bloque_norm"].map(lv).to_numpy(), np.zeros(len(vv)),
                              "SIMPLE", "diputados", n_sims=1200, seed=1)["p_aprobacion"]
pp = vv["bloque_norm"].map({"A": 70/150, "B": 60/107}).to_numpy(dtype=float)
p_nuevo = ag.simular_votacion(vv["bloque_norm"].map(dr).to_numpy(), np.zeros(len(vv)),
                              "SIMPLE", "diputados", n_sims=1200, seed=1, p_presente=pp)["p_aprobacion"]
check(p_viejo < 0.05, f"motor viejo: pesimista y equivocado (P={p_viejo:.2f}, real=aprueba)")
check(p_nuevo > p_viejo + 0.3, f"modo asistencia corrige el sesgo (P={p_nuevo:.2f} >> {p_viejo:.2f})")

# --- errores defensivos ---
try:
    ag.simular_votacion(np.array([]), np.array([]), "SIMPLE", "diputados")
    check(False, "roster vacío debe fallar")
except ValueError:
    check(True, "roster vacío lanza ValueError")
try:
    ag.simular_votacion(np.array(["AFIRMATIVO"] * 3), np.zeros(3), "SIMPLE", "diputados",
                        p_presente=np.ones(5))
    check(False, "p_presente de largo distinto debe fallar")
except ValueError:
    check(True, "p_presente mal dimensionado lanza ValueError")

print(f"OK — {ok} chequeos pasaron")
