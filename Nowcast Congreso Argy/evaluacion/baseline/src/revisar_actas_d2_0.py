# -*- coding: utf-8 -*-
"""D2.0 de la auditoría 2026-09: la revisión de las actas de la canónica (el runner).

    python evaluacion/baseline/src/revisar_actas_d2_0.py --muestra    # sortea las 260 actas (sin resultado) y arma
                                                                       # el paquete del etiquetador y la clave aparte
    (los pasos siguientes —la planilla de Franco, --validar, --actas, --duplicados, --medir— se agregan en orden)

LA REGLA es el pre-registro de D2.0 (`ESTADO-EJECUCION.md`, «D2.0 — pre-registro»); este archivo la ejecuta y no la
cambia. Los pasos van en el orden del pre-registro (punto 7), cada uno commiteado antes del siguiente; ninguna tabla que
lea `resultado` se calcula antes de que la validación esté commiteada. Este archivo, hasta acá, NO lee `resultado`,
`tipo_mayoria` ni los conteos.

LA MUESTRA. 260 actas, `default_rng(20261005)`, estratificada por subtipo de la regla con el reparto fijo de
`REPARTO`; dentro de cada subtipo, entre fuentes por restos mayores, al menos 1 por fuente no vacía si alcanza, con los
mínimos de `MINIMOS`. El estrato real es la celda subtipo × fuente: peso de cada acta = N_celda / n_celda.

EL PAQUETE DEL ETIQUETADOR (`Archivos_Borrar/d2_0/etiquetado/`): las instrucciones con las definiciones en prosa (no la
regla) y, por acta, cámara, fecha, fuente, título y expediente, con el contexto de la sesión (los otros títulos de la
misma cámara y fecha, por número de `acta_id`, hasta 30 antes y 30 después). Lo que delata el resultado va tapado con
`[…]`, en el acta y en el contexto. La clase de la regla queda en `muestra_clave.csv`, que el etiquetador no recibe.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import clasificar_actas_d2_0 as C  # noqa: E402

SEMILLA = 20261005
DIR_MUESTRA = REPO / "coordinacion" / "AUDITORIA-2026-09" / "resultados" / "d2_0_muestra"
DIR_PAQUETE = REPO / "Archivos_Borrar" / "d2_0" / "etiquetado"
CONTEXTO = 30
INFERIDOS = ("unica_sin_marca", "senado_votacion_unica", "senado_particular_tras_general", "repetida_sin_marca")
REPARTO = {  # el del pre-registro, punto 2 (orden fijo: es el orden del sorteo)
    "general": 14, "general_y_particular": 18, "senado_tag_general": 4, "unica_sin_marca": 24,
    "senado_votacion_unica": 20, "particular": 57, "senado_particular_tras_general": 8, "procedimiento": 55,
    "conjunto": 11, "acuerdo_pliego": 10, "decreto": 7, "repetida_sin_marca": 7, "insistencia": 6,
    "resolucion_declaracion": 5, "juicio_desafuero": 5, "interno": 5, "sin_titulo": 4}
MINIMOS = {"particular": {"senado": 8}, "procedimiento": {"senado": 3}}

_TAPAR = [re.compile(r"\b\d+\s+(AFIRMATIVOS?|NEGATIVOS?|ABSTENCI[OÓ]N(ES)?|AUSENTES?)\b", re.I),
          re.compile(r"\b(AFIRMATIV\w*|NEGATIV\w*|SE RECHAZ\w*|SE APRUEB\w*|APROBAD[OA]S?|RECHAZAD[OA]S?)\b", re.I)]

INSTRUCCIONES = """# Etiquetado de actas (auditoría D2.0) — instrucciones

Sos un etiquetador CIEGO. Leé SÓLO los archivos de esta carpeta. **No abras ningún otro archivo del repositorio, no
corras git y no busques nada fuera de esta carpeta.** Escribí tu resultado en `etiquetas_opus.csv` (en esta carpeta)
apenas lo tengas, aunque falte revisar algo.

## Qué hay que hacer

`actas_1.md` a `actas_4.md` traen 260 votaciones del Congreso argentino (65 por archivo). Leelos en orden, de a uno.
Para cada acta ponés UNA etiqueta:

- **GENERAL**: la votación de una ley o proyecto **como un todo**: «en general», o «en general y en particular en una
  sola votación»; o el único voto de un proyecto cuando el título no dice más.
- **PARTICULAR**: la votación de **una parte** de una ley (uno o varios artículos, capítulos o títulos, o la
  incorporación de uno nuevo) después de la general. La mención del artículo de OTRA norma («modifica el art. 3 de la
  ley 25.413») no la hace particular: es el asunto de la ley.
