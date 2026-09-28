# -*- coding: utf-8 -*-
"""La historia del récord no puede traer la respuesta (ADR-0034, URGENTE U1).

Lo que fija, y por qué:

1. **Dos actas de la MISMA ley el MISMO día: la segunda no puede usar la primera.** Es el
   caso que infló el skill publicado de 0,092 a 0,161: el art. 3 "aprendía" de los arts.
   1 y 2, votados minutos antes y con el mismo resultado.
2. **Tampoco una votación de la misma ley en una fecha ANTERIOR.** La general del martes
   no es historia legítima para la particular del jueves: no es una observación
   independiente (1.070 actas son 310 leyes, ADR-0032).
3. **Lo de OTRA ley, de fecha anterior, sí cuenta.** Si el corte se come todo, el test
   pasa por la razón equivocada.
4. **El modo viejo ("fila") SÍ tiene la fuga.** Si deja de tenerla, este test ya no
   prueba nada: el caso sintético dejó de ejercitar el bug.
5. **El motor corta con `<`**: un backtest fechado el día de una sesión no ve ese día.
6. **Las claves de ley se unen**: un acta con `proyecto_id` y otra sólo con expediente de
   la misma ley quedan en la misma ley.

    python evaluacion/baseline/tests/test_historia_sin_fuga.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))

import nowcast_puertas as NP  # noqa: E402
from baseline_voto_individual import agrupar_leyes  # noqa: E402
from medir_fuga_historia import record_previo  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# Un legislador, cinco actas, en el orden en que el harness las ve (por fecha):
#   a0  ley Y  01-03  NEGATIVO    <- otra ley, antes: historia legítima
#   a1  ley X  05-03  AFIRMATIVO  <- general de X
#   a2  ley X  12-03  AFIRMATIVO  <- particular de X, otro día
#   a3  ley Z  20-03  AFIRMATIVO  <- art. 1 de Z
#   a4  ley Z  20-03  AFIRMATIVO  <- art. 2 de Z, MISMO día
filas = [("a0", "Y", "2024-03-01", 0), ("a1", "X", "2024-03-05", 1),
         ("a2", "X", "2024-03-12", 1), ("a3", "Z", "2024-03-20", 1),
         ("a4", "Z", "2024-03-20", 1)]
v = pd.DataFrame([{"acta_id": a, "_ley": ley, "fecha": pd.Timestamp(f), "af": y,
                   "legislador_id": "leg:1", "_era": "2023-12-10"} for a, ley, f, y in filas])
v = v.sort_values("fecha").reset_index(drop=True)
por_acta = {h: dict(zip(v["acta_id"], zip(*record_previo(v, ["legislador_id", "_era"], h))))
            for h in ("fila", "fecha", "estricta")}

print("1. misma ley, mismo día: la segunda acta no ve a la primera")
# a4 (ley Z, 20-03): historia legítima = votos de fecha < 20-03 y ley != Z = a0, a1, a2
check(por_acta["estricta"]["a4"] == (3.0, 2.0),
      f"a4 estricta tendría que ser (3, 2) = a0+a1+a2; dio {por_acta['estricta']['a4']}")
check(por_acta["fecha"]["a4"] == (3.0, 2.0),
      f"a4 con corte por fecha tendría que ser (3, 2); dio {por_acta['fecha']['a4']}")
check(por_acta["estricta"]["a3"] == por_acta["estricta"]["a4"],
      "dos actas de la misma ley el mismo día tienen que tener LA MISMA historia")

print("2. misma ley, fecha anterior: tampoco es historia")
check(por_acta["estricta"]["a2"] == (1.0, 0.0),
      f"a2 (ley X) sólo puede ver a0 (ley Y): esperaba (1, 0), dio {por_acta['estricta']['a2']}")
check(por_acta["fecha"]["a2"] == (2.0, 1.0),
      f"con corte sólo por fecha a2 ve a0 y a1: esperaba (2, 1), dio {por_acta['fecha']['a2']}")

print("3. otra ley, antes: sí cuenta")
check(por_acta["estricta"]["a1"] == (1.0, 0.0),
      f"a1 tiene que ver a0 (otra ley, antes): dio {por_acta['estricta']['a1']}")
check(por_acta["estricta"]["a0"] == (0.0, 0.0), "a0 es el primer voto: sin historia")

print("4. el modo viejo tiene la fuga (si no, este test no prueba nada)")
n_fila_a4 = por_acta["fila"]["a4"][0]
check(n_fila_a4 == 4.0, f"con shift(1) a4 ve a a3 (misma ley, mismo día): n tendría que ser 4, "
      f"dio {n_fila_a4}")

print("   ...y el test de arriba no depende del orden dentro del día")
v2 = v.iloc[[0, 1, 2, 4, 3]].reset_index(drop=True)
r2 = dict(zip(v2["acta_id"], zip(*record_previo(v2, ["legislador_id", "_era"], "estricta"))))
check(r2 == por_acta["estricta"], "invertir el orden dentro del día cambió la historia estricta")

print("   ...y con muchos legisladores al azar, 'estricta' = definición por fuerza bruta")
rng = np.random.default_rng(3)
N = 400
d = pd.DataFrame({"legislador_id": rng.choice(["l1", "l2", "l3"], N),
                  "_era": "e", "fecha": pd.to_datetime("2024-01-01")
                  + pd.to_timedelta(rng.integers(0, 40, N), unit="D"),
                  "_ley": rng.choice(list("ABCDEFG"), N), "af": rng.integers(0, 2, N)})
d = d.sort_values("fecha").reset_index(drop=True)
n_r, a_r = record_previo(d, ["legislador_id", "_era"], "estricta")
ok = True
for i in range(N):
    m = ((d["legislador_id"] == d.at[i, "legislador_id"]) & (d["fecha"] < d.at[i, "fecha"])
         & (d["_ley"] != d.at[i, "_ley"]))
    if n_r[i] != m.sum() or a_r[i] != d.loc[m, "af"].sum():
        ok = False
        break
check(ok, "record_previo('estricta') difiere de la definición por fuerza bruta")

print("5. el motor corta con `<`: el día de la sesión no es historia")
vm = pd.DataFrame([{"acta_id": a, "fecha": pd.Timestamp(f), "camara": "diputados",
                    "legislador_id": "leg:1", "bloque_linaje": "PRO",
                    "conducta": "AFIRMATIVO" if y else "NEGATIVO"} for a, _, f, y in filas])
r = NP.alineacion_individual(vm, {}, None, hasta="2024-03-20", guard_era=True)
p, n_tot, _, n_emit = r[("diputados", "leg:1")]
check(n_emit == 3 and abs(p - 2 / 3) < 1e-12,
      f"al 20-03 el motor tiene que ver a0, a1, a2 (n=3, p=2/3), no las actas del 20-03; "
      f"dio n={n_emit}, p={p:.3f}")
r = NP.alineacion_individual(vm, {}, None, hasta="2024-03-21", guard_era=True)
check(r[("diputados", "leg:1")][3] == 5, "al día siguiente sí ve las del 20-03")

print("6. las claves de ley se unen (proyecto_id y expediente son la misma ley)")
g = agrupar_leyes([("a1", "pid:HCDN1"), ("a2", "pid:HCDN1"), ("a2", "exp:0016-PE-2019"),
                   ("a3", "exp:0016-PE-2019"), ("a4", "exp:0099-D-2020")])
check(g["a1"] == g["a2"] == g["a3"], f"a1-a2 comparten pid y a2-a3 expediente: una ley; {g}")
check(g["a4"] != g["a1"], "a4 es otra ley")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for x in fallos:
        print(f"  - {x}")
    sys.exit(1)
print("todos los tests pasaron")
