# -*- coding: utf-8 -*-
"""Tests de `beta_dictamen.py` — el dictamen por legislador (ADR-0016, S:III.A.2).

Desde el 14-09-2026 NO lleva el carácter del dictamen (M6, no M5): un backtest
walk-forward mostró que ese término no generaliza (ver el docstring del módulo
y `validar_beta_dictamen_walkforward.py`). Sólo F_i y lealtad_x_jefe.

Offline salvo los que dicen "requiere datos": esos leen los parquets de firmas
reales (contexto_de) y se saltean solos si no están en disco.

    python modelo/ensemble/tests/test_beta_dictamen.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import beta_dictamen as bd  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


COEF = {"F_i": 1.5444, "lealtad_x_jefe": 1.2943}

# ── sin contexto o sin coeficientes, delta es siempre 0 ─────────────────────
print("1. sin dictamen (contexto None) o sin coeficientes, el delta es 0")
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, None, COEF) == 0.0,
      "contexto None -> 0")
ctx_vacio = {"firmantes": frozenset(), "lin_jefe": frozenset()}
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, ctx_vacio, COEF) == 0.0,
      "sin firmantes ni jefe firmante -> 0 (proyecto hipotético / sin dato)")
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, ctx_vacio, {}) == 0.0,
      "sin coeficientes (archivo ausente o mal estimado) -> 0")

# ── F_i y lealtad_x_jefe entran como se documentan ───────────────────────────
print("\n2. F_i y lealtad-por-jefe se suman en logit")
ctx = {"firmantes": frozenset({"leg:firma"}), "lin_jefe": frozenset({"LIN_JEFE"})}
check(bd.delta_legislador("OTRO_LINAJE", "leg:nadie", 0.20, ctx, COEF) == 0.0,
      "sin firmar y sin jefe firmante -> 0 (ya no hay término de carácter)")
con_firma = bd.delta_legislador("OTRO_LINAJE", "leg:firma", 0.20, ctx, COEF)
check(abs(con_firma - COEF["F_i"]) < 1e-9,
      f"F_i suma su coeficiente completo (dio {con_firma}, esperaba {COEF['F_i']})")
con_jefe = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.20, ctx, COEF)
esperado_jefe = COEF["lealtad_x_jefe"] * (1 - 0.20)
check(abs(con_jefe - esperado_jefe) < 1e-9,
      f"jefe firmante entra filtrado por (1-desvío) (dio {con_jefe}, esperaba {esperado_jefe})")
mas_leal = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.0, ctx, COEF)
menos_leal = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.9, ctx, COEF)
check(mas_leal > menos_leal,
      "a menor desvío (más lealtad), el arrastre del jefe pesa más")
ambos = bd.delta_legislador("LIN_JEFE", "leg:firma", 0.20, ctx, COEF)
check(abs(ambos - (COEF["F_i"] + esperado_jefe)) < 1e-9,
      "firmar Y tener al jefe firmante suma los dos términos")

# ── ambos coeficientes son positivos: nunca hay penalización, sólo impulso ───
print("\n3. sin firma propia ni de jefe, nunca hay penalización (a diferencia de M5)")
check(bd.delta_legislador("X", "leg:nadie", 0.5, ctx_vacio, COEF) == 0.0,
      "M6 no tiene término de carácter: quien no firmó ni tiene jefe firmante "
      "queda en 0, no en un delta negativo (eso fue lo que colapsaba P con M5)")

# ── la bandera apaga `ajuste` aunque haya contexto y coeficientes ────────────
print("\n4. la bandera apagada no toca nada, aunque haya contexto")
p0 = 0.5
check(bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, ctx, activo=False) == p0,
      "con activo=False, ajuste() devuelve p0 tal cual")
prendido = bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, ctx, activo=True)
check(prendido != p0, "con activo=True y contexto real, sí mueve la P")
check(prendido > p0, "y como F_i>0 solamente, la mueve hacia ARRIBA")
check(bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, None, activo=True) == p0,
      "con activo=True pero contexto=None (proyecto hipotético), no mueve nada")

# ── el default del módulo respeta la variable de entorno ────────────────────
print("\n5. BETA_DICTAMEN está PRENDIDA por defecto desde el 14-09 (BETA_DICTAMEN=0 apaga)")
import os  # noqa: E402
check(os.environ.get("BETA_DICTAMEN", "1") != "0" or not bd.BETA_DICTAMEN,
      "si el proceso tiene BETA_DICTAMEN=0, el módulo tiene que quedar apagado")
check(os.environ.get("BETA_DICTAMEN", "1") == "0" or bd.BETA_DICTAMEN,
      "sin BETA_DICTAMEN=0 explícito (incluida la variable ausente), el default es prendido")

# ── armar_roster con contexto=None es un no-op (paridad con el default viejo) ─
print("\n6. armar_roster sin contexto se comporta EXACTAMENTE como antes")
sys.path.insert(0, str(SRC))
from nowcast_puertas import armar_roster  # noqa: E402

BLOQ = [{"bloque": "LIN_A", "linea": "AFIRMATIVO", "desvio": 0.05, "_share_afirm": 0.90}]
det = {"filas": [{"legislador_id": "a", "legislador": "A", "bloque_linaje": "LIN_A",
                  "linea": "AFIRMATIVO", "desvio": 0.05, "desvio_de": "ficha_reciente"}],
      "padron": "test"}
lin1, des1, pre1, perf1 = armar_roster("diputados", BLOQ, {}, det)
lin2, des2, pre2, perf2 = armar_roster("diputados", BLOQ, {}, det, contexto_dictamen=None)
check(list(lin1) == list(lin2) and list(des1) == list(des2),
      "contexto_dictamen por defecto (no pasado) y pasado explícitamente en None dan lo mismo")
check(perf1[0]["p_afirma_si_vota"] == perf2[0]["p_afirma_si_vota"], "y el perfil también")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
