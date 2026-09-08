# -*- coding: utf-8 -*-
"""Mide los criterios de aceptacion de la regeneracion del 2026-09-04 (ADR-0017).

NO toca nada: solo lee y reporta. Lo corre `REGENERAR.ps1` al final, y se puede
correr solo en cualquier momento:

    python verificar_regeneracion.py

Cada control dice **que se esperaba y por que**, para que un numero raro se pueda
leer sin tener que abrir el ADR. Los valores esperados salen de la muestra de 449
Ordenes del Dia reales que se leyo el 04-09 (220 de Diputados, 229 del Senado).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CLEAN = RAIZ / "datos/expedientes/data/clean"
ok, alerta, falta = [], [], []


def linea(txt=""):
    print(txt)


def check(cond, titulo, detalle):
    (ok if cond else alerta).append(titulo)
    print(f"  [{'OK ' if cond else '!! '}] {titulo}")
    if detalle:
        print(f"         {detalle}")


def leer(p, **kw):
    try:
        import pandas as pd
        return pd.read_parquet(p, **kw)
    except Exception as e:  # noqa: BLE001
        falta.append(f"{Path(p).name}: {type(e).__name__}")
        print(f"  [-- ] no pude leer {Path(p).name}: {e}")
        return None


def pct(n, d):
    return f"{100 * n / d:.2f}%" if d else "s/d"


linea("=" * 78)
linea("VERIFICACION DE LA REGENERACION — criterios del ADR-0017")
linea("=" * 78)

# ── 1. SENADO: es el control que decide ────────────────────────────────────
linea("\n1. SENADO — el reparto de dictamen_clase")
linea("   Que se espera, medido sobre 229 Ordenes del Dia reales del Senado:")
linea("   el Senado rotula el caracter en el SUMARIO y el parser lo perdia. Al")
linea("   arreglarlo, ~1,6% pasa a 'mayoria' y ~3% a 'desconocido'. Y las 19")
linea("   'minorias' que habia tienen que DESAPARECER: eran una reimpresion.")
s = leer(CLEAN / "dictamenes_firmas_senado.parquet")
if s is not None:
    v = s["dictamen_clase"].fillna("").value_counts().to_dict()
    tot = len(s)
    linea(f"   filas: {tot:,} | reparto: " +
          ", ".join(f"{k or '(vacio)'}={n:,}" for k, n in sorted(v.items(), key=lambda x: -x[1])))
    may, mino = v.get("mayoria", 0), v.get("minoria", 0)
    desc, uni = v.get("desconocido", 0), v.get("unico", 0)
    check(may > 0, "el Senado dejo de tener CERO dictamenes de mayoria",
          f"mayoria = {may:,} ({pct(may, tot)}). Si sigue en 0 EXACTO, el cambio del "
          f"parser no se aplico: el 04-09 se leyeron 3 ODs de 193 que dicen 'de mayoria'.")
    check(bool(may) and may / tot < 0.06, "y no se paso de rosca",
          f"si 'mayoria' se va muy por encima del ~2% el regex agarra de mas. "
          f"Ahora: {pct(may, tot)}")
    # OJO: el criterio NO es "minoria == 0". Lo escribi asi el 04-09 y dio falso
    # positivo en la corrida del 06-09. Las 19 fantasma eran de senado-2018-16.pdf
    # impreso dos veces, y esas SI tienen que desaparecer; pero el Senado tiene
    # minorias REALES y una es senado-2010-54.pdf (11 firmas, 6-abr-2010). Un
    # control que exige cero declara roto un dato que esta bien.
    fantasma = int(s[s["dictamen_clase"].eq("minoria")
                     & s["archivo"].astype(str).str.contains("2018-16")].shape[0]) \
        if "archivo" in s.columns else -1
    reales = sorted(set(s.loc[s["dictamen_clase"].eq("minoria"), "archivo"].astype(str))) \
        if "archivo" in s.columns else []
    check(fantasma == 0, "desaparecieron las 'minorias' fantasma de senado-2018-16",
          f"minoria total = {mino} en {len(reales)} Ordenes del Dia: {reales[:4]}. "
          f"De senado-2018-16.pdf quedan {fantasma} (tienen que ser 0: era el mismo "
          f"dictamen impreso dos veces). Las demas son minorias reales del Senado.")
    # OJO: el criterio NO es "desconocido > 0". Lo escribi asi el 04-09 —cuando el
    # objetivo era que la clase EXISTIERA, para dejar de disfrazar "no encontre el
    # rotulo" de "despacho unico"— y quedo al reves el 06-09: el arreglo del parser
    # recupero las 39 OD del Senado que quedaban sin rotular, `desconocido` bajo a CERO,
    # y el control lo marco como problema. Cero es el mejor resultado posible, no un
    # fallo. Lo que hay que vigilar es lo contrario: que no se dispare.
    #
    # Es el segundo control que escribi al reves en dos dias (el otro pedia
    # `minoria == 0`). Los dos tenian la misma forma: fijar el numero que dio el dia que
    # se escribio, en vez de la propiedad que tiene que valer siempre.
    check(desc / tot < 0.10 if tot else False, "'desconocido' no se disparo",
          f"desconocido = {desc:,} ({pct(desc, tot)}). Es 'no encontre el rotulo'. "
          f"CERO es el mejor resultado: significa que el parser rotulo todo lo que "
          f"pudo leer. Si pasa del 10%, algo del parser dejo de reconocer cabeceras.")
    if "dictamenes_repetidos" in s.columns:
        rep = int(s["dictamenes_repetidos"].fillna(0).sum())
        arch = s.loc[s["dictamenes_repetidos"].fillna(0) > 0, "archivo"].nunique()
        check(rep >= 1, "se detectaron reimpresiones", f"{rep} en {arch} Ordenes del Dia")
    else:
        check(False, "falta la columna dictamenes_repetidos",
              "el parquet se construyo con el parser viejo: rehace el paso 4")
    linea(f"   (unico = {uni:,}, {pct(uni, tot)} — sigue siendo la enorme mayoria, y eso"
          f" es CORRECTO: el Senado casi no publica despachos de mayoria/minoria)")

# ── 2. DIPUTADOS: el control de que NO se rompio nada ───────────────────────
linea("\n2. DIPUTADOS — el control de que el arreglo no rompio la otra camara")
linea("   Que se espera: las FIRMAS no se mueven (6.968 antes y despues en la")
linea("   muestra de 220 ODs) y aparece ~3% de 'desconocido'.")
d = leer(CLEAN / "dictamenes_firmas.parquet")
if d is not None:
    v = d["dictamen_clase"].fillna("").value_counts().to_dict()
    tot = len(d)
    linea(f"   filas: {tot:,} | reparto: " +
          ", ".join(f"{k or '(vacio)'}={n:,}" for k, n in sorted(v.items(), key=lambda x: -x[1])))
    check(abs(tot - 125_820) / 125_820 < 0.05, "el total de firmas no se movio",
          f"{tot:,} contra 125.820 del 03-09 (se tolera 5%). Si cayo mucho, algo del "
          f"parser esta cortando firmas de mas.")
    check(v.get("mayoria", 0) > 30_000 and v.get("minoria", 0) > 10_000,
          "mayoria y minoria de Diputados siguen en pie",
          f"mayoria={v.get('mayoria', 0):,} (era 35.191), minoria={v.get('minoria', 0):,} "
          f"(era 12.984)")
    # mismo criterio que en el Senado: CERO es el mejor resultado, no un fallo.
    _d = v.get("desconocido", 0)
    check(_d / tot < 0.10 if tot else False, "'desconocido' no se disparo en Diputados",
          f"{_d:,} ({pct(_d, tot)}). Bajo de 2.659 a 0 con el arreglo del 06-09.")

# ── 3. el enlace, que es lo que destrabo al Senado ──────────────────────────
linea("\n3. ENLACE acta -> expediente")
p = CLEAN / "acta_expediente_todas.parquet"
if not p.exists():
    check(False, "falta acta_expediente_todas.parquet",
          "lo arma el paso 5 (enlace_senado.py). Sin el, `estimar_beta` cae al "
          "fallback ruidoso y el Senado vuelve a dar 0 actas.")
else:
    ae = leer(p)
    if ae is not None:
        camaras = ae["camara"].value_counts().to_dict() if "camara" in ae else {}
        check(len(ae) > 4_000, "tiene las dos camaras y el volumen esperado",
              f"{len(ae):,} filas | por camara: {camaras} (el 04-09: 5.030, "
              f"2.745 senado + 2.285 diputados)")
        viejo = CLEAN / "acta_expediente_senado.parquet"
        check(not viejo.exists(), "no quedo el nombre viejo dando vueltas",
              "un archivo generado, un nombre: si `acta_expediente_senado.parquet` "
              "reaparecio, borralo (ADR-0017)." if viejo.exists() else "ok")

# ── 4. beta ────────────────────────────────────────────────────────────────
linea("\n4. BETA — el Senado tiene que dejar de dar 'panel vacio'")
for nombre, ruta in (("ambas camaras", "modelo/ensemble/outputs/beta_dictamen.json"),
                     ("solo Senado", "modelo/ensemble/outputs/beta_dictamen_senado.json")):
    f = RAIZ / ruta
    if not f.exists():
        check(False, f"falta {Path(ruta).name} ({nombre})", "lo escribe el paso 6")
        continue
    try:
        j = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        check(False, f"{Path(ruta).name} ilegible", str(e)); continue
    args = j.get("_args", {})
    desc = j.get("_descriptivos", {})
    m4 = j.get("M4_ADR_mas_caracter", {})
    b1 = m4.get("coef", {}).get("F_i")
    b2 = m4.get("coef", {}).get("lealtad_x_jefe")
    p2 = m4.get("p", {}).get("lealtad_x_jefe")
    check(desc.get("n_actas", 0) > 0, f"{nombre}: el panel tiene actas",
          f"n_actas={desc.get('n_actas')}, n_votos={desc.get('n_votos'):,} | "
          f"beta_1={b1} beta_2={b2} (p={p2}) | muestra={args.get('muestra') or 'completa'}")
    if nombre == "solo Senado":
        car = desc.get("reparto_caracter", {})
        linea(f"         reparto_caracter del Senado: {car}")
        linea("         (que siga siendo casi todo UNICO es CORRECTO y esta documentado:")
        linea("          delta no es estimable en el Senado, y no es culpa del parser)")

# ── 5. baseline ────────────────────────────────────────────────────────────
linea("\n5. BASELINE — cuantas actas tienen caracter de dictamen")
f = RAIZ / "evaluacion/baseline/outputs/baseline_voto_individual.json"
if not f.exists():
    check(False, "falta baseline_voto_individual.json", "lo escribe el paso 7")
else:
    try:
        j = json.loads(f.read_text(encoding="utf-8"))
        car = j.get("por_caracter_dictamen", {})
        check(bool(car), "el baseline corta por caracter de dictamen",
              f"categorias: {list(car)} (el 04-09, con la tabla nueva: 1.574 actas "
              f"con caracter, 1.100 Diputados + 474 Senado, contra 710 solo-Diputados)")
    except Exception as e:  # noqa: BLE001
        check(False, "baseline ilegible", str(e))

# ── 6. el panel ────────────────────────────────────────────────────────────
linea("\n6. PANEL DE PUERTAS — un solo umbral")
f = RAIZ / "Nowcast-Puertas.html"
if not f.exists():
    check(False, "falta Nowcast-Puertas.html", "lo escribe el paso 8")
else:
    h = f.read_text(encoding="utf-8", errors="ignore")
    i = h.find("const DATA = ")
    dat = {}
    if i >= 0:
        try:
            dat = json.loads(h[i + len("const DATA = "): h.index("\n", i)].rstrip(";"))
        except Exception:  # noqa: BLE001
            pass
    c = (dat.get("camaras") or {}).get("origen") or {}
    check("umbral_mayoria_absoluta" in c,
          "el payload trae el umbral con el nombre que dice lo que es",
          f"mayoria_absoluta={c.get('umbral_mayoria_absoluta')} | "
          f"simulado={c.get('umbral_simulado')} | afirm esperados="
          f"{c.get('afirmativos_esperados')} | P(aprob)={dat.get('p_aprobacion')}")
    if c.get("umbral_simulado") and c.get("afirmativos_esperados"):
        margen = round(c["afirmativos_esperados"] - c["umbral_simulado"], 1)
        linea(f"         margen que se muestra ahora (contra el umbral simulado): {margen:+}")
        linea("         (el 04-09 daba +28,4 en origen y +9,9 en revisora)")

# ── 7. el mapa ─────────────────────────────────────────────────────────────
linea("\n7. MAPA")
f = RAIZ / "MAPA.md"
if f.exists():
    n = len(f.read_text(encoding="utf-8").split("\n"))
    check(n <= 262, "MAPA.md dentro del presupuesto de contexto",
          f"{n} lineas (presupuesto 260; el 04-09 quedo en 257)")

# ── cierre ─────────────────────────────────────────────────────────────────
linea("\n" + "=" * 78)
linea(f"RESULTADO: {len(ok)} controles OK · {len(alerta)} a mirar · {len(falta)} sin poder leer")
if alerta:
    linea("\nA MIRAR:")
    for a in alerta:
        linea(f"  - {a}")
if falta:
    linea("\nNO PUDE LEER:")
    for a in falta:
        linea(f"  - {a}")
linea("\nRegla de la casa: un porcentaje imposible es un bug, no un fenomeno.")
linea("Si algo da un numero absurdo, sospecha del cruce antes que de la hipotesis.")
linea("=" * 78)
sys.exit(0)
