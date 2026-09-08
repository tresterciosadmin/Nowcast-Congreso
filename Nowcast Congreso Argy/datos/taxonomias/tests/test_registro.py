# -*- coding: utf-8 -*-
"""El registro único de taxonomías tiene que ser el lugar donde SIEMPRE están.

Por qué existe: el 06-09-2026 Franco preguntó por las taxonomías históricas y yo contesté
que la tabla estaba vacía. Las dos cosas eran ciertas — había CUATRO lugares donde podían
estar y ninguno era EL lugar. Este test cuida que no vuelva a haber cinco.

Lo que fija:

1. **Merge por (nivel, objeto, taxonomia_id)**, ganando la de MAYOR confianza; a igualdad,
   la más reciente. Sin eso, consolidar dos veces duplica o pisa trabajo bueno con malo.
2. **Consolidar es idempotente.** Es lo que lo hace seguro de correr en cada clasificación.
3. **Multitaxonomía** (ADR-0006): un acta con varias taxonomías da varias filas, y sólo UNA
   es `principal`.
4. **Los ids se validan contra el vocabulario** y los que no están se REPORTAN. Así
   aparecieron `OPACO` y `PROCEDIMENTAL`, dos etiquetas que la revisión manual usó y el
   vocabulario no tiene.
5. **Una fuente rota no tumba el barrido**: se reporta y se sigue con las demás.
6. **Sin archivo, lista vacía** — no una excepción: un clon nuevo tiene que poder correr.
7. **EL REGISTRO NO PUEDE ESTAR IGNORADO POR GIT.** Es la razón de ser del archivo: cae en
   el `*.csv` del .gitignore salvo por su excepción explícita, y sin ella no viaja y se
   pierde trabajo pago. Este chequeo es el más importante de todos.

    python datos/taxonomias/tests/test_registro.py
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import registro as R  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def fila(objeto, tid, conf, cuando, fuente="agente:texto", principal=1, nivel="acta"):
    return {"nivel": nivel, "objeto": objeto, "taxonomia_id": tid, "area": R.area_de(tid),
            "principal": principal, "confianza": conf, "fuente": fuente,
            "asignada_en": cuando}


print("merge: gana la de mayor confianza")
a = [fila("acta:1", "ECON.TRIB", 0.6, "2026-01-01T00:00:00Z")]
b = [fila("acta:1", "ECON.TRIB", 0.9, "2025-01-01T00:00:00Z", fuente="manual")]
out, n = R.merge(a, b)
check(len(out) == 1, f"la misma clave no puede duplicar: {len(out)}")
check(float(out[0]["confianza"]) == 0.9 and out[0]["fuente"] == "manual",
      f"tenía que ganar la de 0,9 aunque sea más vieja: {out[0]}")
check(n["reemplazadas"] == 1, f"conteo de reemplazos: {n}")

print("a igualdad de confianza, gana la más reciente")
out, _ = R.merge([fila("acta:1", "ECON.TRIB", 0.9, "2025-01-01T00:00:00Z")],
                 [fila("acta:1", "ECON.TRIB", 0.9, "2026-01-01T00:00:00Z")])
check(out[0]["asignada_en"].startswith("2026"), f"tenía que ganar la de 2026: {out[0]}")

print("merge idempotente: mergear dos veces lo mismo no cambia nada")
una, _ = R.merge([], a)
dos, n2 = R.merge(una, a)
check(una == dos, "mergear lo mismo dos veces tiene que dar igual")
check(n2["agregadas"] == 0, f"nada nuevo la segunda vez: {n2}")

print("multitaxonomía: varias filas por objeto, UNA principal")
out, _ = R.merge([], [fila("acta:9", "ECON.TRIB", 0.9, "2026-01-01T00:00:00Z", principal=1),
                      fila("acta:9", "JUST.PENAL", 0.9, "2026-01-01T00:00:00Z", principal=0)])
check(len(out) == 2, f"dos taxonomías, dos filas: {len(out)}")
check(sum(int(r["principal"]) for r in out) == 1, "sólo una puede ser principal")

print("area_de saca el prefijo del id")
for tid, area in (("ECON.TRIB", "ECON"), ("AUX.TRAMITE", "AUX"), ("ECON", "ECON")):
    check(R.area_de(tid) == area, f"area_de({tid}) tendría que dar {area}")

print("sin archivo: lista vacía, no excepción")
check(R.cargar(Path("/no/existe/registro.csv")) == [], "un clon nuevo tiene que poder correr")

print("guardar y cargar dan la vuelta completa")
import tempfile
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / "r.csv"
    R.guardar(out, p)
    leidas = R.cargar(p)
    check(len(leidas) == len(out), f"ida y vuelta: {len(leidas)} contra {len(out)}")
    check({r["taxonomia_id"] for r in leidas} == {r["taxonomia_id"] for r in out},
          "los ids tienen que sobrevivir la ida y vuelta")

print("una fuente rota se reporta y no corta el barrido")
_orig = dict(R.FUENTES)
try:
    with tempfile.TemporaryDirectory() as d:
        malo = Path(d) / "roto.parquet"
        malo.write_text("esto no es un parquet", encoding="utf-8")
        R.FUENTES.clear()
        R.FUENTES["tema_por_acta"] = malo
        R.FUENTES["muestra_manual"] = Path("/no/existe.csv")
        res = R.consolidar(Path(d) / "reg.csv")
    check("ERROR" in str(res["por_fuente"]["tema_por_acta"]),
          f"la fuente rota tiene que reportarse: {res['por_fuente']}")
    check(res["por_fuente"]["muestra_manual"] == "no existe",
          "una fuente ausente no es un error")
finally:
    R.FUENTES.clear()
    R.FUENTES.update(_orig)

print("el vocabulario se lee y tiene los ids conocidos")
ids = R.ids_validos()
if ids:
    for t in ("ECON.TRIB", "AUX.TRAMITE", "AUX.SINCLASIF"):
        check(t in ids, f"{t} tendría que estar en el vocabulario")
    check("OPACO" not in ids and "PROCEDIMENTAL" not in ids,
          "OPACO y PROCEDIMENTAL NO están en el vocabulario: por eso se mapean "
          "(ver ALIAS_FUERA_DEL_VOCABULARIO). Si aparecen, hay que sacar el alias.")
else:
    print("  (salteo: no está docs/taxonomias/taxonomias.json)")

print("EL REGISTRO NO PUEDE ESTAR IGNORADO POR GIT")
raiz = Path(__file__).resolve().parents[3]
try:
    r = subprocess.run(["git", "-C", str(raiz.parent), "check-ignore",
                        str(R.REGISTRO.relative_to(raiz.parent))],
                       capture_output=True, text=True, timeout=20)
    check(r.returncode != 0,
          "el registro está IGNORADO por git. Cae en el `*.csv` del .gitignore y sin la "
          "excepción `!datos/taxonomias/data/asignaciones.csv` NO VIAJA: es perder "
          "trabajo que cuesta llamadas de API. Es la razón de ser de este archivo.")
except (OSError, subprocess.SubprocessError, ValueError) as e:
    print(f"  (salteo el chequeo de git: {e})")

print("y el registro real tiene contenido")
reales = R.cargar()
check(len(reales) > 1000, f"el registro tendría que tener las clasificaciones: {len(reales)}")
check({r["nivel"] for r in reales} <= set(R.NIVELES), "nivel fuera del enum")
sin_area = [r for r in reales if not r.get("area")]
check(not sin_area, f"{len(sin_area)} filas sin area")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
