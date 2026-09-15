"""Tests offline de variables/proyecto/src/tema_por_proyecto.py — sin red, sin
API key. Este módulo NO clasifica (eso es agente_taxonomias.clasificar_lote,
que necesita red): sólo LEE proyecto_taxonomias y resuelve el cruce
proyecto_id (HCDN) <-> denominador (NNNN-X-AAAA).

    python variables/proyecto/tests/test_tema_por_proyecto.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tema_por_proyecto import (  # noqa: E402
    cargar_crosswalk,
    taxonomias_de,
    temas_de_proyecto,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _db_fixture(tmp: Path) -> Path:
    """Una base mínima con el schema real de proyecto_taxonomias (PK compuesta
    denominador+taxonomia_id), con un caso multietiqueta (Ley Bases en
    miniatura) y un caso donde el humano corrigió al agente."""
    db = tmp / "proyectos_test.db"
    con = sqlite3.connect(str(db))
    con.execute("""
        CREATE TABLE proyecto_taxonomias (
            denominador TEXT NOT NULL, taxonomia_id TEXT, taxonomia TEXT,
            fuente TEXT, confianza REAL, asignada_en TEXT,
            PRIMARY KEY (denominador, taxonomia_id)
        )
    """)
    filas = [
        ("100-D-2024", "POLINST.CONST", "Const.", "agente", 0.85, "2026-01-01T00:00:00Z"),
        ("100-D-2024", "DESREG.DESECO", "Desreg.", "agente", 0.80, "2026-01-01T00:00:00Z"),
        ("100-D-2024", "ECON.PRESU", "Presu.", "agente", 0.75, "2026-01-01T00:00:00Z"),
        ("100-D-2024", "AUX.TRAMITE", "Trámite", "agente", 0.60, "2026-01-01T00:00:00Z"),
        # PK real es (denominador, taxonomia_id) SIN fuente: `persistir()` nunca deja
        # dos filas para el mismo id (si ya hay una 'humano', el agente ni se inserta).
        # Esta fila simula el resultado DESPUÉS de esa resolución: sólo queda la humana.
        ("200-D-2024", "TRAB.RELAB", "Rel. laboral", "humano", 0.99, "2026-01-02T00:00:00Z"),
    ]
    con.executemany(
        "INSERT INTO proyecto_taxonomias VALUES (?,?,?,?,?,?)", filas)
    con.commit()
    con.close()
    return db


def _expedientes_fixture(tmp: Path) -> Path:
    p = tmp / "expedientes_test.parquet"
    pd.DataFrame([
        {"proyecto_id": "HCDN000100", "exp_diputados": "100-D-2024"},
        {"proyecto_id": "HCDN000200", "exp_diputados": "200-D-2024"},
    ]).to_parquet(p, index=False)
    return p


with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    db = _db_fixture(tmp)
    exped = _expedientes_fixture(tmp)
    cruce = cargar_crosswalk(exped)

    print("cargar_crosswalk")
    check(cruce["pid_a_denom"]["HCDN000100"] == "100-D-2024", "HCDN -> denominador")
    check(cruce["denom_a_pid"]["100-D-2024"] == "HCDN000100", "denominador -> HCDN")

    print("\ntaxonomias_de")
    df = taxonomias_de("100-D-2024", db)
    check(len(df) == 4, "las 4 filas del proyecto multietiqueta")

    print("\ntemas_de_proyecto — multietiqueta, por proyecto_id (HCDN)")
    temas = temas_de_proyecto(proyecto_id="HCDN000100", db_path=db, cruce=cruce)
    areas = {a for a, _ in temas}
    check(areas == {"POLINST", "DESREG", "ECON"}, f"3 áreas sustantivas, AUX excluida: {areas}")
    check(len(temas) == 3, "una fila por ÁREA (no por taxonomia_id)")
    check(temas[0][0] == "POLINST" and abs(temas[0][1] - 0.85) < 1e-9,
          f"ordenado por confianza descendente: {temas}")

    print("\ntemas_de_proyecto — mismo resultado por denominador directo")
    temas2 = temas_de_proyecto(denominador="100-D-2024", db_path=db, cruce=cruce)
    check(temas == temas2, "proyecto_id y denominador dan el mismo resultado")

    print("\ntemas_de_proyecto — respeta una taxonomía de fuente humana")
    temas3 = temas_de_proyecto(proyecto_id="HCDN000200", db_path=db, cruce=cruce)
    check(temas3 == [("TRAB", 0.99)], f"confianza de la fila humana: {temas3}")

    print("\ntemas_de_proyecto — proyecto sin taxonomias todavia (caso NORMAL hoy)")
    temas4 = temas_de_proyecto(proyecto_id="HCDN999999", db_path=db, cruce=cruce)
    check(temas4 == [], "lista vacía, no excepción — es el estado normal hasta que se clasifique")

    print("\ntemas_de_proyecto — proyecto_id sin cruce a denominador (origen Senado puro)")
    temas5 = temas_de_proyecto(proyecto_id="HCDN_SENADO_PURO", db_path=db, cruce=cruce)
    check(temas5 == [], "sin cruce -> vacío, no rompe")

    print("\ntemas_de_proyecto — sin proyecto_id ni denominador")
    try:
        temas_de_proyecto(db_path=db, cruce=cruce)
        check(False, "debía levantar ValueError")
    except ValueError:
        check(True, "ValueError claro sin ningún identificador")

    print("\ncargar_crosswalk — contrato ausente degrada limpio")
    vacio = cargar_crosswalk(tmp / "no_existe.parquet")
    check(vacio == {"pid_a_denom": {}, "denom_a_pid": {}}, "sin archivo -> dict vacío, no rompe")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
