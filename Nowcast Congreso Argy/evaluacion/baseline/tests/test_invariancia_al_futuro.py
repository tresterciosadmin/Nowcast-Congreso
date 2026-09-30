# -*- coding: utf-8 -*-
"""INVARIANCIA AL FUTURO sobre actas reales (auditoría 2026-09: Fase 2 y, como test de la suite, ítem B2).

IDEA. Si el motor + el harness no ven el futuro ni la misma ley, entonces CORROMPER en memoria todo voto de
fecha >= la del acta y todo voto de su misma ley no puede mover ninguna P_i. Es una prueba metamórfica: no
depende de cómo se implementó el corte, sólo de que no se filtre información. Cada voto corrompido cambia
SIEMPRE de conducta (AFIRMATIVO -> NEGATIVO; cualquier otra -> AFIRMATIVO). Se hace sobre actas REALES, no sobre
un caso sintético como `test_historia_sin_fuga.py`.

POR QUÉ UN TEST DETERMINÍSTICO Y NO UN GATE ESTADÍSTICO. Un gate por skill no atrapa las fugas: el efecto de la
fuga del harness (ΔBrier -0,031) es heterogéneo entre leyes y con 500 leyes el efecto mínimo detectable es 0,052,
mayor que el propio efecto (`05-consolidacion-y-anclaje.md` §5.3). A las fugas las atrapa ESTA prueba; a las
regresiones de skill, un gate pareado. Hacen falta las dos.

QUÉ CORRE SIN ARGUMENTOS (lo que corre el CI; ≈ 2 minutos). Muestra DETERMINÍSTICA (semilla 7):
  1. PRUEBA PRINCIPAL, `historia="estricta"` (el motor de hoy), max|dP_i| <= 1e-12, sobre tres grupos de actas:
     5 estratificadas (una por era, alternando la cámara), las 3 del control de la fecha y las 8 del control de la
     ley. Estos dos últimos grupos no son un lujo: una fuga en el harness REAL sólo se ve en las actas donde esa
     fuga es observable (con otras actas el mismo día; con una acta anterior de su misma ley). La primera versión
     corría la prueba principal sólo sobre 10 estratificadas y una fuga por la misma ley, puesta en el archivo
     del harness, NO la ponía en rojo (sólo el control, que la inyecta por parche, la veía).
     Guarda anti-vacuidad: ninguna acta con postura no proyectable, en cada una se corrompen votos y se compara al
     menos la MITAD de sus votantes (un test que no compara nada pasa por la razón equivocada).
  2. CONTROL POSITIVO 1 — fuga por la FECHA, inyectada en el harness real: `Contexto._hasta` pasa a «fecha + 1 día»
     (el corte viejo, que dejaba ver el día de la sesión). Sobre 3 actas que tienen otras el mismo día, LAS 3 tienen
     que mover alguna P_i (en la auditoría el corte viejo se detectó en 144 de 144).
  3. CONTROL POSITIVO 2 — fuga por la MISMA LEY, inyectada en el harness real: `Contexto._sin_ley` deja de excluir
     la ley. Sobre 8 actas con una acta anterior de su misma ley, al menos 1 tiene que mover alguna P_i (la
     sensibilidad medida en la auditoría fue del 48%: la probabilidad de 0 en 8 es ≈ 0,5%).
  4. LAS FUGAS SE SACAN: los parches van en try/finally y después se repite la prueba estricta sobre 1 acta.
Regla 5 (`REGLAS-borrador.md`): un control tiene que poder fallar. Las secciones 2 y 3 son ese control: si el
harness dejara de ver la fecha o la ley como lo hace el corte estricto, la sección 1 se pone en rojo; y si la
prueba dejara de poder ver una fuga, las secciones 2 o 3 se ponen en rojo. Las actas de cada control se eligen por
una regla fija (muestra con semilla 7 de las que cumplen la condición), no por el resultado.

MODO DE LA AUDITORÍA (la muestra grande, ≈ 17 min con 150 actas, y el JSON):

    python evaluacion/baseline/tests/test_invariancia_al_futuro.py                       # el test (rápido)
    python evaluacion/baseline/tests/test_invariancia_al_futuro.py --por-era 30 --salida X.json

NO CUBRE: dictámenes ni taxonomías posteriores (β, TEMA_AUTO, RECORD_POR_TEMA no entran al harness), la ficha de
desvío (`disciplina_individual.csv`, toda la historia) ni la presencia.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
for sub in ("modelo/ensemble/src", "variables/bloque/src", "evaluacion/baseline/src"):
    sys.path.insert(0, str(RAIZ / sub))
import nowcast_puertas as NP  # noqa: E402,F401  (el harness lo importa; acá para que el motor quede cargado)
from baseline_voto_individual import Contexto, ERA_BINS, ERA_LABELS, silenciar_avisos_del_motor  # noqa: E402

SALIDA = RAIZ / "Archivos_Borrar" / "auditoria" / "invariancia_al_futuro.json"
SEMILLA = 7
UMBRAL = 1e-12
N_CONTROL_FECHA, N_CONTROL_LEY, N_RESTAURADA = 3, 8, 1   # 1ª versión: 4, 8, 2 (no entraba en 4 minutos)
MIN_COBERTURA = 0.5             # de los votantes de cada acta, cuántos se comparan como mínimo


# ═══════════════════════════════════════════════════════════════════════ la prueba
def corromper(votos: pd.DataFrame, fecha: pd.Timestamp, ley: str):
    """Cambia la conducta de todo voto de fecha >= `fecha` y de todo voto de la ley `ley`. (votos, cuántos)."""
    v = votos.copy()
    m = (v["fecha"] >= fecha) | (v["_ley"] == ley)
    v.loc[m, "conducta"] = np.where(v.loc[m, "conducta"] == "AFIRMATIVO", "NEGATIVO", "AFIRMATIVO")
    return v, int(m.sum())


def comparar(a: dict | None, b: dict | None) -> tuple[int, float, int]:
    """(n comparados, max |dP|, n con diferencia > 1e-12). (0, 0, 0) si alguna postura no se pudo proyectar."""
    if a is None or b is None:
        return 0, 0.0, 0
    ks = set(a) & set(b)
    d = np.array([abs(a[k][0] - b[k][0]) for k in ks]) if ks else np.zeros(1)
    return len(ks), float(d.max()), int((d > UMBRAL).sum())


def _vaciar(ctx: Contexto) -> None:
    """Los cachés del harness no saben qué corte está vigente: hay que vaciarlos al cambiar de escenario."""
    ctx._rec.clear()
    ctx._post.clear()
    ctx._fecha_cache = None


def tabla_de_actas(ctx: Contexto) -> tuple[pd.DataFrame, dict]:
    """Las actas evaluables (con voto emitido y con una ventana de historia), con su ley y su era; y sus votantes."""
    v = ctx.votos
    emit = v[v["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    actas = (emit[["acta_id", "fecha", "camara", "_ley"]].drop_duplicates("acta_id")
             .rename(columns={"_ley": "ley"}).sort_values(["fecha", "acta_id"]))
    actas = actas[actas["fecha"] >= v["fecha"].min() + pd.Timedelta(days=730)].copy()
    actas["era"] = pd.cut(actas["fecha"], ERA_BINS, labels=ERA_LABELS)
    n_actas_por_fecha = v.groupby("fecha")["acta_id"].nunique()
    actas["otras_el_mismo_dia"] = actas["fecha"].map(n_actas_por_fecha).fillna(1) > 1
    primera_fecha_de_ley = v.groupby("_ley")["fecha"].min()
    actas["ley_con_acta_anterior"] = actas["ley"].map(primera_fecha_de_ley) < actas["fecha"]
    return actas, {k: g for k, g in emit.groupby("acta_id", sort=False)}


def muestra_por_era(actas: pd.DataFrame, por_era: int) -> pd.DataFrame:
    """`por_era` actas por era, mitad de cada cámara, con semilla fija."""
    partes = [g.sample(min(len(g), max(1, por_era // 2)), random_state=SEMILLA)
              for _, g in actas.groupby(["era", "camara"], observed=True)]
    return pd.concat(partes).sort_values(["fecha", "acta_id"])


def muestra_rapida(actas: pd.DataFrame) -> pd.DataFrame:
    """Una acta por era, alternando la cámara (Diputados, Senado, Diputados…): 5 actas y las dos cámaras. Con semilla fija."""
    partes = []
    for i, era in enumerate(ERA_LABELS):
        g = actas[(actas["era"] == era) & (actas["camara"] == ("diputados", "senado")[i % 2])]
        partes.append(g.sample(1, random_state=SEMILLA))
    return pd.concat(partes).sort_values(["fecha", "acta_id"])


def muestra_de(elegibles: pd.DataFrame, n: int) -> pd.DataFrame:
    """`n` actas de las que cumplen una condición, con semilla fija: la regla no mira el resultado."""
    return elegibles.sort_values(["fecha", "acta_id"]).sample(min(len(elegibles), n), random_state=SEMILLA) \
                    .sort_values(["fecha", "acta_id"])


def verificar(ctx0: Contexto, muestra: pd.DataFrame, por_acta: dict, historia: str = "estricta",
              progreso: str = "") -> list[dict]:
    """Para cada acta: P_i del harness con la historia limpia contra P_i con el futuro y la ley corrompidos."""
    v = ctx0.votos
    filas, t0 = [], time.time()
    for k, r in enumerate(muestra.itertuples(), 1):
        votantes = por_acta[r.acta_id][["legislador_id", "bloque_linaje"]]
        f = pd.Timestamp(r.fecha)
        base = ctx0.p_legisladores(r.acta_id, r.camara, f, votantes, historia, False)
        vc, n_cor = corromper(v, f, r.ley)
        ctx1 = Contexto(vc, ctx0.ley_de_acta, ctx0.origen_map, ctx0.cond, ctx0.conf_area)
        n, mx, nd = comparar(base, ctx1.p_legisladores(r.acta_id, r.camara, f, votantes, historia, False))
        filas.append({"acta_id": r.acta_id, "era": str(r.era), "camara": r.camara, "fecha": str(f.date()),
                      "votos_corrompidos": n_cor, "n": n, "n_votantes": len(votantes), "max_abs_dP": mx, "n_distintos": nd,
                      "proyectable": base is not None})
        if progreso and k % 5 == 0:
            print(f"    {progreso}: {k}/{len(muestra)} actas · {time.time() - t0:.0f} s", flush=True)
    return filas


# ══════════════════════════════════════════ las fugas sintéticas, inyectadas en el harness real
@contextmanager
def fuga_por_la_fecha():
    """El corte viejo: la historia llega hasta el día SIGUIENTE, o sea que ve el día de la sesión."""
    original = Contexto.__dict__["_hasta"]
    Contexto._hasta = staticmethod(lambda fecha, historia: pd.Timestamp(fecha) + pd.Timedelta(days=1))
    try:
        yield
    finally:
        Contexto._hasta = original


@contextmanager
def fuga_por_la_misma_ley():
    """No se excluye la ley del acta: la historia trae los artículos anteriores de la MISMA ley."""
    original = Contexto.__dict__["_sin_ley"]
    Contexto._sin_ley = staticmethod(lambda v, ley, historia: v)
    try:
        yield
    finally:
        Contexto._sin_ley = original


# ═════════════════════════════════════════════════════════════════════════ el test
def test(fallos: list[str]) -> int:
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    t0 = time.time()
    silenciar_avisos_del_motor()
    ctx0 = Contexto.desde_repo()
    actas, por_acta = tabla_de_actas(ctx0)
    print(f"contexto cargado en {time.time() - t0:.0f} s; {len(actas)} actas evaluables")

    # 1. la prueba principal: las estratificadas y las actas donde cada fuga es observable
    print("\n1. historia ESTRICTA (el motor de hoy): corromper el futuro y la misma ley no mueve ninguna P_i")
    principal = muestra_rapida(actas)
    check(len(principal) == 5 and principal["era"].nunique() == 5 and principal["camara"].nunique() == 2,
          f"la muestra tiene que tener 5 actas de 5 eras y las dos cámaras: {len(principal)} actas, "
          f"{principal['era'].nunique()} eras, {principal['camara'].nunique()} cámaras")
    sel_fecha = muestra_de(actas[actas["otras_el_mismo_dia"]], N_CONTROL_FECHA)
    sel_ley = muestra_de(actas[actas["ley_con_acta_anterior"]], N_CONTROL_LEY)
    todas = (pd.concat([principal, sel_fecha, sel_ley]).drop_duplicates("acta_id")
             .sort_values(["fecha", "acta_id"]))
    print(f"  {len(principal)} estratificadas + {len(sel_fecha)} con otras actas el mismo día + {len(sel_ley)} con "
          f"acta anterior de su ley = {len(todas)} actas distintas")
    filas = verificar(ctx0, todas, por_acta, "estricta", "estricta")
    movidas = [f for f in filas if f["n_distintos"] > 0]
    check(not movidas, "LA HISTORIA ESTRICTA VE EL FUTURO O LA MISMA LEY: corromperlos mueve P_i en "
          f"{len(movidas)} de {len(filas)} actas: "
          + "; ".join(f"{f['acta_id']} ({f['era']}, {f['fecha']}): {f['n_distintos']} de {f['n']} P_i, "
                      f"max|dP| {f['max_abs_dP']:.3g}" for f in movidas[:5]))
    check(all(f["proyectable"] for f in filas), "hay actas cuya postura no se pudo proyectar (no se compararon)")
    check(all(f["votos_corrompidos"] > 0 for f in filas), "hay actas en las que no se corrompe nada")
    pobres = [f"{f['acta_id']} ({f['n']} de {f['n_votantes']})" for f in filas if f["n"] < MIN_COBERTURA * f["n_votantes"]]
    check(not pobres, f"actas en las que se compara menos de la mitad de los votantes: la prueba pasaría por la "
          f"razón equivocada: {pobres}")
    total = sum(f["n"] for f in filas)
    print(f"  {len(filas)} actas, {total} P_i comparadas (cobertura mínima "
          f"{min(f['n'] / f['n_votantes'] for f in filas):.0%} de los votantes), "
          f"max|dP| = {max(f['max_abs_dP'] for f in filas):.3g} "
          f"({time.time() - t0:.0f} s desde el inicio)")

    # 2. control positivo: fuga por la fecha
    print("\n2. CONTROL POSITIVO — fuga por la FECHA inyectada en `Contexto._hasta`: la prueba la tiene que ver")
    _vaciar(ctx0)
    with fuga_por_la_fecha():
        filas = verificar(ctx0, sel_fecha, por_acta, "estricta", "fuga por la fecha")
    _vaciar(ctx0)
    sin = [f["acta_id"] for f in filas if f["n_distintos"] == 0]
    check(len(filas) == N_CONTROL_FECHA and not sin,
          f"la fuga por la FECHA no se detectó en {len(sin)} de {len(filas)} actas {sin}: la prueba no puede ver "
          "el futuro")
    print(f"  detectada en {len(filas) - len(sin)} de {len(filas)} actas "
          f"(max|dP| {max(f['max_abs_dP'] for f in filas):.3g})")

    # 3. control positivo: fuga por la misma ley
    print("\n3. CONTROL POSITIVO — fuga por la MISMA LEY inyectada en `Contexto._sin_ley`: la prueba la tiene que ver")
    _vaciar(ctx0)
    with fuga_por_la_misma_ley():
        filas = verificar(ctx0, sel_ley, por_acta, "estricta", "fuga por la ley")
    _vaciar(ctx0)
    detectadas = sum(1 for f in filas if f["n_distintos"] > 0)
    check(len(filas) == N_CONTROL_LEY and detectadas >= 1,
          f"la fuga por la MISMA LEY no se detectó en ninguna de {len(filas)} actas: la prueba no puede ver la ley")
    print(f"  detectada en {detectadas} de {len(filas)} actas (sensibilidad de la auditoría: 48%)")

    # 4. las fugas se sacaron
    print("\n4. las fugas se sacaron: la prueba estricta vuelve a dar cero")
    filas = verificar(ctx0, principal.head(N_RESTAURADA), por_acta, "estricta")
    check(all(f["n_distintos"] == 0 and f["n"] > 0 for f in filas),
          "después de los controles la historia estricta ya no es invariante: un parche no se restauró")

    print(f"\n{corridos - len([f for f in fallos])}/{corridos} OK  ({time.time() - t0:.0f} s)")
    return corridos


# ════════════════════════════════════════════════ el modo de la auditoría (muestra grande + JSON)
def auditoria(por_era: int, salida: Path) -> int:
    silenciar_avisos_del_motor()
    ctx0 = Contexto.desde_repo()
    actas, por_acta = tabla_de_actas(ctx0)
    muestra = muestra_por_era(actas, por_era)
    v = ctx0.votos
    filas, t0 = [], time.time()
    for k, r in enumerate(muestra.itertuples(), 1):
        votantes = por_acta[r.acta_id][["legislador_id", "bloque_linaje"]]
        f = pd.Timestamp(r.fecha)
        base = ctx0.p_legisladores(r.acta_id, r.camara, f, votantes, "estricta", False)
        vc, n_cor = corromper(v, f, r.ley)
        ctx1 = Contexto(vc, ctx0.ley_de_acta, ctx0.origen_map, ctx0.cond, ctx0.conf_area)
        fila = {"acta_id": r.acta_id, "era": str(r.era), "camara": r.camara, "fecha": str(f.date()),
                "votos_corrompidos": n_cor,
                "n_mismo_dia_otras_actas": int(((v["fecha"] == f) & (v["acta_id"] != r.acta_id)).sum()),
                "n_misma_ley_otras_actas": int(((v["_ley"] == r.ley) & (v["acta_id"] != r.acta_id)).sum())}
        for nom, hist in (("estricta", "estricta"), ("CONTROL_dia_incluido", "dia_incluido"),
                          ("CONTROL_fecha", "fecha")):
            n, mx, nd = comparar(base, ctx1.p_legisladores(r.acta_id, r.camara, f, votantes, hist, False))
            fila[nom] = {"n": n, "max_abs_dP": mx, "n_distintos": nd}
        filas.append(fila)
        if k % 15 == 0:
            print(f"  {k}/{len(muestra)} actas · {(time.time() - t0) / 60:.1f} min", flush=True)
    d = pd.DataFrame(filas)
    res = {"n_actas": int(len(d)), "por_era": por_era,
           "estricta_max_abs_dP_global": float(d["estricta"].map(lambda x: x["max_abs_dP"]).max()),
           "estricta_actas_con_diferencia": int(d["estricta"].map(lambda x: x["n_distintos"] > 0).sum()),
           "por_era_estricta": {e: {"actas": int(len(g)),
                                    "con_diferencia": int(g["estricta"].map(lambda x: x["n_distintos"] > 0).sum()),
                                    "max_abs_dP": float(g["estricta"].map(lambda x: x["max_abs_dP"]).max())}
                                for e, g in d.groupby("era")}}
    for ctrl, cond in (("CONTROL_dia_incluido", d["n_mismo_dia_otras_actas"] > 0),
                       ("CONTROL_fecha", d["n_misma_ley_otras_actas"] > 0)):
        sel = d[cond]
        res[ctrl] = {"actas_donde_deberia_detectar": int(len(sel)),
                     "actas_donde_detecta": int(sel[ctrl].map(lambda x: x["n_distintos"] > 0).sum()),
                     "max_abs_dP": float(sel[ctrl].map(lambda x: x["max_abs_dP"]).max()) if len(sel) else None}
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps({"resumen": res, "detalle": filas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res["estricta_actas_con_diferencia"] == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Invariancia al futuro: el test rápido (sin argumentos) o el modo de la auditoría.")
    ap.add_argument("--por-era", type=int, default=0, help="modo de la auditoría: N actas por era (30 = 150 actas)")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)
    if a.por_era:
        return auditoria(a.por_era, Path(a.salida))
    fallos: list[str] = []
    test(fallos)
    if fallos:
        print(f"\n{len(fallos)} FALLAS:")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("todos los tests pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
