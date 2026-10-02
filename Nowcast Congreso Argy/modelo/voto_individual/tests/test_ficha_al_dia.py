# -*- coding: utf-8 -*-
"""La ficha de desvío AL DÍA (auditoría 2026-09, D1.0, decisión de Franco: «eliminemos la fuga del sistema»).

`disciplina.FichaAlDia` aplica la regla de `indice_por_legislador` sólo con los votos de fecha < F (y, en el harness,
sin la misma ley). Estos chequeos fijan que es LA MISMA regla y que no mira el futuro, sobre la canónica real (viaja
por git, así que corre también en el CI):

1. Cortada después de la última acta, da EXACTAMENTE `indice_por_legislador` sobre la misma tabla (las seis columnas
   que lee `ensemble.roster_nominal`, en todos los legisladores).
2. Contra una referencia directa (filtrar la tabla y llamar a `indice_por_legislador`) en 200 pares (F, legislador)
   al azar, con semilla 7, con y sin ley excluida, y en tres casos fijos elegidos por regla: una F dentro de una
   presidencia de Diputados (la del presidente), un legislador con votos en las dos cámaras, y un legislador cuyos
   votos del último año antes de F son todos de la ley excluida.
3. La tabla por voto no mira el futuro: armada sobre la canónica recortada a una fecha T da lo mismo, fila por fila,
   que la completa restringida a fecha < T (dos cortes: uno dentro de la presidencia de Monzó y otro de la de Menem,
   donde decide la exclusión del presidente «al día»).
4. Control positivo: la referencia detecta una ficha que ve el día de corte.

    python modelo/voto_individual/tests/test_ficha_al_dia.py      (≈ 1 min)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import CANONICA_CLEAN, RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "modelo" / "voto_individual" / "src"))
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import disciplina as D  # noqa: E402

SEMILLA = 7
N_PARES = 200
CORTES_TABLA = ("2016-06-01", "2024-03-01")

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def iguales(a: dict, b: dict) -> list[str]:
    """Columnas de la ficha en las que `a` y `b` difieren (NaN == NaN)."""
    out = []
    for c in D.COLUMNAS_FICHA:
        x, y = a.get(c, np.nan), b.get(c, np.nan)
        if not ((pd.isna(x) and pd.isna(y)) or x == y):
            out.append(f"{c}: {x} != {y}")
    return out


def referencia(tab: pd.DataFrame, ley_fila: np.ndarray, lid: str, corte, ley=None) -> dict | None:
    m = (tab["legislador_id"].values == lid) & (tab["fecha"].values < np.datetime64(pd.Timestamp(corte)))
    if ley is not None:
        m &= ley_fila != ley
    sub = tab[m]
    if sub.empty:
        return None
    return D.indice_por_legislador(sub, set()).iloc[0][list(D.COLUMNAS_FICHA)].to_dict()


print("cargando la tabla por voto desde la canónica…")
tab = D.tabla_desvios_al_dia(CANONICA_CLEAN, completa=True)
from baseline_voto_individual import ley_por_acta  # noqa: E402
leyes = ley_por_acta(RAIZ)
acta = tab["acta_id"].astype(str)
ley_fila = acta.map(leyes)
ley_fila = ley_fila.where(ley_fila.notna(), "acta:" + acta).astype(str).values
fa = D.FichaAlDia(tab, leyes)
print(f"  {len(tab)} votos con fecha, {tab['legislador_id'].nunique()} legisladores")

# 1 ────────────────────────────────────────────────────────────────────────────────
print("1. después de la última acta = indice_por_legislador sobre la misma tabla")
fin = tab["fecha"].max() + pd.Timedelta(days=1)
mia = fa.al(fin)
ref = D.indice_por_legislador(tab, set()).set_index("legislador_id")[list(D.COLUMNAS_FICHA)].to_dict("index")
check(set(mia) == set(ref), f"legisladores distintos: {len(set(mia) ^ set(ref))}")
dist = {lid: iguales(mia[lid], ref[lid]) for lid in set(mia) & set(ref)}
dist = {k: v for k, v in dist.items() if v}
check(not dist, f"{len(dist)} legisladores con otra ficha: {list(dist.items())[:3]}")
print(f"  {len(mia)} legisladores; distintos {len(dist)}")

# 2 ────────────────────────────────────────────────────────────────────────────────
print("2. contra la referencia directa: 200 pares al azar (con y sin ley) y 3 casos fijos")
rng = np.random.default_rng(SEMILLA)
filas = rng.choice(len(tab), size=N_PARES, replace=False)
casos = []
for i in filas:                      # F = la fecha de un voto del legislador; ley = la de un voto anterior suyo
    lid, corte = str(tab.at[i, "legislador_id"]), tab.at[i, "fecha"]
    previos = np.flatnonzero((tab["legislador_id"].values == lid) & (tab["fecha"].values < np.datetime64(corte)))
    ley = ley_fila[previos[rng.integers(len(previos))]] if len(previos) else None
    casos.append((lid, corte, None))
    casos.append((lid, corte, ley))
# casos fijos, por regla. El presidente se busca en la canónica, no en la tabla: la exclusión «al día» saca sus
# filas de la presidencia (eso mismo es lo que se prueba: su ficha a una fecha dentro de la presidencia)
canon_v = pd.read_parquet(Path(CANONICA_CLEAN) / "votos_resuelto.parquet", columns=["acta_id", "legislador_id",
                                                                                   "legislador_nombre"])
canon_a = pd.read_parquet(Path(CANONICA_CLEAN) / "actas_canonico.parquet", columns=["acta_id", "camara", "fecha"])
canon_v = canon_v.merge(canon_a, on="acta_id", how="left")
menem = canon_v[(canon_v["camara"] == "diputados")
                & canon_v["legislador_nombre"].astype(str).str.upper().str.contains("MENEM")
                & (pd.to_datetime(canon_v["fecha"], errors="coerce") >= "2023-12-10")]
check(not menem.empty, "no encontré a MENEM en Diputados desde 2023-12-10 en la canónica (caso fijo de la presidencia)")
if not menem.empty:
    lid_menem = str(menem["legislador_id"].mode().iat[0])
    n_pres = int(((tab["legislador_id"] == lid_menem) & (tab["fecha"] >= "2023-12-10")).sum())
    print(f"  presidente: {lid_menem}; filas de su presidencia que quedan en la tabla: {n_pres} de {len(menem)}")
    casos.append((lid_menem, pd.Timestamp("2024-06-01"), None))
dos = tab.groupby("legislador_id")["camara"].nunique()
lid_dos = str(dos[dos > 1].index.sort_values()[0])
casos.append((lid_dos, tab["fecha"].max() + pd.Timedelta(days=1), None))
# un legislador cuyos votos del último año antes de F son todos de una sola ley: F = el día después de su último voto
t_fin = tab.assign(_ley=ley_fila).groupby("legislador_id")
caso3 = None
for lid, g in t_fin:
    ult = g[g["anio"] == g["anio"].max()]
    if ult["_ley"].nunique() == 1 and len(g) > len(ult):
        caso3 = (str(lid), g["fecha"].max() + pd.Timedelta(days=1), ult["_ley"].iat[0])
        break
check(caso3 is not None, "no encontré un legislador con todo su último año en una sola ley (caso fijo 3)")
if caso3:
    casos.append(caso3)
malos = []
for lid, corte, ley in casos:
    a = fa.al(corte, [lid], excluir_ley=ley).get(lid)
    b = referencia(tab, ley_fila, lid, corte, ley)
    if (a is None) != (b is None) or (a is not None and iguales(a, b)):
        malos.append((lid, str(pd.Timestamp(corte).date()), ley, a, b))
check(not malos, f"{len(malos)} de {len(casos)} casos difieren de la referencia: {malos[:2]}")
print(f"  {len(casos)} casos (incluidos 3 fijos); distintos {len(malos)}")
if caso3:
    a = fa.al(caso3[1], [caso3[0]], excluir_ley=caso3[2]).get(caso3[0])
    b = fa.al(caso3[1], [caso3[0]]).get(caso3[0])
    check(a is not None and b is not None and a["n_reciente"] != b["n_reciente"],
          "en el caso 3, excluir la ley no cambió el «reciente»: el caso no ejercita el borde")

# 3 ────────────────────────────────────────────────────────────────────────────────
print("3. la tabla por voto no mira el futuro (canónica recortada)")
votos = pd.read_parquet(Path(CANONICA_CLEAN) / "votos_resuelto.parquet")
actas_c = pd.read_parquet(Path(CANONICA_CLEAN) / "actas_canonico.parquet")
f_acta = pd.to_datetime(actas_c["fecha"], errors="coerce")
claves = ["acta_id", "legislador_id"]
for T in CORTES_TABLA:
    with tempfile.TemporaryDirectory() as tmp:
        a_t = actas_c[f_acta < pd.Timestamp(T)]
        a_t.to_parquet(Path(tmp) / "actas_canonico.parquet", index=False)
        votos[votos["acta_id"].isin(a_t["acta_id"])].to_parquet(Path(tmp) / "votos_resuelto.parquet", index=False)
        t_rec = D.tabla_desvios_al_dia(Path(tmp), completa=True)
    completa = tab[tab["fecha"] < pd.Timestamp(T)]
    x = completa.set_index(claves)[["desvio", "presente"]].sort_index()
    y = t_rec.set_index(claves)[["desvio", "presente"]].sort_index()
    mismas = x.index.equals(y.index)
    check(mismas, f"corte {T}: la tabla recortada tiene otras filas ({len(x)} contra {len(y)})")
    if mismas:
        dd = float(np.abs(x["desvio"].values - y["desvio"].values).max())
        check(dd == 0 and (x["presente"].values == y["presente"].values).all(),
              f"corte {T}: el desvío de algún voto anterior cambia al recortar el futuro (max|Δ| {dd})")
        print(f"  corte {T}: {len(x)} votos, idénticos")

# 4 ────────────────────────────────────────────────────────────────────────────────
print("4. control positivo: la referencia ve una ficha que mira el día de corte")
lid, corte, _ = casos[0]
mira = fa.al(corte + pd.Timedelta(days=1), [lid]).get(lid)
check(mira is not None and bool(iguales(mira, referencia(tab, ley_fila, lid, corte) or {})),
      "una ficha que ve el día de corte no se distingue de la buena: el chequeo 2 no podría fallar")

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for x in fallos:
        print(f"  - {x}")
    sys.exit(1)
print("todos los tests pasaron")
