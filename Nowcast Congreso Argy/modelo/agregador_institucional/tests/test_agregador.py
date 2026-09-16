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
# SIMPLE = MAS de la mitad de los emitidos (ADR-0013, 2026-08-22). Con `emitidos/2` un
# EMPATE aprobaba, porque la aprobacion se decide con `afirm >= umbral`.
check(ag.umbral_aprobacion("SIMPLE", 200, "diputados") == 101.0,
      "simple = mitad de los emitidos MAS UNO (101 sobre 200)")
check(ag.umbral_aprobacion("SIMPLE", 256, "diputados") == 129.0,
      "con 256 emitidos hacen falta 129: 128 contra 128 es empate y NO aprueba")
check(ag.umbral_aprobacion("SIMPLE", 251, "diputados") == 126.0,
      "con emitidos impares tambien: 126 sobre 251")
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


# --- el quórum y las abstenciones: BANDERA APAGADA (revisión 25-08) ---
# Lo que fija: que apagada NO mueva nada, que prendida cuente al que se abstiene, y
# que en ningún caso toque el conteo de votos (sólo el quórum).
_lin = np.array(["AFIRMATIVO"] * 140 + ["NEGATIVO"] * 117)
_dv = np.full(257, 0.05)

check(ag.QUORUM_CUENTA_ABSTENCIONES is False,
      "la bandera arranca APAGADA: sin QUORUM_ABSTENCIONES=1 el número publicado no cambia")

_base = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0)
_off = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0,
                           quorum_cuenta_abstenciones=False)
check(_base["p_aprobacion"] == _off["p_aprobacion"] and
      _base["afirm_medio"] == _off["afirm_medio"],
      "pedir explícitamente False tiene que dar exactamente lo mismo que el default")
check(_off["presentes_medio"] == _off["emitidos_medio"],
      "apagada, presentes == emitidos (que es el v1 que se está corrigiendo)")
check(_off["abstenciones_medio"] == 0.0, "apagada no cuenta abstenciones")
check(_off["quorum_cuenta_abstenciones"] is False, "y lo declara en la salida")

# SIN modelo de asistencia no hay ausentes: todo el roster está en el recinto
_on = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0,
                          quorum_cuenta_abstenciones=True)
check(_on["presentes_medio"] == 257.0,
      f"sin p_presente nadie falta: presentes = 257, dio {_on['presentes_medio']}")
check(_on["abstenciones_medio"] > 0, "y el desvío produce abstenciones que hacen quórum")
check(_on["afirm_medio"] == _off["afirm_medio"],
      "LA BANDERA NO TOCA LOS VOTOS: sólo el quórum. Si esto falla, mueve el conteo "
      f"y no es lo que dice hacer ({_on['afirm_medio']} vs {_off['afirm_medio']})")

# CON modelo de asistencia sí hay ausentes, y la abstención se separa de la ausencia
_pp = np.full(257, 0.55)
_a_off = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0,
                             p_presente=_pp)
_a_on = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0,
                            p_presente=_pp, quorum_cuenta_abstenciones=True)
check(_a_on["afirm_medio"] == _a_off["afirm_medio"],
      "tampoco en modo asistencia puede moverse el conteo de votos")
check(_a_off["emitidos_medio"] < _a_on["presentes_medio"] < 257.0,
      "los presentes están ENTRE los que emitieron y el roster entero: hay ausentes "
      f"de verdad ({_a_off['emitidos_medio']:.1f} < {_a_on['presentes_medio']:.1f} < 257)")
check(_a_on["sims_sin_quorum"] < _a_off["sims_sin_quorum"],
      "con presentismo 0,55 el quórum muerde menos al contar a los que se abstienen "
      f"({100*_a_on['sims_sin_quorum']:.1f}% vs {100*_a_off['sims_sin_quorum']:.1f}%)")
check(_a_on["p_aprobacion"] > _a_off["p_aprobacion"],
      "y por lo tanto la probabilidad sube, no baja")

# el caso donde HOY no cambia nada, que es el que explica por qué está apagada
_pp85 = np.full(257, 0.85)
_b_off = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0, p_presente=_pp85)
_b_on = ag.simular_votacion(_lin, _dv, "SIMPLE", "diputados", n_sims=2000, seed=0,
                            p_presente=_pp85, quorum_cuenta_abstenciones=True)
check(_b_off["p_aprobacion"] == _b_on["p_aprobacion"],
      "con presentismo realista (0,85) el quórum no muerde y prender la bandera no "
      "mueve NADA. Es el motivo por el que el bug es real y hoy es inerte")


# ─────────────────────────────────────────────────────────────────────────────
# epsilon0 + tau (§III.A.3, ADR-0025): incertidumbre a nivel LEGISLADOR,
# reemplaza el clip agregado. Apagado por defecto (epsilon0=0, tau=0).
# ─────────────────────────────────────────────────────────────────────────────
_lin_e = np.array(["AFIRMATIVO"] * 140 + ["NEGATIVO"] * 117)
_dv_e = np.array([0.03] * 140 + [0.04] * 117)

_e_default = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=3000, seed=0)
_e_off_explicito = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=3000,
                                       seed=0, epsilon0=0.0, tau=0.0)
check(_e_default == _e_off_explicito,
      "epsilon0=0,tau=0 explícito tiene que dar EXACTAMENTE lo mismo que omitirlos "
      "(mismo rng, ni un draw de más)")
check(_e_default["epsilon0_aplicado"] == 0.0 and _e_default["tau_aplicado"] == 0.0,
      "trazabilidad: apagado se reporta como 0.0, no se esconde")

