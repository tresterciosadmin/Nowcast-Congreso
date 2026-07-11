"""modelo/agregador_institucional/src/agregador.py
Motor de AGREGACIÓN INSTITUCIONAL — el recuento como DISTRIBUCIÓN.

Dada una votación (roster de legisladores con la línea esperada de su bloque y su
tasa de desvío individual), simula el resultado muchas veces y devuelve:
  - P(aprobación): fracción de simulaciones donde los afirmativos alcanzan el umbral
  - la distribución de afirmativos (media, desvío, banda 5-95%)
No entrega un número seco: entrega un rango con su incertidumbre (el "80% ± 9%").

MODELO (una jugada por legislador, coherente con el desvío v2 / ADR-0004):
  cada legislador tiene una LÍNEA de bloque en {AFIRMATIVO, NEGATIVO, NO_ACOMPANA}
  y una tasa de desvío d (de modelo/voto_individual). En cada simulación:
    - sigue la línea con probabilidad (1 - d)
    - se desvía con probabilidad d, repartida en partes iguales entre las otras dos
      conductas (parámetro `reparto_desvio`, editable).
  Se cuentan AFIRMATIVO y NEGATIVO (los emitidos); NO_ACOMPANA no suma a emitidos.

UMBRAL (misma regla que datos/export y modelo/voto_individual — MANTENER SINCRONIZADAS):
  SIMPLE            -> emitidos / 2
  ABSOLUTA          -> miembros // 2 + 1        (129 dip / 37 sen)
  DOS_TERCIOS       -> ceil(emitidos * 2/3)
  DOS_TERCIOS_CUERPO-> ceil(miembros * 2/3)
  TRES_CUARTOS      -> ceil(emitidos * 3/4)

SIMPLIFICACIÓN v1 (documentada): el quórum se modela de forma laxa (se asume reunido
si los presentes ≥ mitad + 1 de los miembros). El modelado fino de asistencia/quórum
es su propio módulo (variables/asistencia_quorum, pendiente); acá entra como un dato
del roster (quién se cuenta como presente).

Uso:
  # backtest sobre la canónica (valida que el motor reproduce la historia)
  python modelo/agregador_institucional/src/agregador.py backtest
  # backtest en MODO ASISTENCIA (escalón 1): dirección de bloque entre presentes +
  # presentismo histórico (variables/asistencia_quorum) — corrige el sesgo pesimista.
  python modelo/agregador_institucional/src/agregador.py backtest_asistencia
  CANON=/ruta/clean DISC=/ruta/outputs N_SIMS=400 python .../agregador.py backtest
  # nowcast de una sola acta/proyecto desde un JSON de escenario
  python modelo/agregador_institucional/src/agregador.py nowcast escenario.json
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("agregador")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# --- constantes compartidas (mantener sincronizadas con export/voto_individual) ---
MIEMBROS = {"diputados": 257, "senado": 72}
CONDUCTAS = ("AFIRMATIVO", "NEGATIVO", "NO_ACOMPANA")
SUST = ("AFIRMATIVO", "NEGATIVO")


def normalizar_mayoria(tipo) -> str:
    """SIMPLE | ABSOLUTA | DOS_TERCIOS | DOS_TERCIOS_CUERPO | TRES_CUARTOS.
    Sin dato -> SIMPLE (el caso abrumadoramente más común)."""
    s = ("" if tipo is None else str(tipo)).upper()
    if "TERCIO" in s:
        return "DOS_TERCIOS_CUERPO" if "CUERPO" in s else "DOS_TERCIOS"
    if "CUARTO" in s:
        return "TRES_CUARTOS"
    if s == "ABSOLUTA" or "CUERPO" in s or "MITAD MÁS UNO" in s or "MITAD MAS UNO" in s:
        return "ABSOLUTA"
    return "SIMPLE"


def umbral_aprobacion(tipo_norm: str, emitidos: float, camara: str) -> float:
    """Umbral de afirmativos para aprobar, según el tipo de mayoría."""
    miembros = MIEMBROS.get(camara, 257)
    if tipo_norm == "ABSOLUTA":
        return float(miembros // 2 + 1)
    if tipo_norm == "DOS_TERCIOS":
        return float(np.ceil(emitidos * 2 / 3))
    if tipo_norm == "DOS_TERCIOS_CUERPO":
        return float(np.ceil(miembros * 2 / 3))
    if tipo_norm == "TRES_CUARTOS":
        return float(np.ceil(emitidos * 3 / 4))
    # SIMPLE
    return emitidos / 2


def _prob_conductas(linea: str, desvio: float, reparto_desvio: float = 0.5) -> np.ndarray:
    """Vector [p(AFIRM), p(NEG), p(NO_ACOMPANA)] para un legislador dada su línea y
    su tasa de desvío. Se sigue la línea con (1-d); el desvío se reparte entre las
    otras dos conductas (por defecto mitad y mitad)."""
    d = float(np.clip(desvio if pd.notna(desvio) else 0.0, 0.0, 1.0))
    idx = {c: i for i, c in enumerate(CONDUCTAS)}
    p = np.zeros(3)
    li = idx.get(linea, idx["NO_ACOMPANA"])
    p[li] = 1.0 - d
    otros = [i for i in range(3) if i != li]
    p[otros[0]] += d * reparto_desvio
    p[otros[1]] += d * (1.0 - reparto_desvio)
    s = p.sum()
    return p / s if s > 0 else np.array([0.0, 0.0, 1.0])


def simular_votacion(
    lineas: np.ndarray,
    desvios: np.ndarray,
    tipo_mayoria: str,
    camara: str,
    n_sims: int = 400,
    reparto_desvio: float = 0.5,
    seed: int | None = 0,
    p_presente=None,
) -> dict:
    """Simula la votación n_sims veces a partir del roster (una línea y un desvío por
    legislador) y devuelve la distribución del resultado.

    lineas   : array de str en CONDUCTAS, la línea esperada de cada legislador.
    desvios  : array de float [0,1], la tasa de desvío individual de cada legislador.
    p_presente: array de float [0,1] o None. Si se pasa (modo asistencia), la línea
      es la DIRECCIÓN del bloque (AFIRMATIVO/NEGATIVO) y cada legislador la emite solo
      si está presente: se escala P(afirm) y P(neg) por p_presente y el resto va a
      NO_ACOMPANA (ausencia). Corrige el sesgo pesimista de contar ausentes como línea.
    Devuelve dict con p_aprobacion, afirm_medio, afirm_std, banda (p5,p50,p95), etc.
    """
    n = len(lineas)
    if n == 0:
        raise ValueError("roster vacío: no hay legisladores para simular")
    if len(desvios) != n:
        raise ValueError(f"lineas ({n}) y desvios ({len(desvios)}) no coinciden")
    tipo = normalizar_mayoria(tipo_mayoria)
    rng = np.random.default_rng(seed)

    # matriz de probabilidades por legislador (n x 3), muestreo categórico vectorizado
    probs = np.vstack([_prob_conductas(l, dv, reparto_desvio) for l, dv in zip(lineas, desvios)])
    if p_presente is not None:
        pp = np.clip(np.asarray(p_presente, dtype=float), 0.0, 1.0)
        if len(pp) != n:
            raise ValueError(f"p_presente ({len(pp)}) no coincide con roster ({n})")
        # solo emite si está presente: afirm/neg se escalan por pp; el resto = ausencia
        probs[:, 0] *= pp
        probs[:, 1] *= pp
        probs[:, 2] = 1.0 - probs[:, 0] - probs[:, 1]
    cum = np.cumsum(probs, axis=1)                       # n x 3
    u = rng.random((n_sims, n))                          # sims x n
    # conducta elegida por (sim, legislador): primer umbral acumulado superado
    elec = (u[:, :, None] < cum[None, :, :]).argmax(axis=2)  # sims x n -> {0,1,2}

    afirm = (elec == 0).sum(axis=1).astype(float)        # sims
    neg = (elec == 1).sum(axis=1).astype(float)          # sims
    no_ac = (elec == 2).sum(axis=1).astype(float)
    emitidos = afirm + neg
    presentes = afirm + neg  # v1: no_acompaña incluye ausentes; quórum se trata laxo abajo

    # umbral por simulación (depende de emitidos para SIMPLE/DOS_TERCIOS/TRES_CUARTOS)
    umbrales = np.array([umbral_aprobacion(tipo, e, camara) for e in emitidos])
    # quórum laxo v1: la sesión es válida si votó al menos la mitad+1 de los miembros
    quorum_min = MIEMBROS.get(camara, 257) // 2 + 1
    con_quorum = presentes >= min(quorum_min, n)  # si el roster es chico no lo forzamos
    aprob = (afirm >= umbrales) & con_quorum

    return {
        "n_roster": int(n),
        "tipo_mayoria": tipo,
        "camara": camara,
        "n_sims": int(n_sims),
        "p_aprobacion": float(aprob.mean()),
        "afirm_medio": float(afirm.mean()),
        "afirm_std": float(afirm.std()),
        "afirm_p5": float(np.percentile(afirm, 5)),
        "afirm_p50": float(np.percentile(afirm, 50)),
        "afirm_p95": float(np.percentile(afirm, 95)),
        "umbral_medio": float(np.mean(umbrales)),
        "emitidos_medio": float(emitidos.mean()),
    }


# --------------------------- BACKTEST sobre la canónica ---------------------------
def _linea_bloque_por_acta(votos: pd.DataFrame) -> pd.DataFrame:
    """Línea observada de cada bloque en cada acta = conducta con mayoría simple sobre
    TODOS sus escaños presentes (misma idea bottom-up que disciplina v2). Devuelve
    por (acta_id, bloque_norm) la conducta AFIRMATIVO/NEGATIVO/NO_ACOMPANA."""
    v = votos.copy()
    # mapear el voto crudo a las 3 conductas del agregador
    m = {"AFIRMATIVO": "AFIRMATIVO", "NEGATIVO": "NEGATIVO",
         "ABSTENCION": "NO_ACOMPANA", "AUSENTE": "NO_ACOMPANA"}
    v["conducta"] = v["voto"].map(m).fillna("NO_ACOMPANA")
    g = (v.groupby(["acta_id", "bloque_norm", "conducta"]).size()
           .reset_index(name="n"))
    # conducta mayoritaria por (acta, bloque)
    idx = g.groupby(["acta_id", "bloque_norm"])["n"].idxmax()
    lineas = g.loc[idx, ["acta_id", "bloque_norm", "conducta"]].rename(
        columns={"conducta": "linea"})
    return lineas


def _direccion_bloque_por_acta(votos: pd.DataFrame) -> pd.DataFrame:
    """DIRECCIÓN del bloque = mayoría AFIRMATIVO vs NEGATIVO SOLO entre los que emitieron
    (ignora ausentes y abstenciones). Es la postura del bloque desacoplada de cuántos
    asistieron; la asistencia la aporta el presentismo. Bloque sin votos sustantivos ->
    NO_ACOMPANA."""
    v = votos[votos["voto"].isin(["AFIRMATIVO", "NEGATIVO"])]
    if v.empty:
        return pd.DataFrame(columns=["acta_id", "bloque_norm", "linea"])
    g = v.groupby(["acta_id", "bloque_norm", "voto"]).size().reset_index(name="n")
    idx = g.groupby(["acta_id", "bloque_norm"])["n"].idxmax()
    return g.loc[idx, ["acta_id", "bloque_norm", "voto"]].rename(columns={"voto": "linea"})


def backtest(canon: Path, disc: Path, n_sims: int, max_actas: int | None,
             reparto_desvio: float = 0.5, seed: int = 0,
             usar_asistencia: bool = False, asist_dir: Path | None = None,
             ruido_asistencia: bool = True) -> dict:
    """Corre el agregador sobre las actas históricas (alimentándolo con la línea de
    bloque observada + el desvío individual medido) y mide qué tan bien predice el
    resultado real. Métricas: Brier, accuracy@0.5, calibración por deciles.

    usar_asistencia=True: modo escalón-1 de asistencia. La línea es la DIRECCIÓN del
    bloque entre presentes, y cada legislador emite con su presentismo histórico
    (variables/asistencia_quorum) — corrige el sesgo pesimista de contar ausentes."""
    votos = pd.read_parquet(canon / "votos_resuelto.parquet")
    actas = pd.read_parquet(canon / "actas_canonico.parquet")
    # desvío individual (si existe la salida de voto_individual; si no, d=0 para todos)
    dv_path = disc / "disciplina_individual.csv"
    if dv_path.exists():
        di = pd.read_csv(dv_path)
        desv_map = dict(zip(di["legislador_id"], di["tasa_desvio"].fillna(0.0)))
        log.info("desvío individual cargado para %d legisladores", len(desv_map))
    else:
        desv_map = {}
        log.warning("sin disciplina_individual.csv: se asume desvío 0 (motor 'ideal')")

    # presentismo por legislador (solo en modo asistencia)
    pres_map, pres_global = {}, 0.75
    if usar_asistencia:
        adir = asist_dir or (canon.parents[3] / "variables" / "asistencia_quorum" / "outputs")
        ppath = Path(adir) / "presentismo_legislador.csv"
        if not ppath.exists():
            raise FileNotFoundError(f"modo asistencia sin {ppath} (correr asistencia.py)")
        pr = pd.read_csv(ppath)
        pres_map = dict(zip(pr["legislador_id"], pr["p_present"]))
        pres_global = float(pr["p_present"].mean())
        log.info("presentismo cargado para %d legisladores (global %.3f)", len(pres_map), pres_global)

    # solo actas con resultado sustantivo (aprobada/rechazada) para poder evaluar
    actas = actas[actas["resultado"].isin(["AFIRMATIVO", "NEGATIVO"])].copy()
    actas["y_real"] = (actas["resultado"] == "AFIRMATIVO").astype(int)
    ids = list(actas["acta_id"])
    if max_actas:
        ids = ids[:max_actas]
    vsub = votos[votos["acta_id"].isin(ids)]
    fn_linea = _direccion_bloque_por_acta if usar_asistencia else _linea_bloque_por_acta
    lineas_all = fn_linea(vsub)
    lineas_by_acta = {k: g for k, g in lineas_all.groupby("acta_id")}
    votos_by_acta = {k: g for k, g in vsub.groupby("acta_id")}
    ainfo = actas.set_index("acta_id")

    filas = []
    for aid in ids:
        vg = votos_by_acta.get(aid)
        lg = lineas_by_acta.get(aid)
        if vg is None or lg is None or vg.empty:
            continue
        linea_de_bloque = dict(zip(lg["bloque_norm"], lg["linea"]))
        lineas = vg["bloque_norm"].map(linea_de_bloque).fillna("NO_ACOMPANA").to_numpy()
        desvios = vg["legislador_id"].map(desv_map).fillna(0.0).to_numpy(dtype=float)
        cam = str(ainfo.at[aid, "camara"])
        tipo = ainfo.at[aid, "tipo_mayoria"]
        pp = None
        if usar_asistencia and ruido_asistencia:
            pp = vg["legislador_id"].map(pres_map).fillna(pres_global).to_numpy(dtype=float)
        try:
            r = simular_votacion(lineas, desvios, tipo, cam, n_sims=n_sims,
                                 reparto_desvio=reparto_desvio, seed=seed, p_presente=pp)
        except ValueError as e:
            log.debug("acta %s salteada: %s", aid, e)
            continue
        filas.append({"acta_id": aid, "p_pred": r["p_aprobacion"],
                      "y_real": int(ainfo.at[aid, "y_real"]),
                      "afirm_medio": r["afirm_medio"], "camara": cam})

    if not filas:
        raise RuntimeError("el backtest no produjo filas: revisar rutas de datos")
    res = pd.DataFrame(filas)
    p, y = res["p_pred"].to_numpy(), res["y_real"].to_numpy()
    brier = float(np.mean((p - y) ** 2))
    acc = float(np.mean((p >= 0.5).astype(int) == y))
    base = float(y.mean())
    brier_base = float(np.mean((base - y) ** 2))
    # calibración por deciles de p
    res["bin"] = np.clip((p * 10).astype(int), 0, 9)
    calib = (res.groupby("bin").agg(p_medio=("p_pred", "mean"),
                                    y_medio=("y_real", "mean"),
                                    n=("y_real", "size")).reset_index())
    resumen = {
        "n_actas": int(len(res)),
        "brier": round(brier, 4),
        "brier_baseline_tasa_base": round(brier_base, 4),
        "skill_score": round(1 - brier / brier_base, 4) if brier_base > 0 else None,
        "accuracy_0.5": round(acc, 4),
        "tasa_base_aprobacion": round(base, 4),
        "n_sims": n_sims,
        "calibracion": calib.to_dict("records"),
    }
    return {"resumen": resumen, "detalle": res}


def main() -> None:
    modo = sys.argv[1] if len(sys.argv) > 1 else "backtest"
    here = Path(__file__).resolve()
    root = here.parents[3]
    canon = Path(os.environ.get("CANON", root / "datos" / "canonica" / "data" / "clean"))
    disc = Path(os.environ.get("DISC", root / "modelo" / "voto_individual" / "outputs"))
    out = Path(os.environ.get("OUT", here.parents[1] / "outputs"))
    out.mkdir(parents=True, exist_ok=True)
    n_sims = int(os.environ.get("N_SIMS", "400"))

    if modo in ("backtest", "backtest_asistencia"):
        asist = (modo == "backtest_asistencia") or os.environ.get("ASIST") == "1"
        sufijo = "_asistencia" if asist else ""
        max_actas = int(os.environ["MAX_ACTAS"]) if os.environ.get("MAX_ACTAS") else None
        ruido = os.environ.get("SIN_RUIDO") != "1"  # SIN_RUIDO=1 -> dirección entre presentes SIN bajar asistencia
        if asist and not ruido:
            sufijo = "_dir_presentes"
        r = backtest(canon, disc, n_sims=n_sims, max_actas=max_actas,
                     usar_asistencia=asist, ruido_asistencia=ruido)
        (out / f"backtest_agregador{sufijo}.json").write_text(
            json.dumps(r["resumen"], ensure_ascii=False, indent=2))
        r["detalle"].to_csv(out / f"backtest_detalle{sufijo}.csv", index=False, encoding="utf-8-sig")
        print(json.dumps(r["resumen"], ensure_ascii=False, indent=2))
    elif modo == "nowcast":
        if len(sys.argv) < 3:
            sys.exit("uso: agregador.py nowcast <escenario.json>")
        esc = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        lineas = np.array(esc["lineas"])
        desvios = np.array(esc.get("desvios", [0.0] * len(lineas)), dtype=float)
        r = simular_votacion(lineas, desvios, esc.get("tipo_mayoria", "SIMPLE"),
                             esc.get("camara", "diputados"), n_sims=n_sims)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        sys.exit(f"modo desconocido: {modo} (usar 'backtest' o 'nowcast')")


if __name__ == "__main__":
    main()
