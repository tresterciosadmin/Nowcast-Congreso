"""Tests offline de la Puerta D (voto en la cámara revisora). Sin red, sin datos reales.

Cubre: elección de la cámara revisora, el ajuste 'pasó por origen' con su
fallback, el pipeline completo sobre un padrón sintético, y que Manera 1 sea
exactamente el límite de Manera 2 cuando no hay muestra.

    python modelo/ensemble/tests/test_puerta_d.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from puerta_d import (  # noqa: E402
    ajuste_paso_origen,
    camara_revisora,
    p_voto_revisora,
)

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ───────────── cámara revisora ─────────────
print("camara_revisora")
check(camara_revisora("Diputados") == "senado", "Diputados -> Senado revisa")
check(camara_revisora("senado") == "diputados", "Senado -> Diputados revisa")
check(camara_revisora("SENADO") == "diputados", "tolera mayúsculas")
try:
    camara_revisora("comisión bicameral")
    check(False, "cámara desconocida debe levantar ValueError")
except ValueError:
    check(True, "cámara desconocida levanta ValueError")


# ───────────── ajuste 'pasó por origen' ─────────────
print("\najuste_paso_origen")
check(ajuste_paso_origen(0.60, delta=0.0, factor_encogimiento=1.0) == 0.60,
      "delta=0 no cambia nada (no hay efecto)")
check(ajuste_paso_origen(0.60, delta=0.9, factor_encogimiento=0.0) == 0.60,
      "factor=0 no cambia nada = FALLBACK a Manera 1")
check(ajuste_paso_origen(0.60, delta=0.9, factor_encogimiento=1.0) > 0.60,
      "delta>0 con muestra sube la probabilidad")
check(ajuste_paso_origen(0.60, delta=-0.9, factor_encogimiento=1.0) < 0.60,
      "delta<0 la baja")
check(0.0 <= ajuste_paso_origen(0.99, delta=5.0, factor_encogimiento=1.0) <= 1.0,
      "nunca se sale de [0,1] aunque delta sea grande")

# Manera 1 == límite de Manera 2 al encoger a 0 (la propiedad clave del diseño)
for p in (0.2, 0.5, 0.8):
    check(ajuste_paso_origen(p, delta=1.5, factor_encogimiento=0.0) == p,
          f"Manera 1 es el límite exacto de Manera 2 en p={p}")


# ───────────── pipeline completo sobre padrón sintético ─────────────
print("\npipeline completo (padrón sintético)")


def padron_falso(path: Path):
    # Roster chico: 6 de un linaje afirmativo, 4 de uno negativo, vigentes en 2019.
    filas = ["legislador,clave,legislador_id,camara,distrito,bloque,bloque_norm,"
             "desde,hasta,bloque_linaje,fuente,nota"]
    for i in range(6):
        filas.append(f"AF {i},AF{i},leg:af{i},senado,X,BLOQUE_AF,BLOQUE_AF,"
                     f"2017-12-10,2023-12-09,LINAJE_AF,test,")
    for i in range(4):
        filas.append(f"NE {i},NE{i},leg:ne{i},senado,Y,BLOQUE_NE,BLOQUE_NE,"
                     f"2017-12-10,2023-12-09,LINAJE_NE,test,")
    path.write_text("\n".join(filas) + "\n", encoding="utf-8-sig")


bloques = [
    {"bloque": "LINAJE_AF", "linea": "AFIRMATIVO", "desvio": 0.02},
    {"bloque": "LINAJE_NE", "linea": "NEGATIVO", "desvio": 0.02},
]

with tempfile.TemporaryDirectory() as td:
    pf = Path(td) / "padron_senado_historico.csv"
    padron_falso(pf)

    # camara_origen=Diputados -> revisa el Senado (nuestro padrón sintético)
    r = p_voto_revisora("Diputados", "2019-06-01", bloques,
                        padron_file=str(pf), disciplina_path="/no/existe",
                        n_sims=300, seed=1)
    check(r["camara_revisora"] == "senado", "revisora correcta en el resultado")
    check(r["n_roster"] == 10, f"roster point-in-time = 10 (dio {r['n_roster']})")
    check(0.0 <= r["p_aprobacion"] <= 1.0, "p_aprobacion en rango")
    check(r["p_aprobacion"] > 0.9, "6 afirmativos vs 4 negativos -> aprueba casi seguro")
    check(r["manera"] == "1", "sin delta corre en Manera 1")
    check(r["p0"] == r["p_aprobacion"], "en Manera 1, p0 == p_aprobacion")

    # invertir la mayoría: 4 afirm, 6 neg -> ahora NO aprueba
    bloques_inv = [
        {"bloque": "LINAJE_AF", "linea": "NEGATIVO", "desvio": 0.02},
        {"bloque": "LINAJE_NE", "linea": "AFIRMATIVO", "desvio": 0.02},
    ]
    r2 = p_voto_revisora("Diputados", "2019-06-01", bloques_inv,
                         padron_file=str(pf), disciplina_path="/no/existe",
                         n_sims=300, seed=1)
    check(r2["p_aprobacion"] < 0.1, "invertida la mayoría, no aprueba")

    # Manera 2 sobre el mismo caso: delta>0 con muestra sube p respecto de p0
    r3 = p_voto_revisora("Diputados", "2019-06-01", bloques_inv,
                         padron_file=str(pf), disciplina_path="/no/existe",
                         delta=1.2, factor_encogimiento=1.0, n_sims=300, seed=1)
    check(r3["manera"] == "2", "con delta y factor corre en Manera 2")
    check(r3["p_aprobacion"] > r3["p0"], "el ajuste positivo sube sobre la base")

    # fuera de la ventana del padrón: no hay mandato vigente -> error claro
    try:
        p_voto_revisora("Diputados", "2010-01-01", bloques,
                        padron_file=str(pf), disciplina_path="/no/existe")
        check(False, "fecha sin mandato vigente debe romper")
    except ValueError:
        check(True, "fecha fuera de la cobertura del padrón levanta ValueError")


print("\ncámara revisora = Senado usa el padrón histórico por defecto")
from puerta_d import _padron_de  # noqa: E402
check(_padron_de("senado").name == "padron_senado_historico.csv",
      "el Senado apunta al padrón HISTÓRICO, no al de los 72 vigentes")
check(_padron_de("diputados").name == "padron_diputados.csv",
      "Diputados usa su padrón oficial (ya trae los tramos)")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
