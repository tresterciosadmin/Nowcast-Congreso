"""MEDICIÓN (no toca el repo): ¿prender el filtro por origen mejora el acierto
del voto contra los votos REALES de la era Milei?

Walk-forward, sin leakage: para cada acta era-Milei con origen conocido, se
proyecta la postura de cada bloque con la ventana ANTERIOR, en dos modos:
  - INCONDICIONAL (filtro apagado): _share_incond
  - CONDICIONADO por el origen del proyecto (filtro prendido): _share_afirm
Cada legislador que votó en esa acta recibe la P(afirmativo) de su bloque, y se
compara contra su voto REAL. Métrica: Brier y accuracy, global y partido por
lado del proyecto (GOBIERNO=reformas del oficialismo vs OPOSICION).

Reusa el contrato de variables/bloque (proyectar_postura) — no reimplementa.
Sólo LEE datos del repo; escribe el resumen en el scratch.
"""
from __future__ import annotations
import sys, os, logging
from pathlib import Path
import numpy as np, pandas as pd

MAX_ACTAS = int(os.environ.get("MAX_ACTAS", "0"))   # 0 = todas
SOLO_CAMARA = os.environ.get("CAMARA", "")           # "" = ambas

# REPO: por defecto se autodetecta subiendo hasta encontrar 'coordinacion/'.
# En PowerShell podés fijarlo:  $env:NOWCAST_REPO = "C:\ruta\Nowcast Congreso Argy"
def _hallar_repo():
    env = os.environ.get("NOWCAST_REPO")
    if env:
        return Path(env)
    p = Path(__file__).resolve()
    for cand in [p, *p.parents]:
        if (cand / "coordinacion").is_dir() and (cand / "variables").is_dir():
            return cand
    # fallback: sandbox
    return Path("/sessions/wizardly-friendly-hamilton/mnt/Nowcast Congreso Argy")
REPO = _hallar_repo()
print(f"REPO: {REPO}")
sys.path.insert(0, str(REPO / "variables" / "bloque" / "src"))
sys.path.insert(0, str(REPO / "variables" / "proyecto" / "src"))
logging.basicConfig(level=logging.WARNING)

from bloque import cargar as cargar_bloque, proyectar_postura, cargar_tema_por_acta

MILEI_DESDE = pd.Timestamp("2023-12-10")

def _dir_real(v):
    """Voto real -> 1 afirmativo / 0 negativo / None si no computa."""
    s = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
    s = s.upper()[:2]
    return 1 if s == "AF" else (0 if s == "NE" else None)

def brier(p, y):
    p = np.asarray(p, float); y = np.asarray(y, float)
    return float(np.mean((p - y) ** 2))

def acc(p, y):
    p = np.asarray(p, float); y = np.asarray(y, float)
    return float(np.mean((p >= 0.5).astype(int) == y))

def main():
    votos = cargar_bloque()
    votos["fecha"] = pd.to_datetime(votos["fecha"], errors="coerce")
    cond = cargar_tema_por_acta()          # tema + origen fusionados (DataFrame)
    # mapa acta -> origen_lado (sólo actas con lado GOBIERNO/OPOSICION)
    cdf = cond.copy()
    cdf["origen_lado"] = cdf["origen_lado"].astype("string")
    cdf["origen"] = cdf["origen"].astype("string")
    lado = dict(zip(cdf["acta_id"].astype(str), cdf["origen_lado"]))
    fino = dict(zip(cdf["acta_id"].astype(str), cdf["origen"]))   # EJECUTIVO/OFICIALISMO/OPOSICION

    milei = votos[votos["fecha"] >= MILEI_DESDE].copy()
    actas = (milei[["acta_id", "fecha", "camara"]]
             .drop_duplicates("acta_id"))
    actas["lado"] = actas["acta_id"].astype(str).map(lado)
    actas = actas[actas["lado"].isin(["GOBIERNO", "OPOSICION"])]
    if SOLO_CAMARA:
        actas = actas[actas["camara"].astype(str) == SOLO_CAMARA]
    if os.environ.get("LADO"):
        actas = actas[actas["lado"] == os.environ["LADO"]]
    if os.environ.get("FINO"):
        actas = actas[actas["acta_id"].astype(str).map(fino) == os.environ["FINO"]]
    if MAX_ACTAS:
        actas = actas.sort_values("fecha").iloc[-MAX_ACTAS:]   # las más recientes
    print(f"Actas era-Milei con lado conocido: {len(actas)} "
          f"(GOBIERNO {int((actas['lado']=='GOBIERNO').sum())} / "
          f"OPOSICION {int((actas['lado']=='OPOSICION').sum())})")

    filas = []   # (acta, lado, fino, p_lado, p_fino, p_unc, y)
    saltadas = 0
    for _, a in actas.iterrows():
        aid, fecha, cam, ld = str(a["acta_id"]), a["fecha"], str(a["camara"]), a["lado"]
        fn = fino.get(aid)
        try:
            proj_l = proyectar_postura(votos, fecha, cam, origen=ld, cond_por_acta=cond)
            proj_f = proyectar_postura(votos, fecha, cam, origen=fn, cond_por_acta=cond) \
                     if fn else proj_l
        except Exception:
            saltadas += 1
            continue
        p_lado = {d["bloque"]: d["_share_afirm"] for d in proj_l}
        p_fino = {d["bloque"]: d["_share_afirm"] for d in proj_f}
        punc   = {d["bloque"]: d["_share_incond"] for d in proj_l}
        va = milei[milei["acta_id"].astype(str) == aid]
        for _, r in va.iterrows():
            y = _dir_real(r["conducta"])
            if y is None:
                continue
            blo = r["bloque_linaje"]
            if blo not in p_lado:
                continue
            filas.append((aid, ld, str(fn), p_lado[blo], p_fino.get(blo, p_lado[blo]), punc[blo], y))
    df = pd.DataFrame(filas, columns=["acta_id", "lado", "fino", "p_lado", "p_fino", "p_unc", "y"])
    print(f"Votos-legislador evaluados: {len(df):,} | actas salteadas (sin historia): {saltadas}")

    def reporte(sub, nombre):
        if not len(sub):
            print(f"\n[{nombre}] sin datos"); return
        print(f"\n=== {nombre}  (n={len(sub):,} votos, {sub['acta_id'].nunique()} actas) ===")
        print(f"  Accuracy  APAGADO {acc(sub['p_unc'],sub['y']):.4f}  |  por LADO {acc(sub['p_lado'],sub['y']):.4f}  |  FINO (PE≠oficialista) {acc(sub['p_fino'],sub['y']):.4f}")
        print(f"  Brier     APAGADO {brier(sub['p_unc'],sub['y']):.4f}  |  por LADO {brier(sub['p_lado'],sub['y']):.4f}  |  FINO {brier(sub['p_fino'],sub['y']):.4f}")

    reporte(df, "TODAS las actas")
    reporte(df[df["fino"] == "EJECUTIVO"], "Proyectos del PODER EJECUTIVO (mensajes PE / JGM)")
    reporte(df[df["fino"] == "OFICIALISMO"], "Proyectos de LEGISLADORES OFICIALISTAS")
    reporte(df[df["lado"] == "OPOSICION"], "Proyectos de la OPOSICION")

if __name__ == "__main__":
    main()
