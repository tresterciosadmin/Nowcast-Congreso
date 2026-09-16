"""Tests offline de variables/proyecto/src/tema_por_capitulo.py — sin red, sin
API key: la clasificación se prueba con un clasificador FALSO inyectado (mismo
patrón que test_tema_por_proyecto.py/test_tema_por_acta.py).

    python variables/proyecto/tests/test_tema_por_capitulo.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tema_por_capitulo import (  # noqa: E402
    cargar_capitulos,
    clasificar_capitulos,
    _sumarios,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _capitulos_nombre_fixture(tmp: Path) -> Path:
    """Espeja capitulos_nombre.parquet: dos capítulos de un mismo proyecto con
    DOS candidatos de nombre cada uno (dos ODs) — el caso real documentado en
    el segundo addendum de ADR-0023."""
    p = tmp / "capitulos_nombre.parquet"
    pd.DataFrame([
        {"archivo": "141-1.pdf", "proyecto_ids": "HCDN000100",
         "capitulo_num": "I", "nombre_capitulo": "I de"},  # candidato corto/ruidoso
        {"archivo": "141-7.pdf", "proyecto_ids": "HCDN000100;HCDN000200",
         "capitulo_num": "I", "nombre_capitulo": "Disposiciones generales de la ley"},
        {"archivo": "141-1.pdf", "proyecto_ids": "HCDN000100",
         "capitulo_num": "II", "nombre_capitulo": "Del régimen laboral"},
    ]).to_parquet(p, index=False)
    return p


def _db_fixture(tmp: Path) -> Path:
    db = tmp / "proyectos_test.db"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE proyectos (denominador TEXT PRIMARY KEY, sumario TEXT)")
    con.executemany("INSERT INTO proyectos VALUES (?,?)", [
        ("100-D-2024", "Ley de bases y reforma laboral"),
    ])
    con.commit()
    con.close()
    return db


def _expedientes_fixture(tmp: Path) -> Path:
    p = tmp / "expedientes.parquet"
    pd.DataFrame([{"proyecto_id": "HCDN000100", "exp_diputados": "100-D-2024"}]).to_parquet(p, index=False)
    return p


def _falso(texto: str) -> list[tuple[str, float]]:
    """`clasificar_capitulos` espera `clasificar(texto) -> [(tema_id, confianza),
    ...]` — el mismo contrato YA desempaquetado que usa `_clasificador_agente()`
    (igual que tema_por_acta.py; distinto del `_Res(asignaciones=...)` crudo que
    usa tema_por_proyecto.py — cada módulo hace su propio unwrap en el punto
    donde llama al agente real, no acá)."""
    if "laboral" in texto.lower():
        return [("TRAB.LABOR", 0.9), ("AUX.TRAMITE", 0.5)]
    return [("POLINST.CONST", 0.7)]


with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    cap_path = _capitulos_nombre_fixture(tmp)
    db = _db_fixture(tmp)
    exped = _expedientes_fixture(tmp)

    print("cargar_capitulos — dedup por (proyecto_id, capitulo_num), se queda con el más largo")
    caps = cargar_capitulos(cap_path)
    check(len(caps) == 3, f"3 pares únicos (HCDN100/I, HCDN200/I, HCDN100/II): {len(caps)}")
    fila_100_I = caps[(caps["proyecto_id"] == "HCDN000100") & (caps["capitulo_num"] == "I")]
    check(fila_100_I.iloc[0]["nombre_capitulo"] == "Disposiciones generales de la ley",
          f"se queda con el nombre más largo, no el ruidoso: {fila_100_I.iloc[0]['nombre_capitulo']!r}")
    fila_200_I = caps[(caps["proyecto_id"] == "HCDN000200") & (caps["capitulo_num"] == "I")]
    check(len(fila_200_I) == 1, "HCDN000200 también aparece (la OD 141-7 lo incluye)")

    print("\n_sumarios — resuelve contexto vía crosswalk, degrada limpio para el que no cruza")
    sumarios = _sumarios(["HCDN000100", "HCDN000200"], db, exped)
    check(sumarios.get("HCDN000100") == "Ley de bases y reforma laboral",
          f"HCDN000100 resuelve su sumario: {sumarios}")
    check("HCDN000200" not in sumarios, "HCDN000200 sin cruce -> sin contexto, no rompe")

    print("\nclasificar_capitulos — clasifica y persiste, usando el sumario como contexto")
    res = clasificar_capitulos(caps, clasificar=_falso, db_path=db, expedientes=exped)
    check(len(res) == 3, f"las 3 filas clasificadas: {len(res)}")
    fila = res[(res["proyecto_id"] == "HCDN000100") & (res["capitulo_num"] == "I")].iloc[0]
    check(fila["tema_area"] == "TRAB",
          f"el contexto del sumario ('...reforma laboral') hace que el capítulo 'Disposiciones "
          f"generales' clasifique como TRAB: {fila['tema_area']}")
    check(fila["todas_ids"] == "TRAB.LABOR;AUX.TRAMITE", f"todas_ids conserva el orden: {fila['todas_ids']}")

    print("\nclasificar_capitulos — idempotente: correr de nuevo no reclasifica lo ya hecho")
    res2 = clasificar_capitulos(caps, clasificar=_falso, previas=res, db_path=db, expedientes=exped)
    check(len(res2) == 3, f"sigue en 3 filas, no duplica: {len(res2)}")

    print("\nclasificar_capitulos — --todos reclasifica igual")
    res3 = clasificar_capitulos(caps, clasificar=_falso, previas=res, todos=True,
                                db_path=db, expedientes=exped)
    check(len(res3) == 3, f"todos=True reclasifica las 3 sin duplicar: {len(res3)}")

    print("\nclasificar_capitulos — resiliente: un capítulo roto no corta el lote")
    def _rompe(texto):
        if "laboral" in texto.lower():
            raise RuntimeError("simulo un error de red")
        return _falso(texto)
    res4 = clasificar_capitulos(caps, clasificar=_rompe, db_path=db, expedientes=exped)
    # HCDN000100 tiene "laboral" en su SUMARIO (contexto), así que sus dos capítulos
    # (I y II) rompen con _rompe; sólo HCDN000200 (sin sumario resuelto, sin "laboral"
    # en su nombre) sobrevive -- el lote sigue, no corta en el primer error.
    check(len(res4) == 1, f"sólo HCDN000200/I (sin 'laboral' en el contexto) sobrevive: {len(res4)}")
    check(res4.iloc[0]["proyecto_id"] == "HCDN000200", f"y es el proyecto correcto: {res4.iloc[0]['proyecto_id']}")

    print("\nclasificar_capitulos — respeta --limite")
    res5 = clasificar_capitulos(caps, clasificar=_falso, limite=1, db_path=db, expedientes=exped)
    check(len(res5) == 1, f"limite=1 procesa sólo 1: {len(res5)}")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
