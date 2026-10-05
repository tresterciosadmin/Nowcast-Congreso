# -*- coding: utf-8 -*-
"""Estadísticos suficientes del censo, para que viajen por git (auditoría 2026-09, ítem A2).

El detalle del censo (`censo_detalle_*.parquet`, 37 MB, voto a voto) está ignorado por git
(`*.parquet`), así que vive en un solo disco: quien clona no puede recalcular el skill, su
IC, τ ni ε₀. Este módulo guarda, en un JSON versionado, lo MÍNIMO que esos cálculos piden:

  * UNA FILA POR ACTA con su ley, cámara, fecha y era: n votos, Σy y, para cada variante de
    P_i guardada, Σ(p−y)², Σp y Σp². Con eso salen, por suma, las sumas POR LEY de cualquier
    corte (global, era, cámara) → el skill y su IC re-muestreando leyes (bootstrap de
    Poisson, ADR-0032) y el ΔBrier pareado entre dos variantes; y, por acta, la sobre-
    dispersión del recuento que estima τ (Σp y Σp² alcanzan para cualquier ε₀ porque el
    encogimiento p̃ = ε₀ + (1−2ε₀)p es afín).
  * LA GRILLA DE ε₀: Σ(p̃−y)² y Σ log-loss para cada ε₀ de la grilla, por cámara. El
    log-loss depende de la distribución completa de p (135.000 valores distintos), así que
    no se reduce a unos momentos: se guarda la curva sobre la grilla que usa el estimador
    (0 a 0,30 cada 0,005). LÍMITE DECLARADO: otra grilla u otra pérdida exigen regenerar
    desde el detalle.

Qué NO alcanza (y por eso sigue pidiendo el detalle voto a voto): la cobertura de la banda
(simula acta por acta con cada P_i), las tablas por fuente y por carácter del dictamen, y
cualquier re-estimación que cambie las P_i — para eso se regenera el censo (43 min,
`censo_detalle_paralelo.py`), que al terminar vuelve a escribir este JSON.

    python evaluacion/baseline/src/censo_estadisticos.py            # el censo del 28-09
    python evaluacion/baseline/src/censo_estadisticos.py --detalle X.parquet --salida Y.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

# El censo del motor de HOY (auditoría 2026-09, lote de D1: la ventana de la postura en 2190 días; re-anclado a
# propósito). El del 2026-10-02 (D1.0, la ficha al día) fue V0 de D1: queda en git y en disco, no se pisa.
DETALLE = "evaluacion/baseline/outputs/censo_detalle_2026-10-03.parquet"
ESTADISTICOS = "evaluacion/baseline/outputs/censo_estadisticos_2026-10-03.json"
DETALLE_2026_10_02 = "evaluacion/baseline/outputs/censo_detalle_2026-10-02.parquet"
ESTADISTICOS_2026_10_02 = "evaluacion/baseline/outputs/censo_estadisticos_2026-10-02.json"
# El censo del 28-09 (motor antes de la fase D): sus estadísticos siguen en git y son la CONTINUIDAD con lo
# publicado (0,1333 y la tabla del §9.2). No se pisan: los tests que prueban esa continuidad los nombran acá.
DETALLE_2026_09_28 = "evaluacion/baseline/outputs/censo_detalle_2026-09-28.parquet"
ESTADISTICOS_2026_09_28 = "evaluacion/baseline/outputs/censo_estadisticos_2026-09-28.json"

FORMATO = 1
# Variantes que se guardan: el motor de hoy (RECORD_POR_TEMA apagado) y la que tenía prendida
# el censo al generarse. Las otras del censo (`fecha__tema`, `dia_incluido__*`) sirven para
# descomponer la fuga del 28-09 (ADR-0034) y se piden con --variantes.
VARIANTES_POR_DEFECTO = ("estricta__general", "estricta__tema")
# La columna `p` del censo es la variante principal: historia estricta con RECORD_POR_TEMA según su
# bandera EN ESE MOMENTO. En el censo del 28-09 estaba prendida (`p` = `p__estricta__tema`); desde el
# del 2026-10-02 (D1.0) está apagada (`p` = `p__estricta__general`). Por eso el alias ya no es una
# constante: `generar` lo DEDUCE (la variante guardada cuya columna es idéntica a `p`) y, si ninguna lo
# es, falla en vez de aliasar mal (`_alias_de_p`).

# La grilla de `estimar_epsilon_tau.estimar_epsilon`: una sola copia.
GRILLA_EPS = np.round(np.arange(0.0, 0.301, 0.005), 3)
_CLIP = 1e-9   # el de `estimar_epsilon_tau._logloss`


# ────────────────────────────── el bootstrap por ley, desde sumas ──────────────────────────────
# Estas dos funciones son el cuerpo de `baseline_voto_individual.skill_ic_por_ley` y
# `dif_brier_ic_por_ley` a partir de las sumas por ley; el harness las llama (una sola copia).

def skill_ic_desde_sumas(se, sy, n, n_boot: int = 300, seed: int = 7) -> list:
    """IC 95% del skill re-muestreando LEYES enteras (bootstrap de Poisson, ADR-0032).
    `se`, `sy`, `n`: Σ(p−y)², Σy y n votos POR LEY. La climatología se recalcula en cada
    réplica con la tasa base de esa réplica."""
    se, sy, n = (np.asarray(x, float) for x in (se, sy, n))
    k = len(n)
    W = np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)
    N, SY, SE = W @ n, W @ sy, W @ se
    with np.errstate(divide="ignore", invalid="ignore"):
        base = SY / N
        s = 1 - (SE / N) / (base - base ** 2)  # y binaria: brier de climatología = b(1-b)
    s = s[np.isfinite(s)]                      # réplicas vacías o sin varianza (pocas leyes)
    if len(s) < n_boot // 2:
        return [None, None]
    return [round(float(np.percentile(s, 2.5)), 4), round(float(np.percentile(s, 97.5)), 4)]


def dif_brier_ic_desde_sumas(d, b0, n, n_boot: int = 300, seed: int = 7) -> dict:
    """ΔBrier (p1 − p0), relativo, y su IC 95% re-muestreando LEYES. `d` = Σ(e1−e0) por
    ley, `b0` = Σe0 por ley, `n` = votos por ley."""
    d, b0, n = (np.asarray(x, float) for x in (d, b0, n))
    k = len(n)
    W = np.random.default_rng(seed).poisson(1.0, (n_boot, k)).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = (W @ d) / (W @ b0)
    rel = rel[np.isfinite(rel)]
    return {"dBrier": round(float(d.sum() / n.sum()), 6),
            "dBrier_rel_%": round(100 * float(d.sum() / b0.sum()), 2),
            "ic95_rel_%_ley": [round(100 * float(np.percentile(rel, 2.5)), 2),
                               round(100 * float(np.percentile(rel, 97.5)), 2)]}


# ────────────────────────────────────────── generar ──────────────────────────────────────────

def _sha16(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()[:16]


def _git_head() -> str | None:
    try:
        r = subprocess.run(["git", "--no-optional-locks", "rev-parse", "--short", "HEAD"],
                           cwd=str(REPO), capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _curvas_epsilon(p: np.ndarray, y: np.ndarray) -> tuple[list, list]:
    """Σ(p̃−y)² y Σ log-loss para cada ε₀ de la grilla (mismas definiciones que
    `estimar_epsilon_tau._brier/_logloss`, pero SUMAS, para poder combinar cámaras)."""
    brier, logloss = [], []
    for e in GRILLA_EPS:
        pe = e + (1 - 2 * e) * p
        brier.append(float(((pe - y) ** 2).sum()))
        q = np.clip(pe, _CLIP, 1 - _CLIP)
        logloss.append(float(-(y * np.log(q) + (1 - y) * np.log(1 - q)).sum()))
    return brier, logloss


def _alias_de_p(d: pd.DataFrame, cols: dict) -> str | None:
    """La variante guardada cuya columna es IDÉNTICA a `p` (None si el detalle no trae `p`). Si `p` no coincide
    con ninguna, falla: un alias falso haría que «p» quiera decir otra cosa en el JSON."""
    if "p" not in d.columns:
        return None
    p = d["p"].to_numpy()
    iguales = [v for v, c in cols.items() if np.array_equal(p, d[c].to_numpy())]
    if not iguales:
        raise ValueError("`p` no es igual a ninguna de las variantes guardadas "
                         f"{sorted(cols)}: revisar el alias antes de guardar")
    return iguales[0]


def generar(d: pd.DataFrame, variantes=VARIANTES_POR_DEFECTO, detalle: str | Path | None = None,
            era_bins=None, era_labels=None) -> dict:
    """Estadísticos a partir del detalle voto a voto `d` (columnas: acta_id, fecha, camara,
    y, ley, y una `p__<variante>` por variante; `p` para el alias)."""
    if era_bins is None:                      # import diferido: el harness pesa; sólo generar lo necesita
        from baseline_voto_individual import ERA_BINS as era_bins, ERA_LABELS as era_labels
    d = d.copy()
    d["ley"] = d["ley"].fillna("acta:" + d["acta_id"].astype(str))
    if (d["fecha"] != d["fecha"].dt.normalize()).any():
        raise ValueError("hay fechas con hora: la fila por acta pierde información")
    ley_por_acta = d.groupby("acta_id")["ley"].nunique()
    if (ley_por_acta > 1).any():
        raise ValueError(f"{int((ley_por_acta > 1).sum())} actas con más de una ley: la fila "
                         "por acta no alcanza")
    cols = {v: f"p__{v}" for v in variantes}
    faltan = [c for c in cols.values() if c not in d.columns]
    if faltan:
        raise KeyError(f"el detalle no tiene {faltan}; hay "
                       f"{[c for c in d.columns if c == 'p' or c.startswith('p__')]}")
    alias_p = _alias_de_p(d, cols)

    y = d["y"].to_numpy(float)
    g = pd.DataFrame({"acta_id": d["acta_id"].to_numpy(), "y": y})
    for v, c in cols.items():
        p = d[c].to_numpy(float)
        g[f"se__{v}"], g[f"sp__{v}"], g[f"sp2__{v}"] = (p - y) ** 2, p, p * p
    agg = {"y": ["size", "sum"], **{k: "sum" for k in g.columns if k not in ("acta_id", "y")}}
    a = g.groupby("acta_id", sort=True).agg(agg)
    a.columns = ["n", "sy"] + [c for c in a.columns.get_level_values(0)[2:]]
    meta = (d.groupby("acta_id")[["ley", "camara", "fecha"]].first())
    a = meta.join(a).reset_index().sort_values(["fecha", "acta_id"], kind="stable")
    a["era"] = pd.cut(a["fecha"], bins=era_bins, labels=era_labels).astype(str)
    orden = ["acta_id", "ley", "camara", "fecha", "era", "n", "sy"] + [
        f"{k}__{v}" for v in cols for k in ("se", "sp", "sp2")]
    a = a[orden]
    filas = []
    for r in a.itertuples(index=False):
        fila = list(r)
        fila[3] = fila[3].strftime("%Y-%m-%d")
        filas.append([int(x) if isinstance(x, (np.integer,)) else
                      float(x) if isinstance(x, (np.floating,)) else x for x in fila])

    camaras = sorted(d["camara"].unique())
    eps = {"grilla": [float(e) for e in GRILLA_EPS],
           "n_votos": {c: int((d["camara"] == c).sum()) for c in camaras}, "variantes": {}}
    for v, c in cols.items():
        eps["variantes"][v] = {}
        for cam in camaras:
            m = (d["camara"] == cam).to_numpy()
            b, ll = _curvas_epsilon(d.loc[m, c].to_numpy(float), y[m])
            eps["variantes"][v][cam] = {"brier_suma": b, "logloss_suma": ll}

    fuente = {"n_votos": int(len(d)), "n_actas": int(d["acta_id"].nunique()),
              "n_leyes": int(d["ley"].nunique())}
    if detalle is not None:
        detalle = Path(detalle)
        fuente["detalle"] = (detalle.relative_to(REPO).as_posix()
                             if detalle.is_absolute() and REPO in detalle.parents else detalle.as_posix())
        fuente["detalle_sha256_16"] = _sha16(detalle)
    return {
        "formato": FORMATO, "generado": date.today().isoformat(),
        "generador": "evaluacion/baseline/src/censo_estadisticos.py", "motor_sha": _git_head(),
        "fuente": fuente,
        "variantes": cols, "alias": {"p": alias_p},
        "actas": {"columnas": orden, "filas": filas},
        "epsilon": eps,
    }


def escribir(est: dict, ruta: str | Path) -> Path:
    """Un renglón por acta: el diff de git sirve y el archivo se lee a ojo."""
    partes = []
    for k, v in est.items():
        if k == "actas":
            filas = ",\n".join(json.dumps(f, ensure_ascii=False, separators=(",", ":"))
                               for f in v["filas"])
            partes.append(f' "actas": {{"columnas": {json.dumps(v["columnas"])},\n"filas": [\n'
                          f'{filas}\n]}}')
        else:
            partes.append(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}")
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("{\n" + ",\n".join(partes) + "\n}\n", encoding="utf-8")
    return ruta


def ruta_estadisticos_de(detalle: str | Path) -> Path:
    """`censo_detalle_X.parquet` → `censo_estadisticos_X.json`, en la misma carpeta."""
    detalle = Path(detalle)
    return detalle.with_name(detalle.name.replace("censo_detalle_", "censo_estadisticos_")
                             .rsplit(".", 1)[0] + ".json")


def generar_y_escribir(detalle: str | Path, salida: str | Path | None = None,
                       variantes=VARIANTES_POR_DEFECTO) -> Path:
    detalle = Path(detalle)
    d = pd.read_parquet(detalle)
    est = generar(d, variantes, detalle)
    return escribir(est, salida or ruta_estadisticos_de(detalle))


# ────────────────────────────────────────── consumir ──────────────────────────────────────────

def cargar(ruta: str | Path | None = None) -> dict:
    ruta = Path(ruta) if ruta else REPO / ESTADISTICOS
    if not ruta.is_file():
        raise FileNotFoundError(
            f"falta {ruta}. Se regenera con `python evaluacion/baseline/src/"
            "censo_estadisticos.py` (necesita el detalle del censo, 43 min con "
            "`censo_detalle_paralelo.py`) o con `git checkout` si se borró.")
    est = json.loads(ruta.read_text(encoding="utf-8"))
    if est.get("formato") != FORMATO:
        raise ValueError(f"formato {est.get('formato')!r} != {FORMATO}: regenerar")
    return est


def variante(est: dict, nombre: str) -> str:
    """Resuelve el alias `p` y valida que la variante esté guardada."""
    v = est["alias"].get(nombre, nombre) if nombre == "p" else nombre
    if v not in est["variantes"]:
        raise KeyError(f"el JSON no guarda la variante {nombre!r}; guarda "
                       f"{sorted(est['variantes'])} (alias p → {est['alias'].get('p')}). "
                       "Para otra: regenerar con --variantes")
    return v


def tabla_actas(est: dict) -> pd.DataFrame:
    a = pd.DataFrame(est["actas"]["filas"], columns=est["actas"]["columnas"])
    a["fecha"] = pd.to_datetime(a["fecha"])
    return a


def sumas_por_ley(a: pd.DataFrame, v: str, mascara=None, v0: str | None = None):
    """(n, Σy, Σ(p−y)²) por ley — ordenadas como `np.unique` de los ids como texto — de las
    actas de `mascara`. Con `v0`, también (Σ(e1−e0), Σe0) para el ΔBrier pareado."""
    if mascara is not None:
        a = a[mascara]
    cols = ["n", "sy", f"se__{v}"] + ([f"se__{v0}"] if v0 else [])
    s = a.groupby("ley", sort=True)[cols].sum()
    if v0:
        return (s["n"].to_numpy(float), s["sy"].to_numpy(float), s[f"se__{v}"].to_numpy(float),
                (s[f"se__{v}"] - s[f"se__{v0}"]).to_numpy(float), s[f"se__{v0}"].to_numpy(float))
    return s["n"].to_numpy(float), s["sy"].to_numpy(float), s[f"se__{v}"].to_numpy(float)


def cortes(a: pd.DataFrame) -> dict:
    """Los cortes de `resumir`: global, por era y por cámara (máscaras sobre `a`)."""
    out = {"global": np.ones(len(a), bool)}
    for e in dict.fromkeys(a["era"]):
        out[f"era={e}"] = (a["era"] == e).to_numpy()
    for c in sorted(a["camara"].unique()):
        out[f"camara={c}"] = (a["camara"] == c).to_numpy()
    return out


def skill(est: dict, nombre: str = "estricta__general", corte: str = "global",
          a: pd.DataFrame | None = None, n_boot: int = 300, seed: int = 7) -> dict:
    """skill contra la tasa base del corte, con IC 95% re-muestreando leyes."""
    v = variante(est, nombre)
    a = tabla_actas(est) if a is None else a
    m = cortes(a)[corte]
    n, sy, se = sumas_por_ley(a, v, m)
    base = sy.sum() / n.sum()
    bb = base * (1 - base)
    return {"skill": round(float(1 - (se.sum() / n.sum()) / bb), 4) if bb > 0 else None,
            "skill_ic95_ley": skill_ic_desde_sumas(se, sy, n, n_boot, seed),
            "n_votos": int(n.sum()), "n_leyes": int(len(n))}


def dif_brier(est: dict, nombre1: str, nombre0: str, corte: str = "global",
              a: pd.DataFrame | None = None, n_boot: int = 300, seed: int = 7) -> dict:
    """ΔBrier pareado (variante 1 − variante 0), relativo, con IC re-muestreando leyes."""
    v1, v0 = variante(est, nombre1), variante(est, nombre0)
    a = tabla_actas(est) if a is None else a
    n, _sy, _se, d, b0 = sumas_por_ley(a, v1, cortes(a)[corte], v0)
    return dif_brier_ic_desde_sumas(d, b0, n, n_boot, seed)


def curvas_epsilon(est: dict, nombre: str, camara: str | None = None):
    """(grilla, Brier medio, log-loss medio, n) sobre la grilla de ε₀ — una cámara o todas."""
    v = variante(est, nombre)
    e = est["epsilon"]
    cams = [camara] if camara else sorted(e["variantes"][v])
    n = sum(e["n_votos"][c] for c in cams)
    b = np.sum([e["variantes"][v][c]["brier_suma"] for c in cams], axis=0) / n
    ll = np.sum([e["variantes"][v][c]["logloss_suma"] for c in cams], axis=0) / n
    return np.asarray(e["grilla"], float), b, ll, int(n)


def panel_actas(est: dict, nombre: str, camara: str | None = None,
                a: pd.DataFrame | None = None) -> pd.DataFrame:
    """Por acta: n, A = Σy, Σp y Σp² de la variante — lo que pide el estimador de τ."""
    v = variante(est, nombre)
    a = tabla_actas(est) if a is None else a
    if camara:
        a = a[a["camara"] == camara]
    out = a[["acta_id", "camara", "n", "sy", f"sp__{v}", f"sp2__{v}"]].rename(
        columns={"sy": "A", f"sp__{v}": "sp", f"sp2__{v}": "sp2"})
    return out.sort_values("acta_id").reset_index(drop=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--detalle", default=None, help=f"parquet del censo (default: {DETALLE})")
    ap.add_argument("--salida", default=None, help="default: censo_estadisticos_<fecha>.json al lado")
    ap.add_argument("--variantes", default=",".join(VARIANTES_POR_DEFECTO),
                    help="variantes p__<x> a guardar, separadas por coma")
    args = ap.parse_args(argv)
    detalle = Path(args.detalle) if args.detalle else REPO / DETALLE
    salida = generar_y_escribir(detalle, args.salida, tuple(args.variantes.split(",")))
    est = cargar(salida)
    print(f"-> {salida}  ({salida.stat().st_size / 1e6:.2f} MB, {len(est['actas']['filas'])} actas)")
    print("skill global:", skill(est, "estricta__general"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
