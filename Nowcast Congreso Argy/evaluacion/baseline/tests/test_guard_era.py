# -*- coding: utf-8 -*-
"""El guard de era y los dos atajos de rendimiento que lo hacen medible.

Lo que fija, y por que cada cosa:

1. **`era_de` devuelve el ARRANQUE del gobierno que contiene la fecha**, y usa el mismo
   calendario que `variables/bloque` — el que ya usa `proyectar_postura` para su propio
   corte. Dos calendarios distintos para el record individual y para la postura de
   bloque serian exactamente el bug que esto cierra.
2. **La bandera apagada no mueve nada.** `alineacion_individual` con `guard_era=False`
   tiene que dar identico a antes: misma fecha fija, mismo resultado.
3. **La bandera prendida arregla el backtest.** Con fecha fija, un nowcast anterior a
   2023-12-10 deja el conjunto VACIO y TODOS caen a la rama de bloque; con el guard,
   cada fecha usa su propia era. Medido el 06-09: 478 legisladores al 2026-06-01 y
   CERO al 2022, 2018 y 2013.
4. **El atajo de cumsum es identico a `shift(1).expanding()`.** `medir_guard_era`
   reemplaza el `transform(lambda)` por cumsum porque sobre un millon de filas el
   original tarda minutos. Un atajo que no se verifica es un resultado inventado, asi
   que se compara contra la version lenta fila por fila.
5. **`eras_de` (una vez por fecha distinta) es identico a mapear fila por fila.**

    python evaluacion/baseline/tests/test_guard_era.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _repo() -> Path:
    p = Path(__file__).resolve()
    for c in [p, *p.parents]:
        if (c / "coordinacion").is_dir() and (c / "variables").is_dir():
            return c
    raise FileNotFoundError("no encontre la raiz del repo")


REPO = _repo()
sys.path.insert(0, str(REPO / "modelo" / "ensemble" / "src"))
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "evaluacion" / "baseline" / "src"))

import nowcast_puertas as NP  # noqa: E402
import medir_guard_era as MG  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


print("era_de devuelve el arranque del gobierno que contiene la fecha")
for fecha, esperado in (("2026-06-01", "2023-12-10"), ("2023-12-10", "2023-12-10"),
                        ("2023-12-09", "2019-12-10"), ("2022-06-01", "2019-12-10"),
                        ("2018-06-01", "2015-12-10"), ("2015-12-09", "1900-01-01")):
    check(NP.era_de(fecha) == esperado,
          f"era_de({fecha}) tendria que dar {esperado}, dio {NP.era_de(fecha)}")

print("el calendario es el de variables/bloque, no una copia")
from bloque import _GOBIERNOS  # noqa: E402
check([g[0] for g in _GOBIERNOS] == ["1900-01-01", "2015-12-10", "2019-12-10", "2023-12-10"],
      "cambio _GOBIERNOS en variables/bloque: revisar era_de y esta lista")
check(NP.ERA_FIJA == "2023-12-10", "ERA_FIJA es la fecha que se usaba antes del guard")
check(NP.GUARD_ERA is False or NP.GUARD_ERA is True, "GUARD_ERA tiene que ser booleano")

print("la bandera APAGADA no mueve nada, y la PRENDIDA arregla el backtest")
fechas = pd.to_datetime(["2018-03-01", "2018-04-01", "2018-05-01", "2018-06-01",
                         "2022-03-01", "2022-04-01", "2022-05-01", "2022-06-01",
                         "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"])
filas = []
for i, f in enumerate(fechas):
    for lid in ("leg:a", "leg:b"):
        filas.append({"fecha": f, "camara": "diputados", "legislador_id": lid,
                      "acta_id": f"a{i}", "conducta": "AFIRMATIVO" if i % 2 else "NEGATIVO",
                      "bloque_linaje": "PRO"})
v = pd.DataFrame(filas)
om = {}
for corte, esperado_off, esperado_on in (("2024-12-31", 2, 2),
                                         ("2022-12-31", 0, 2),
                                         ("2018-12-31", 0, 2)):
    off = NP.alineacion_individual(v, om, None, hasta=corte, guard_era=False)
    on = NP.alineacion_individual(v, om, None, hasta=corte, guard_era=True)
    check(len(off) == esperado_off,
          f"con la bandera APAGADA y hasta={corte} tendrian que salir {esperado_off}, "
          f"salieron {len(off)}")
    check(len(on) == esperado_on,
          f"con la bandera PRENDIDA y hasta={corte} tendrian que salir {esperado_on}, "
          f"salieron {len(on)}")

print("un era_desde explicito manda sobre la bandera (lo usan los tests viejos)")
exp = NP.alineacion_individual(v, om, None, era_desde="2000-01-01", hasta="2024-12-31",
                               guard_era=True)
check(len(exp) == 2, f"era_desde explicito tendria que respetarse, dio {len(exp)}")

print("el atajo de cumsum da lo MISMO que shift(1).expanding()")
rng = np.random.default_rng(11)
n = 600
d = pd.DataFrame({
    "af": rng.integers(0, 2, n),
    "legislador_id": rng.choice([f"leg:{i}" for i in range(9)], n),
    "_era": rng.choice(["1900-01-01", "2015-12-10", "2023-12-10"], n),
    "bloque_linaje": rng.choice(["PRO", "UCR"], n),
}).reset_index(drop=True)
for llave in (["legislador_id"], ["legislador_id", "_era"], ["bloque_linaje", "_era"]):
    rapido_m, rapido_n = MG._walk_forward(d, llave)
    g = d.groupby(llave, sort=False)["af"]
    lento_m = g.transform(lambda s: s.shift(1).expanding().mean())
    lento_n = g.transform(lambda s: s.shift(1).expanding().count()).fillna(0)
    check(bool(np.allclose(rapido_m.fillna(-9), lento_m.fillna(-9))),
          f"la media rapida difiere de la lenta con llave={llave}")
    check(bool((rapido_n.values == lento_n.values).all()),
          f"el n rapido difiere del lento con llave={llave}")
    # y que el test sirva de algo: la version lenta NO puede ser trivial
    check(lento_m.notna().sum() > n * 0.8,
          f"la comparacion no cubre casi nada con llave={llave}")

print("eras_de (una vez por fecha distinta) = mapear fila por fila")
f = pd.Series(pd.to_datetime(["2013-01-01", "2013-01-01", "2018-06-01", "2022-06-01",
                              "2026-06-01", "2026-06-01"]))
check(list(MG.eras_de(f)) == [NP.era_de(x) for x in f],
      "eras_de tiene que dar lo mismo que mapear una por una")

print("el walk-forward no mira el futuro: el primer voto de cada grupo no tiene record")
m, cnt = MG._walk_forward(d, ["legislador_id", "_era"])
primeros = d.groupby(["legislador_id", "_era"], sort=False).head(1).index
check(bool(m.loc[primeros].isna().all()),
      "el primer voto de cada (legislador, era) tiene que quedar sin record")
check(bool((cnt.loc[primeros] == 0).all()), "y con n = 0")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for x in fallos:
        print(f"  - {x}")
    sys.exit(1)
print("todos los tests pasaron")
