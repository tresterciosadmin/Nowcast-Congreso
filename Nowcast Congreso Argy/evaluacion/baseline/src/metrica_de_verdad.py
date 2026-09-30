# -*- coding: utf-8 -*-
"""La métrica de verdad del voto individual, con UN comando (auditoría 2026-09, ítem C1; pieza 1 del anclaje).

    python evaluacion/baseline/src/metrica_de_verdad.py                     # → outputs/metrica_de_verdad.json
    python evaluacion/baseline/src/metrica_de_verdad.py --verificar-motor 60   # + certificado del motor (PC, ≈ 10 min)

QUÉ DA. El skill del motor de hoy (`estricta__general`: historia estricta —fecha anterior y otra ley— y
RECORD_POR_TEMA apagado) sobre los votos emitidos del censo, con IC 95% re-muestreando LEYES (bootstrap de Poisson,
ADR-0032; 2.000 réplicas y semilla 7 por defecto, la pieza 1 pide ≥ 2.000) en: global, las 5 eras, las 2 cámaras y
un control de muestra (global sin los votos cuya ley no se conoce). Y, por corte, el ΔBrier PAREADO (las mismas leyes
re-muestreadas en las dos variantes) de la alternativa `estricta__tema` (RECORD_POR_TEMA prendido, el motor hasta
el 28-09) contra el motor de hoy. Positivo = la alternativa es peor.

DE DÓNDE SALE. De los estadísticos por acta que viajan por git (`censo_estadisticos.py`, ítem A2): no lee el detalle
voto a voto de 37 MB, así que corre en el CI y en un clon (segundos). El bootstrap es UNA sola copia
(`censo_estadisticos.skill_ic_desde_sumas`): con `--n-boot 300` reproduce al dígito lo que publica el harness. Para un
motor nuevo: regenerar el censo (`censo_detalle_paralelo.py`, 43 min, que reescribe ese JSON) y correr éste con
`--estadisticos <el nuevo>`.

PROCEDENCIA (lo que queda escrito en el JSON, y lo que NO se puede afirmar):
  * `HEAD` al correr y si hay archivos rastreados del motor modificados sin commitear.
  * El JSON de estadísticos: ruta, sha256 (con los finales de línea normalizados: en Windows está en CRLF y en el CI
    en LF), y de adentro, tal cual, la fecha en que se escribió, su `motor_sha` y el detalle del censo que cita.
    OJO: ese `motor_sha` es el `HEAD` del día que se ESCRIBIÓ el JSON, no el del motor que calculó las P_i.
  * Que las P_i del JSON sean las del motor de HOY se certifica con `--verificar-motor N`: re-corre el harness
    sobre N actas estratificadas (era × cámara) y compara voto a voto contra el detalle del censo. Necesita el
    detalle (no viaja por git: sólo la PC de Franco) y el resultado queda en `vigencia_del_motor`.

NO PISA NADA. Si el destino existe, falla (salida 3) salvo `--reemplazar`; y aun con `--reemplazar` se niega a
escribir sobre un archivo que no sea de este comando (marca `generador`): `baseline_voto_individual.json`, el resumen
del censo limpio y cualquier otro número versionado quedan fuera de su alcance. (`resumen_censo_limpio.py` sí pisa
`baseline_voto_individual.json`; no se tocó.)

NO HACE: no mide P(aprobación) (ítem C2), no cambia ningún término del motor, no valida las etiquetas de origen ni
la presencia, y no arregla que el IC de la era vigente (±0,25) sea ancho: lo declara.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import censo_estadisticos as ce  # noqa: E402

GENERADOR = "evaluacion/baseline/src/metrica_de_verdad.py"
SALIDA = Path(ce.ESTADISTICOS).with_name("metrica_de_verdad.json")   # al lado del JSON de estadísticos
FORMATO = 1
N_BOOT = 2000      # la pieza 1 del anclaje pide ≥ 2.000 (el harness usaba 300)
SEMILLA = 7        # la del harness
VARIANTE = "estricta__general"   # el motor de hoy
CONTRA = "estricta__tema"        # la alternativa pareada: RECORD_POR_TEMA prendido
CORTE_SIN_LEY = "global_sin_votos_sin_ley"
UMBRAL_VIGENCIA = 1e-9
SEMILLA_VIGENCIA = 7
# Lo que se considera "el motor" para decir si hay cambios sin commitear.
RUTAS_DEL_MOTOR = ("modelo", "variables", "definiciones.py", "rutas.py", "evaluacion/baseline/src")


class DestinoProtegido(Exception):
    """El destino existe y no se le puede escribir encima."""


# ────────────────────────────────────────────── la métrica ──────────────────────────────────────────────

def cortes_de(a: pd.DataFrame) -> dict:
    """Los cortes de `censo_estadisticos.cortes` (global, eras, cámaras) y el control de muestra."""
    c = dict(ce.cortes(a))
    c[CORTE_SIN_LEY] = ~a["ley"].astype(str).str.startswith("acta:").to_numpy()
    return c


def _skill(a: pd.DataFrame, v: str, mascara, n_boot: int, seed: int) -> dict:
    n, sy, se = ce.sumas_por_ley(a, v, mascara)
    base = sy.sum() / n.sum()
    bb = base * (1 - base)
    return {"skill": round(float(1 - (se.sum() / n.sum()) / bb), 4) if bb > 0 else None,
            "skill_ic95_ley": ce.skill_ic_desde_sumas(se, sy, n, n_boot, seed),
            "n_votos": int(n.sum()), "n_leyes": int(len(n))}


def _dif_brier(a: pd.DataFrame, v1: str, v0: str, mascara, n_boot: int, seed: int) -> dict:
    n, _sy, _se, d, b0 = ce.sumas_por_ley(a, v1, mascara, v0)
    r = ce.dif_brier_ic_desde_sumas(d, b0, n, n_boot, seed)
    r.update({"n_votos": int(n.sum()), "n_leyes": int(len(n))})
    return r


def medir(est: dict, variante: str = VARIANTE, contra: str = CONTRA, n_boot: int = N_BOOT,
          seed: int = SEMILLA) -> dict:
    """El skill y el ΔBrier pareado por corte, sólo a partir de los estadísticos por acta."""
    v, v1 = ce.variante(est, variante), ce.variante(est, contra)
    a = ce.tabla_actas(est)
    cs = cortes_de(a)
    return {"skill": {k: _skill(a, v, m, n_boot, seed) for k, m in cs.items()},
            "dif_brier_pareado": {k: _dif_brier(a, v1, v, m, n_boot, seed) for k, m in cs.items()}}


# ───────────────────────────────────────────── procedencia ─────────────────────────────────────────────

def _sha256_lf(ruta: Path) -> str:
    """sha256 del archivo con CRLF → LF (así da lo mismo en Windows, donde git lo saca en CRLF, y en Linux)."""
    return hashlib.sha256(ruta.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args: str):
    try:
        r = subprocess.run(["git", "--no-optional-locks", *args], cwd=str(REPO),
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def git_head():
    s = _git("rev-parse", "--short", "HEAD")
    return s.strip() if s else None


def motor_modificado():
    """Archivos RASTREADOS del motor con cambios sin commitear (None si no hay git, [] si está limpio). Los
    archivos nuevos sin rastrear no se cuentan: es un límite, dicho acá."""
    s = _git("status", "--porcelain", "--untracked-files=no", "--", *RUTAS_DEL_MOTOR)
    return None if s is None else [ln[3:].strip() for ln in s.splitlines() if ln.strip()]


def procedencia(est: dict, ruta_est: Path, argv: list) -> dict:
    try:
        ruta_rel = ruta_est.resolve().relative_to(REPO).as_posix()
    except ValueError:
        ruta_rel = ruta_est.as_posix()
    return {
        "head_sha_al_correr": git_head(),
        "motor_modificado_sin_commitear": motor_modificado(),
        "comando": ["metrica_de_verdad.py", *argv],
        "estadisticos": {
            "ruta": ruta_rel, "sha256_lf": _sha256_lf(ruta_est),
            "escrito_el": est.get("generado"),
            "motor_sha_al_escribirlo": est.get("motor_sha"),
            "nota_motor_sha": "es el HEAD del día en que se escribió el JSON, NO el del motor que calculó las P_i; "
                              "eso lo certifica `vigencia_del_motor` (--verificar-motor)",
            "censo": est.get("fuente"),
        },
    }


# ───────────────────────────────────────── vigencia del motor ─────────────────────────────────────────

def verificar_motor(detalle: Path, n_actas: int, seed: int = SEMILLA_VIGENCIA) -> dict:
    """Re-corre el harness con el motor de HOY (historia estricta, RECORD_POR_TEMA apagado) sobre `n_actas` actas
    estratificadas por era × cámara y compara voto a voto contra `p__estricta__general` del detalle del censo."""
    from baseline_voto_individual import (ERA_BINS, ERA_LABELS, Contexto,  # noqa: E402  (carga el motor: diferido)
                                          silenciar_avisos_del_motor)
    t0 = time.time()
    d = pd.read_parquet(detalle, columns=["acta_id", "fecha", "camara", "legislador",
                                          "p__estricta__general"])
    d["acta_id"] = d["acta_id"].astype(str)
    actas = d.drop_duplicates("acta_id")[["acta_id", "fecha", "camara"]].copy()
    actas["era"] = pd.cut(actas["fecha"], ERA_BINS, labels=ERA_LABELS)
    celdas = [g for _, g in actas.groupby(["era", "camara"], observed=True)]
    por_celda = max(1, n_actas // len(celdas))
    muestra = pd.concat([g.sort_values("acta_id").sample(min(len(g), por_celda), random_state=seed)
                         for g in celdas]).sort_values(["fecha", "acta_id"])
    silenciar_avisos_del_motor()
    ctx = Contexto.desde_repo()
    emitidos = ctx.votos[ctx.votos["conducta"].isin(["AFIRMATIVO", "NEGATIVO"])]
    por_acta = {k: g for k, g in emitidos.groupby("acta_id", sort=False)}
    ref = d[d["acta_id"].isin(muestra["acta_id"])].set_index(["acta_id", "legislador"])[
        "p__estricta__general"]
    n_comp = n_solo_det = n_solo_har = n_dist = 0
    max_dp, peores, saltadas = 0.0, [], 0
    for r in muestra.itertuples():
        sub = por_acta[r.acta_id]
        res = ctx.p_legisladores(r.acta_id, r.camara, r.fecha, sub, "estricta", False)
        det = ref.xs(r.acta_id, level="acta_id")
        if res is None:
            saltadas += 1
            n_solo_det += len(det)
            continue
        har = {lid: v[0] for lid, v in res.items()}
        comunes = set(har) & set(det.index)
        n_comp += len(comunes)
        n_solo_det += len(set(det.index) - set(har))
        n_solo_har += len(set(har) - set(det.index))
        for lid in comunes:
            dp = abs(har[lid] - float(det.loc[lid]))
            if dp > UMBRAL_VIGENCIA:
                n_dist += 1
                peores.append({"acta_id": r.acta_id, "legislador": str(lid), "dP": dp})
            max_dp = max(max_dp, dp)
    vigente = bool(n_comp > 0 and max_dp <= UMBRAL_VIGENCIA and n_solo_det == 0 and n_solo_har == 0)
    return {"vigente": vigente, "umbral": UMBRAL_VIGENCIA, "semilla": seed,
            "actas": int(len(muestra)), "por_celda": int(por_celda), "celdas": int(len(celdas)),
            "votos_comparados": int(n_comp), "max_abs_dP": max_dp, "votos_con_diferencia": int(n_dist),
            "votos_solo_en_el_detalle": int(n_solo_det), "votos_solo_en_el_motor_de_hoy": int(n_solo_har),
            "actas_con_postura_no_proyectable": int(saltadas),
            "peores": sorted(peores, key=lambda x: -x["dP"])[:5],
            "motor_head_sha": git_head(), "comparado_contra": "p__estricta__general del detalle del censo",
            "detalle": detalle.name, "minutos": round((time.time() - t0) / 60, 1)}


# ────────────────────────────────────────────────── E/S ──────────────────────────────────────────────────

def proteger_destino(salida: Path, reemplazar: bool) -> None:
    """Se llama ANTES de calcular nada: un número versionado no se pisa por descuido."""
    if not salida.exists():
        return
    if not reemplazar:
        raise DestinoProtegido(f"{salida} ya existe: no se pisa (pasar --reemplazar si es una métrica de "
                               "este comando que hay que regenerar)")
    try:
        propio = json.loads(salida.read_text(encoding="utf-8")).get("generador") == GENERADOR
    except (OSError, ValueError, AttributeError):
        propio = False
    if not propio:
        raise DestinoProtegido(f"{salida} existe y no es una métrica generada por este comando "
                               "(falta su marca `generador`): no se pisa ni con --reemplazar")


def escribir(res: dict, salida: Path) -> Path:
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_bytes((json.dumps(res, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))   # LF en todos lados
    return salida


def imprimir(res: dict) -> None:
    m = res["metodo"]
    print(f"skill de {m['variante']} · IC 95% re-muestreando leyes ({m['n_boot']} réplicas, semilla {m['semilla']})")
    for k, r in res["skill"].items():
        d = res["dif_brier_pareado"][k]
        print(f"  {k:<26} skill {r['skill']:>7} {r['skill_ic95_ley']}  {r['n_votos']:>7} votos {r['n_leyes']:>5} leyes"
              f"   |  ΔBrier {m['contra']} − motor: {d['dBrier_rel_%']:+.2f}% {d['ic95_rel_%_ley']}")
    v = res.get("vigencia_del_motor")
    if v:
        print(f"vigencia del motor: {'VIGENTE' if v['vigente'] else 'NO VIGENTE'} · {v['actas']} actas, "
              f"{v['votos_comparados']} votos, max|ΔP| = {v['max_abs_dP']:.3g}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--estadisticos", default=None,
                    help=f"JSON de estadísticos por acta (default: {ce.ESTADISTICOS})")
    ap.add_argument("--variante", default=VARIANTE)
    ap.add_argument("--contra", default=CONTRA, help="variante de la comparación pareada")
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    ap.add_argument("--salida", default=None, help=f"default: {SALIDA}")
    ap.add_argument("--reemplazar", action="store_true",
                    help="regenerar una métrica de este comando ya escrita (nunca pisa un archivo ajeno)")
    ap.add_argument("--verificar-motor", type=int, default=0, metavar="N",
                    help="re-correr el harness sobre N actas y compararlo con el detalle del censo (sólo donde "
                         "está el detalle)")
    ap.add_argument("--detalle", default=None,
                    help="parquet del censo para --verificar-motor (default: el que cita el JSON)")
    args = ap.parse_args(argv)
    raw = sys.argv[1:] if argv is None else list(argv)

    salida = Path(args.salida) if args.salida else REPO / SALIDA
    try:
        proteger_destino(salida, args.reemplazar)
    except DestinoProtegido as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3
    ruta_est = Path(args.estadisticos) if args.estadisticos else REPO / ce.ESTADISTICOS
    est = ce.cargar(ruta_est)

    res = {"formato": FORMATO, "generador": GENERADOR, "generado": date.today().isoformat(),
           "metodo": {"variante": args.variante, "contra": args.contra, "n_boot": args.n_boot,
                      "semilla": args.semilla, "unidad_de_remuestreo": "ley (bootstrap de Poisson, ADR-0032)",
                      "skill": "1 − Brier / Brier de la climatología de la muestra (se recalcula en cada réplica)",
                      "dif_brier_pareado": "alternativa − motor, relativo al Brier del motor; positivo = la "
                                           "alternativa es peor; las mismas leyes re-muestreadas en las dos",
                      "votos": "emitidos (afirmativo / negativo); una unidad-ley por acta sin ley identificable"},
           "procedencia": procedencia(est, ruta_est, raw)}
    res.update(medir(est, args.variante, args.contra, args.n_boot, args.semilla))
    codigo = 0
    if args.verificar_motor:
        detalle = Path(args.detalle) if args.detalle else REPO / (est.get("fuente") or {}).get("detalle", "")
        if not detalle.is_file():
            print(f"ERROR: --verificar-motor necesita el detalle del censo y no está: {detalle}", file=sys.stderr)
            return 4
        res["vigencia_del_motor"] = verificar_motor(detalle, args.verificar_motor)
        if not res["vigencia_del_motor"]["vigente"]:
            codigo = 2
    escribir(res, salida)
    imprimir(res)
    print(f"-> {salida}")
    if codigo:
        print("ATENCIÓN: el motor de hoy NO reproduce las P_i del censo (vigencia_del_motor): "
              "las cifras no son del motor de hoy.", file=sys.stderr)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
