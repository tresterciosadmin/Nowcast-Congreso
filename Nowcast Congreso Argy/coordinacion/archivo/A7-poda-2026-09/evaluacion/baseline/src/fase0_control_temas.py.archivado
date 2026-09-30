# -*- coding: utf-8 -*-
"""FASE 0 de coordinacion/PROMPT-MULTITEMA-V2.md — el re-test que sí puede cerrar
la discusión del multitema.

QUÉ HACE DISTINTO A ESTO DE PASO 2 (ADR-0024)
----------------------------------------------
PASO 2 comparó 4 reglas de combinación SIN un brazo de control, sobre una MUESTRA
de 3.000 actas, promediando en probabilidad, y con `peor_tema` medido con un
estimador (mínimo de shares ruidosos) sesgado hacia abajo. Ninguno de esos cuatro
problemas se corrige ajustando el resultado: hace falta re-correr con el diseño
arreglado. Este script:

1. Agrega el brazo `sin_tema` (control: la rama de bloque NUNCA condiciona por
   tema) — sin él no se puede distinguir "la regla de combinación es mala" de
   "condicionar por tema acá hace daño".
2. Usa `ponderada_logit` (combina en LOGIT, con confianza REAL por etiqueta) en
   vez de `ponderada` (probabilidad, peso igual).
3. Corre sobre el CENSO completo (todas las actas con historia suficiente), no
   una muestra.
4. NO re-corre `peor_tema` a nivel proyecto (cerrado por decisión de Franco; su
   revancha es a nivel CAPÍTULO, FASE 2).
5. Reporta INTERVALO (bootstrap clusterizado por acta_id, no por voto — los
   votos de una acta no son observaciones independientes), no sólo el punto.
6. Compara SIEMPRE contra `primaria` (lo de hoy), en la RAMA DE BLOQUE (el
   subconjunto que el cambio toca: `fuente=='bloque'` en el detalle de
   `baseline_voto_individual.correr`) y también por ERA.

NO TOCA EL REPO: sólo lee. Escribe el reporte en outputs/ y el detalle
voto-a-voto de cada brazo (para poder re-analizar sin re-correr el walk-forward,
que es la parte cara).

Uso:
    python evaluacion/baseline/src/fase0_control_temas.py                # censo completo
    python evaluacion/baseline/src/fase0_control_temas.py --muestra 3000 # smoke/comparación con PASO 2
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger("fase0_control_temas")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_voto_individual import correr, REPO  # noqa: E402

ARMS = ["sin_tema", "primaria", "union", "ponderada_logit"]
N_BOOT = 1000
SEED = 7

_ERA_BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2011-12-10"), pd.Timestamp("2015-12-10"),
             pd.Timestamp("2019-12-10"), pd.Timestamp("2023-12-10"), pd.Timestamp("2030-01-01")]
_ERA_LABELS = ["hasta 2011", "2011-2015", "2015-2019", "2019-2023", "desde 2023"]


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(((p - y) ** 2).mean())


def bootstrap_cluster(d: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict | None:
    """Brier + intervalo 95% bootstrap, clusterizado por acta_id: cada réplica
    resamplea ACTAS ENTERAS (con reemplazo), no votos sueltos — resamplear
    votos trataría a los ~15 legisladores de una misma acta como observaciones
    independientes, y no lo son (comparten la misma postura de bloque)."""
    if d.empty:
        return None
    actas = d["acta_id"].unique()
    punto = _brier(d["p"].values, d["y"].values)
    grupos = {a: g[["p", "y"]].to_numpy() for a, g in d.groupby("acta_id")}
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        muestra = rng.choice(actas, size=len(actas), replace=True)
        pv = np.concatenate([grupos[a][:, 0] for a in muestra])
        yv = np.concatenate([grupos[a][:, 1] for a in muestra])
        boots[i] = _brier(pv, yv)
    return {"punto": round(punto, 5),
            "boot_lo_95": round(float(np.percentile(boots, 2.5)), 5),
            "boot_hi_95": round(float(np.percentile(boots, 97.5)), 5),
            "n_actas": int(len(actas)), "n_votos": int(len(d))}


def _diferencia_pareada(sub_arm: pd.DataFrame, sub_base: pd.DataFrame,
                        n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Brier(arm) - Brier(primaria) sobre las actas EN COMÚN entre los dos
    brazos, con bootstrap PAREADO (misma remuestra de actas aplicada a los
    dos) — más ajustado que restar dos intervalos independientes, porque
    comparte la fuente de variación entre actas."""
    actas_arm = set(sub_arm["acta_id"])
    actas_base = set(sub_base["acta_id"])
    comunes = sorted(actas_arm & actas_base)
    if not comunes:
        return {"n_actas_comunes": 0, "aviso": "sin actas en común entre los dos brazos"}
    gp_arm = {a: g[["p", "y"]].to_numpy() for a, g in sub_arm.groupby("acta_id") if a in actas_arm & set(comunes)}
    gp_base = {a: g[["p", "y"]].to_numpy() for a, g in sub_base.groupby("acta_id") if a in actas_base & set(comunes)}
    comunes_arr = np.array(comunes)

    def _brier_de(gp, actas_):
        pv = np.concatenate([gp[a][:, 0] for a in actas_])
        yv = np.concatenate([gp[a][:, 1] for a in actas_])
        return _brier(pv, yv)

    punto = _brier_de(gp_arm, comunes_arr) - _brier_de(gp_base, comunes_arr)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        muestra = rng.choice(comunes_arr, size=len(comunes_arr), replace=True)
        boots[i] = _brier_de(gp_arm, muestra) - _brier_de(gp_base, muestra)
    lo, hi = float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))
    faltan_arm = len(actas_arm - actas_base)
    faltan_base = len(actas_base - actas_arm)
    if faltan_arm or faltan_base:
        logger.warning("actas en rama de bloque que NO coinciden entre brazos: "
                       "%d sólo en el brazo, %d sólo en primaria (de %d/%d totales)",
                       faltan_arm, faltan_base, len(actas_arm), len(actas_base))
    return {"n_actas_comunes": len(comunes), "n_actas_solo_en_brazo": faltan_arm,
            "n_actas_solo_en_primaria": faltan_base,
            "diff_punto": round(punto, 5), "diff_boot_lo_95": round(lo, 5),
            "diff_boot_hi_95": round(hi, 5),
            "distinguible_de_cero": bool(lo > 0 or hi < 0)}


