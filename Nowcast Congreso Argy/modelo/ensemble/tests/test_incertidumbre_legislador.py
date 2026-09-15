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


# Import DESPUÉS de fijar el env var por defecto (apagado), para que el módulo
# lea la bandera apagada al cargar sus constantes de nivel de módulo.
os.environ.pop("INCERTIDUMBRE_LEGISLADOR", None)
import nowcast_puertas as N  # noqa: E402

print("INCERTIDUMBRE_LEGISLADOR apagada por defecto (sin tocar el env)")
check(N.INCERTIDUMBRE_LEGISLADOR is False, "default: apagada")

print("\ncontrol real, bandera apagada: P(aprobación) = 0,9801 de siempre")
r_off = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
check(abs(r_off["p_aprobacion"] - 0.9801) < 1e-9,
      f"apagada tiene que dar EXACTAMENTE el número publicado de siempre: {r_off['p_aprobacion']}")

print("\ncon la bandera prendida (a mano, sin depender del env var): mueve algo")
N.INCERTIDUMBRE_LEGISLADOR = True
try:
    r_on = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
    check(r_on["p_aprobacion"] != r_off["p_aprobacion"],
          f"con epsilon0={N.EPSILON0}, tau={N.TAU} el número tiene que moverse: "
          f"{r_off['p_aprobacion']} -> {r_on['p_aprobacion']}")
    check(0.0 <= r_on["p_aprobacion"] <= 1.0, "sigue siendo una probabilidad válida")
finally:
    N.INCERTIDUMBRE_LEGISLADOR = False  # no contaminar otros tests del proceso

print("\nrestaurada: vuelve a dar el número de siempre")
r_restaurado = N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)
check(abs(r_restaurado["p_aprobacion"] - 0.9801) < 1e-9,
      "apagar la bandera de nuevo tiene que volver al número publicado")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
