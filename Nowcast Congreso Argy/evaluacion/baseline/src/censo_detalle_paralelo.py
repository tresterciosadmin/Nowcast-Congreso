# -*- coding: utf-8 -*-
"""El censo de `baseline_voto_individual.correr` partido por FECHAS en procesos
paralelos, con el detalle voto a voto guardado.

Da el MISMO detalle que una corrida única: `desde`/`hasta` sólo recortan qué actas se
evalúan (la historia es siempre toda la anterior), y desde el 28-09 la postura y el
récord se calculan a la fecha exacta de cada acta — ya no por mes —, así que no
dependen de dónde caen los bordes.

Desde el 28-09 (ADR-0034) calcula varias variantes en la misma pasada: la principal
(historia estricta, el motor como está) y las que hacen falta para descomponer el
arreglo de la fuga y para medir RECORD_POR_TEMA con el harness limpio.

    python evaluacion/baseline/src/censo_detalle_paralelo.py --procesos 7

Al terminar deja, junto al parquet, `censo_estadisticos_*.json` (lo que SÍ viaja por git;
ver `censo_estadisticos.py`).
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

SALIDA = "evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet"

# (historia, record_por_tema). La primera es la principal (columna `p`): la del motor
# como está (RECORD_POR_TEMA según su bandera), con historia estricta.
VARIANTES = (("estricta", None),
             ("estricta", False), ("estricta", True),
             ("fecha", True),
             ("dia_incluido", True), ("dia_incluido", False))


def _tramo(args):
    desde, hasta, variantes = args
    from baseline_voto_individual import correr, silenciar_avisos_del_motor, _nombre
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format=f"%(asctime)s [{desde}] %(levelname)s %(message)s")
    silenciar_avisos_del_motor()
    principal = variantes[0]
    extra = tuple(x for x in variantes[1:] if _nombre(*x) != _nombre(*principal))
    t0 = time.time()
    res, d = correr(desde=desde, hasta=hasta, historia=principal[0],
                    record_por_tema=principal[1], variantes_extra=extra,
                    devolver_detalle=True)
    logging.getLogger("censo").info("tramo %s..%s: %d votos en %.1f min · avisos %s",
                                    desde, hasta, len(d), (time.time() - t0) / 60,
                                    res.get("avisos_motor"))
    return d


def bordes(n_tramos: int) -> list[tuple[str, str]]:
    from baseline_voto_individual import REPO, VENTANA_DIAS
    sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
    from bloque import cargar
    v = cargar()
    a = v.drop_duplicates("acta_id")["fecha"].sort_values()
    a = a[a >= a.min() + pd.Timedelta(days=VENTANA_DIAS)]
    q = [a.quantile(i / n_tramos) for i in range(1, n_tramos)]
    cortes = [""] + sorted({pd.Timestamp(x).strftime("%Y-%m-%d") for x in q}) + [""]
    return [(cortes[i], cortes[i + 1]) for i in range(len(cortes) - 1)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesos", type=int, default=7)
    ap.add_argument("--tramos", type=int, default=21)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    from baseline_voto_individual import REPO
    tramos = bordes(args.tramos)
    logging.info("tramos: %s", tramos)
    t0 = time.time()
    with get_context("spawn").Pool(args.procesos) as pool:
        partes = list(pool.imap_unordered(_tramo, [(a, b, VARIANTES) for a, b in tramos]))
    d = pd.concat(partes, ignore_index=True).sort_values(["fecha", "acta_id"]).reset_index(drop=True)
    dup = d.duplicated(["acta_id", "legislador"]).sum()
    if dup:
        raise RuntimeError(f"{dup} votos duplicados entre tramos: los bordes se pisan")
    out = Path(args.salida) if args.salida else REPO / SALIDA
    out.parent.mkdir(parents=True, exist_ok=True)
    d.to_parquet(out, index=False)
    logging.info("-> %s: %d votos, %d actas, %.1f min", out, len(d), d["acta_id"].nunique(),
                 (time.time() - t0) / 60)
    # El detalle no viaja por git; sus estadisticos sí (auditoría A2). Se regeneran acá para
    # que nadie deje el JSON viejo respecto del parquet (tests/test_censo_estadisticos.py).
    from censo_estadisticos import generar_y_escribir
    logging.info("-> %s", generar_y_escribir(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
