# -*- coding: utf-8 -*-
"""La barandilla estructural (ADR-0034): el harness del censo MIDE EL MOTOR, no una copia.

Hasta el 28-09 el harness tenía su propio récord y su propio `perfil`, con el comentario
"espejo exacto de `perfil_legislador`". Divergió dos veces sin que nada fallara: el motor
condicionaba el récord por origen y el harness no (0,19 contra −0,03 desde 2023), y el
harness contaba votos del mismo día. Estos tests fallan si vuelve a pasar.

1. **Contra `nowcast()` real, legislador por legislador.** Un acta real de Diputados, de
   origen EJECUTIVO, que es la PRIMERA votación de su ley en CUALQUIER cámara (así excluir
   la ley no cambia nada —tampoco en la ficha de desvío, que es de las dos cámaras— y el
   harness tiene que dar exactamente lo del motor). Para cada legislador con el mismo
   linaje en el padrón, la `p_si_vota` del harness tiene que ser la de `nowcast()` (que la
   redondea a 4 decimales): los que tienen récord en la era **y, desde D1.0 (auditoría
   2026-09), también los de la rama de bloque**, cuyo desvío sale de la ficha AL DÍA en los
   dos lados. Hasta el 2026-10-01 la rama de bloque no se comparaba (el harness ponía el
   desvío del linaje y el motor el de la ficha con toda la historia).
2. **El caché no filtra entre leyes.** Dos actas del mismo día, de leyes distintas, con
   historia de las dos leyes en fechas anteriores: cada una ve la otra ley y no la suya.
3. **El récord por tema del harness es el del motor** sobre la historia sin la ley.
4. **`perfil` del harness es el del motor** (queda por los estimar_*.py viejos).

    python evaluacion/baseline/tests/test_harness_es_el_motor.py
    (el 1 usa los datos reales y tarda ~1 min; sin datos se saltea avisando)
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
import baseline_voto_individual as H  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


# ── sintético ──────────────────────────────────────────────────────────────────
# 6 legisladores, dos linajes; leyes A y B votadas el 05-03 y el 12-03; el 20-03 se
# votan otra vez A y B (las actas a evaluar). Todo en la era Milei.
rng = np.random.default_rng(5)
filas = []
actas = [("a1", "A", "2024-03-05"), ("b1", "B", "2024-03-05"), ("x1", "X", "2024-03-01"),
         ("a2", "A", "2024-03-12"), ("b2", "B", "2024-03-12"),
         ("a3", "A", "2024-03-20"), ("b3", "B", "2024-03-20")]
for acta, ley, f in actas:
    for i in range(6):
        lin = "PRO" if i < 3 else "UCR"
        # la ley A la votan a favor, la B en contra: si el caché mezclara leyes, se nota
        y = {"A": 1, "B": 0, "X": int(rng.integers(0, 2))}[ley]
        filas.append({"acta_id": acta, "fecha": pd.Timestamp(f), "camara": "diputados",
                      "legislador_id": f"leg:{i}", "bloque_linaje": lin,
                      "conducta": "AFIRMATIVO" if y else "NEGATIVO"})
votos = pd.DataFrame(filas)
leyes = {a: f"ley:{ley}" for a, ley, _ in actas}
origen_map = {a: "EJECUTIVO" for a, _, _ in actas}
cond = pd.DataFrame({"acta_id": [a for a, _, _ in actas],
                     "tema_area": ["ECON" if l == "A" else "TRAB" for _, l, _ in actas],
                     "todas_ids": ["ECON.X;TRAB.Y" if l == "A" else "TRAB.Y" for _, l, _ in actas],
                     "origen": "EJECUTIVO", "origen_lado": "GOBIERNO", "gobierno": "MILEI"})
ctx = H.Contexto(votos, leyes, origen_map, cond, conf_area={})
f3 = pd.Timestamp("2024-03-20")

print("2. el caché no filtra entre leyes")
ra = ctx.record("diputados", f3, "ley:A", "EJECUTIVO", None, "estricta", False)
rb = ctx.record("diputados", f3, "ley:B", "EJECUTIVO", None, "estricta", False)
# a3 (ley A) ve: x1 + b1 + b2 (la B, en contra) -> p_af baja; b3 ve x1 + a1 + a2 (a favor)
pa, _, _, na = ra[("diputados", "leg:0")]
pb, _, _, nb = rb[("diputados", "leg:0")]
check(na == 3 and nb == 3, f"cada acta ve 3 votos previos (x1 + la OTRA ley); vio {na} y {nb}")
check(pa < pb, f"a3 no puede ver la ley A (a favor) y b3 no puede ver la B (en contra): "
      f"p(a3)={pa:.2f} tendría que ser < p(b3)={pb:.2f}")
directo = NP.alineacion_individual(votos[~votos["acta_id"].isin(["a1", "a2"])], origen_map,
                                   "EJECUTIVO", hasta=f3)
check(ra == directo, "el récord del harness para a3 tiene que ser el del motor sin la ley A")
rf = ctx.record("diputados", f3, "ley:A", "EJECUTIVO", None, "fecha", False)
check(rf[("diputados", "leg:0")][3] == 5, "con historia 'fecha' a3 ve las 5 actas anteriores")
rd = ctx.record("diputados", f3, "ley:A", "EJECUTIVO", None, "dia_incluido", False)
check(rd[("diputados", "leg:0")][3] == 7, "con 'dia_incluido' (el `<=` viejo) ve también el 20-03")

print("3. el récord por tema del harness es el del motor")
areas = ctx.areas_del_acta("a3")
check(areas == [("ECON", 1.0), ("TRAB", 1.0)], f"áreas de a3: {areas}")
rt = ctx.record("diputados", f3, "ley:A", "EJECUTIVO", areas, "estricta", True)
base = votos[~votos["acta_id"].isin(["a1", "a2"])]
ind = NP.alineacion_individual(base, origen_map, "EJECUTIVO", hasta=f3)
esperado = NP.alineacion_individual_por_area(base, cond, origen_map, "EJECUTIVO", areas, ind,
                                             hasta=f3)
check(rt == esperado, "el récord por tema del harness difiere del del motor")

print("   ...y P_i sale de perfil_legislador con la postura de proyectar_postura")
sub = votos[votos["acta_id"] == "a3"]
out = ctx.p_legisladores("a3", "diputados", f3, sub, "estricta", False)
from bloque import proyectar_postura  # noqa: E402
post = {p["bloque"]: p for p in proyectar_postura(base, f3, "diputados", origen="EJECUTIVO",
                                                  cond_por_acta=cond)}
p0, n0 = ind[("diputados", "leg:0")][0], ind[("diputados", "leg:0")][3]
esp = NP.perfil_legislador(post["PRO"]["_share_afirm"], post["PRO"]["desvio"], record=p0,
                           n_emitidos=n0)["p_afirma_si_vota"]
check(abs(out["leg:0"][0] - esp) < 1e-12, f"P_i del harness {out['leg:0'][0]} != motor {esp}")

print("4. perfil del harness delega en el motor")
for args in ((0.7, 0.1, 0.9, 12, True), (0.7, 0.1, 0.9, 12, False), (0.3, 0.2, None, 0, False),
             (0.6, 0.05, float("nan"), 0, True)):
    s, dv, r, n, sh = args
    esp = NP.perfil_legislador(s, dv, record=None if (r is None or r != r) else r,
                               n_emitidos=n, shrink=sh)["p_afirma_si_vota"]
    check(abs(H.perfil(s, dv, r, n, sh) - esp) < 1e-15, f"perfil{args} difiere del motor")

print("1. contra nowcast() real, legislador por legislador")
import logging  # noqa: E402
logging.disable(logging.WARNING)
ctx_r = None
try:
    ctx_r = H.Contexto.desde_repo()
except Exception as e:  # noqa: BLE001 — sin datos reales (CI) se saltea; con datos, se compara
    print(f"   SALTEADO (no pude cargar los datos reales: {type(e).__name__}: {e}) -- este es "
          "el test que importa, correlo en la PC")
if ctx_r is not None:
    v = ctx_r.votos
    em = v[v["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    a = em.drop_duplicates("acta_id")[["acta_id", "fecha", "camara"]]
    a = a[(a["camara"] == "diputados") & (a["fecha"] >= "2024-06-01")]
    a = a[a["acta_id"].map(ctx_r.origen_map) == "EJECUTIVO"]
    a["ley"] = a["acta_id"].map(ctx_r.ley_de_acta)
    primera = v.groupby("_ley")["fecha"].min()      # en cualquier cámara (D1.0)
    a = a[a["fecha"] == a["ley"].map(primera)].sort_values(["fecha", "acta_id"])
    check(not a.empty, "no encontré un acta EJECUTIVO que sea la primera de su ley")
    if not a.empty:
        x = a.iloc[len(a) // 2]
        F = pd.Timestamp(x["fecha"])
        print(f"   acta {x['acta_id']} ({F.date()}, ley {x['ley']})")
        sub = em[em["acta_id"] == x["acta_id"]]
        h = ctx_r.p_legisladores(x["acta_id"], "diputados", F, sub, "estricta", False)
        nc = NP.nowcast("diputados", F, origen="EJECUTIVO", n_sims=50)
        leg = {r["legislador_id"]: r for r in nc["camaras"]["origen"]["legisladores"]}
        lin_voto = dict(zip(sub["legislador_id"], sub["bloque_linaje"]))
        comparados, de_bloque, distintos = 0, 0, []
        for lid, (p, fuente, *_rest) in h.items():
            r = leg.get(lid)
            if r is None or r["bloque"] != lin_voto.get(lid):
                continue
            comparados += 1
            de_bloque += int(r["n_emitidos"] < NP.MIN_HIST_INDIVIDUAL)
            if abs(round(p, 4) - r["p_si_vota"]) > 1e-4 + 1e-9:
                distintos.append((lid, round(p, 4), r["p_si_vota"], fuente))
        print(f"   comparados {comparados} legisladores ({de_bloque} de la rama de bloque); "
              f"distintos {len(distintos)}")
        check(comparados >= 100, f"muy pocos legisladores comparables ({comparados}): el test "
              "no prueba nada")
        check(de_bloque >= 1, "ningún legislador de la rama de bloque en el acta: la ficha al "
              "día no se está comparando (D1.0)")
        check(not distintos, f"el harness y nowcast() difieren en {len(distintos)}: {distintos[:5]}")
logging.disable(logging.NOTSET)

print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for x in fallos:
        print(f"  - {x}")
    sys.exit(1)
print("todos los tests pasaron")
