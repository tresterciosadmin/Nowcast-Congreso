"""Tests offline de `_tema_auto` en modelo/ensemble/src/nowcast_puertas.py — el
enganche proyecto_id -> tema (Parte A, coordinacion/PROMPT-MULTIETIQUETA.md).

Sin red, sin API key: usa una base de proyectos y un crosswalk sintéticos. El
punto de estos tests es la bandera y la degradación, no la clasificación (eso
ya lo cubre variables/proyecto/tests/test_tema_por_proyecto.py).

    python modelo/ensemble/tests/test_tema_auto.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import nowcast_puertas as N  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _db_con_multietiqueta(tmp: Path) -> Path:
    db = tmp / "proyectos_test.db"
    con = sqlite3.connect(str(db))
    con.execute("""
        CREATE TABLE proyecto_taxonomias (
            denominador TEXT NOT NULL, taxonomia_id TEXT, taxonomia TEXT,
            fuente TEXT, confianza REAL, asignada_en TEXT,
            PRIMARY KEY (denominador, taxonomia_id)
        )
    """)
    con.executemany("INSERT INTO proyecto_taxonomias VALUES (?,?,?,?,?,?)", [
        ("100-D-2024", "POLINST.CONST", "Const.", "agente", 0.85, "2026-01-01T00:00:00Z"),
        ("100-D-2024", "DESREG.DESECO", "Desreg.", "agente", 0.80, "2026-01-01T00:00:00Z"),
        ("100-D-2024", "ECON.PRESU", "Presu.", "agente", 0.60, "2026-01-01T00:00:00Z"),
    ])
    con.commit()
    con.close()
    return db


def _expedientes(tmp: Path) -> Path:
    p = tmp / "expedientes_test.parquet"
    pd.DataFrame([{"proyecto_id": "HCDN000100", "exp_diputados": "100-D-2024"}]).to_parquet(
        p, index=False)
    return p


with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    db = _db_con_multietiqueta(tmp)
    exped = _expedientes(tmp)

    print("TEMA_AUTO apagada (default): siempre no-op, ni con proyecto_id ni datos")
    N.TEMA_AUTO = False
    tema, temas, modo = N._tema_auto("HCDN000100", db_path=db, expedientes=exped)
    check((tema, temas, modo) == (None, None, "primaria"), "bandera apagada -> no-op total")

    print("\nTEMA_AUTO prendida, sin proyecto_id: no-op")
    N.TEMA_AUTO = True
    tema, temas, modo = N._tema_auto(None, db_path=db, expedientes=exped)
    check((tema, temas, modo) == (None, None, "primaria"), "sin proyecto_id -> no-op")

    print("\nTEMA_AUTO prendida, proyecto SIN taxonomías (caso normal hoy): no-op")
    tema, temas, modo = N._tema_auto("HCDN999999", db_path=db, expedientes=exped)
    check((tema, temas, modo) == (None, None, "primaria"),
          "proyecto no clasificado -> no-op, no excepción")

    print("\nTEMA_AUTO prendida + combinar_temas='primaria' (default): 1 tema, el de mayor confianza")
    N.COMBINAR_TEMAS = "primaria"
    tema, temas, modo = N._tema_auto("HCDN000100", db_path=db, expedientes=exped)
    check(tema == "POLINST", f"área de mayor confianza (0.85): {tema}")
    check(temas is None, "en modo primaria, `temas` (plural) no se usa")
    check(modo == "primaria", modo)

    print("\nTEMA_AUTO prendida + combinar_temas='union': multietiqueta completa, sin `tema` singular")
    N.COMBINAR_TEMAS = "union"
    tema, temas, modo = N._tema_auto("HCDN000100", db_path=db, expedientes=exped)
    check(tema is None, "en modo union, `tema` (singular) no se usa")
    check({a for a, _ in temas} == {"POLINST", "DESREG", "ECON"}, f"las 3 áreas: {temas}")
    check(modo == "union", modo)

    N.TEMA_AUTO = False  # reset por las dudas de que algo más importe este módulo
    N.COMBINAR_TEMAS = "primaria"


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