- **MOCION**: una votación **de procedimiento**: apartamiento del reglamento, habilitación del tratamiento sobre tablas,
  preferencia, emplazamiento, moción de orden, vuelta o pase a comisión, reconsideración, cuarto intermedio, cuestión de
  privilegio, plan de labor.
- **OTRA**: cualquier otra cosa: acuerdos y pliegos (designaciones), validez o rechazo de decretos, juicio político o
  desafuero, insistencia o aceptación de modificaciones, licencias y asuntos internos, resoluciones y declaraciones,
  votaciones en conjunto de varios proyectos.
- **INDETERMINABLE**: ni el título ni el contexto alcanzan para decidir.

## Cómo leer cada acta

- Cámara, fecha, fuente, título y expediente.
- **Contexto de la sesión**: los otros títulos de la misma cámara y fecha, ordenados por el número del identificador
  (hasta 30 antes y 30 después). El acta a etiquetar va marcada con `>>`. **Ese orden puede no ser el de la sesión.**
  Sirve, por ejemplo, para ver si un título sin marca es la única votación de esa ley en el día (→ GENERAL) o si hay
  otras con artículos (→ hay que decidir cuál es cuál; si no se puede, INDETERMINABLE).
- Algunas palabras están tapadas con `[…]`: no intentes adivinarlas, no hacen falta.
- Las actas sin fecha van sin contexto.

## Formato de salida

`etiquetas_opus.csv`, con encabezado y una fila por acta, en el orden de las filas. **Al terminar cada archivo,
agregá sus 65 filas al CSV** (no esperes al final):

    fila,acta_id,etiqueta,nota