def correr_fase0(camara_filtro: str = "", muestra: int = 0, seed: int = SEED,
                 n_boot: int = N_BOOT) -> dict:
    detalles: dict[str, pd.DataFrame] = {}
    resumenes: dict[str, dict] = {}
    for arm in ARMS:
        logger.info("=== brazo %s (muestra=%s) ===", arm, muestra or "censo completo")
        res, d = correr(camara_filtro=camara_filtro, muestra=muestra, seed=seed,
                        combinar_temas=arm, devolver_detalle=True)
        resumenes[arm] = res
        d = d.copy()
        d["fecha"] = pd.to_datetime(d["fecha"])
        detalles[arm] = d
        out_p = REPO / f"evaluacion/baseline/outputs/fase0_detalle_{arm}.parquet"
        d.to_parquet(out_p, index=False)
        logger.info("brazo %s: %d votos, %d actas, Brier global=%.5f -> %s",
                    arm, len(d), d["acta_id"].nunique(), res["global"]["brier"], out_p)

    reporte: dict = {"arms": ARMS, "n_boot": n_boot, "seed": seed,
                     "muestra": muestra or "censo completo", "camara_filtro": camara_filtro or "ambas",
                     "por_arm": {}}
    for arm in ARMS:
        sub = detalles[arm]
        bloque_sub = sub[sub["fuente"] == "bloque"].copy()
        entrada: dict = {
            "n_actas_totales": int(sub["acta_id"].nunique()),
            "n_votos_totales": int(len(sub)),
            "global": bootstrap_cluster(sub, n_boot, seed),
            "rama_bloque": bootstrap_cluster(bloque_sub, n_boot, seed),
        }
        bloque_sub["era"] = pd.cut(bloque_sub["fecha"], bins=_ERA_BINS, labels=_ERA_LABELS)
        entrada["rama_bloque_por_era"] = {
            str(e): bootstrap_cluster(g, n_boot, seed)
            for e, g in bloque_sub.groupby("era", observed=True)
        }
        reporte["por_arm"][arm] = entrada

    base_bloque = detalles["primaria"][detalles["primaria"]["fuente"] == "bloque"]
    diffs = {}
    for arm in ARMS:
        if arm == "primaria":
            continue
        arm_bloque = detalles[arm][detalles[arm]["fuente"] == "bloque"]
        diffs[f"{arm}_menos_primaria__rama_bloque"] = _diferencia_pareada(
            arm_bloque, base_bloque, n_boot, seed)
    reporte["diferencias_vs_primaria"] = diffs

    # criterio de decisión explícito (PROMPT-MULTITEMA-V2.md FASE 0)
    st = reporte["por_arm"]["sin_tema"]["rama_bloque"]
    pr = reporte["por_arm"]["primaria"]["rama_bloque"]
    pl = reporte["por_arm"]["ponderada_logit"]["rama_bloque"]
    d_st = diffs["sin_tema_menos_primaria__rama_bloque"]
    d_pl = diffs["ponderada_logit_menos_primaria__rama_bloque"]
    if st and pr and st["punto"] <= pr["punto"]:
        criterio = ("sin_tema <= primaria (Brier, punto): apagar el condicionamiento "
                    "por tema en la rama de bloque es al menos tan bueno como condicionar "
                    "-> ver si la diferencia es DISTINGUIBLE DE CERO antes de recomendar "
                    "apagarlo en firme")
    elif pl and pr and pl["punto"] < pr["punto"] and d_st.get("distinguible_de_cero") is False:
        criterio = ("primaria < sin_tema Y ponderada_logit < primaria: hay señal real de "
                    "que condicionar por tema ayuda, y la especificación en probabilidad "
                    "la estaba destruyendo")
    else:
        criterio = ("resultado mixto o ninguna diferencia distinguible de cero contra el "
                    "brazo de control: ver diferencias_vs_primaria para el detalle antes "
                    "de concluir")
    reporte["lectura_automatica"] = criterio
    return reporte


