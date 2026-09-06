# -*- coding: utf-8 -*-
"""La tabla de alias de `legislador_id` tiene que estar sana.

Lo que fija, y por que cada cosa:

- **No hay cadenas colgando.** Si A->B y B->C, A tiene que terminar en C. Una cadena
  a medias deja dos canonicos para la misma persona, que es el problema que la tabla
  viene a resolver.
- **Ningun id es absorbido y canonico a la vez.**
- **El canonico es el de MAS votos** (decision de Franco, 04-09): preserva el
  historial largo, que es lo que alimenta el record individual.
- **Falta el archivo -> tabla vacia, no excepcion.** Un clon recien bajado tiene que
  poder correr sin esto.

    python datos/canonica/tests/test_alias_legislador.py
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from alias_legislador import RUTA, canonico, cargar_alias  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("la tabla carga")
a = cargar_alias()
check(isinstance(a, dict), "cargar_alias devuelve un dict")
check(len(a) > 0, f"la tabla tiene alias (dio {len(a)}); si es 0, falta {RUTA.name}")

print("no quedan cadenas a medias")
colgadas = [(k, v) for k, v in a.items() if v in a]
check(not colgadas, f"si A->B y B->C, A tiene que ir directo a C. Colgadas: {colgadas[:3]}")

print("ningun id es absorbido y canonico a la vez")
ambos = set(a) & set(a.values())
check(not ambos, f"un id no puede ser las dos cosas: {sorted(ambos)[:3]}")

print("nadie se apunta a si mismo")
check(not [k for k, v in a.items() if k == v], "un alias a si mismo no dice nada")

print("los ids tienen la forma del repo")
malos = [x for x in list(a) + list(a.values()) if not str(x).startswith("leg:")]
check(not malos, f"todos empiezan con 'leg:': {malos[:3]}")

print("canonico() resuelve y no rompe con lo desconocido")
if a:
    k = next(iter(a))
    check(canonico(k) == a[k], "un id absorbido devuelve su canonico")
    check(canonico(a[k]) == a[k], "un canonico se devuelve a si mismo")
check(canonico("leg:no-existe") == "leg:no-existe", "lo que no esta vuelve tal cual")
check(canonico(None) is None, "None no rompe")

print("sin archivo, tabla vacia y sin excepcion")
cargar_alias.cache_clear()
try:
    vacia = cargar_alias.__wrapped__("/no/existe/alias.csv")
    check(vacia == {}, f"tiene que dar {{}}, dio {vacia}")
except Exception as e:  # noqa: BLE001
    check(False, f"no puede lanzar excepcion: {type(e).__name__}: {e}")
cargar_alias.cache_clear()

print("los tres que trancaban el roster de jefes estan resueltos")
for absorbido, canon in (("leg:3a122de91183", "leg:3cc84340cad1"),   # ROSSI, AGUSTIN
                         ("leg:9c9abb302e88", "leg:b067aa2a9852"),   # STOLBIZER
                         ("leg:c4eabf6d9ca4", "leg:97bbbf7cc358")):  # ROYON
    check(canonico(absorbido) == canon,
          f"{absorbido} tiene que ir a {canon} (dio {canonico(absorbido)})")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
