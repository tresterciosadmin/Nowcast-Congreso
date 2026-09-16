# -*- coding: utf-8 -*-
"""FASE 1 de coordinacion/PROMPT-MULTITEMA-V2.md — validación de `rec_i^tema`
sobre el CENSO completo, walk-forward, comparado PAREADO voto a voto contra el
récord general (lo que el motor usa HOY).

QUÉ AGREGA sobre `medir_rec_por_tema.py` (que ya midió, por ÁREA SUELTA, que el
récord encogido hacia el general gana ~8% de Brier relativo, ver salida
`medir_rec_por_tema_2026-09-16.json`):

  1. COMBINACIÓN MULTI-TEMA: un voto de un proyecto con VARIAS áreas sustantivas
     combina el récord de cada área EN LOGIT (mismo principio que
     `bloque.proyectar_postura(combinar_temas='ponderada_logit')`, acá a nivel
     legislador), ponderado por la confianza REAL de cada etiqueta.
  2. CORTES por cámara y por era, que el prompt pide explícitamente.

DISEÑO — un solo grado de libertad cambiado: para el MISMO voto,

    p_general = rec_i_general                       (walk-forward, sin tema)
    p_tema    = combinar_logit({área: rec_i^área_encogido}, pesos=confianza real)

`rec_i^área_encogido` ya viene encogido (Empirical-Bayes k=5) hacia el récord
GENERAL de la MISMA persona en ese momento (walk-forward) — es información
INDIVIDUAL, no de bloque: la doctrina de FASE 1 es mover el tema adonde hay
datos, y adonde hay datos es acá, no en el share del bloque.

SUBCONJUNTO QUE TOCA: sólo votos de actas con >=1 área sustantiva clasificada
(hoy ~51-57% del universo). Ahí es donde se mide el efecto.

NO TOCA EL REPO: sólo lee. Escribe el reporte en outputs/.

Uso:
    python evaluacion/baseline/src/fase1_rec_por_tema.py
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("fase1_rec_por_tema")

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

K_SHRINK = 5.0
_AUX_PREFIX = "AUX"
_ERA_BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
             pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
_ERA_LABELS = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


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


def combinar_logit(shares: list[float], pesos: list[float]) -> float:
    """sigmoid(promedio ponderado de logit(share)) — mismo principio que
    `bloque.proyectar_postura(combinar_temas='ponderada_logit')`, acá a nivel
    legislador en vez de bloque."""
    if not shares:
        raise ValueError("combinar_logit necesita al menos un share")
    num, den = 0.0, 0.0
    for s, w in zip(shares, pesos):
        p = float(np.clip(s, 1e-9, 1.0 - 1e-9))
        num += w * np.log(p / (1.0 - p))
        den += w
    if den <= 0:
        raise ValueError("suma de pesos <= 0")
    return float(1.0 / (1.0 + np.exp(-(num / den))))


def preparar(camara_filtro: str = "") -> pd.DataFrame:
    """Un DataFrame, una fila por voto EMITIDO de un acta con >=1 área
    sustantiva, con rec_general, rec_tema_combinado y af (el real)."""
    from bloque import cargar as cargar_bloque
    from baseline_voto_individual import cargar_confianza_por_area

    votos = cargar_bloque()
    v = votos[votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    if camara_filtro:
        v = v[v["camara"] == camara_filtro]
    v["af"] = (v["conducta"] == "AFIRMATIVO").astype(int)
    v = v.sort_values("fecha").reset_index(drop=True)

    gp = v.groupby("legislador_id")["af"]
    v["rec_general"] = gp.transform(lambda s: s.shift(1).expanding().mean())
    v["n_general"] = gp.transform(lambda s: s.shift(1).expanding().count()).fillna(0)

    tpa = pd.read_parquet(REPO / "variables/proyecto/data/tema_por_acta.parquet")
    tpa = tpa[["acta_id", "todas_ids"]].drop_duplicates("acta_id")
    v = v.merge(tpa, on="acta_id", how="left")
    v["areas"] = v["todas_ids"].map(_areas_de)
    v = v[v["areas"].map(len) > 0].dropna(subset=["rec_general"]).reset_index(drop=True)
    v["_voto_id"] = v.index

    vx = v[["_voto_id", "acta_id", "legislador_id", "fecha", "areas", "af",
           "rec_general"]].explode("areas").rename(columns={"areas": "area"})
    vx = vx.sort_values(["legislador_id", "area", "fecha"])
    gpa = vx.groupby(["legislador_id", "area"])["af"]
    vx["rec_area"] = gpa.transform(lambda s: s.shift(1).expanding().mean())
    vx["n_area"] = gpa.transform(lambda s: s.shift(1).expanding().count()).fillna(0)
    n = vx["n_area"].to_numpy(float)
    r_area = vx["rec_area"].fillna(vx["rec_general"]).to_numpy(float)
    vx["rec_area_encogido"] = (n * r_area + K_SHRINK * vx["rec_general"].to_numpy(float)) / (n + K_SHRINK)

    conf = cargar_confianza_por_area(REPO)
    vx["peso_area"] = [conf.get(str(a), {}).get(ar, 1.0)
                       for a, ar in zip(vx["acta_id"], vx["area"])]

    def _combinar(g: pd.DataFrame) -> float:
        try:
            return combinar_logit(g["rec_area_encogido"].tolist(), g["peso_area"].tolist())
        except ValueError:
            return float(g["rec_general"].iloc[0])

    comb = vx.groupby("_voto_id").apply(_combinar, include_groups=False)
    comb.name = "rec_tema_combinado"
    n_areas = vx.groupby("_voto_id").size().rename("n_areas")
    out = v.set_index("_voto_id").join(comb).join(n_areas)
    return out.reset_index(drop=True)


def _resumen(sub: pd.DataFrame) -> dict | None:
    if sub.empty:
        return None
    bg = _brier(sub["rec_general"], sub["af"])
    bt = _brier(sub["rec_tema_combinado"], sub["af"])
    return {"n": int(len(sub)), "brier_general": round(bg, 5), "brier_tema": round(bt, 5),
           "mejora_relativa": round(1 - bt / bg, 4) if bg > 0 else None}


def correr_fase1(camara_filtro: str = "") -> dict:
    logger.info("preparando récord general + por área combinado en logit (censo completo)...")
    d = preparar(camara_filtro)
    logger.info("%d votos en el subconjunto que toca (acta con >=1 área sustantiva)", len(d))

    reporte: dict = {"camara_filtro": camara_filtro or "ambas",
                     "global_subconjunto_con_tema": _resumen(d),
                     "por_camara": {c: _resumen(g) for c, g in d.groupby("camara")}}
    d = d.copy()
    d["era"] = pd.cut(d["fecha"], bins=_ERA_BINS, labels=_ERA_LABELS)
    reporte["por_era"] = {str(e): _resumen(g) for e, g in d.groupby("era", observed=True)}
    reporte["por_n_areas_del_voto"] = {int(k): _resumen(g) for k, g in d.groupby("n_areas")}
    return reporte


def main() -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    reporte = correr_fase1()
    out = REPO / "evaluacion/baseline/outputs/fase1_rec_por_tema_censo.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
