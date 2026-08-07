"""Tests OFFLINE del ENCOGIMIENTO del desvío en el modulador del ICG.

Cubre el defecto detectado el 2026-08-07: los legisladores de la camada dic-2025
tenían mediana de 2 votaciones disputadas, y con 2 observaciones el desvío solo
puede valer 0 / 0,5 / 1 — mientras los tramos de gamma cortan en 0,10 / 0,20 /
0,30 / 0,40. Resultado: imposible caer en los tramos intermedios; 6 novatos
quedaron en gamma 0,555 (el máximo de la cámara) con dos datos.

Correr:  python variables/proyecto/tests/test_modulador_shrink.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import modulador_icg as M  # noqa: E402

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print(f"  FALLA: {msg}")


# --- 1. La fórmula: peso proporcional a la muestra -------------------------
# n=2, k=5 -> el dato propio pesa 2/7 = 0,286
check(abs(M.encoger_desvio(1.0, 2, 0.0, k=5.0) - 2 / 7) < 1e-9,
      "n=2 debe dar (2*1 + 5*0)/7")
# n grande -> manda el dato propio
check(abs(M.encoger_desvio(1.0, 500, 0.0, k=5.0) - 500 / 505) < 1e-9,
      "con n grande el encogimiento casi no debe mover")
# n=0 -> manda el prior por completo
check(M.encoger_desvio(1.0, 0, 0.20, k=5.0) == 0.20,
      "sin observaciones el resultado debe ser el prior")
# NaN -> prior (no 0.0, que era el default silencioso viejo)
check(M.encoger_desvio(np.nan, 3, 0.20) == 0.20,
      "desvío NaN debe caer al prior, no a cero")
check(M.encoger_desvio(None, 3, 0.20) == 0.20, "None debe caer al prior")

# --- 2. El caso que motivó el fix: 2 de 2 no puede dar el tramo máximo -----
crudo = M.gamma_individual(1.0)                       # desvío 1,0 sin encoger
enc = M.gamma_individual(M.encoger_desvio(1.0, 2, 0.04))
check(crudo == 0.555, "sin encoger, desvío 1,0 cae en el tramo máximo")
check(enc < crudo, f"con 2 disputadas no debe quedar en el máximo (dio {enc})")

# --- 3. Un veterano no se mueve de tramo ----------------------------------
vet = M.encoger_desvio(0.45, 47, 0.04)
check(M.gamma_individual(vet) == M.gamma_individual(0.45),
      "un veterano (47 disputadas) no debe cambiar de tramo")

# --- 4. El prior se calcula SOLO con muestra sólida ------------------------
# bloque con 1 veterano díscolo (0,40) y 3 novatos en 0: el prior debe ser 0,40,
# no 0 — si se usara el bloque entero, los novatos se encogerían hacia sí mismos.
df = pd.DataFrame({
    "p_acompana": [0.8] * 4,
    "desvio":     [0.40, 0.0, 0.0, 0.0],
    "n_disputadas": [50, 2, 2, 2],
    "bloque": ["X"] * 4,
})
r = M.aplicar_individual(df, s=1.0, log_rel=0.1)
check(abs(r["desvio_enc"].iloc[1] - (2 * 0.0 + 5 * 0.40) / 7) < 1e-9,
      "el prior debe salir del veterano del bloque, no de los novatos")
check(r["desvio_enc"].iloc[1] > 0, "un novato de bloque díscolo no debe quedar en 0")

# --- 5. Contrato intacto: sin `n_disputadas` se comporta como antes --------
df2 = df.drop(columns=["n_disputadas"])
r2 = M.aplicar_individual(df2, s=1.0, log_rel=0.1)
check("desvio_enc" not in r2.columns, "sin n_disputadas no debe inventar la columna")
check(list(r2["gamma"]) == [M.gamma_individual(x) for x in df2["desvio"]],
      "sin n_disputadas el gamma debe ser el de siempre")
check({"gamma", "p_mod", "delta"} <= set(r2.columns), "faltan columnas del contrato")

# --- 6. `encoger=False` desactiva explícitamente --------------------------
r3 = M.aplicar_individual(df, s=1.0, log_rel=0.1, encoger=False)
check(list(r3["gamma"]) == [M.gamma_individual(x) for x in df["desvio"]],
      "encoger=False debe dar el resultado crudo")

# --- 7. El encogimiento nunca invierte el orden entre legisladores ---------
a = M.encoger_desvio(0.60, 10, 0.05)
b = M.encoger_desvio(0.20, 10, 0.05)
check(a > b, "a igual muestra, más desvío debe seguir dando más desvío encogido")

# --- 8. Las probabilidades siguen en rango --------------------------------
check(r["p_mod"].between(0, 1).all(), "p_mod fuera de [0,1]")

print(f"\n{ok} chequeos OK, {fail} fallas")
raise SystemExit(1 if fail else 0)
