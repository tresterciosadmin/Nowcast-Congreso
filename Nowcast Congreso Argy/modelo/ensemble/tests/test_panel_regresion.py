"""El panel de regresión: el número del motor de hoy, guardado, y un test que lo compara.

Auditoría 2026-09, ítem A6 (decisiones 1 y 6 de Franco). Reemplaza al panel HTML
(`Nowcast-Puertas.html`, eliminado): `REGENERAR.ps1` paso 8 corre

    python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 \\
        --origen EJECUTIVO --json modelo/ensemble/outputs/panel_regresion.json

y este test corre el MOTOR con los mismos argumentos (`n_sims = 2000`, `seed = 0`) y exige que la
salida completa —todos los campos: la probabilidad, los pasos, el tablero de las dos cámaras y la
postura de cada legislador— sea IGUAL a la guardada.

PARA QUÉ SIRVE. Detecta que un cambio mueve el número sin que nadie lo haya visto. Un cambio que
mueve el número **a propósito** (una re-estimación de la fase D, por ejemplo) hace fallar este
test: se regenera el JSON con el comando de arriba y se commitea; **el diff de ese archivo es la
evidencia de cuánto se movió** y entra al registro de parámetros (`afecta_panel`).

QUÉ NO HACE. No es un pronóstico ni una medición de calidad: sólo dice «esto es lo que el motor
devolvía y sigue devolviendo». Que el número sea bueno lo dicen las mediciones de `QUE-SE-MIDE.md`.

RIESGO CONOCIDO (para D6). El panel no depende de lo que suben los bots (`bot-diario` y
`padron-vivo` sólo escriben tramites, votaciones nuevas y vigilancia del padrón, ninguno es insumo
del motor a 2026-06-01). Sí es insumo del motor `icg_mensual.csv`, que escribe `icg-mensual` el día
5 de cada mes: hoy no mueve el número porque el ICG está desconectado de la fórmula; cuando D6 lo
conecte, este test se va a mover una vez por mes y habrá que decidir qué se compara.

    python modelo/ensemble/tests/test_panel_regresion.py
"""
from __future__ import annotations

import json
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


import nowcast_puertas as N  # noqa: E402

PANEL = Path(__file__).resolve().parents[1] / "outputs" / "panel_regresion.json"
COMANDO = ("python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 "
           "--origen EJECUTIVO --json modelo/ensemble/outputs/panel_regresion.json")


def _diferencias(a, b, ruta="", salida=None, tope=15):
    """(campo, guardado, motor) de los primeros `tope` campos que difieren."""
    salida = [] if salida is None else salida
    if len(salida) >= tope:
        return salida
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                salida.append((f"{ruta}/{k}", "<falta>" if k not in a else "presente",
                               "<falta>" if k not in b else "presente"))
            else:
                _diferencias(a[k], b[k], f"{ruta}/{k}", salida, tope)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            salida.append((ruta, f"{len(a)} elementos", f"{len(b)} elementos"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _diferencias(x, y, f"{ruta}[{i}]", salida, tope)
    elif a != b:
        salida.append((ruta, a, b))
    return salida


print("1. el panel guardado existe y tiene la forma del motor")
check(PANEL.is_file(), f"falta {PANEL}: {COMANDO}")
guardado = json.loads(PANEL.read_text(encoding="utf-8")) if PANEL.is_file() else {}
check(isinstance(guardado.get("p_aprobacion"), float) and 0.0 < guardado["p_aprobacion"] < 1.0,
      f"p_aprobacion tiene que ser un número entre 0 y 1: {guardado.get('p_aprobacion')!r}")
check({"origen", "revisora"} <= set(guardado.get("camaras", {})), "trae el tablero de las dos cámaras")
check("umbral_mayoria_absoluta" in guardado.get("camaras", {}).get("origen", {}),
      "el umbral lleva el nombre que dice lo que es (mayoría absoluta), no «simple» (URGENTE 6, 04-09)")

print("\n2. el motor de hoy da EXACTAMENTE lo guardado (salida completa, campo por campo)")
motor = json.loads(json.dumps(
    N.nowcast("diputados", "2026-06-01", origen="EJECUTIVO", n_sims=2000, seed=0)))
dif = _diferencias(guardado, motor)
check(not dif, "el motor ya no da lo guardado en `modelo/ensemble/outputs/panel_regresion.json`.\n"
      f"      p_aprobacion: guardado {guardado.get('p_aprobacion')} · motor {motor.get('p_aprobacion')}\n"
      "      primeros campos distintos (guardado -> motor):\n"
      + "\n".join(f"        {c}: {x!r} -> {y!r}" for c, x, y in dif)
      + f"\n      Si el cambio es a propósito: regenerar con\n        {COMANDO}\n"
      "      y commitear el JSON (su diff es la evidencia de cuánto se movió el número).")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
