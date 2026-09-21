# -*- coding: utf-8 -*-
"""FASE 0 — contar celdas ANTES de calcular. ¿Hay con qué correr el test de la firma temática?
    python evaluacion/baseline/src/firma_tematica_fase0_celdas.py"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import firma_tematica_desvio as f

UMBRALES = [3, 5, 10]
NOMBRE = {0: "2015 (K→Macri)", 1: "2019 (Macri→AF)", 2: "2023 (AF→Milei)"}


def pares_por_recambio(c: pd.DataFrame, e: int) -> pd.DataFrame:
    a = c[c.era == e].drop(columns="era").rename(columns={"n": "n_a", "d": "d_a"})
    b = c[c.era == e + 1].drop(columns="era").rename(columns={"n": "n_b", "d": "d_b"})
    return a.merge(b, on=["legislador_id", "area"], how="inner")


def main() -> int:
    d = f.construir_base()
    out = {"por_filtro": {}}
    for filtro in ("disputada", "contestada"):
        c = f.celdas(d, filtro)
        r = {"por_recambio": {}, "pooled": {}}
        for e in (0, 1, 2):
            p = pares_por_recambio(c, e)
            rr = {}
            for u in UMBRALES:
                q = p[(p.n_a >= u) & (p.n_b >= u)]
                por = q.groupby("legislador_id")["area"].nunique()
                rr[f"n>={u}"] = {"pares": int(len(q)), "legisladores": int(q.legislador_id.nunique()),
                                 "leg_3+_areas": int((por >= 3).sum()), "leg_2+_areas": int((por >= 2).sum())}
            r["por_recambio"][NOMBRE[e]] = rr
        for u in UMBRALES:
            pares, l3, l3d = 0, set(), set()
            for e in (0, 1, 2):
                q = pares_por_recambio(c, e); q = q[(q.n_a >= u) & (q.n_b >= u)]
                pares += len(q); por = q.groupby("legislador_id")["area"].nunique()
                l3 |= {(e, l) for l in por[por >= 3].index}; l3d |= set(por[por >= 3].index)
            r["pooled"][f"n>={u}"] = {"pares": pares, "leg_recambio_3+_areas": len(l3), "legisladores_distintos_3+": len(l3d)}
        # por cámara
        r["por_camara_n>=3"] = {}
        for cam in ("diputados", "senado"):
            cc = f.celdas(d[d.camara == cam], filtro); tot = 0; l3 = 0
            for e in (0, 1, 2):
                q = pares_por_recambio(cc, e); q = q[(q.n_a >= 3) & (q.n_b >= 3)]
                tot += len(q); por = q.groupby("legislador_id")["area"].nunique(); l3 += int((por >= 3).sum())
            r["por_camara_n>=3"][cam] = {"pares": tot, "leg_recambio_3+_areas": l3}
        out["por_filtro"][filtro] = r
    cob = {}
    for era in range(4):
        act = d[(d.era == era) & d.presente].drop_duplicates("acta_id")
        row = {"actas": int(len(act)), "cob_tema_general": round(float((act.areas.map(len) > 0).mean()), 4)}
        for filtro in ("disputada", "contestada"):
            a2 = act[act[filtro]]
            row[filtro] = {"actas": int(len(a2)), "con_tema": int((a2.areas.map(len) > 0).sum()),
                           "cob_tema": round(float((a2.areas.map(len) > 0).mean()), 4) if len(a2) else None}
        cob[f"era{era}"] = row
    out["cobertura_tema"] = cob
    print(json.dumps(out, ensure_ascii=False, indent=1))
    p = Path(f.REPO) / "evaluacion/baseline/outputs/firma_tematica_fase0_celdas_2026-09-21.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