`etiqueta` ∈ {GENERAL, PARTICULAR, MOCION, OTRA, INDETERMINABLE}. `nota`: una frase corta, sólo si dudaste
(entre comillas si lleva comas). Al terminar, verificá que haya 260 filas y que cada `acta_id` coincida con su fila.
"""


def tapar(t) -> tuple[str, bool]:
    s = "" if t is None or t is pd.NA or (isinstance(t, float) and t != t) else str(t)
    s0 = s
    for rx in _TAPAR:
        s = rx.sub("[…]", s)
    return re.sub(r"\s+", " ", s).strip(), s != s0


def _num(aid: str) -> float:
    m = re.search(r"(\d+)\D*$", aid)
    return float(m.group(1)) if m else float("inf")


def reparto_celdas(c: pd.DataFrame) -> pd.DataFrame:
    """Las celdas subtipo × fuente con su N y su n (el reparto del pre-registro). Determinista."""
    filas = []
    for st, k in REPARTO.items():
        sz = c[c["subtipo"] == st]["fuente"].value_counts().sort_index()
        m = pd.Series(1 if k >= len(sz) else 0, index=sz.index)
        for f, v in MINIMOS.get(st, {}).items():
            m[f] = max(m[f], v)
        resto = k - m.sum()
        w = (sz - m).clip(lower=0)
        q = w / w.sum() * resto
        fl = np.floor(q).astype(int)
        m = m + fl
        r = (q - fl).sort_values(ascending=False, kind="stable")
        m[r.index[: int(resto - fl.sum())]] += 1
        assert int(m.sum()) == k and (m <= sz).all(), (st, m.to_dict(), sz.to_dict())
        filas += [{"subtipo": st, "fuente": f, "N_celda": int(sz[f]), "n_celda": int(m[f])} for f in sz.index if m[f] > 0]
    return pd.DataFrame(filas)


def sortear(a: pd.DataFrame) -> pd.DataFrame:
    c = C.clasificar(a).merge(a[C.COLUMNAS_QUE_LEE], on="acta_id")
    rng = np.random.default_rng(SEMILLA)
    elegidas = []
    for x in reparto_celdas(c).itertuples(index=False):
        pool = np.sort(c[(c["subtipo"] == x.subtipo) & (c["fuente"] == x.fuente)]["acta_id"].to_numpy())
        for aid in rng.choice(pool, size=x.n_celda, replace=False):
            elegidas.append({"acta_id": aid, "subtipo": x.subtipo, "fuente": x.fuente, "N_celda": x.N_celda,
                             "n_celda": x.n_celda})
    m = pd.DataFrame(elegidas)
    m = m.iloc[rng.permutation(len(m))].reset_index(drop=True)   # orden al azar para el etiquetador
    m.insert(0, "fila", np.arange(1, len(m) + 1))
    m = m.merge(c[["acta_id", "clase"]], on="acta_id", how="left")
    m["inferido"] = m["subtipo"].isin(INFERIDOS)
    m["peso"] = m["N_celda"] / m["n_celda"]
    return m


def contexto(a: pd.DataFrame, aid: str) -> list[tuple[bool, str]]:
    r = a.loc[a["acta_id"] == aid].iloc[0]
    if pd.isna(r["fecha"]) or str(r["fecha"]).strip() == "":
        return []
    s = a[(a["camara"] == r["camara"]) & (a["fecha"] == r["fecha"])].copy()
    s["_n"] = s["acta_id"].map(_num)
    s = s.sort_values(["_n", "acta_id"]).reset_index(drop=True)
    i = int(s.index[s["acta_id"] == aid][0])
    s = s.iloc[max(0, i - CONTEXTO): i + CONTEXTO + 1]
    return [(x == aid, t) for x, t in zip(s["acta_id"], s["titulo"])]


def paquete(a: pd.DataFrame, m: pd.DataFrame) -> dict:
    DIR_PAQUETE.mkdir(parents=True, exist_ok=True)
    tap_acta = tap_ctx = 0
    partes: list[list[str]] = []
    lineas: list[str] = []
    filas_csv = []
    ai = a.set_index("acta_id")
    for x in m.itertuples(index=False):
        if (x.fila - 1) % 65 == 0:   # cuatro archivos de 65 actas: el paquete entero no entra de una vez
            lineas = [f"# Actas a etiquetar — parte {(x.fila - 1) // 65 + 1} de 4 (filas {x.fila} a {x.fila + 64})\n"]
            partes.append(lineas)
        r = ai.loc[x.acta_id]
        t, tp = tapar(r["titulo"])
        tap_acta += tp
        exp = "" if pd.isna(r["expediente"]) else str(r["expediente"])
        fecha = "" if pd.isna(r["fecha"]) else str(r["fecha"])
        lineas += [f"## Fila {x.fila} — `{x.acta_id}`", "",
                   f"- cámara: {r['camara']} · fecha: {fecha or '(sin fecha)'} · fuente: {r['fuente']} · expediente: {exp or '—'}",
                   f"- título: {t}", ""]
        ctx = contexto(a, x.acta_id)
        if ctx:
            lineas.append(f"Contexto de la sesión ({len(ctx)} títulos; el orden puede no ser el de la sesión):")
            lineas.append("")
            for es, tt in ctx:
                tt2, tp2 = tapar(tt)
                if not es:
                    tap_ctx += tp2
                lineas.append(("    >> " if es else "       ") + tt2[:300])
        else:
            lineas.append("(sin contexto: el acta no tiene fecha)")
        lineas.append("")
        filas_csv.append({"fila": x.fila, "acta_id": x.acta_id, "camara": r["camara"], "fecha": fecha,
                          "fuente": r["fuente"], "titulo_tapado": t, "expediente": exp})
    for i, ls in enumerate(partes, 1):
        (DIR_PAQUETE / f"actas_{i}.md").write_text("\n".join(ls), encoding="utf-8")
    (DIR_PAQUETE / "INSTRUCCIONES.md").write_text(INSTRUCCIONES, encoding="utf-8")
    pd.DataFrame(filas_csv).to_csv(DIR_MUESTRA / "muestra.csv", index=False, encoding="utf-8")
    return {"titulos_tapados_en_actas": int(tap_acta), "titulos_tapados_en_contexto": int(tap_ctx)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--muestra", action="store_true")
    args = ap.parse_args(argv)
    if not args.muestra:
        ap.print_help()
        return 0
    a = pd.read_parquet(C.CANONICA, columns=C.COLUMNAS_QUE_LEE + ["expediente"])
    a["acta_id"] = a["acta_id"].astype(str)
    DIR_MUESTRA.mkdir(parents=True, exist_ok=True)
    m = sortear(a)
    tap = paquete(a, m)
    m[["fila", "acta_id", "clase", "subtipo", "inferido", "fuente", "N_celda", "n_celda", "peso"]].to_csv(
        DIR_MUESTRA / "muestra_clave.csv", index=False, encoding="utf-8")
    info = {"semilla": SEMILLA, "n": int(len(m)), "por_clase": m["clase"].value_counts().to_dict(),
            "canonica_sha256_16": C_sha16(C.CANONICA), **tap}
    (DIR_MUESTRA / "muestra_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(info, ensure_ascii=False))
    return 0


def C_sha16(p: Path) -> str:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


if __name__ == "__main__":
    sys.exit(main())
