# -*- coding: utf-8 -*-
"""Compara la cohorte del embudo construida por las DOS rutas (parquet vs SQLite).

## Por que vive ACA y no en `datos/proyectos`

Hasta 2026-08-20 esta comparacion vivia dentro de
`datos/proyectos/src/verificar.py`, que hacia `sys.path.insert(.../variables/embudo/src)`
e importaba `embudo`. Eso creaba una dependencia HACIA ARRIBA: un modulo de
`datos/` (capa 1) importando el codigo interno de un modulo de `variables/`
(capa 2), justo lo que CLAUDE.md prohibe ("consumi su salida, no su codigo
interno"). Consecuencias concretas:

  - `datos/proyectos` no se podia verificar si `variables/embudo` estaba roto;
  - un cambio en `construir_cohorte` cambiaba en silencio que significa "la base
    esta verificada";
  - y el `sys.path.insert` con import por nombre pelado es la misma trampa que
    en este repo ya tiene tres `to_canonical.py` esperando para chocar.

La cohorte es un concepto de ESTE modulo. El instrumento de medicion vive donde
vive el concepto; `datos/proyectos` le pide el numero y lo controla. La direccion
queda embudo -> proyectos, que es la que ya existia igual (embudo lee
`proyectos.db`).

## Contrato de salida

Imprime **una linea de JSON** por stdout y sale con 0. Los errores van por
stderr y salen con != 0. Quien lo llama decide si un numero es aceptable: este
script MIDE, no juzga.

    {"n_parquet": 1234, "n_sqlite": 1300, "n_comun": 1234,
     "cols_movidas": {"sancionado": 0, "llega_recinto": 0, ...}}

## Uso

    python variables/embudo/src/cohorte_dos_rutas.py
    CLEAN=... DB=... python variables/embudo/src/cohorte_dos_rutas.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
RAIZ = _HERE.parents[2]

CLEAN = Path(os.environ.get("CLEAN", RAIZ / "datos" / "expedientes" / "data" / "clean"))
DB = Path(os.environ.get("PROYECTOS_DB", RAIZ / "datos" / "proyectos" / "data" / "proyectos.db"))

# Columnas de RESULTADO: no dependen del bot, no se pueden mover entre rutas.
COLS_RESULTADO = ("sancionado", "llega_recinto", "con_dictamen", "etapa_actual")


def medir(clean: Path = CLEAN, db: Path = DB) -> dict:
    sys.path.insert(0, str(_HERE))
    import embudo  # noqa: E402  (necesita el sys.path de arriba; es su propio src)

    cp = embudo.construir_cohorte(embudo.cargar(clean))
    cs = embudo.construir_cohorte(embudo.cargar_sqlite(db))
    com = set(cp["proyecto_id"]) & set(cs["proyecto_id"])

    a = cp[cp["proyecto_id"].isin(com)].sort_values("proyecto_id").reset_index(drop=True)
    b = cs[cs["proyecto_id"].isin(com)].sort_values("proyecto_id").reset_index(drop=True)
    movidas = {}
    for col in COLS_RESULTADO:
        if col in a.columns and col in b.columns:
            iguales = (a[col] == b[col]) | (a[col].isna() & b[col].isna())
            movidas[col] = int((~iguales).sum())

    return {
        "n_parquet": int(len(cp)),
        "n_sqlite": int(len(cs)),
        "n_comun": int(len(com)),
        "cols_movidas": movidas,
        "clean": str(clean),
        "db": str(db),
    }


def main() -> int:
    try:
        print(json.dumps(medir(), ensure_ascii=False))
    except (OSError, ImportError, KeyError, ValueError) as e:
        print(f"cohorte_dos_rutas: no pude medir ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
