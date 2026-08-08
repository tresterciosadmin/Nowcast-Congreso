"""Tests OFFLINE del respaldo de `proyecto_taxonomias` (base temporal, sin red).

Lo que se prueba es el escenario real que motiva el módulo: alguien corre
`migrar_ckan.py` —comando inocente y documentado— y la tabla de taxonomías, que
cuesta llamadas a la API, se va a cero. El respaldo tiene que devolverla intacta.

Correr:  python datos/proyectos/tests/test_taxonomias_backup.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import taxonomias_backup as T  # noqa: E402

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print(f"  FALLA: {msg}")


ESQUEMA = """
CREATE TABLE proyectos (denominador TEXT PRIMARY KEY);
CREATE TABLE proyecto_taxonomias (
    denominador TEXT NOT NULL, taxonomia_id TEXT, taxonomia TEXT,
    fuente TEXT, confianza REAL, asignada_en TEXT,
    PRIMARY KEY (denominador, taxonomia_id));
"""


def base(tmp: Path) -> Path:
    db = tmp / "p.db"
    con = sqlite3.connect(db)
    con.executescript(ESQUEMA)
    con.executemany("INSERT INTO proyectos VALUES (?)",
                    [("0001-D-2026",), ("0002-D-2026",), ("0003-D-2026",)])
    con.commit()
    con.close()
    return db


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    db, csv = base(tmp), tmp / "taxo.csv"

    def filas(**kw):
        con = sqlite3.connect(db)
        r = con.execute("SELECT denominador, taxonomia_id, fuente FROM proyecto_taxonomias "
                        "ORDER BY denominador").fetchall()
        con.close()
        return r

    def poner(rows):
        con = sqlite3.connect(db)
        con.executemany("INSERT OR REPLACE INTO proyecto_taxonomias VALUES (?,?,?,?,?,?)", rows)
        con.commit()
        con.close()

    # --- 1. Tabla vacía: el respaldo igual se escribe (señal de "montado") ---
    check(T.exportar(db, csv) == 0, "exportar con 0 filas debe devolver 0")
    check(csv.exists(), "el CSV debe crearse aunque no haya filas")
    check(csv.read_text(encoding="utf-8").strip() == ",".join(T.COLS),
          "un respaldo vacío debe tener solo el encabezado")

    # --- 2. EL CASO REAL: migrar_ckan borra la tabla y el respaldo la devuelve ---
    poner([("0001-D-2026", "POLINST.ETICA", "Transparencia", "agente", 0.9, "2026-08-07"),
           ("0001-D-2026", "JUST.PENAL", "Penal", "agente", 0.7, "2026-08-07"),
           ("0002-D-2026", "ECON.TRIB", "Tributario", "humano", 1.0, "2026-08-07")])
    check(T.exportar(db, csv) == 3, "deben exportarse las 3 filas")

    con = sqlite3.connect(db)          # <- esto es lo que hace migrar_ckan
    con.execute("DELETE FROM proyecto_taxonomias")
    con.commit()
    con.close()
    check(len(filas()) == 0, "la simulación de migrar_ckan debe dejar la tabla vacía")

    check(T.restaurar(db, csv) == 3, "deben restaurarse las 3")
    check(len(filas()) == 3, "la tabla debe quedar como estaba")

    # --- 3. Idempotencia: restaurar dos veces no duplica ---
    T.restaurar(db, csv)
    check(len(filas()) == 3, "restaurar dos veces no debe duplicar")

    # --- 4. Precedencia: una revisión HUMANA no se pisa con una del agente ---
    poner([("0003-D-2026", "AMB.AGUA", "Agua", "humano", 1.0, "2026-08-07")])
    csv2 = tmp / "viejo.csv"
    csv2.write_text(",".join(T.COLS) + "\n"
                    "0003-D-2026,AMB.AGUA,Agua,agente,0.4,2026-01-01\n",
                    encoding="utf-8")
    T.restaurar(db, csv2)
    con = sqlite3.connect(db)
    f = con.execute("SELECT fuente, confianza FROM proyecto_taxonomias "
                    "WHERE denominador='0003-D-2026'").fetchone()
    con.close()
    check(f[0] == "humano" and f[1] == 1.0,
          f"la clasificación humana no debe ser pisada por la del agente (quedó {f})")

    # --- 5. `estado` es la alarma: base con filas y respaldo viejo ---
    e = T.estado(db, csv)
    check(e["en_base"] == 4 and e["en_respaldo"] == 3,
          f"estado debe contar ambos lados (dio {e})")
    check(e["desprotegidas"] == 1, "debe avisar cuántas quedan sin respaldar")

    # --- 6. Defensivo: sin respaldo no rompe; CSV mal formado avisa ---
    check(T.restaurar(db, tmp / "no_existe.csv") == 0,
          "sin archivo de respaldo debe devolver 0, no explotar")
    malo = tmp / "malo.csv"
    malo.write_text("otra,cosa\n1,2\n", encoding="utf-8")
    try:
        T.restaurar(db, malo)
        check(False, "un CSV sin las columnas del contrato debe fallar explícito")
    except ValueError:
        check(True, "")

    # --- 7. Base inexistente: error claro con la receta para crearla ---
    try:
        T.exportar(tmp / "nada.db", csv)
        check(False, "debe fallar si no existe la base")
    except FileNotFoundError as ex:
        check("migrar_ckan" in str(ex), "el error debe decir cómo crear la base")

print(f"\n{ok} chequeos OK, {fail} fallas")
raise SystemExit(1 if fail else 0)
