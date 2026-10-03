"""Tests de integración de `INCERTIDUMBRE_LEGISLADOR` (§III.A.3, ADR-0025) en
`modelo/ensemble/src/nowcast_puertas.py`. Usa datos reales (misma canónica que
usa el motor) — sin red, ninguna llamada a LLM.

    python modelo/ensemble/tests/test_incertidumbre_legislador.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# Import DESPUÉS de fijar el env var por defecto (sin tocar), para que el módulo
# lea la bandera tal como la ve cualquiera que corra el motor sin configurar nada.
os.environ.pop("INCERTIDUMBRE_LEGISLADOR", None)
import nowcast_puertas as N  # noqa: E402

# PRENDIDA por defecto desde el 16-09-2026 (ADR-0025, "Hagamos el cambio" — Franco).
# El número prendido es el del panel de regresión: 0,6132 hasta el 2026-10-03; 0,6117 desde la auditoría D1 (la
# ventana de la postura pasó de 730 a 2190 días; ver `ESTADO-EJECUCION.md`, «D1 — lote»). El apagado no cambia.
print("INCERTIDUMBRE_LEGISLADOR prendida por defecto (sin tocar el env)")
check(N.INCERTIDUMBRE_LEGISLADOR is True, "default: prendida")

print("\ncontrol real, bandera prendida (default): mueve el número de siempre")
r_on_default = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
check(abs(r_on_default["p_aprobacion"] - 0.6117) < 1e-4,
      f"prendida por defecto tiene que dar el número re-estimado el 16-09: "
      f"{r_on_default['p_aprobacion']}")

print("\napagada a mano (opt-out, INCERTIDUMBRE_LEGISLADOR=0): vuelve al número histórico")
N.INCERTIDUMBRE_LEGISLADOR = False
try:
    r_off = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
    check(abs(r_off["p_aprobacion"] - 0.9801) < 1e-9,
          f"apagada tiene que dar EXACTAMENTE el número publicado de antes del 16-09: "
          f"{r_off['p_aprobacion']}")
    check(r_off["p_aprobacion"] != r_on_default["p_aprobacion"],
          f"apagada y prendida tienen que dar números distintos: "
          f"{r_off['p_aprobacion']} vs {r_on_default['p_aprobacion']}")
finally:
    N.INCERTIDUMBRE_LEGISLADOR = True  # no contaminar otros tests del proceso

print("\nrestaurada: vuelve a dar el número prendido de siempre")
r_restaurado = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
check(abs(r_restaurado["p_aprobacion"] - 0.6117) < 1e-4,
      "prender la bandera de nuevo tiene que volver al número publicado actual")
check(0.0 <= r_restaurado["p_aprobacion"] <= 1.0, "sigue siendo una probabilidad válida")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
