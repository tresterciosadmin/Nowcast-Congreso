"""Baseline 'vota con tu bloque' — gate cuantitativo de Fase 0.

Mide el accuracy de predecir el voto de cada diputado por la mayoria de su bloque,
en DOS cortes que deciden el rumbo del producto:
  A) Todas las votaciones.
  B) Solo las votaciones DISPUTADAS (donde el resultado no es cuasi-unanime).

Usa leave-one-out: la mayoria del bloque se calcula EXCLUYENDO el voto del propio
diputado, para no inflar bloques unipersonales. Reporta sobre dos universos de voto:
substantivo (AFIRMATIVO/NEGATIVO) y total (incluye ABSTENCION/AUSENTE).

Uso: python src/baseline_bloque.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import CLEAN, OUT, log

VOTOS = ["AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE"]
SUBST = ["AFIRMATIVO", "NEGATIVO"]
CONTESTED_MIN_SHARE = 0.10  # minoria >=10% de los votos substantivos => disputada


def loo_majority_accuracy(df: pd.DataFrame, clases: list[str]) -> tuple[float, int]:
    """Accuracy de la mayoria de bloque leave-one-out. df ya filtrado a 'clases'."""
    d = df[df["voto"].isin(clases)].copy()
    if d.empty:
        return float("nan"), 0
    # Conteo por (acta, bloque, voto) -> matriz ancha de clases.
    counts = (
        d.groupby(["acta_id", "bloque", "voto"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=clases, fill_value=0)
    )
    d = d.merge(counts, left_on=["acta_id", "bloque"], right_index=True, how="left")
    mat = d[clases].to_numpy(dtype=float)
    # Leave-one-out: restar 1 a la clase propia de cada fila.
    own = d["voto"].map({c: i for i, c in enumerate(clases)}).to_numpy()
    mat[np.arange(len(d)), own] -= 1.0
    # Filas donde el bloque (sin uno mismo) queda vacio -> prediccion indefinida.
    valid = mat.sum(axis=1) > 0
    pred_idx = mat.argmax(axis=1)
    pred = np.array(clases)[pred_idx]
    hit = (pred == d["voto"].to_numpy()) & valid
    n = int(valid.sum())
    return (float(hit.sum() / n) if n else float("nan")), n


def main() -> None:
    det = pd.read_parquet(CLEAN / "detalle.parquet")
    cab = pd.read_parquet(CLEAN / "cabecera.parquet")

    det = det.dropna(subset=["bloque", "voto"])
    det = det[det["voto"].isin(VOTOS)]

    # --- Clasificar actas en disputadas vs cuasi-unanimes (sobre votos substantivos) ---
    sub = det[det["voto"].isin(SUBST)]
    per_acta = (
        sub.groupby("acta_id", observed=True)["voto"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=SUBST, fill_value=0)
    )
    tot = per_acta.sum(axis=1)
    minoria = per_acta.min(axis=1)
    share_min = (minoria / tot).where(tot > 0, 0.0)
    disputadas = set(share_min[share_min >= CONTESTED_MIN_SHARE].index)
    log.info(
        "clasificacion_actas",
        actas_con_votos_substantivos=int((tot > 0).sum()),
        disputadas=len(disputadas),
        cuasi_unanimes=int((tot > 0).sum()) - len(disputadas),
        umbral_minoria=CONTESTED_MIN_SHARE,
    )

    det_disp = det[det["acta_id"].isin(disputadas)]

    res = {}
    # Universo substantivo (AFIRMATIVO/NEGATIVO) — el que importa para el producto.
    res["substantivo_todas"] = loo_majority_accuracy(det, SUBST)
    res["substantivo_disputadas"] = loo_majority_accuracy(det_disp, SUBST)
    # Universo total (4 clases) — referencia.
    res["total_todas"] = loo_majority_accuracy(det, VOTOS)
    res["total_disputadas"] = loo_majority_accuracy(det_disp, VOTOS)

    # --- Cohesion de bloque (corrobora literatura ~77%) ---
    # % de votos substantivos de cada miembro que coinciden con la mayoria de su bloque.
    coh_acc, coh_n = loo_majority_accuracy(det, SUBST)

    out = {
        "fuente": "CKAN HCDN votaciones_nominales periodos 129-137 (2011-03..2020-01)",
        "n_actas_total": int(det["acta_id"].nunique()),
        "n_votos_substantivos": int(det["voto"].isin(SUBST).sum()),
        "n_bloques": int(det["bloque"].nunique()),
        "umbral_disputada_minoria_pct": CONTESTED_MIN_SHARE,
        "baseline": {
            k: {"accuracy": round(v[0], 4), "n_votos": v[1]} for k, v in res.items()
        },
        "lectura": (
            "El benchmark a superar por el ML es 'substantivo_disputadas'. "
            "'substantivo_todas' suele estar inflado por votaciones cuasi-unanimes."
        ),
    }
    (OUT / "baseline_resultados.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("baseline_ok", **{k: v["accuracy"] for k, v in out["baseline"].items()})
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
