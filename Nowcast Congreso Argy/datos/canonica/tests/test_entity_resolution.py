# -*- coding: utf-8 -*-
"""Tests del linaje de bloque — sin red y sin datos del repo.

Lo que fija, y por qué existe cada cosa:

- **El patrón de IZQUIERDA sigue cubriendo las 13 variantes del FIT.** Se
  reconoce **por patrón y no por lista** (07-08-2026) porque el frente rota la
  etiqueta cada elección y una lista exacta se desactualiza sola.
- **`BLOQUE DE LOS TRABAJADORES` NO es izquierda** (URGENTE 4, resuelto el
  04-09-2026). Era una alternativa literal del patrón, y en toda la canónica la
  usa una sola persona: Héctor Daer, CGT, peronista.
- **`SOCIALISTA` a secas es el PS**, no el FIT.
- **El patrón sólo RESCATA lo que quedó en OTRO / PROVINCIAL**: nunca pisa un
  linaje ya asignado a mano.

    python datos/canonica/tests/test_entity_resolution.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from entity_resolution import _bloque_norm, _linaje_vec  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def linaje(etiqueta: str, fecha: str = "2016-01-01") -> str:
    """La cadena completa, como en el pipeline: normalizar y despues linaje.

    `_linaje_vec` recibe `bloque_norm`, no la etiqueta cruda: pasarle
    "UNION CIVICA RADICAL" en vez de "UCR" da OTRO / PROVINCIAL y el test miente.
    """
    norm = pd.Series([etiqueta]).map(_bloque_norm)
    return _linaje_vec(norm, pd.Series([pd.Timestamp(fecha)]))[0]


# ─────────────── el FIT, por patrón ───────────────
print("las variantes del FIT siguen entrando por patrón")
FIT = [
    "FRENTE DE IZQUIERDA",
    "PTS-FRENTE DE IZQUIERDA UNIDAD",
    "PTS-FRENTE DE IZQUIERDA Y DE TRABAJADORES UNIDAD",
    "PARTIDO OBRERO EN EL FRENTE DE IZQUIERDA Y DE TRABAJADORES-U",
    "PARTIDO OBRERO -FRENTE DE IZQUIERDA Y DE TRABAJADORES -UNIDA",
    "MST - FRENTE DE IZQUIERDA Y TRABAJADORES UNIDAD",
    "IZQUIERDA SOCIALISTA FIT-UNIDAD",
    "IZQUIERDA SOCIALISTA - FRENTE DE IZQUIERDA",
    "IZQUIERDA UNIDA",
    "AUTODETERMINACION Y LIBERTAD",
    "PROYECTO SUR",
    "MOVIMIENTO PROYECTO SUR",
    "PROYECTO SUR - UNEN",
]
for e in FIT:
    check(linaje(e) == "IZQUIERDA", f"{e!r} tiene que ser IZQUIERDA, dio {linaje(e)!r}")

# ─────────────── el falso positivo (URGENTE 4) ───────────────
print("BLOQUE DE LOS TRABAJADORES no es izquierda")
got = linaje("BLOQUE DE LOS TRABAJADORES")
check(got != "IZQUIERDA",
      "es el bloque personal de Héctor Daer (CGT, peronista), 237 votos "
      "2014-2017. Su coincidencia con el núcleo de izquierda es 78,6% y queda "
      f"SÉPTIMA de nueve, debajo de peronismo federal (90,0%) y massismo (88,9%). Dio {got!r}")
check(got == "OTRO / PROVINCIAL",
      f"sin la alternativa del patrón cae al mapa LINAJE, que no la tiene: {got!r}")

print("y las etiquetas con 'trabajadores' que SÍ son del FIT no se rompen")
for e in ("PTS-FRENTE DE IZQUIERDA Y DE TRABAJADORES UNIDAD",
          "MST - FRENTE DE IZQUIERDA Y TRABAJADORES UNIDAD"):
    check(linaje(e) == "IZQUIERDA",
          f"lleva 'trabajadores' pero también la marca del frente: {e!r} -> {linaje(e)!r}")

# ─────────────── el socialismo no es el FIT ───────────────
print("SOCIALISTA a secas es el PS, no el FIT")
for e in ("PARTIDO SOCIALISTA", "SOCIALISTA", "PARTIDO SOCIALISTA POPULAR"):
    check(linaje(e) != "IZQUIERDA", f"{e!r} es progresismo, dio {linaje(e)!r}")

# ─────────────── el patrón no pisa lo asignado a mano ───────────────
print("el patrón sólo rescata lo que quedó en OTRO / PROVINCIAL")
check(linaje("UNION CIVICA RADICAL") == "RADICALISMO",
      f"un linaje del mapa exacto no lo toca nadie: {linaje('UNION CIVICA RADICAL')!r}")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
