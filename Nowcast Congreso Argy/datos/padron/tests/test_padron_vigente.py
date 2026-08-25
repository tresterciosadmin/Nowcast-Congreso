# -*- coding: utf-8 -*-
"""Tests de la foto de la cámara a una fecha (oficial + histórico, sin duplicados).

Los sintéticos corren sin datos del repo. Los de CONTROL usan los padrones reales
y se saltean solos si no están (un clon recién bajado no los tiene todos).

Lo que vigilan:
  1. Que el oficial GANE y el histórico sólo rellene.
  2. Que la misma persona escrita distinto NO entre dos veces — que es lo que
     rompía: al 2026-06-01 el concat crudo daba 513 diputados en vez de 257.
  3. Que un empate NO se rompa por la fuerza: ambiguo se descarta y se CUENTA.

    python datos/padron/tests/test_padron_vigente.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from padron_vigente import BANCAS, padron_vigente, verificar  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


COLS = ["legislador", "clave", "legislador_id", "camara", "distrito", "bloque",
        "bloque_norm", "desde", "hasta", "bloque_linaje", "fuente", "nota"]


def csv(path: Path, filas: list[dict]) -> None:
    df = pd.DataFrame(filas)
    for c in COLS:
        if c not in df:
            df[c] = ""
    df[COLS].to_csv(path, index=False, encoding="utf-8-sig")


def leg(nombre, clave, lid, desde="2015-12-10", hasta="2019-12-09",
        linaje="LIN_A", camara="diputados"):
    return {"legislador": nombre, "clave": clave, "legislador_id": lid,
            "camara": camara, "bloque_linaje": linaje, "desde": desde, "hasta": hasta}


# ───────────── el oficial gana y el histórico rellena ─────────────
print("el oficial gana, el histórico rellena")
with tempfile.TemporaryDirectory() as td:
    of, hi = Path(td) / "of.csv", Path(td) / "hi.csv"
    csv(of, [leg("Perez, Juan", "JUAN PEREZ", "leg:of1")])
    csv(hi, [leg("PEREZ Juan", "JUAN PEREZ", "leg:hi1"),
             leg("GOMEZ Ana", "ANA GOMEZ", "leg:hi2")])
    df, det = padron_vigente("diputados", "2017-06-01", rutas=[of, hi], con_detalle=True)
    check(len(df) == 2, f"2 bancas, no 3 (dio {len(df)})")
    check("leg:of1" in set(df["legislador_id"]), "el id OFICIAL sobrevive")
    check("leg:hi1" not in set(df["legislador_id"]), "el duplicado del histórico se descarta")
    check("leg:hi2" in set(df["legislador_id"]), "el que sólo está en el histórico entra")
    check(det["colapsadas"] == 1, f"cuenta 1 colapsada (dio {det['colapsadas']})")


# ───────────── el caso real: nombres de distinto largo ─────────────
print("\nla misma persona escrita distinto NO entra dos veces")
casos = [
    ("Rach Quiroga, Analia", "ANALIA QUIROGA RACH",
     "RACH QUIROGA Analía Alexandra", "ALEXANDRA ANALIA QUIROGA RACH"),
    ("Urroz, Paula Marcela", "MARCELA PAULA URROZ", "URROZ Paula", "PAULA URROZ"),
]
for n_of, c_of, n_hi, c_hi in casos:
    with tempfile.TemporaryDirectory() as td:
        of, hi = Path(td) / "of.csv", Path(td) / "hi.csv"
        csv(of, [leg(n_of, c_of, "leg:of")])
        csv(hi, [leg(n_hi, c_hi, "leg:hi")])
        df = padron_vigente("diputados", "2017-06-01", rutas=[of, hi])
        check(len(df) == 1, f"'{c_of}' y '{c_hi}' son UNA banca (dio {len(df)})")


# ───────────── un empate no se rompe por la fuerza ─────────────
print("\nun empate NO se rompe por la fuerza")
with tempfile.TemporaryDirectory() as td:
    of, hi = Path(td) / "of.csv", Path(td) / "hi.csv"
    # dos oficiales distintos que comparten apellido y el histórico trae sólo eso
    csv(of, [leg("Perez, Juan", "JUAN PEREZ", "leg:of1"),
             leg("Perez, Ana", "ANA PEREZ", "leg:of2")])
    csv(hi, [leg("PEREZ", "PEREZ", "leg:hi1")])
    df, det = padron_vigente("diputados", "2017-06-01", rutas=[of, hi], con_detalle=True)
    check(det["ambiguas"] == 1, f"la fila ambigua se CUENTA (dio {det['ambiguas']})")
    check(len(df) == 2, "y no se colapsa contra ninguna de las dos ni se agrega")


# ───────────── la ventana de mandato manda ─────────────
print("\nla ventana de mandato se respeta")
with tempfile.TemporaryDirectory() as td:
    of = Path(td) / "of.csv"
    csv(of, [leg("Viejo, Uno", "UNO VIEJO", "leg:v", "2009-12-10", "2013-12-09"),
             leg("Nuevo, Dos", "DOS NUEVO", "leg:n", "2015-12-10", "2019-12-09")])
    df = padron_vigente("diputados", "2017-06-01", rutas=[of])
    check(list(df["legislador_id"]) == ["leg:n"], "sólo el mandato vigente a la fecha")
    df2 = padron_vigente("diputados", "2011-06-01", rutas=[of])
    check(list(df2["legislador_id"]) == ["leg:v"], "y a otra fecha, el otro")


# ───────────── trazabilidad ─────────────
print("\ncada banca dice de qué archivo salió")
with tempfile.TemporaryDirectory() as td:
    of, hi = Path(td) / "of.csv", Path(td) / "hi.csv"
    csv(of, [leg("Perez, Juan", "JUAN PEREZ", "leg:of1")])
    csv(hi, [leg("GOMEZ Ana", "ANA GOMEZ", "leg:hi2")])
    df, det = padron_vigente("diputados", "2017-06-01", rutas=[of, hi], con_detalle=True)
    check("padron_archivo" in df.columns, "la salida trae el archivo de origen")
    check(det["por_archivo"] == {"of.csv": 1, "hi.csv": 1}, "y el detalle lo resume")


# ───────────── fechas y errores ─────────────
print("\nerrores claros")
with tempfile.TemporaryDirectory() as td:
    ok = Path(td) / "of.csv"
    csv(ok, [leg("Perez, Juan", "JUAN PEREZ", "leg:of1")])
    try:
        padron_vigente("diputados", "no-es-fecha", rutas=[ok])
        check(False, "una fecha inválida debe romper")
    except ValueError:
        check(True, "fecha inválida levanta ValueError, no FileNotFound tres capas abajo")
    try:
        padron_vigente("diputados", "2017-06-01", rutas=[Path(td) / "no_existe.csv"])
        check(False, "sin archivos legibles debe romper")
    except (FileNotFoundError, OSError):
        check(True, "sin archivo levanta error claro")


# ───────────── CONTROL contra las bancas reales ─────────────
print("\nCONTROL contra las bancas reales (se saltea si faltan los padrones)")
check(BANCAS == {"diputados": 257, "senado": 72}, "las bancas por cámara están declaradas")
try:
    filas = verificar("diputados", ["2013-06-01", "2019-06-01", "2026-06-01"])
except (FileNotFoundError, ImportError) as e:
    print(f"  (salteado: {e})")
    filas = []
for d in filas:
    check(abs(d.get("desvio_vs_bancas", 99)) <= 3,
          f"{d['fecha']}: {d['n']} bancas contra 257 — desvío {d.get('desvio_vs_bancas')}, "
          "más de 3 no es rotación, es un problema de emparejamiento")
    check(d["ambiguas"] == 0, f"{d['fecha']}: sin ambigüedades (dio {d['ambiguas']})")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
