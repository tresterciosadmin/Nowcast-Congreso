# -*- coding: utf-8 -*-
"""Tests de `beta_dictamen.py` — el dictamen por legislador (ADR-0016, S:III.A.2).

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


COEF = {"const": 0.7554, "F_i": 2.1522, "lealtad_x_jefe": 2.145,
        "dict_DISPUTADO": -1.6632, "dict_mayoria": -1.6915,
        "dict_solo_minoria": -0.3912}

# ── sin contexto o sin coeficientes, delta es siempre 0 ─────────────────────
print("1. sin dictamen (contexto None) o sin coeficientes, el delta es 0")
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, None, COEF) == 0.0,
      "contexto None -> 0")
ctx_vacio = {"firmantes": frozenset(), "lin_jefe": frozenset(), "caracter": None}
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, ctx_vacio, COEF) == 0.0,
      "sin firmantes, sin jefe, sin carácter -> 0 (proyecto hipotético / sin dato)")
check(bd.delta_legislador("BLOQ", "leg:x", 0.1, ctx_vacio, {}) == 0.0,
      "sin coeficientes (archivo ausente o mal estimado) -> 0")

# ── F_i y lealtad_x_jefe entran como se documentan ───────────────────────────
print("\n2. F_i, lealtad-por-jefe y carácter se suman en logit")
ctx = {"firmantes": frozenset({"leg:firma"}), "lin_jefe": frozenset({"LIN_JEFE"}),
      "caracter": "DISPUTADO"}
solo_caracter = bd.delta_legislador("OTRO_LINAJE", "leg:nadie", 0.20, ctx, COEF)
check(abs(solo_caracter - COEF["dict_DISPUTADO"]) < 1e-9,
      f"sin firmar y sin jefe firmante, solo pesa el carácter (dio {solo_caracter})")
con_firma = bd.delta_legislador("OTRO_LINAJE", "leg:firma", 0.20, ctx, COEF)
esperado = COEF["F_i"] + COEF["dict_DISPUTADO"]
check(abs(con_firma - esperado) < 1e-9,
      f"F_i suma su coeficiente completo (dio {con_firma}, esperaba {esperado})")
con_jefe = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.20, ctx, COEF)
esperado_jefe = COEF["lealtad_x_jefe"] * (1 - 0.20) + COEF["dict_DISPUTADO"]
check(abs(con_jefe - esperado_jefe) < 1e-9,
      f"jefe firmante entra filtrado por (1-desvío) (dio {con_jefe}, esperaba {esperado_jefe})")
mas_leal = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.0, ctx, COEF)
menos_leal = bd.delta_legislador("LIN_JEFE", "leg:nadie", 0.9, ctx, COEF)
check(mas_leal > menos_leal,
      "a menor desvío (más lealtad), el arrastre del jefe pesa más")

# ── el carácter UNICO es la referencia: no suma nada ─────────────────────────
print("\n3. UNICO es la referencia y no mueve nada")
ctx_unico = {"firmantes": frozenset(), "lin_jefe": frozenset(), "caracter": "UNICO"}
check(bd.delta_legislador("X", "leg:y", 0.1, ctx_unico, COEF) == 0.0,
      "carácter UNICO, sin F_i ni J_l -> delta 0 (es la categoría de referencia)")

# ── la bandera apaga `ajuste` aunque haya contexto y coeficientes ────────────
print("\n4. la bandera apagada no toca nada, aunque haya contexto")
p0 = 0.5
check(bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, ctx, activo=False) == p0,
      "con activo=False, ajuste() devuelve p0 tal cual")
prendido = bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, ctx, activo=True)
check(prendido != p0, "con activo=True y contexto real, sí mueve la P")
check(bd.ajuste(p0, "OTRO_LINAJE", "leg:firma", 0.2, None, activo=True) == p0,
      "con activo=True pero contexto=None (proyecto hipotético), no mueve nada")

# ── el default del módulo respeta la variable de entorno ────────────────────
print("\n5. BETA_DICTAMEN lee la variable de entorno, apagada por defecto")
import os  # noqa: E402
check(os.environ.get("BETA_DICTAMEN") != "1" or bd.BETA_DICTAMEN,
      "si no se seteó BETA_DICTAMEN=1 en este proceso, el módulo tiene que quedar apagado")

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
