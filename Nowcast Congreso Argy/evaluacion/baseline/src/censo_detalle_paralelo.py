# -*- coding: utf-8 -*-
"""El censo de `baseline_voto_individual.correr` partido por FECHAS en procesos
paralelos, con el detalle voto a voto guardado (incluye share y desvío del linaje, el
récord y su n), para poder recomputar brazos del récord sin re-proyectar la postura.

Da el MISMO detalle que una corrida única: el récord walk-forward se calcula sobre toda
la historia en cada proceso y `hasta`/`desde` sólo recortan qué actas se evalúan; la
postura depende sólo de (cámara, mes, tema, origen).

    python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 3
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from multiprocessing import get_context
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

SALIDA = "evaluacion/baseline/outputs/censo_detalle_2026-09-27.parquet"


def _tramo(args):
    desde, hasta = args
    from baseline_voto_individual import correr, _ContadorAvisos
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format=f"%(asctime)s [{desde}] %(levelname)s %(message)s")
    logging.getLogger("bloque").addFilter(_ContadorAvisos())
    t0 = time.time()
    _, d = correr(desde=desde, hasta=hasta, devolver_detalle=True)
    logging.getLogger("censo").info("tramo %s..%s: %d votos en %.1f min",
                                    desde, hasta, len(d), (time.time() - t0) / 60)
    return d


def bordes(n_tramos: int) -> list[tuple[str, str]]:
    from baseline_voto_individual import REPO, VENTANA_DIAS
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar
    v = cargar()
    a = v.drop_duplicates("acta_id")["fecha"].sort_values()
    a = a[a >= a.min() + pd.Timedelta(days=VENTANA_DIAS)]
    q = [a.quantile(i / n_tramos) for i in range(1, n_tramos)]
    cortes = [""] + [pd.Timestamp(x).strftime("%Y-%m-%d") for x in q] + [""]
    return [(cortes[i], cortes[i + 1]) for i in range(n_tramos)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesos", type=int, default=3)
    ap.add_argument("--tramos", type=int, default=9)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    from baseline_voto_individual import REPO
    tramos = bordes(args.tramos)
    logging.info("tramos: %s", tramos)
    t0 = time.time()
    with get_context("spawn").Pool(args.procesos) as pool:
        partes = list(pool.imap_unordered(_tramo, tramos))
    d = pd.concat(partes, ignore_index=True).sort_values(["fecha", "acta_id"]).reset_index(drop=True)
    dup = d.duplicated(["acta_id", "legislador"]).sum()
    if dup:
        raise RuntimeError(f"{dup} votos duplicados entre tramos: los bordes se pisan")
    out = Path(args.salida) if args.salida else REPO / SALIDA
    out.parent.mkdir(parents=True, exist_ok=True)
    d.to_parquet(out, index=False)
    logging.info("-> %s: %d votos, %d actas, %.1f min", out, len(d), d["acta_id"].nunique(),
                 (time.time() - t0) / 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
