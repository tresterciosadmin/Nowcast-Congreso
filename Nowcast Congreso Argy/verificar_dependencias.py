# -*- coding: utf-8 -*-
"""Chequea en dos segundos que este todo lo que la corrida larga necesita.

**Por que existe.** El 06-09-2026 el PASO 6 de `REGENERAR.ps1` murio con
`ModuleNotFoundError: No module named 'statsmodels'` **despues de 9,2 minutos**, cuando ya
habia procesado las 1.556 actas: el import esta adentro de `estimar()`, o sea en la ultima
linea util del programa. Nueve minutos de CPU para descubrir un `pip install` que faltaba.

La regla que deja: **lo que puede fallar en el segundo 1 no puede fallar en el minuto 9.**

    python verificar_dependencias.py          # todo
    python verificar_dependencias.py --paso 6 # solo lo que necesita ese paso
"""
from __future__ import annotations

import argparse
import importlib.util
import sys

# modulo importable -> (paquete para pip, para que se usa)
REQUERIDOS = {
    "pandas": ("pandas", "toda la capa de datos"),
    "numpy": ("numpy", "simulacion y metricas"),
    "pyarrow": ("pyarrow", "backend de parquet"),
    "requests": ("requests", "scrapers"),
    "tenacity": ("tenacity", "reintentos de los scrapers"),
    "bs4": ("beautifulsoup4", "HTML del Senado y de HCDN"),
    "openpyxl": ("openpyxl", "el Excel de manual_2026 y los export"),
    "pypdf": ("pypdf", "Ordenes del Dia, lectura primaria"),
    "pdfminer": ("pdfminer.six", "Ordenes del Dia, respaldo de texto"),
    "statsmodels": ("statsmodels", "beta del dictamen, psi, theta"),
}
OPCIONALES = {
    "sklearn": ("scikit-learn", "solo variables/embudo; su test se saltea si falta"),
}
# que necesita cada paso de REGENERAR.ps1
POR_PASO = {
    1: ["pandas", "pyarrow", "pypdf", "pdfminer"],
    2: ["requests", "bs4", "tenacity"],
    3: ["requests", "bs4", "tenacity"],
    4: ["pandas", "pyarrow", "pypdf", "pdfminer"],
    5: ["pandas", "pyarrow"],
    6: ["pandas", "numpy", "pyarrow", "statsmodels"],
    7: ["pandas", "numpy", "pyarrow"],
    8: ["pandas", "numpy", "pyarrow"],
}


def falta(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is None
    except (ImportError, ValueError):
        return True


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--paso", type=int, default=0,
                    help="chequear solo lo que necesita ese paso de REGENERAR.ps1")
    a = ap.parse_args(argv)

    mods = POR_PASO.get(a.paso, list(REQUERIDOS)) if a.paso else list(REQUERIDOS)
    faltan = [m for m in mods if falta(m)]
    for m in mods:
        pip, para = REQUERIDOS[m]
        print(f"  {'FALTA' if m in faltan else '  ok '}  {pip:<16} {para}")
    for m, (pip, para) in OPCIONALES.items():
        print(f"  {'(opc)' if falta(m) else '  ok '}  {pip:<16} {para}")

    if faltan:
        pips = " ".join(REQUERIDOS[m][0] for m in faltan)
        print(f"\nFALTAN {len(faltan)}. Instalalos ANTES de largar la corrida:\n")
        print(f"    python -m pip install {pips}\n")
        return 1
    print("\nEsta todo. La corrida no se va a caer por una dependencia.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
