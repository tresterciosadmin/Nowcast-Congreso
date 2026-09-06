# -*- coding: utf-8 -*-
"""La MISMA votacion entrando dos veces con dos `acta_id` distintos.

**Por que existe.** El dedup de `build.py` es por `acta_id`, asi que dos ingestores que le
ponen distinto id a la misma votacion pasan los dos. El 06-09-2026 se midio que eso pasa
con **274 actas y 68.282 votos, el 6,7% de la canonica**: `ckan_diputados:361` y
`argentinadatos:diputados:361` son la misma sesion del 2012-05-23, con 257 votos cada una
e identicas voto por voto. Nunca dio error.

Lo que fija:

1. **Dos actas de FUENTES DISTINTAS, misma camara, misma fecha y mismo recuento** salen
   marcadas. Es la evidencia fuerte: dos votaciones distintas el mismo dia no dan el mismo
   reparto exacto por casualidad.
2. **Dos actas de la MISMA fuente no se marcan**, aunque coincidan: pueden ser la votacion
   en general y la votacion en particular del mismo proyecto.
3. **Distinta camara nunca es la misma votacion.**
4. **Distinto recuento tampoco.**
5. **Sin fecha, el par sale marcado como INDICIO y no como evidencia** (es el caso de
   `manual_2026`). ⚠️ La primera version del control agrupaba SOLO por recuento y devolvia
   12.469 pares, casi todos ruido: sin el dia, el recuento coincide por casualidad seguido.
6. **Un acta chica no se marca**: con 20 votos el recuento colisiona facil. `MIN_VOTOS_GEMELA`.

    python datos/canonica/tests/test_actas_gemelas.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build import MIN_VOTOS_GEMELA, actas_gemelas  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _votos(aid, af, ne, ab=0):
    return ([{"acta_id": aid, "voto": "AFIRMATIVO"} for _ in range(af)]
            + [{"acta_id": aid, "voto": "NEGATIVO"} for _ in range(ne)]
            + [{"acta_id": aid, "voto": "ABSTENCION"} for _ in range(ab)])


def _actas(filas):
    return pd.DataFrame([{"acta_id": a, "camara": c, "fuente": f, "titulo": "t", "fecha": d}
                         for a, c, f, d in filas])


print("misma camara + misma fecha + mismo recuento + fuentes distintas -> se marca")
g = actas_gemelas(
    _actas([("A", "diputados", "argentinadatos", "2020-01-01"),
            ("B", "diputados", "ckan_diputados", "2020-01-01")]),
    pd.DataFrame(_votos("A", 30, 20) + _votos("B", 30, 20)))
check(len(g) == 1, f"tendria que salir 1 par, salieron {len(g)}")
check(len(g) and g.iloc[0]["evidencia"].startswith("misma fecha"),
      "con fecha, la evidencia es fuerte")

print("la MISMA fuente no se marca (puede ser en general y en particular)")
g = actas_gemelas(
    _actas([("A", "diputados", "ckan_diputados", "2020-01-01"),
            ("B", "diputados", "ckan_diputados", "2020-01-01")]),
    pd.DataFrame(_votos("A", 30, 20) + _votos("B", 30, 20)))
check(len(g) == 0, f"misma fuente no es gemela: salieron {len(g)}")

print("distinta camara, distinta fecha y distinto recuento: ninguno se marca")
for filas, vs, que in (
    ([("A", "diputados", "argentinadatos", "2020-01-01"),
      ("B", "senado", "ckan_diputados", "2020-01-01")], _votos("A", 30, 20) + _votos("B", 30, 20),
     "camara distinta"),
    ([("A", "diputados", "argentinadatos", "2020-01-01"),
      ("B", "diputados", "ckan_diputados", "2020-06-01")], _votos("A", 30, 20) + _votos("B", 30, 20),
     "fecha distinta"),
    ([("A", "diputados", "argentinadatos", "2020-01-01"),
      ("B", "diputados", "ckan_diputados", "2020-01-01")], _votos("A", 30, 20) + _votos("B", 25, 25),
     "recuento distinto"),
):
    g = actas_gemelas(_actas(filas), pd.DataFrame(vs))
    check(len(g) == 0, f"{que}: no tendria que marcarse, salieron {len(g)}")

print("un acta chica no se marca: con pocos votos el recuento colisiona facil")
n = MIN_VOTOS_GEMELA - 2
g = actas_gemelas(
    _actas([("A", "diputados", "argentinadatos", "2020-01-01"),
            ("B", "diputados", "ckan_diputados", "2020-01-01")]),
    pd.DataFrame(_votos("A", n, 0) + _votos("B", n, 0)))
check(len(g) == 0, f"con {n} votos (< {MIN_VOTOS_GEMELA}) no se marca: salieron {len(g)}")

print("sin fecha: sale como INDICIO, no como evidencia (el caso de manual_2026)")
g = actas_gemelas(
    _actas([("A", "senado", "argentinadatos", "2026-03-01"),
            ("M", "senado", "manual_2026", None)]),
    pd.DataFrame(_votos("A", 40, 20) + _votos("M", 40, 20)))
check(len(g) == 1, f"tendria que salir 1 par, salieron {len(g)}")
check(len(g) and "INDICIO" in g.iloc[0]["evidencia"],
      f"sin fecha tiene que decir INDICIO: dijo {g.iloc[0]['evidencia'] if len(g) else None!r}")

print("el control NO borra nada: devuelve un reporte")
check(isinstance(g, pd.DataFrame) and {"acta_a", "acta_b", "fuente_a", "fuente_b"} <= set(g.columns),
      "tiene que devolver los dos lados del par para que decida una persona")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
