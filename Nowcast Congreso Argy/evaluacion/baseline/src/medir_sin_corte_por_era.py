# -*- coding: utf-8 -*-
"""El brazo «sin corte por era» con el motor completo (auditoría 2026-09, ítem C3; decisión 7 de Franco).

    python evaluacion/baseline/src/medir_sin_corte_por_era.py            # el veredicto, desde los estadísticos de git (segundos)
    python evaluacion/baseline/src/medir_sin_corte_por_era.py --censo    # el censo del brazo (PC, 7 procesos) + controles

QUÉ ES. El guard de era (ADR-0018) corta el récord individual en el arranque de la era (gobierno) del acta. Franco lo
dejó prendido «bajo revisión». `GUARD_ERA=0` NO sirve para medir qué pasa sin él: deja la fecha fija en 2023-12-10 y
vacía el récord de todo lo anterior. Acá el brazo es del HARNESS (`baseline_voto_individual.correr(era_desde=…)`): el
motor corre igual, con el récord acumulando desde 1900-01-01. UN solo brazo: el récord. El corte propio de la postura de
bloque (ventana de 730 días y «mismo gobierno» al condicionar por origen) queda como está.

QUÉ DA. ΔBrier PAREADO (las mismas leyes re-muestreadas en las dos variantes) = (Brier sin corte − Brier con corte) /
Brier con corte: POSITIVO = EL GUARD AYUDA. 2.000 réplicas, semilla 7. PRIMARIO: las actas desde 2015-12-10, donde el
guard actúa (antes la era KIRCHNER arranca en 1900 y el guard ya no corta: ahí el brazo es idéntico al motor, y eso es un
control, no un resultado). Secundarios: global, cada era, cada cámara. El veredicto sale de la regla fijada antes de
medir (ver `ESTADO-EJECUCION.md`, «C3 — pre-registro»): el extremo inferior del primario > 0 → el guard se sostiene; el
superior < 0 → sin corte es mejor; el IC incluye 0 → no se distingue (y se recomienda subir el modelo a Opus). EN
NINGÚN CASO se toca la bandera: decide Franco.

DE DÓNDE SALE. Los estadísticos por acta con las dos variantes (`outputs/censo_estadisticos_sin_corte_era_2026-10-01.json`,
versionado, como los de A2): `estricta__general` (el motor de hoy, la columna del censo del 28-09, certificada vigente en
C1) y `estricta__sin_corte_era` (el censo del brazo). Con `--censo` los regenera (≈ 15 min) y escribe además lo que sólo
sale del voto a voto (PC): los CONTROLES DEL BRAZO —mismo conjunto de votos; antes de 2015-12-10 max|Δp| = 0;
`n_prev` del brazo ≥ el del motor; postura (share y desvío) idéntica— y el efecto sobre los votos que el corte toca.
Si un control falla, NO se interpreta ningún Δ.

NO PISA NADA (como `metrica_de_verdad.py`): destino que existe → salida 3 salvo `--reemplazar`, y aun así no se pisa un
JSON ajeno. No cambia ningún término del motor.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_estadisticos as ce  # noqa: E402
import metrica_de_verdad as MV  # noqa: E402

GENERADOR = "evaluacion/baseline/src/medir_sin_corte_por_era.py"
ERA_DESDE = "1900-01-01"             # el récord acumula desde acá: nada se corta por era
BASE, ARM = "estricta__general", "estricta__sin_corte_era"
# El brazo sobre el motor de HOY (lote de D1: re-corrido sobre el censo del 2026-10-03, ventana de la postura en 2190)
# y el de C3 (sobre el censo del 28-09: su veredicto queda en git como evidencia; no se pisa). El del 2026-10-02 (D1.0)
# es el insumo del guard en D1 (`medir_d1_parametros_pi.DETALLE_GUARD`): queda en disco y en git, no se pisa.
DETALLE_ARM = Path(ce.DETALLE).with_name("censo_detalle_sin_corte_era_2026-10-03.parquet")   # ignorado por git
ESTADISTICOS = Path(ce.ESTADISTICOS).with_name("censo_estadisticos_sin_corte_era_2026-10-03.json")
ESTADISTICOS_C3 = Path(ce.ESTADISTICOS).with_name("censo_estadisticos_sin_corte_era_2026-10-01.json")
SALIDA = Path(ce.ESTADISTICOS).with_name("guard_era_sin_corte.json")
PRIMARIO_DESDE = "2015-12-10"        # el primer recambio donde el guard corta (KIRCHNER arranca en 1900)
N_BOOT, SEMILLA = 2000, 7
UMBRAL_IGUAL = 1e-12
FORMATO = 1


# ──────────────────────────────────────────── el veredicto (git) ────────────────────────────────────────────

def cortes_de(a: pd.DataFrame) -> dict:
    """Primario, control, secundarios. Máscaras sobre la tabla de actas."""
    f = a["fecha"] >= pd.Timestamp(PRIMARIO_DESDE)
    c = {"primario__desde_2015-12-10": f.to_numpy(), "control__antes_de_2015-12-10": (~f).to_numpy(),
         "secundario__global": np.ones(len(a), bool)}
    for e in ("2015-2019", "2019-2023", "desde 2023"):
        c[f"secundario__era={e}"] = (a["era"] == e).to_numpy()
    for cam in sorted(a["camara"].unique()):
        c[f"secundario__desde_2015-12-10 & camara={cam}"] = (f & (a["camara"] == cam)).to_numpy()
    return c


def regla(ic: list) -> dict:
    """La regla del pre-registro de C3, sobre el IC del ΔBrier relativo (sin corte − con corte) del primario."""
    lo, hi = ic
    if lo > 0:
        r, rec = "EL_GUARD_SE_SOSTIENE", "conservar el guard: sin el corte el Brier empeora (el IC excluye 0)"
    elif hi < 0:
        r, rec = "SIN_CORTE_ES_MEJOR", "quitar el corte por era: sin él el Brier mejora (el IC excluye 0)"
    else:
        r, rec = "NO_SE_DISTINGUE", ("dejar el guard como está (la bandera no se mueve sin evidencia) y subir el modelo "
                                      "principal a Opus para este veredicto (§9.10): el IC del primario incluye 0")
    return {"resultado": r, "recomendacion": rec, "recomendar_opus": r == "NO_SE_DISTINGUE", "decide": "Franco",
            "la_bandera_se_toca": False}


def veredicto(est: dict, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    a = ce.tabla_actas(est)
    v1, v0 = ce.variante(est, ARM), ce.variante(est, BASE)
    out = {"dif_brier_pareado": {}, "skill": {}}
    for k, m in cortes_de(a).items():
        out["dif_brier_pareado"][k] = MV._dif_brier(a, v1, v0, m, n_boot, seed)
        out["skill"][k] = {"con_corte": MV._skill(a, v0, m, n_boot, seed), "sin_corte": MV._skill(a, v1, m, n_boot, seed)}
    prim = out["dif_brier_pareado"]["primario__desde_2015-12-10"]
    out["veredicto"] = {"primario": prim, **regla(prim["ic95_rel_%_ley"])}
    return out


def proteger(destino: Path, reemplazar: bool) -> None:
    if not destino.exists():
        return
    if not reemplazar:
        raise MV.DestinoProtegido(f"{destino} ya existe: no se pisa (pasar --reemplazar si es de este comando)")
    if destino.suffix == ".json":
        try:
            propio = json.loads(destino.read_text(encoding="utf-8")).get("generador") == GENERADOR
        except (OSError, ValueError, AttributeError):
            propio = False
        if not propio:
            raise MV.DestinoProtegido(f"{destino} existe y no es de este comando (falta su marca `generador`): no se pisa")


def procedencia(est: dict, ruta: Path, argv: list) -> dict:
    try:
        rel = ruta.resolve().relative_to(REPO).as_posix()
    except ValueError:
        rel = ruta.as_posix()
    return {"head_sha_al_correr": MV.git_head(), "motor_modificado_sin_commitear": MV.motor_modificado(),
            "comando": ["medir_sin_corte_por_era.py", *argv],
            "estadisticos": {"ruta": rel, "sha256_lf": MV._sha256_lf(ruta), "escrito_el": est.get("generado"),
                             "motor_head_sha_al_escribirlo": est.get("motor_sha"), "fuente": est.get("fuente"),
                             "variantes": est.get("variantes")}}


# ─────────────────────────────────────── el censo del brazo (PC) ───────────────────────────────────────

def _tramo(args):
    """Un tramo de fechas del censo del brazo. `era_desde` viaja como ARGUMENTO: el pool usa `spawn` y una variable
    de módulo cambiada en el proceso padre no llegaría al trabajador."""
    desde, hasta, era_desde = args
    import logging
    from baseline_voto_individual import correr, silenciar_avisos_del_motor
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format=f"%(asctime)s [{desde}] %(levelname)s %(message)s")
    silenciar_avisos_del_motor()
    t0 = time.time()
    res, d = correr(desde=desde, hasta=hasta, historia="estricta", record_por_tema=False, devolver_detalle=True,
                    era_desde=era_desde)
    logging.getLogger("censo").info("tramo %s..%s: %d votos en %.1f min", desde, hasta, len(d), (time.time() - t0) / 60)
    return d[["acta_id", "fecha", "camara", "legislador", "y", "ley", "p", "share", "desvio", "record", "n_prev"]]


def censo_del_brazo(procesos: int, tramos: int) -> pd.DataFrame:
    if os.environ.get("GUARD_ERA") == "0":
        raise RuntimeError("GUARD_ERA=0 en el entorno: el brazo mediría otra cosa (el motor fija la fecha en ERA_FIJA)")
    from censo_detalle_paralelo import bordes
    trs = bordes(tramos)
    with get_context("spawn").Pool(procesos) as pool:
        partes = list(pool.imap_unordered(_tramo, [(a, b, ERA_DESDE) for a, b in trs]))
    d = pd.concat(partes, ignore_index=True).sort_values(["fecha", "acta_id"]).reset_index(drop=True)
    if d.duplicated(["acta_id", "legislador"]).any():
        raise RuntimeError("votos duplicados entre tramos: los bordes se pisan")
    return d


def controles_del_censo(m: pd.DataFrame, n_base: int, n_arm: int) -> dict:
    """Los controles del brazo (criterio 3 del pre-registro) sobre los votos que están en los dos censos (`m`). Si
    fallan, no se interpreta ningún Δ."""
    antes = (m["fecha"] < pd.Timestamp(PRIMARIO_DESDE)).to_numpy()
    dp = (m["p__brazo"] - m["p__estricta__general"]).abs().to_numpy()
    dn = (m["n_prev__brazo"] - m["n_prev__estricta__general"]).to_numpy()
    c = {"votos": int(len(m)),
         "mismo_conjunto_de_votos": bool(len(m) == n_base == n_arm),
         "y_y_ley_identicos": bool((m["y_brazo"] == m["y"]).all() and (m["ley_brazo"] == m["ley"]).all()),
         "antes_de_2015-12-10": {"votos": int(antes.sum()), "max_abs_dp": float(dp[antes].max()),
                                 "votos_distintos": int((dp[antes] > UMBRAL_IGUAL).sum())},
         "desde_2015-12-10": {"votos": int((~antes).sum()), "max_abs_dp": float(dp[~antes].max()),
                              "votos_distintos": int((dp[~antes] > UMBRAL_IGUAL).sum()),
                              "fraccion_distintos": round(float((dp[~antes] > UMBRAL_IGUAL).mean()), 4)},
         "n_prev_brazo_menor_que_el_motor": int((dn < 0).sum()),
         "n_prev_distinto_antes_de_2015-12-10": int((dn[antes] != 0).sum()),
         "n_prev_mayor_desde_2015-12-10": int((dn[~antes] > 0).sum()),
         "postura_share_max_abs_dif": float((m["share__brazo"] - m["share__estricta__general"]).abs().max()),
         "postura_desvio_max_abs_dif": float((m["desvio__brazo"] - m["desvio__estricta__general"]).abs().max())}
    c["cumple"] = bool(c["mismo_conjunto_de_votos"] and c["y_y_ley_identicos"]
                       and c["antes_de_2015-12-10"]["max_abs_dp"] <= UMBRAL_IGUAL
                       and c["n_prev_brazo_menor_que_el_motor"] == 0
                       and c["n_prev_distinto_antes_de_2015-12-10"] == 0
                       and c["n_prev_mayor_desde_2015-12-10"] > 0
                       and c["postura_share_max_abs_dif"] <= UMBRAL_IGUAL and c["postura_desvio_max_abs_dif"] <= UMBRAL_IGUAL)
    return c


def efecto_en_lo_que_toca(m: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEMILLA) -> dict:
    """ΔBrier pareado sólo sobre los votos donde el corte cambia la P_i (necesita el voto a voto: sólo PC)."""
    toca = ((m["p__brazo"] - m["p__estricta__general"]).abs() > UMBRAL_IGUAL).to_numpy()
    y = m["y"].to_numpy(float)
    e1, e0 = (m["p__brazo"].to_numpy(float) - y) ** 2, (m["p__estricta__general"].to_numpy(float) - y) ** 2
    _, cod = np.unique(m["ley"].to_numpy().astype(str)[toca], return_inverse=True)
    k = int(cod.max()) + 1
    d = np.bincount(cod, (e1 - e0)[toca], k)
    b0 = np.bincount(cod, e0[toca], k)
    n = np.bincount(cod, minlength=k).astype(float)
    r = ce.dif_brier_ic_desde_sumas(d, b0, n, n_boot, seed)
    r.update({"votos_que_toca": int(toca.sum()), "fraccion_de_los_votos": round(float(toca.mean()), 4),
              "n_leyes": int(k)})
    return r


def leer_base(detalle_base: Path) -> pd.DataFrame:
    """Las columnas de la variante del motor (`estricta__general`) en el censo de base. En el censo del 28-09 esa
    variante era una extra (columnas `*__estricta__general`); desde el del 2026-10-02 (auditoría D1.0, RECORD_POR_TEMA
    apagado) es la PRINCIPAL: sus columnas no llevan sufijo y sólo `p` tiene el alias `p__estricta__general`. Se usan las
    de la principal sólo si `p` es idéntica a `p__estricta__general` (si no, falla)."""
    import pyarrow.parquet as pq
    hay = set(pq.ParquetFile(detalle_base).schema_arrow.names)
    comunes = ["acta_id", "legislador", "fecha", "camara", "y", "ley", "p__estricta__general"]
    extra = ["n_prev", "share", "desvio"]
    if all(f"{c}__estricta__general" in hay for c in extra):
        return pd.read_parquet(detalle_base, columns=comunes + [f"{c}__estricta__general" for c in extra])
    b = pd.read_parquet(detalle_base, columns=comunes + ["p"] + extra)
    if not np.array_equal(b["p"].to_numpy(), b["p__estricta__general"].to_numpy()):
        raise ValueError(f"{detalle_base.name}: no trae las columnas de `estricta__general` y su principal no es esa variante")
    return b.drop(columns="p").rename(columns={c: f"{c}__estricta__general" for c in extra})


def correr_censo(args, raw: list) -> int:
    t0 = time.time()
    detalle_base = REPO / ce.DETALLE
    base = leer_base(detalle_base)
    print("censo del brazo (era_desde =", ERA_DESDE, ") …", flush=True)
    arm = censo_del_brazo(args.procesos, args.tramos)
    DETALLE_ARM_ABS = REPO / DETALLE_ARM
    DETALLE_ARM_ABS.parent.mkdir(parents=True, exist_ok=True)
    arm.to_parquet(DETALLE_ARM_ABS, index=False)
    print(f"-> {DETALLE_ARM_ABS} ({len(arm)} votos, {(time.time() - t0) / 60:.1f} min)", flush=True)

    arm = arm.rename(columns={"p": "p__brazo", "n_prev": "n_prev__brazo", "share": "share__brazo",
                              "desvio": "desvio__brazo", "y": "y_brazo", "ley": "ley_brazo"})
    m = base.merge(arm[["acta_id", "legislador", "p__brazo", "n_prev__brazo", "share__brazo", "desvio__brazo",
                        "y_brazo", "ley_brazo"]], on=["acta_id", "legislador"], how="outer", indicator=True,
                   validate="1:1")
    mm = m[m["_merge"] == "both"].copy()
    ctl = controles_del_censo(mm, len(base), len(arm))
    print("controles del brazo:", json.dumps(ctl, ensure_ascii=False))
    if not ctl["cumple"]:
        print("ATENCIÓN: un control del brazo FALLA: no se interpreta ningún Δ.", file=sys.stderr)

    d = mm.rename(columns={"p__brazo": f"p__{ARM}"})[
        ["acta_id", "fecha", "camara", "y", "ley", "p__estricta__general", f"p__{ARM}"]]
    est = ce.generar(d, (BASE, ARM), DETALLE_ARM_ABS)
    est["generador"], est["generado_con"] = GENERADOR, "censo_estadisticos.generar"
    est["fuente"]["detalle_base"] = ce.DETALLE
    est["fuente"]["detalle_base_sha256_16"] = ce._sha16(detalle_base)
    est["fuente"]["era_desde_del_brazo"] = ERA_DESDE
    # el panel no cambió: las sumas de `estricta__general` coinciden con las de los estadísticos de A2
    a_nuevo, a_viejo = ce.tabla_actas(est), ce.tabla_actas(ce.cargar())
    ctl["sumas_del_motor_iguales_a_las_de_A2"] = bool(
        list(a_nuevo["acta_id"]) == list(a_viejo["acta_id"])
        and np.allclose(a_nuevo["se__estricta__general"], a_viejo["se__estricta__general"], rtol=0, atol=1e-9))
    ce.escribir(est, REPO / ESTADISTICOS)
    print(f"-> {REPO / ESTADISTICOS}", flush=True)
    pc = {"controles_del_brazo": ctl, "efecto_en_los_votos_que_el_corte_toca": efecto_en_lo_que_toca(mm), "minutos": round((time.time() - t0) / 60, 1)}
    return finalizar(args, raw, pc)


def finalizar(args, raw: list, pc: dict | None) -> int:
    ruta = REPO / ESTADISTICOS
    est = ce.cargar(ruta)
    res = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "metodo": {"n_boot": args.n_boot, "semilla": args.semilla, "era_desde_del_brazo": ERA_DESDE,
                      "unidad_de_remuestreo": "ley (bootstrap de Poisson, ADR-0032)",
                      "dif_brier_pareado": "(Brier sin corte − Brier con corte) / Brier con corte; positivo = el guard ayuda",
                      "primario": f"actas desde {PRIMARIO_DESDE} (donde el guard corta)",
                      "control": f"antes de {PRIMARIO_DESDE} el guard no corta: el brazo es idéntico al motor y Δ ≡ 0",
                      "alcance": "un solo brazo, el récord; la postura de bloque conserva su propio corte"},
           "procedencia": procedencia(est, ruta, raw)}
    res.update(veredicto(est, args.n_boot, args.semilla))
    if pc:
        res["pc_solo"] = pc
    salida = Path(args.salida) if args.salida else REPO / SALIDA
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes((json.dumps(res, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    imprimir(res)
    print(f"-> {salida}")
    return 0 if (pc is None or pc["controles_del_brazo"]["cumple"]) else 2


def imprimir(res: dict) -> None:
    print("ΔBrier pareado (sin corte − con corte) / con corte; POSITIVO = el guard ayuda:")
    for k, d in res["dif_brier_pareado"].items():
        s = res["skill"][k]
        print(f"  {k:<44} {d['dBrier_rel_%']:+7.2f}% {d['ic95_rel_%_ley']}  {d['n_votos']:>7} votos {d['n_leyes']:>5} leyes"
              f"  skill {s['con_corte']['skill']} → {s['sin_corte']['skill']}")
    v = res["veredicto"]
    print(f"VEREDICTO (regla fijada antes de medir): {v['resultado']} — {v['recomendacion']}. Decide {v['decide']}.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--censo", action="store_true", help="correr el censo del brazo (PC; ≈ 15 min) y los controles")
    ap.add_argument("--procesos", type=int, default=7)
    ap.add_argument("--tramos", type=int, default=21)
    ap.add_argument("--salida", default=None, help=f"default: {SALIDA}")
    ap.add_argument("--reemplazar", action="store_true", help="regenerar archivos de este comando (nunca uno ajeno)")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    args = ap.parse_args(argv)
    raw = sys.argv[1:] if argv is None else list(argv)
    salida = Path(args.salida) if args.salida else REPO / SALIDA
    try:
        proteger(salida, args.reemplazar)
        if args.censo:
            for dest in (REPO / ESTADISTICOS, REPO / DETALLE_ARM):
                proteger(dest, args.reemplazar)
    except MV.DestinoProtegido as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    return correr_censo(args, raw) if args.censo else finalizar(args, raw, None)


if __name__ == "__main__":
    raise SystemExit(main())
