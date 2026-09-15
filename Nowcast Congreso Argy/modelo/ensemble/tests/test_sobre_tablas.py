# -*- coding: utf-8 -*-
"""Tests de `sobre_tablas.py` — el sobre tablas como votación (S:III.A.5).

Offline salvo los que leen `outputs/theta_sobre_tablas.json` (la estimación real
del 03-09): esos se saltean solos si el archivo no está en disco.

    python modelo/ensemble/tests/test_sobre_tablas.py
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import sobre_tablas as st  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ── la bandera nace apagada ──────────────────────────────────────────────────
print("1. SOBRE_TABLAS apagada por defecto")
check(os.environ.get("SOBRE_TABLAS", "0") != "0" or not st.SOBRE_TABLAS,
      "sin SOBRE_TABLAS=1 en el entorno, la bandera tiene que estar apagada")
check(os.environ.get("SOBRE_TABLAS", "0") == "0" or st.SOBRE_TABLAS,
      "con SOBRE_TABLAS=1 en el entorno, la bandera tiene que estar prendida")

# ── es_admisible: C_c, sólo `sin_dictamen` confirmado la apaga ──────────────
print("\n2. es_admisible (C_c) — sólo `sin_dictamen` bloquea la vía normal")
check(st.es_admisible({"estado": "con_caracter"}) is True,
      "con dictamen leído -> admisible")
check(st.es_admisible({"estado": "sin_dato"}) is True,
      "sin dato (no se sabe) -> admisible, elección conservadora")
check(st.es_admisible({"estado": "sin_dictamen"}) is False,
      "sin dictamen CONFIRMADO -> no admisible, toma la vía sobre tablas")

# ── logit/sigmoide: inversas exactas ─────────────────────────────────────────
print("\n3. logit y sigmoide son inversas")
for p in (0.01, 0.2, 0.5, 0.8, 0.99):
    ida_vuelta = st._sigmoide(st._logit(p))
    check(abs(ida_vuelta - p) < 1e-6, f"logit/sigmoide no invierten para p={p}")

# ── p_afirma_tablas: sin theta (0.0) no toca nada ────────────────────────────
print("\n4. p_afirma_tablas sin corrimiento (theta=0) es identidad")
check(st.p_afirma_tablas(0.73, "camara_sin_estimacion") == 0.73,
      "cámara sin theta estimado -> p_afirma sin tocar")

# ── p_afirma_tablas: con theta negativo, la P baja ───────────────────────────
print("\n5. p_afirma_tablas con theta negativo (Diputados) BAJA la P")
th_neg = -2.0
p0 = 0.80
p1 = st._sigmoide(st._logit(p0) + th_neg)
check(p1 < p0, "un theta negativo tiene que bajar P(afirmativo)")
check(abs(st._logit(p1) - (st._logit(p0) + th_neg)) < 1e-9,
      "el corrimiento tiene que ser exactamente theta, en logit")

# ── theta_de: si hay estimación real en disco, Diputados != 0 y Senado == 0 ──
print("\n6. theta_de contra la estimación real (si está en disco)")
if st.SALIDA.exists():
    th_dip = st.theta_de("diputados")
    th_sen = st.theta_de("senado")
    check(th_dip < 0,
          f"Diputados: theta significativo (p<0,05 el 03-09) tiene que ser < 0 (dio {th_dip})")
    check(th_sen == 0.0,
          f"Senado: theta NO significativo (p=0,157 el 03-09) tiene que entrar en 0 (dio {th_sen})")
    check(st.p_afirma_tablas(0.9, "senado") == 0.9,
          "Senado sin theta -> p_afirma_tablas es identidad")
else:
    print("  (salteado: no está outputs/theta_sobre_tablas.json)")

# ── theta_de: cámara desconocida no rompe, devuelve 0 ────────────────────────
print("\n7. cámara sin estimación no rompe")
check(st.theta_de("camara_que_no_existe") == 0.0,
      "cámara sin theta estimado -> 0.0, no KeyError")

print(f"\n{'='*60}")
print(f"{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    raise SystemExit(1)
