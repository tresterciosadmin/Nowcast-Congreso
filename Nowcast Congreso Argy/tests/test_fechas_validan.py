# -*- coding: utf-8 -*-
"""Los CUATRO `_fecha_iso` del repo tienen que rechazar fechas que no existen.

POR QUE EXISTE ESTE TEST
------------------------
El repo tiene cuatro funciones `_fecha_iso`, y **esta bien que sean cuatro**:
parsean formatos genuinamente distintos ("14 DE MARZO DE 2026", `dd/mm/YYYY`,
`dd-mm-YYYY`). Eso no se unifica. Lo que si tiene que ser igual en las cuatro es
la VALIDACION, y hasta el 2026-09-04 solo `giros.py` la hacia. En las otras tres
un "31/02/2026" salia como la cadena `"2026-02-31"` sin chistar, y despues
`pd.to_datetime(..., errors="coerce")` lo convertia en `NaT` **en silencio**.

En este repo ese es el modo de fallar mas caro: no da error, da una columna
vacia. Es la misma familia de problemas que el default `"unico"` del parser de
dictamenes y que el padron pisado con 257 filas — el dato malo no se anuncia.

Este test NO unifica las funciones. Afirma que las cuatro **coinciden en decir
que no** sobre el mismo puñado de fechas imposibles. Si alguna vez falla, la
respuesta no es tocar el test: es ponerle la validacion a la que falta.

    python tests/test_fechas_validan.py
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
for sub in ("datos/seguimiento/src", "datos/bot_recoleccion/src",
            "datos/padron/src", "datos/senado/src"):
    sys.path.insert(0, str(RAIZ / sub))

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _cargar():
    """Importa las cuatro, cada una con el formato que sabe leer."""
    from giros import _fecha_iso as f_giros
    from tp_diputados import _fecha_iso as f_tp
    from ingesta_padron import _fecha_iso as f_padron
    from padron_bloques import _fecha_iso as f_senado
    return [
        ("datos/seguimiento/src/giros.py", f_giros, "{d:02d}-{m:02d}-{y}"),
        ("datos/bot_recoleccion/src/tp_diputados.py", f_tp, None),   # texto, aparte
        ("datos/padron/src/ingesta_padron.py", f_padron, "{d:02d}/{m:02d}/{y}"),
        ("datos/senado/src/padron_bloques.py", f_senado, "{d:02d}/{m:02d}/{y}"),
    ]


MESES_TEXTO = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 12: "DICIEMBRE"}
IMPOSIBLES = [(31, 2, 2026), (30, 2, 2026), (32, 1, 2026), (29, 2, 2023)]
VALIDAS = [(10, 12, 2019), (29, 2, 2024), (1, 1, 2026)]

for nombre, fn, molde in _cargar():
    print(nombre)
    for d, m, y in IMPOSIBLES:
        if molde is None:
            if m not in MESES_TEXTO:
                continue
            txt = f"{d} DE {MESES_TEXTO[m]} DE {y}"
        else:
            txt = molde.format(d=d, m=m, y=y)
        got = fn(txt)
        check(got is None,
              f"{nombre}: {txt!r} no existe en el calendario y tiene que dar None, "
              f"dio {got!r} (que despues se vuelve NaT en silencio)")
    for d, m, y in VALIDAS:
        if molde is None:
            if m not in MESES_TEXTO:
                continue
            txt = f"{d} DE {MESES_TEXTO[m]} DE {y}"
        else:
            txt = molde.format(d=d, m=m, y=y)
        check(fn(txt) == f"{y}-{m:02d}-{d:02d}",
              f"{nombre}: {txt!r} es una fecha real y tiene que salir "
              f"{y}-{m:02d}-{d:02d}, dio {fn(txt)!r}")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
