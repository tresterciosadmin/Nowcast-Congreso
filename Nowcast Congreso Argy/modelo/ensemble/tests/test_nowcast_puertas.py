# -*- coding: utf-8 -*-
"""Tests del punto de entrada por puertas. Offline: no toca la canónica ni el padrón.

Cubre los seis defectos que salieron de la auditoría del 22-08-2026, y cada bloque
falla con el código anterior a su arreglo:

  1. El número del bloque se redondeaba a SÍ/NO en 0,5. La Coalición Cívica, que
     acompaña el 60,9% de las veces, salía 0,967; Peronismo Federal salía 1,000
     EXACTO. Era la razón de que todas las votaciones dieran 99%.
  2. La DIRECCIÓN salía siempre del linaje y sólo el desvío era individual. Como el
     desvío se mide contra el bloque REAL, quien está en un bloque chico dentro de un
     linaje-bolsa se llevaba lo peor de los dos (De la Sota: P=1,00, récord 0,17).
  3. El récord miraba el futuro: sin tope de fecha.
  4. Faltar se leía como votar en contra (denominador = todas las votaciones).
  5. El tablero y la probabilidad salían de cálculos distintos.
  6. La banda de afirmativos se rellenaba con la media si faltaba un percentil.

    python modelo/ensemble/tests/test_nowcast_puertas.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from nowcast_puertas import (  # noqa: E402
    DESVIO_BISAGRA,
    INCERTIDUMBRE_INCOGNITA,
    MIN_HIST_INDIVIDUAL,
    PRESENCIA_MINIMA,
    REPARTO_DESVIO,
    _tablero_camara,
    a_linea_y_desvio,
    alineacion_individual,
    armar_roster,
    perfil_legislador,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ── 1. el número del bloque NO se redondea ──────────────────────────────────
print("1. la duda del bloque no se tira en el redondeo")
cc = perfil_legislador(0.609, 0.033)          # Coalición Cívica, caso real
check(0.55 <= cc["p_afirma_si_vota"] <= 0.65,
      f"un bloque que acompaña el 61% no da 97% (dio {cc['p_afirma_si_vota']:.3f})")
pf = perfil_legislador(0.985, 0.000)          # Peronismo Federal, desvío 0
check(pf["p_afirma_si_vota"] < 1.0,
      f"desvío 0 ya NO da certeza absoluta (dio {pf['p_afirma_si_vota']:.4f})")
check(abs(pf["p_afirma_si_vota"] - 0.985) < 1e-9,
      "con desvío 0, la P es exactamente la del bloque")
k = perfil_legislador(0.224, 0.009)           # kirchnerismo
check(0.20 <= k["p_afirma_si_vota"] <= 0.25,
      f"un bloque que acompaña el 22% no da 0,4% (dio {k['p_afirma_si_vota']:.3f})")
# monotonía: más share, más P
check(perfil_legislador(0.8, 0.05)["p_afirma_si_vota"]
      > perfil_legislador(0.6, 0.05)["p_afirma_si_vota"], "más share -> más P")
# el desvío acerca a la mitad, no aleja
lejos = perfil_legislador(0.95, 0.00)["p_afirma_si_vota"]
cerca = perfil_legislador(0.95, 0.40)["p_afirma_si_vota"]
check(abs(cerca - 0.5) < abs(lejos - 0.5), "más desvío -> más cerca de 50/50")

print("\n   la traducción al agregador conserva P exacto")
# Se verifica contra el AGREGADOR de verdad, no contra la fórmula copiada a mano:
# si su reparto cambia, este test tiene que enterarse.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] /
                       "modelo" / "agregador_institucional" / "src"))
from agregador import CONDUCTAS, _prob_conductas  # noqa: E402
i_af = list(CONDUCTAS).index("AFIRMATIVO")
i_na = list(CONDUCTAS).index("NO_ACOMPANA")
for p in (0.05, 0.35, 0.5, 0.61, 0.985):
    linea, d = a_linea_y_desvio(p)
    probs = _prob_conductas(linea, d, REPARTO_DESVIO)
    check(abs(probs[i_af] - p) < 1e-9,
          f"(linea,desvío) reproduce P={p} en el agregador (dio {probs[i_af]:.6f})")
    check(probs[i_na] < 1e-9,
          f"y NO inventa abstenciones en P={p} (dio {probs[i_na]:.4f}) — con el reparto "
          "por defecto el umbral de mayoría caía a 112 sobre 257")


# ── 2. la dirección puede salir del historial propio ────────────────────────
print("\n2. con historial propio suficiente, manda el historial")
# De la Sota: linaje-bolsa que acompaña mucho, ella no, y no se desvía de SU bloque
sin = perfil_legislador(0.889, 0.000)
con = perfil_legislador(0.889, 0.000, record=0.17, n_emitidos=145)
check(sin["p_afirma_si_vota"] > 0.85, "sin historial hereda el linaje (0,89)")
check(abs(con["p_afirma_si_vota"] - 0.17) < 1e-9,
      f"con historial manda el suyo (dio {con['p_afirma_si_vota']:.3f}) — antes daba 1,00")
check(con["fuente_direccion"] == "record_individual" and sin["fuente_direccion"] == "bloque",
      "y la salida dice de dónde salió la dirección")
poco = perfil_legislador(0.889, 0.000, record=0.17, n_emitidos=MIN_HIST_INDIVIDUAL - 1)
check(poco["fuente_direccion"] == "bloque",
      "con poca historia NO se le hace caso: un novato hereda a su bloque")


# ── 3. el récord no mira el futuro ──────────────────────────────────────────
print("\n3. el récord es walk-forward")
votos = pd.DataFrame({
    "fecha": pd.to_datetime(["2024-03-01", "2024-03-01", "2025-09-01", "2025-09-01"]),
    "acta_id": ["a1", "a1", "a2", "a2"],
    "camara": ["diputados"] * 4,
    "legislador_id": ["x", "y", "x", "y"],
    "conducta": ["AFIRMATIVO", "NEGATIVO", "NEGATIVO", "AFIRMATIVO"],
})
om = {"a1": "EJECUTIVO", "a2": "EJECUTIVO"}
todo = alineacion_individual(votos, om, "EJECUTIVO", era_desde="2020-01-01")
corte = alineacion_individual(votos, om, "EJECUTIVO", era_desde="2020-01-01",
                              hasta="2024-12-31")
check(todo[("diputados", "x")][0] == 0.5, "sin corte, x mezcla los dos años")
check(corte[("diputados", "x")][0] == 1.0,
      f"con corte a 2024, x sólo trae lo de 2024 (dio {corte[('diputados','x')][0]}) "
      "— sin la guarda, el récord de un nowcast de 2024 usaba votos de 2026")
check(corte[("diputados", "x")][1] == 1, "y el n también se corta")


# ── 4. faltar no es votar en contra ─────────────────────────────────────────
print("\n4. faltar no es votar en contra")
v2 = pd.DataFrame({
    "fecha": pd.to_datetime(["2024-01-01"] * 8),
    "acta_id": ["a1"] * 8, "camara": ["diputados"] * 8,
    "legislador_id": ["pres"] * 4 + ["fiel"] * 4,
    "conducta": ["AUSENTE", "AUSENTE", "AUSENTE", "AFIRMATIVO",
                 "AFIRMATIVO", "AFIRMATIVO", "AFIRMATIVO", "AFIRMATIVO"],
})
r = alineacion_individual(v2, {"a1": "EJECUTIVO"}, None, era_desde="2020-01-01")
p_pres, n_pres, presencia_pres, n_emit_pres = r[("diputados", "pres")]
check(p_pres == 1.0,
      f"quien votó una vez y acompañó, da 1,00 de dirección (dio {p_pres}) "
      "— antes daba 0,25 y se leía EN CONTRA")
check(presencia_pres == 0.25, "y su presencia queda en 0,25, aparte")
check(n_emit_pres == 1, "se cuentan los votos EMITIDOS, no las oportunidades")


# ── 5. tablero y probabilidad, del mismo cálculo ────────────────────────────
print("\n5. el tablero sale de lo mismo que el número")
BLOQ = [{"bloque": "LIN_A", "linea": "AFIRMATIVO", "desvio": 0.05, "_share_afirm": 0.90},
        {"bloque": "LIN_B", "linea": "NEGATIVO", "desvio": 0.05, "_share_afirm": 0.10}]


def fila(lid, linaje="LIN_A", desvio=0.05):
    return {"legislador_id": lid, "legislador": lid.upper(), "bloque_linaje": linaje,
            "linea": "AFIRMATIVO", "desvio": desvio, "desvio_de": "ficha_reciente"}


det = {"filas": [fila("a"), fila("b", "LIN_B"), fila("c", "LIN_A", 0.45),
                 fila("pres")], "padron": "test"}
ind = {("diputados", "pres"): (0.96, 150, 0.01, 2)}   # preside: casi nunca vota
lin, des, pre, perf = armar_roster("diputados", BLOQ, ind, det)
check(len(lin) == len(des) == len(pre) == len(perf) == 4, "arrays alineados")
check(pre[3] == 0.01, "la presencia del que no vota viaja al agregador")

SIM = {"afirm_medio": 140.0, "afirm_p5": 133.0, "afirm_p95": 147.0, "umbral_medio": 125.5}
tab = _tablero_camara("diputados", "2026-06-01", perf, SIM, det)
post = {x["legislador_id"]: x["postura"] for x in tab["legisladores"]}
check(post["pres"] == "no_vota",
      f"quien casi nunca vota se marca NO VOTA (dio {post['pres']}) — antes sumaba un voto entero")
check(tab["conteo"]["no_vota"] == 1, "y se cuenta aparte")
check(tab["afirmativos_esperados"] == 140.0, "los afirmativos salen del simulador")
otra = _tablero_camara("diputados", "2026-06-01", perf, {**SIM, "afirm_medio": 99.0}, det)
check(otra["afirmativos_esperados"] == 99.0 and otra["conteo"] == tab["conteo"],
      "cambiar la simulación cambia el número y NO la clasificación: una sola fuente")
check(all(x["legislador_id"] != "pres" for x in tab["a_negociar"]),
      "y a quien no vota no se lo manda a negociar")

print("\n   INCÓGNITA es estar cerca de 50/50, no sólo tener desvío alto")
det2 = {"filas": [fila("dudoso")], "padron": "test"}
ind2 = {("diputados", "dudoso"): (0.52, 150, 1.0, 150)}
_, _, _, perf2 = armar_roster("diputados", BLOQ, ind2, det2)
t2 = _tablero_camara("diputados", "2026-06-01", perf2, SIM, det2)
check(t2["legisladores"][0]["postura"] == "incognita",
      "P=0,52 con desvío bajo es INCÓGNITA (antes sólo miraba el desvío)")
check(INCERTIDUMBRE_INCOGNITA < 0.5 and PRESENCIA_MINIMA > 0 and DESVIO_BISAGRA > 0,
      "los tres umbrales están declarados y son parámetros")


# ── 6. la banda no se inventa ───────────────────────────────────────────────
print("\n6. la banda no se inventa")
try:
    _tablero_camara("diputados", "2026-06-01", perf,
                    {"afirm_medio": 1.0, "umbral_medio": 1.0}, det)
    check(False, "sin percentiles tiene que romper, no rellenar con la media")
except KeyError:
    check(True, "sin percentiles rompe")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
