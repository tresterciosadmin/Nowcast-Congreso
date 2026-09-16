"""Tests offline de evaluacion/baseline/src/fase1_rec_por_tema.py — sin red,
sin datos reales (sólo la función `combinar_logit`, que es la pieza nueva y
reusable; el resto del módulo es orquestación de I/O ya cubierta por la
corrida real sobre el censo, ver evaluacion/baseline/outputs/fase1_*.json).

    python evaluacion/baseline/tests/test_fase1_rec_por_tema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from fase1_rec_por_tema import combinar_logit, _areas_de  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("un solo share, peso 1.0 -> devuelve ese mismo share (identidad)")
check(abs(combinar_logit([0.8], [1.0]) - 0.8) < 1e-9, "un share solo tiene que devolverse igual")

print("\ndos shares iguales -> el combinado da lo mismo que cualquiera de los dos")
check(abs(combinar_logit([0.3, 0.3], [1.0, 1.0]) - 0.3) < 1e-9,
      "dos shares iguales combinan al mismo valor")

print("\npromedio en logit queda ENTRE los dos extremos, pero no en el punto medio simple")
c = combinar_logit([0.1, 0.9], [1.0, 1.0])
check(0.1 < c < 0.9, f"tiene que caer entre los extremos: {c}")
check(abs(c - 0.5) < 1e-9, "con pesos iguales y simetría 0.1/0.9, el logit-promedio cae en 0.5 exacto")

print("\npesos asimétricos empujan hacia el share de más peso")
c1 = combinar_logit([0.2, 0.8], [3.0, 1.0])   # más peso al 0.2 (área con más confianza)
c2 = combinar_logit([0.2, 0.8], [1.0, 3.0])   # más peso al 0.8
check(c1 < c2, f"más peso al share bajo tiene que dar un resultado más bajo: {c1} vs {c2}")

print("\nlista vacía rompe claro")
try:
    combinar_logit([], [])
    check(False, "tenía que levantar ValueError con listas vacías")
except ValueError:
    pass

print("\n_areas_de: multietiqueta, excluye AUX, sin duplicados, orden estable")
check(_areas_de("ECON.DEUDA;ECON.PRESU;TRAB.PREV") == ["ECON", "TRAB"],
      "colapsa a área, dedup, conserva orden")
check(_areas_de("AUX.TRAMITE;ECON.DEUDA") == ["ECON"], "AUX se descarta")
check(_areas_de(None) == [] and _areas_de("") == [], "vacío/None da lista vacía")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
