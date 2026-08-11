"""Tests OFFLINE del modulador del ICG en DOS CAPAS (fondo 6m + sacudón 3m) y del
ENCOGIMIENTO del desvío.

Encogimiento: cubre el defecto del 2026-08-07 (novatos con 2 votaciones saltando
al tramo máximo). Dos capas: cubre la revisión del 2026-08-11 (se sacó la capa 2
global; el ICG entra por z_fondo + z_corto). Los tests NO hardcodean los valores
de gamma (los fija la corrida de Valle): se apoyan en las tablas TRAMOS_FONDO /
TRAMOS_CORTO que el módulo tenga cargadas.

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


# --- 1. La fórmula del encogimiento: peso proporcional a la muestra --------
check(abs(M.encoger_desvio(1.0, 2, 0.0, k=5.0) - 2 / 7) < 1e-9,
      "n=2 debe dar (2*1 + 5*0)/7")
check(abs(M.encoger_desvio(1.0, 500, 0.0, k=5.0) - 500 / 505) < 1e-9,
      "con n grande el encogimiento casi no debe mover")
check(M.encoger_desvio(1.0, 0, 0.20, k=5.0) == 0.20,
      "sin observaciones el resultado debe ser el prior")
check(M.encoger_desvio(np.nan, 3, 0.20) == 0.20,
      "desvío NaN debe caer al prior, no a cero")
check(M.encoger_desvio(None, 3, 0.20) == 0.20, "None debe caer al prior")
# pd.NA (backend pyarrow) también debe caer al prior, no explotar
check(M.encoger_desvio(pd.NA, 3, 0.20) == 0.20, "pd.NA debe caer al prior")

# --- 2. El caso que motivó el fix: 2 de 2 no puede quedar en el tramo máximo -
tf = dict(M.TRAMOS_FONDO)
check(M.gamma_fondo(1.0) == tf[0.40], "desvío 1,0 debe usar el tramo >=0.40 de la tabla")
enc_dv = M.encoger_desvio(1.0, 2, 0.04)               # ~0,314: cae al tramo intermedio
check(0.30 <= enc_dv < 0.40, f"2 de 2 debe caer al tramo intermedio (dio {enc_dv:.3f})")
check(M.gamma_fondo(enc_dv) == tf[0.30],
      "el novato encogido usa el gamma del tramo 0.30, no del >=0.40")

# --- 3. Un veterano no se mueve de tramo ----------------------------------
vet = M.encoger_desvio(0.45, 47, 0.04)
check(M.gamma_fondo(vet) == M.gamma_fondo(0.45),
      "un veterano (47 disputadas) no debe cambiar de tramo (fondo)")
check(M.gamma_corto(vet) == M.gamma_corto(0.45),
      "un veterano (47 disputadas) no debe cambiar de tramo (corto)")

# --- 4. El prior se calcula SOLO con muestra sólida ------------------------
df = pd.DataFrame({
    "p_acompana": [0.8] * 4,
    "desvio":     [0.40, 0.0, 0.0, 0.0],
    "n_disputadas": [50, 2, 2, 2],
    "bloque": ["X"] * 4,
})
r = M.aplicar_individual(df, s=1.0, z_fondo=0.1, z_corto=0.05)
check(abs(r["desvio_enc"].iloc[1] - (2 * 0.0 + 5 * 0.40) / 7) < 1e-9,
      "el prior debe salir del veterano del bloque, no de los novatos")
check(r["desvio_enc"].iloc[1] > 0, "un novato de bloque díscolo no debe quedar en 0")

# --- 5. Las DOS capas se aplican y componen -------------------------------
check({"gamma_fondo", "gamma_corto", "p_mod", "delta"} <= set(r.columns),
      "faltan columnas del contrato de 2 capas")
# con z_fondo>0 y z_corto>0 y s=+1, un bisagra afirmativo sube su p
check(r["p_mod"].iloc[0] >= r["p_acompana"].iloc[0], "clima favorable debe no bajar la p de un afirmativo")
# el disciplinado (desvío 0, gamma_corto 0) no reacciona al sacudón corto
solo_fondo = M._mover(df["p_acompana"].iloc[1], M.gamma_fondo(r["desvio_enc"].iloc[1]), 1.0, 0.1)
check(abs(M._mover(solo_fondo, M.gamma_corto(r["desvio_enc"].iloc[1]), 1.0, 0.05) - r["p_mod"].iloc[1]) < 1e-9,
      "p_mod debe ser la composición fondo→corto")

# --- 6. Contrato: sin `n_disputadas` no inventa la columna ------------------
df2 = df.drop(columns=["n_disputadas"])
r2 = M.aplicar_individual(df2, s=1.0, z_fondo=0.1, z_corto=0.05)
check("desvio_enc" not in r2.columns, "sin n_disputadas no debe inventar la columna")
check(list(r2["gamma_fondo"]) == [M.gamma_fondo(x) for x in df2["desvio"]],
      "sin n_disputadas el gamma_fondo debe ser el de la tabla")

# --- 7. `encoger=False` desactiva explícitamente --------------------------
r3 = M.aplicar_individual(df, s=1.0, z_fondo=0.1, z_corto=0.05, encoger=False)
check(list(r3["gamma_fondo"]) == [M.gamma_fondo(x) for x in df["desvio"]],
      "encoger=False debe dar el gamma_fondo crudo")

# --- 8. Robustez a los DOS backends de dtype (object y pyarrow) ------------
# la corrida de Valle usa columnas pyarrow con nulos pd.NA; acá se ejercita.
for backend in ("numpy_nullable", "pyarrow"):
    try:
        dfb = df.copy()
        dfb.loc[1, "desvio"] = np.nan
        dfb = dfb.convert_dtypes(dtype_backend=backend)
        rb = M.aplicar_individual(dfb, s=1.0, z_fondo=0.1, z_corto=0.05)
        check(rb["p_mod"].astype(float).between(0, 1).all(),
              f"[{backend}] p_mod fuera de [0,1]")
        check(not pd.isna(rb["desvio_enc"].iloc[1]),
              f"[{backend}] el desvío faltante debe encogerse al prior, no quedar NA")
    except Exception as e:                                # noqa: BLE001
        check(False, f"[{backend}] aplicar_individual explotó con nulos: {e!r}")

# --- 9. El encogimiento nunca invierte el orden entre legisladores ---------
check(M.encoger_desvio(0.60, 10, 0.05) > M.encoger_desvio(0.20, 10, 0.05),
      "a igual muestra, más desvío debe seguir dando más desvío encogido")

# --- 10. Las probabilidades siguen en rango --------------------------------
check(r["p_mod"].between(0, 1).all(), "p_mod fuera de [0,1]")

print(f"\n{ok} chequeos OK, {fail} fallas")
raise SystemExit(1 if fail else 0)
