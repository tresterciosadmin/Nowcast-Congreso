# -*- coding: utf-8 -*-
"""FASE 1 de coordinacion/PROMPT-MULTITEMA-V2.md — "medí primero, esto decide el
diseño" de `rec_i^tema` (el récord de un legislador CONDICIONADO por tema, URGENTE 8).

Contesta, con datos reales y walk-forward (sin leakage), las tres preguntas que el
prompt pide medir ANTES de construir nada:

1. ¿Cuántos pares (legislador, área) tienen muestra suficiente? Curva de skill
   contra el umbral n_i^área — no se fija un número a mano (mismo método que ya
   usó §II.5 de FORMULA-COMPLETA.md para decidir MIN_HIST_INDIVIDUAL).
2. ¿Cuánta cobertura de tema hay por acta? Sobre la tabla ANCHA
   (acta_expediente_todas.parquet), no la angosta — la trampa que ya costó dos
   veces en este repo (ver docstring de tema_por_acta.py).
3. ¿El récord por área discrimina? Varianza ENTRE áreas de un mismo legislador
   comparada contra la que esperaría el puro ruido de muestreo (shuffle test).

NO CLASIFICA NADA NUEVO. `tema_por_acta.parquet` tiene la cobertura que tiene HOY
(no se corre `agente_taxonomias` acá: es un LLM pago, y activar eso sin
consultarle antes a Franco es exactamente lo que él pidió no repetir).

NO TOCA EL REPO: sólo lee. Escribe el reporte en outputs/.

Uso:
    python evaluacion/baseline/src/medir_rec_por_tema.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("medir_rec_por_tema")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))

K_SHRINK = 5.0
_AUX_PREFIX = "AUX"
UMBRALES = [0, 1, 2, 4, 8, 16, 32, 64]


def _areas_de(todas_ids) -> list[str]:
    if not todas_ids or (isinstance(todas_ids, float) and pd.isna(todas_ids)):
        return []
    vistas: list[str] = []
    for i in str(todas_ids).split(";"):
        i = i.strip()
        if not i or i.upper().startswith(_AUX_PREFIX):
            continue
        area = i.split(".")[0].upper()
        if area not in vistas:
            vistas.append(area)
    return vistas


def _brier(p, y) -> float:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, float)
    return float(((p - y) ** 2).mean())


def cargar_votos_con_area() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(votos con conducta AFIRMATIVO/NEGATIVO explotados por área sustantiva,
    votos SIN explotar con su record GENERAL walk-forward ya calculado)."""
    from bloque import cargar as cargar_bloque

    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha").reset_index(drop=True)

    # récord GENERAL walk-forward (sin tema), lo que ya hace el motor hoy
    gp = v.groupby("legislador_id")["af"]
    v["rec_general"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_general"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    tpa = tpa[["acta_id", "todas_ids"]].drop_duplicates("acta_id")
    v = v.merge(tpa, on="acta_id", how="left")
    v["areas"] = v["todas_ids"].map(_areas_de)

    vx = v[v["areas"].map(len) > 0].explode("areas").rename(columns={"areas": "area"})
    vx = vx.sort_values(["legislador_id", "area", "fecha"]).reset_index(drop=True)
    gpa = vx.groupby(["legislador_id", "area"])["af"]
    vx["rec_area"] = gpa.transform(lambda s: s.shift(1).expanding().mean())
    vx["n_area"] = gpa.transform(lambda s: s.shift(1).expanding().count()).fillna(0)
    return vx, v


def medir_cobertura() -> dict:
    """Pregunta 2: cobertura de tema por acta, sobre la tabla ANCHA."""
    ae = pd.read_parquet(REPO / "datos/expedientes/data/clean/acta_expediente_todas.parquet")
    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    votos_canon = pd.read_parquet(REPO / "datos/canonica/data/clean/actas_canonico.parquet")
    cov_ancha = float(ae["acta_id"].isin(tpa["acta_id"]).mean())
    cov_canon = float(votos_canon["acta_id"].isin(tpa["acta_id"]).mean())
    con_sustantivo = tpa["todas_ids"].map(lambda t: len(_areas_de(t)) > 0)
    return {
        "n_acta_expediente_todas_ANCHA": int(ae["acta_id"].nunique()),
        "n_tema_por_acta_clasificadas": int(tpa["acta_id"].nunique()),
        "cobertura_sobre_ancha": round(cov_ancha, 4),
        "n_actas_canonico_total": int(votos_canon["acta_id"].nunique()),
        "cobertura_sobre_canonico_total": round(cov_canon, 4),
        "de_las_clasificadas_con_area_sustantiva": round(float(con_sustantivo.mean()), 4),
        "nota": ("no se corrió el clasificador: esto es la cobertura TAL COMO ESTÁ HOY, "
                "sin gastar créditos de API sin permiso de Franco"),
    }


def medir_curva_de_skill(vx: pd.DataFrame) -> dict:
    """Pregunta 1: para cada umbral n_i^área, ¿qué fracción de los votos lo
    alcanza, y el récord por área (encogido EB hacia el récord general) mejora
    el Brier respecto de usar sólo el récord general? Comparación PAREADA: la
    MISMA fila (mismo voto) evaluada con las dos fórmulas."""
    d = vx.dropna(subset=["rec_general", "rec_area"]).copy()
    d = d[d["n_general"] >= 1]  # necesita algo de récord general para poder encoger
    out = {"n_votos_evaluables": int(len(d))}
    curva = []
    for u in UMBRALES:
        sub = d[d["n_area"] >= u]
        if sub.empty:
            curva.append({"umbral_n_area": u, "cobertura": 0.0, "n": 0})
            continue
        n = sub["n_area"].to_numpy(float)
        p_area = (n * sub["rec_area"].to_numpy(float) + K_SHRINK * sub["rec_general"].to_numpy(float)) / (n + K_SHRINK)
        p_general = sub["rec_general"].to_numpy(float)
        y = sub["af"].to_numpy(float)
        brier_area = _brier(p_area, y)
        brier_general = _brier(p_general, y)
        curva.append({
            "umbral_n_area": u,
            "cobertura": round(len(sub) / len(d), 4),
            "n": int(len(sub)),
            "brier_rec_area_encogido": round(brier_area, 5),
            "brier_rec_general": round(brier_general, 5),
            "mejora_relativa": round(1 - brier_area / brier_general, 4) if brier_general > 0 else None,
        })
    out["curva"] = curva
    return out


def medir_discriminacion(vx: pd.DataFrame, min_n_area: int = 8, min_areas: int = 2,
                         n_shuffle: int = 200, seed: int = 7) -> dict:
    """Pregunta 3: para legisladores con >= min_n_area votos EMITIDOS (no walk-
    forward: acá se usa el share REAL, no el proyectado, porque la pregunta es
    descriptiva -¿varía de verdad?- no predictiva) en >= min_areas áreas
    distintas, ¿el rango entre sus áreas excede lo que un shuffle (mismo total
    de votos, área reasignada al azar dentro de la persona) produciría por puro
    ruido de muestreo?"""
    g = vx.groupby(["legislador_id", "area"]).agg(n=("af", "size"), share=("af", "mean"))
    g = g[g["n"] >= min_n_area].reset_index()
    conteo_areas = g.groupby("legislador_id").size()
    elegibles = conteo_areas[conteo_areas >= min_areas].index
    g = g[g["legislador_id"].isin(elegibles)]
    if g.empty:
        return {"n_legisladores_elegibles": 0,
               "nota": f"ningún legislador con >={min_areas} áreas de >={min_n_area} votos"}

    rango_real = g.groupby("legislador_id")["share"].agg(lambda s: s.max() - s.min())

    rng = np.random.default_rng(seed)
    votos_por_legislador = {
        lid: vx.loc[vx["legislador_id"] == lid, "af"].to_numpy()
        for lid in elegibles
    }
    n_por_area = {lid: sub.set_index("area")["n"].to_dict()
                 for lid, sub in g.groupby("legislador_id")}

    rangos_shuffle = []
    for lid in elegibles:
        votos = votos_por_legislador[lid]
        ns = list(n_por_area[lid].values())
        if len(votos) < sum(ns):
            continue
        for _ in range(n_shuffle):
            muestra = rng.choice(votos, size=sum(ns), replace=False)
            cortes = np.cumsum(ns)[:-1]
            partes = np.split(muestra, cortes)
            shares = [p.mean() for p in partes]
            rangos_shuffle.append(max(shares) - min(shares))
    rangos_shuffle = np.array(rangos_shuffle)

    return {
        "n_legisladores_elegibles": int(len(elegibles)),
        "min_n_area": min_n_area, "min_areas": min_areas,
        "rango_real_mediana": round(float(rango_real.median()), 4),
        "rango_real_p75": round(float(rango_real.quantile(0.75)), 4),
        "rango_shuffle_mediana": round(float(np.median(rangos_shuffle)), 4) if len(rangos_shuffle) else None,
        "rango_shuffle_p95": round(float(np.percentile(rangos_shuffle, 95)), 4) if len(rangos_shuffle) else None,
        "pct_legisladores_sobre_p95_shuffle": (
            round(float((rango_real > np.percentile(rangos_shuffle, 95)).mean()), 4)
            if len(rangos_shuffle) else None),
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    logger.info("cobertura de tema por acta (pregunta 2)...")
    cobertura = medir_cobertura()

    logger.info("cargando votos + área explotada...")
    vx, v = cargar_votos_con_area()
    logger.info("%d votos con >=1 área sustantiva (de %d votos AFIRM/NEG totales)",
                len(vx), len(v))

    logger.info("curva de skill contra el umbral n_i^área (pregunta 1)...")
    curva = medir_curva_de_skill(vx)

    logger.info("discriminación: varianza entre áreas vs ruido de muestreo (pregunta 3)...")
    discriminacion = medir_discriminacion(vx)

    reporte = {"cobertura_tema_por_acta": cobertura,
              "curva_skill_umbral_n_area": curva,
              "discriminacion_entre_areas": discriminacion}
    out = REPO / "evaluacion/baseline/outputs/medir_rec_por_tema_2026-09-16.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