_e_solo_eps = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=20000,
                                  seed=0, epsilon0=0.02, tau=0.0)
check(_e_solo_eps["p_aprobacion"] <= _e_default["p_aprobacion"],
      "epsilon0 solo (sin shock) no puede EMPEORAR la sobreconfianza, sólo achicarla "
      f"({_e_solo_eps['p_aprobacion']} vs {_e_default['p_aprobacion']})")

_e_shock = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=20000,
                               seed=0, epsilon0=0.02, tau=1.2)
check(_e_shock["afirm_std"] > _e_solo_eps["afirm_std"] * 3,
      "el shock compartido (tau) es lo que realmente dispersa la banda — epsilon0 solo "
      f"no alcanza ({_e_solo_eps['afirm_std']:.2f} vs {_e_shock['afirm_std']:.2f})")
check(_e_shock["p_aprobacion"] < 0.9,
      "con tau real (1.2) una mayoría holgada dos-tercios-de-confianza deja de ser "
      f"99%+: {_e_shock['p_aprobacion']}")
check(_e_shock["epsilon0_aplicado"] == 0.02 and _e_shock["tau_aplicado"] == 1.2,
      "trazabilidad: prendido se reporta con los valores reales aplicados")

_e_shock2 = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=20000,
                                seed=0, epsilon0=0.02, tau=1.2)
check(_e_shock["p_aprobacion"] == _e_shock2["p_aprobacion"],
      "mismo seed + mismos epsilon0/tau -> mismo resultado (determinismo)")

# el shock no puede escapar el mecanismo de presencia: se sigue pudiendo separar
# abstención de ausencia con la bandera de quórum, ahora con la matriz por-simulación
_e_asist = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=3000, seed=0,
                               p_presente=np.full(257, 0.8), epsilon0=0.02, tau=1.0,
                               quorum_cuenta_abstenciones=True)
check(0.0 <= _e_asist["p_aprobacion"] <= 1.0 and _e_asist["presentes_medio"] > 0,
      "shock + modo asistencia + abstenciones no rompe y da un resultado sensato")

# un roster con P_i pegado a 0 o 1 exactos no puede romper el logit (clip interno)
_lin_ext = np.array(["AFIRMATIVO"] * 257)
_dv_ext = np.zeros(257)  # desvio 0 -> P(afirm) = 1.0 exacto antes del clip interno
try:
    _e_ext = ag.simular_votacion(_lin_ext, _dv_ext, "ABSOLUTA", "diputados", n_sims=500,
                                 seed=0, epsilon0=0.0, tau=1.0)
    check(0.0 <= _e_ext["p_aprobacion"] <= 1.0, "P_i=1.0 exacto con tau>0 no rompe el logit")
except (ZeroDivisionError, FloatingPointError, ValueError) as e:
    check(False, f"P_i=1.0 exacto con tau>0 rompió: {type(e).__name__}: {e}")

# devolver_crudo (FASE 2, PROMPT-MULTITEMA-V2.md): trae el array crudo por-simulación,
# y NO cambia el resumen agregado (mismo p_aprobacion con o sin el flag).
_sin_crudo = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=2000,
                                 seed=3, epsilon0=0.02, tau=1.0)
_con_crudo = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=2000,
                                 seed=3, epsilon0=0.02, tau=1.0, devolver_crudo=True)
check("aprob_por_sim" not in _sin_crudo, "sin el flag, no viene el array crudo")
check("aprob_por_sim" in _con_crudo and "afirm_por_sim" in _con_crudo,
      "con el flag, vienen los dos arrays crudos")
check(len(_con_crudo["aprob_por_sim"]) == 2000 == len(_con_crudo["afirm_por_sim"]),
      "un valor por simulación")
check(_con_crudo["aprob_por_sim"].mean() == _sin_crudo["p_aprobacion"],
      "el array crudo promedia EXACTO al p_aprobacion agregado")

# el mismo seed + mismos n_sims + epsilon0/tau>0 en las DOS llamadas dibuja el MISMO
# eta_j (primer draw del rng) aunque lineas/desvios sean distintos entre las dos
# llamadas -- es la propiedad que hace posible "componer capítulos": simular cada
# capítulo por separado y combinar sus aprob_por_sim sim a sim, sin volver a simular.
_lin_otro = np.array(["NEGATIVO"] * 257)  # roster totalmente distinto al de _lin_e
_dv_otro = np.full(257, 0.3)
_r1 = ag.simular_votacion(_lin_e, _dv_e, "ABSOLUTA", "diputados", n_sims=5000,
                          seed=11, epsilon0=0.02, tau=1.0, devolver_crudo=True)
_r2 = ag.simular_votacion(_lin_otro, _dv_otro, "ABSOLUTA", "diputados", n_sims=5000,
                          seed=11, epsilon0=0.02, tau=1.0, devolver_crudo=True)
# si comparten eta_j, los momentos en que el shock "sube" tienen que coincidir en las
# dos corridas: un eta_j alto empuja a AMBOS rosters hacia más afirmativos a la vez
# (con tau grande, el shock domina sobre la línea de cada uno) -> afirm_por_sim de las
# dos corridas tiene que correlacionar POSITIVO y fuerte, que es lo que NO pasaría con
# eta independientes entre las dos llamadas.
_corr = float(np.corrcoef(_r1["afirm_por_sim"], _r2["afirm_por_sim"])[0, 1])
check(_corr > 0.5, f"con el mismo seed, dos corridas con rosters distintos tienen que "
                   f"correlacionar por compartir eta_j: corr={_corr:.3f}")

print(f"OK — {ok} chequeos pasaron")
