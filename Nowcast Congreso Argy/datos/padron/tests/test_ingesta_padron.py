# -*- coding: utf-8 -*-
"""Tests de datos/padron/src/ingesta_padron.py — sin red y sin datos del repo.

Fijan los dos arreglos del 2026-09-04 (URGENTE 3 y URGENTE 7):

  1. **El control que se NIEGA a escribir.** Correr el script sin argumentos
     tomaba `data/raw/nomina_diputados.csv` (257 filas, la foto vigente) y pisaba
     `padron_diputados.csv` (1.454 filas, 18 años de mandatos) **sin error ni
     aviso**. Ahora, si la salida encoge más de lo tolerado, no escribe y devuelve
     código 2. Se puede forzar, pero hay que decirlo.
  2. **`_fecha_iso` valida contra el calendario.** Un "31/02/2026" salía como
     "2026-02-31", y `pd.to_datetime(errors="coerce")` lo convertía en `NaT` en
     silencio — una columna vacía en vez de un error.

    python datos/padron/tests/test_ingesta_padron.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from ingesta_padron import (  # noqa: E402
    FLAG_ACHICAR, _fecha_iso, control_de_encogimiento,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ─────────────── el control de encogimiento ───────────────
print("el control se niega a pisar 1.454 filas con 257")
with tempfile.TemporaryDirectory() as tmp:
    salida = Path(tmp) / "padron_diputados.csv"
    salida.write_text("legislador,bloque\n" + "\n".join(f"X{i},B" for i in range(1454)),
                      encoding="utf-8-sig")

    motivo = control_de_encogimiento(salida, 257)
    check(motivo is not None, "257 contra 1.454 tiene que frenarse")
    check("1454" in (motivo or "") and "257" in (motivo or ""),
          f"el motivo tiene que decir las dos cifras: {motivo!r}")
    check("nomina_diputados.csv" in (motivo or ""),
          "y el comando correcto, que es la parte accionable")

    print("pero deja pasar la rotación normal")
    check(control_de_encogimiento(salida, 1454) is None, "misma cantidad: pasa")
    check(control_de_encogimiento(salida, 1400) is None,
          "-4% es rotación (bajas, renuncias): pasa")
    check(control_de_encogimiento(salida, 1310) is None,
          "-10% es el borde de la tolerancia: pasa")
    check(control_de_encogimiento(salida, 1200) is not None,
          "-17% ya no es rotación: frena")

    print("y se puede forzar, pero hay que decirlo")
    check(control_de_encogimiento(salida, 257, permitir=True) is None,
          f"con permitir=True escribe ({FLAG_ACHICAR} en la línea de comandos)")

    print("la primera corrida no tiene con qué comparar")
    check(control_de_encogimiento(Path(tmp) / "no_existe.csv", 3) is None,
          "si no hay archivo previo, no hay nada que proteger")

    print("un archivo previo vacío tampoco frena")
    vacio = Path(tmp) / "vacio.csv"
    vacio.write_text("legislador,bloque\n", encoding="utf-8-sig")
    check(control_de_encogimiento(vacio, 1, permitir=False) is None,
          "0 filas viejas: cualquier cosa es mejora")

# ─────────────── _fecha_iso valida ───────────────
print("_fecha_iso rechaza fechas que no existen")
check(_fecha_iso("10/12/2019") == "2019-12-10", "el caso normal dd/mm/YYYY")
check(_fecha_iso("2019-12-10") == "2019-12-10", "y el ISO que ya viene bien")
check(_fecha_iso("31/02/2026") is None,
      f"el 31 de febrero NO existe, tiene que dar None y no '2026-02-31': "
      f"{_fecha_iso('31/02/2026')!r}")
check(_fecha_iso("2026-02-31") is None,
      f"tampoco escrito en ISO: {_fecha_iso('2026-02-31')!r}")
check(_fecha_iso("32/01/2026") is None, "ni el 32 de enero")
check(_fecha_iso("10/13/2019") is None, "ni el mes 13")
check(_fecha_iso("29/02/2024") == "2024-02-29", "pero 2024 SÍ es bisiesto")
check(_fecha_iso("29/02/2023") is None, "y 2023 no")
check(_fecha_iso("En el cargo") is None, "el texto que no es fecha sigue dando None")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
