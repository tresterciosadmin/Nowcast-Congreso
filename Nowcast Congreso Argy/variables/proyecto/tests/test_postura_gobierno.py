"""Tests offline de postura_gobierno — sin red, sin datos reales.

Fija los casos que motivaron el módulo: el rechazo de DNU y la insistencia
invierten el signo (afirmativo = contra el gobierno), y la alineación tiene que
leer al kirchnerismo como oposición aunque vote afirmativo un rechazo.

    python variables/proyecto/tests/test_postura_gobierno.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from postura_gobierno import (  # noqa: E402
    alineacion_por_bloque,
    construir,
    postura_gobierno,
    tipo_mocion,
)

fallos: list[str] = []
n = 0


def check(cond, msg):
    global n
    n += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("tipo_mocion")
check(tipo_mocion("Rechazo del Decreto del Poder Ejecutivo Nº 656/24") == "RECHAZO_GOB",
      "rechazo de decreto")
check(tipo_mocion("Rechazo del decreto de facultades delegadas Nº 462/25") == "RECHAZO_GOB",
      "rechazo de facultades delegadas")
check(tipo_mocion("Insistencia ante el veto presidencial al proyecto...") == "INSISTENCIA",
      "insistencia sobre veto")
check(tipo_mocion("Moción de orden del senador Recalde") == "PROC", "moción de orden")
check(tipo_mocion("PLAN DE LABOR") == "PROC", "plan de labor")
check(tipo_mocion("Ley de Movilidad Previsional. O.D. 78/2024") == "ESTANDAR", "ley normal")
check(tipo_mocion(None) == "ESTANDAR", "título nulo -> estándar, no rompe")

print("\npostura_gobierno (qué vota el gobierno para ganar)")
check(postura_gobierno("RECHAZO_GOB", "EJECUTIVO") == "NEGATIVO",
      "rechazo de un decreto propio: el gobierno vota NEGATIVO (no rechazar)")
check(postura_gobierno("INSISTENCIA", "OPOSICION") == "NEGATIVO",
      "insistencia sobre veto: el gobierno vota NEGATIVO")
check(postura_gobierno("ESTANDAR", "EJECUTIVO") == "AFIRMATIVO", "ley del PE: gobierno AFIRMATIVO")
check(postura_gobierno("ESTANDAR", "OFICIALISMO") == "AFIRMATIVO", "ley oficialista: AFIRMATIVO")
check(postura_gobierno("ESTANDAR", "OPOSICION") == "NEGATIVO", "ley opositora: gobierno NEGATIVO")
check(postura_gobierno("ESTANDAR", "DESCONOCIDO") is None, "origen desconocido: sin postura")
check(postura_gobierno("PROC", "EJECUTIVO") is None, "procedimental: sin postura")

print("\nconstruir + alineación: el rechazo se lee bien")
actas = pd.DataFrame([
    {"acta_id": "a1", "titulo": "Ley de Bases. O.D. 1"},                 # estándar, PE
    {"acta_id": "a2", "titulo": "Rechazo del DNU 340/25"},               # rechazo
    {"acta_id": "a3", "titulo": "Moción de orden"},                      # proc -> excluida
])
origen = pd.DataFrame([
    {"acta_id": "a1", "origen": "EJECUTIVO"},   # gobierno quiere AFIRMATIVO
    {"acta_id": "a2", "origen": "OPOSICION"},   # da igual el origen: rechazo -> gobierno NEGATIVO
    {"acta_id": "a3", "origen": "DESCONOCIDO"},
])
pg = construir(actas, origen).set_index("acta_id")
check(pg.loc["a1", "postura_gobierno"] == "AFIRMATIVO", "ley del PE")
check(pg.loc["a2", "postura_gobierno"] == "NEGATIVO", "rechazo de DNU: gobierno NEGATIVO")
check(pg.loc["a3", "postura_gobierno"] is None, "procedimental sin postura")

# Un bloque OPOSITOR: vota NEGATIVO la ley del gobierno (a1) y AFIRMATIVO el rechazo (a2).
# Con share afirmativo daría 50%; con alineación al gobierno da 0% (oposición pura).
votos = pd.DataFrame([
    {"acta_id": "a1", "bloque_linaje": "OPO", "voto": "NEGATIVO"},   # contra la ley del gob
    {"acta_id": "a2", "bloque_linaje": "OPO", "voto": "AFIRMATIVO"}, # a favor de rechazar el DNU
    {"acta_id": "a1", "bloque_linaje": "OFI", "voto": "AFIRMATIVO"}, # con la ley del gob
    {"acta_id": "a2", "bloque_linaje": "OFI", "voto": "NEGATIVO"},   # contra rechazar el DNU
    {"acta_id": "a3", "bloque_linaje": "OPO", "voto": "AFIRMATIVO"}, # proc: se ignora
])
al = alineacion_por_bloque(votos, construir(actas, origen)).set_index("bloque_linaje")
check(al.loc["OPO", "alineacion"] == 0.0,
      "el opositor: 0% alineado con el gobierno, pese a votar afirmativo el rechazo "
      "(share afirmativo lo daría 50%)")
check(al.loc["OFI", "alineacion"] == 1.0, "el oficialista: 100% alineado")
check(int(al.loc["OPO", "n"]) == 2, "la procedimental no cuenta")

print(f"\n{n - len(fallos)}/{n} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print("  -", f)
    sys.exit(1)
print("todos los tests pasaron")
