"""Tests de las GUARDAS CONTRA LA SOBRECONFIANZA, compartidas por B y por D.

Por qué existe este archivo (2026-08-22, Tarea 1 — una sola formulación):
las dos guardas que pidió Valle el 14-08 —piso de desvío por legislador y techo/piso
de confianza, «ninguna votación es 0%/100%»— vivían SÓLO dentro de
`ensemble.nowcast_proyecto`, o sea sólo en el camino de la formulación v1.
`puerta_d.p_voto_revisora` tomaba `p_aprobacion` cruda y `casos/` tenía su propia
copia del clamp. Al dar de baja v1, la producción se quedaba sin techo de confianza
justo en la puerta que sobrevive, y nada lo iba a avisar: el número seguía saliendo.

Estos tests FALLAN con el código anterior al 22-08 (D devolvía 1.0 exacto).

    python modelo/ensemble/tests/test_guardas_confianza.py
    python -m pytest modelo/ensemble/tests/test_guardas_confianza.py -q
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ensemble import (  # noqa: E402
    DESVIO_MIN_INDIVIDUAL,
    P_INCERTIDUMBRE,
    simular_con_guardas,
)
from puerta_d import p_voto_revisora  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# Roster unánime: sin guardas, el agregador da 1.0 EXACTO. Es el caso que destapa
# la ausencia del clamp, porque no hay ruido que lo disimule.
LINEAS_UNANIMES = np.array(["AFIRMATIVO"] * 12)
DESVIOS_CERO = np.zeros(12)


# ───────────── la guarda existe y acota ─────────────
print("simular_con_guardas: el techo de confianza")

sim = simular_con_guardas(LINEAS_UNANIMES, DESVIOS_CERO, "SIMPLE", "diputados",
                          n_sims=200, desvio_min=0.0)
check(sim["p_aprobacion_cruda"] == 1.0,
      "sin piso de desvío el agregador da 1.0 exacto (el caso que destapa el hueco)")
check(sim["p_aprobacion"] == 1.0 - P_INCERTIDUMBRE,
      f"el clamp la baja a 1-ε (dio {sim['p_aprobacion']})")
check(sim["p_aprobacion"] < 1.0, "nunca 100%")

# el mismo caso al revés: unanimidad en contra no puede dar 0%
sim_no = simular_con_guardas(np.array(["NEGATIVO"] * 12), DESVIOS_CERO,
                             "SIMPLE", "diputados", n_sims=200, desvio_min=0.0)
check(sim_no["p_aprobacion_cruda"] == 0.0, "unanimidad en contra da 0.0 crudo")
check(sim_no["p_aprobacion"] == P_INCERTIDUMBRE, "el clamp la sube a ε: nunca 0%")


print("\nsimular_con_guardas: el piso de desvío")
sim_piso = simular_con_guardas(LINEAS_UNANIMES, DESVIOS_CERO, "SIMPLE", "diputados",
                               n_sims=200)
check(sim_piso["desvio_min_aplicado"] == DESVIO_MIN_INDIVIDUAL,
      "el piso de desvío queda registrado en la salida")
check(sim_piso["p_aprobacion_cruda"] < 1.0,
      "con el piso puesto, ni un roster unánime da 1.0 crudo")

# apagar las dos guardas devuelve el comportamiento crudo: son opt-out, no un camino aparte
sim_crudo = simular_con_guardas(LINEAS_UNANIMES, DESVIOS_CERO, "SIMPLE", "diputados",
                                n_sims=200, desvio_min=0.0, p_incertidumbre=0.0)
check(sim_crudo["p_aprobacion"] == sim_crudo["p_aprobacion_cruda"] == 1.0,
      "con las guardas en 0 se recupera el agregador crudo (opt-out exacto)")


# ───────────── la trazabilidad: el clamp no puede ser invisible ─────────────
print("\nel clamp deja rastro")
check("p_aprobacion_cruda" in sim and "p_incertidumbre_aplicada" in sim,
      "la salida dice qué se aplicó, no sólo el número acotado")


# ───────────── D usa la MISMA guarda que B (esto fallaba antes) ─────────────
print("\nla Puerta D hereda las guardas (FALLA con el código anterior al 22-08)")


def padron_falso(path: Path) -> None:
    filas = ["legislador,clave,legislador_id,camara,distrito,bloque,bloque_norm,"
             "desde,hasta,bloque_linaje,fuente,nota"]
    for i in range(10):
        filas.append(f"AF {i},AF{i},leg:af{i},senado,X,BLOQUE_AF,BLOQUE_AF,"
                     f"2017-12-10,2023-12-09,LINAJE_AF,test,")
    path.write_text("\n".join(filas) + "\n", encoding="utf-8-sig")


# Todo el roster con la misma línea y desvío 0: antes esto daba p0 = 1.0 EXACTO.
bloques_unanimes = [{"bloque": "LINAJE_AF", "linea": "AFIRMATIVO", "desvio": 0.0}]

with tempfile.TemporaryDirectory() as td:
    pf = Path(td) / "padron_senado_historico.csv"
    padron_falso(pf)
    r = p_voto_revisora("Diputados", "2019-06-01", bloques_unanimes,
                        padron_file=str(pf), disciplina_path="/no/existe",
                        n_sims=300, seed=1)
    check(r["p_aprobacion"] < 1.0,
          f"D nunca devuelve 100% (dio {r['p_aprobacion']}) — ANTES daba 1.0")
    check(r["p_aprobacion"] <= 1.0 - P_INCERTIDUMBRE,
          "D respeta el mismo techo 1-ε que B")
    check(r["guardas"]["desvio_min"] == DESVIO_MIN_INDIVIDUAL,
          "D aplica el mismo piso de desvío que B")
    check("p0_cruda" in r, "D reporta también el valor sin acotar")


# ───────────── una sola definición, no tres ─────────────
print("\nuna sola definición de las guardas en todo el repo")
raiz = Path(__file__).resolve().parents[3]
propias = []
for py in raiz.rglob("*.py"):
    partes = set(py.parts)
    if "Archivos_Borrar" in partes or "__pycache__" in partes or "tests" in partes:
        continue
    txt = py.read_text(encoding="utf-8", errors="ignore")
    if "P_INCERTIDUMBRE = " in txt or "DESVIO_MIN_INDIVIDUAL = " in txt:
        propias.append(py.relative_to(raiz).as_posix())
check(propias == ["modelo/ensemble/src/ensemble.py"],
      f"las guardas se DEFINEN en un solo archivo (encontré: {propias})")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