class _ContadorAvisos(logging.Filter):
    """Mismo filtro que `baseline_voto_individual.py`: cuenta los avisos de
    `bloque` (miles, uno por acta) en vez de imprimir uno por uno — sin esto,
    con 4 brazos sobre el censo completo, el log de I/O domina el tiempo de
    corrida por encima del cómputo real."""

    def __init__(self):
        super().__init__()
        self.tally: dict = {}

    def filter(self, record):
        msg = record.getMessage()
        if "padron" in msg and "sin bancas vigentes" in msg:
            self.tally["padron_cae_a_ventana"] = self.tally.get("padron_cae_a_ventana", 0) + 1
            return False
        if "condicionamiento" in msg and "0 actas en ventana" in msg:
            self.tally["sin_actas_condicionadas"] = self.tally.get("sin_actas_condicionadas", 0) + 1
            return False
        if "actas AUX" in msg:
            self.tally["excluyo_aux"] = self.tally.get("excluyo_aux", 0) + 1
            return False
        if msg.startswith("v2:") or msg.startswith("v3"):
            self.tally["condicionamiento_ok"] = self.tally.get("condicionamiento_ok", 0) + 1
            return False
        return True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")
    cont = _ContadorAvisos()
    logging.getLogger("bloque").addFilter(cont)
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--camara", default="")
    ap.add_argument("--muestra", type=int, default=0, help="0 = censo completo (lo que pide FASE 0)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--salida", default=None)
    args = ap.parse_args(argv)

    reporte = correr_fase0(args.camara, args.muestra, args.seed, args.n_boot)
    reporte["avisos_agregados_bloque"] = dict(cont.tally)
    out = Path(args.salida) if args.salida else (
        REPO / "evaluacion/baseline/outputs/fase0_control_temas_censo.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(reporte, ensure_ascii=False, indent=1))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
