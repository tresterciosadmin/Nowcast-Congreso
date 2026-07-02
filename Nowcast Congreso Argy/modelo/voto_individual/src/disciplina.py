"""modelo/voto_individual/src/disciplina.py
Índice de disciplina individual + dimensionamiento del set pivote (gate 1 de ADR-0003).

Para cada voto sustantivo (AFIRMATIVO/NEGATIVO) compara al legislador contra la
posición de su bloque en esa acta, calculada leave-one-out (la mayoría del RESTO
del bloque, para que el propio voto no defina la posición). Un "desvío" es votar
contra esa mayoría. Metodología alineada con evaluacion/baseline/baseline_canonico.py.

La unidad de análisis temporal es el PERÍODO PARLAMENTARIO (entre recambios del
10 de diciembre de años impares): cada recambio reconfigura los escaños y cambia
la disciplina, así que el comportamiento se mide por período además de global.

Salidas:
  - outputs/disciplina_individual.csv   (una fila por legislador: tasas global/disputadas/por período)
  - outputs/disciplina_por_anio.csv     (legislador x año, para análisis time-aware)
  - outputs/disciplina_por_periodo.csv  (legislador x período parlamentario x cámara)
  - outputs/set_pivote.json             (cuántos legisladores superan cada umbral de divergencia)

Uso:
  python modelo/voto_individual/src/disciplina.py
  CANON=/ruta/a/clean OUT=/ruta/salida MIN_VOTOS=50 python .../disciplina.py
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("disciplina")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SUST = ["AFIRMATIVO", "NEGATIVO"]
CONT = 0.10          # disputada: minoría >= 10% de los sustantivos del acta (igual que baseline)
MIN_BLOQUE = 5       # tamaño mínimo del resto-del-bloque en el acta para que exista "posición"
UMBRALES = [0.02, 0.05, 0.10, 0.15]  # umbrales de tasa de desvío para dimensionar el set pivote


def periodo_parlamentario(fecha: pd.Series, anio: pd.Series) -> pd.Series:
    """Período entre recambios legislativos (10 de diciembre de años impares).
    Ej.: 2023-12-10 → 2025-12-09 = "2023-2025". El comportamiento se evalúa por período
    porque cada recambio reconfigura los escaños. Sin fecha exacta se aproxima por año
    (un año par pertenece siempre al período que arrancó el impar anterior)."""
    f = pd.to_datetime(fecha, errors="coerce")
    ini = f.dt.year.where(f.dt.year % 2 == 1, f.dt.year - 1)          # año impar de referencia
    antes_recambio = (f.dt.year % 2 == 1) & (
        (f.dt.month < 12) | ((f.dt.month == 12) & (f.dt.day < 10))
    )
    ini = ini.where(~antes_recambio, ini - 2)                          # impar antes del 10-dic → período previo
    a = pd.to_numeric(anio, errors="coerce")
    ini_aprox = a.where(a % 2 == 1, a - 1)                             # fallback por año (aprox. en impares)
    ini = ini.fillna(ini_aprox)
    out = ini.astype("Int64").astype("string")
    return (out + "-" + (ini + 2).astype("Int64").astype("string")).where(ini.notna())


def cargar(src: Path) -> pd.DataFrame:
    """Carga votos resueltos + cámara del acta. Falla con mensaje claro si no está la base."""
    fv, fa = src / "votos_resuelto.parquet", src / "actas_canonico.parquet"
    for f in (fv, fa):
        if not f.exists():
            raise FileNotFoundError(
                f"No existe {f}. Reconstruí la base primero: python datos/canonica/src/run_pipeline.py"
            )
    v = pd.read_parquet(fv)
    a = pd.read_parquet(fa)[["acta_id", "camara", "fecha"]].rename(columns={"fecha": "fecha_acta"})
    v = v.merge(a, on="acta_id", how="left")
    v["fecha"] = v["fecha"].fillna(v["fecha_acta"])
    v["anio"] = pd.to_datetime(v["fecha"], errors="coerce").dt.year.astype("Int64")
    # manual_2026 no trae fecha en el Excel; el período de la fuente es 2026 (ver datos/manual_2026)
    v.loc[v["anio"].isna() & (v["fuente"] == "manual_2026"), "anio"] = 2026
    v = v[(v["bloque_norm"] != "SIN BLOQUE") & v["voto"].isin(SUST)].copy()
    if v.empty:
        raise ValueError("Base sin votos sustantivos con bloque resuelto; nada que medir.")
    v["periodo"] = periodo_parlamentario(v["fecha"], v["anio"])
    log.info("votos sustantivos con bloque: %d (%d actas)", len(v), v["acta_id"].nunique())
    return v


def marcar_desvios(v: pd.DataFrame) -> pd.DataFrame:
    """Marca cada voto como desvío (True/False) vs. la mayoría LOO de su bloque en el acta.
    Filtra votos sin posición de bloque medible (resto del bloque < MIN_BLOQUE o empate)."""
    cnt = (
        v.groupby(["acta_id", "bloque_norm", "voto"], observed=True).size()
        .unstack(fill_value=0).reindex(columns=SUST, fill_value=0)
    )
    d = v.merge(cnt, left_on=["acta_id", "bloque_norm"], right_index=True, how="left")
    # copy=True: pandas con Copy-on-Write puede devolver arrays de solo-lectura
    mat = d[SUST].to_numpy(dtype=float, copy=True)
    own = d["voto"].map({c: i for i, c in enumerate(SUST)}).to_numpy()
    mat[np.arange(len(d)), own] -= 1  # leave-one-out: saco mi propio voto
    resto = mat.sum(1)
    empate = mat[:, 0] == mat[:, 1]
    valido = (resto >= MIN_BLOQUE) & ~empate
    pred = np.array(SUST)[mat.argmax(1)]
    d = d.loc[valido, [c for c in d.columns if c not in SUST]].copy()
    d["desvio"] = pred[valido] != d["voto"].to_numpy()
    log.info(
        "votos con posición de bloque medible: %d (descartados %d por bloque chico/empate); desvíos: %d (%.2f%%)",
        len(d), int((~valido).sum()), int(d["desvio"].sum()), 100 * d["desvio"].mean(),
    )
    return d


def actas_disputadas(d: pd.DataFrame) -> set:
    pa = (
        d.groupby("acta_id")["voto"].value_counts().unstack(fill_value=0)
        .reindex(columns=SUST, fill_value=0)
    )
    tot, mino = pa.sum(axis=1), pa.min(axis=1)
    return set(((mino / tot).where(tot > 0, 0) >= CONT).loc[lambda s: s].index)


def indice_por_legislador(d: pd.DataFrame) -> pd.DataFrame:
    """Una fila por legislador: tasa de desvío global, en disputadas y en el último tramo."""
    disp = actas_disputadas(d)
    d = d.assign(disputada=d["acta_id"].isin(disp))

    def agg(sub: pd.DataFrame) -> pd.Series:
        anio_max = sub["anio"].max()
        reciente = sub[sub["anio"] >= (anio_max - 1)] if pd.notna(anio_max) else sub.iloc[0:0]
        sd = sub[sub["disputada"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "camaras": "+".join(sorted(sub["camara"].dropna().unique())),
            "bloques": "; ".join(sorted(sub["bloque_norm"].dropna().unique())[:4]),
            "anio_desde": sub["anio"].min(), "anio_hasta": anio_max,
            "n_votos": len(sub), "n_desvios": int(sub["desvio"].sum()),
            "tasa_desvio": round(sub["desvio"].mean(), 4),
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(sd["desvio"].mean(), 4) if len(sd) else np.nan,
            "n_reciente": len(reciente),
            "tasa_desvio_reciente": round(reciente["desvio"].mean(), 4) if len(reciente) else np.nan,
        })

    idx = d.groupby("legislador_id", observed=True).apply(agg, include_groups=False).reset_index()
    return idx.sort_values("tasa_desvio", ascending=False)


def por_anio(d: pd.DataFrame) -> pd.DataFrame:
    g = (
        d.dropna(subset=["anio"])
        .groupby(["legislador_id", "anio"], observed=True)
        .agg(nombre=("legislador_nombre", lambda s: s.mode().iat[0]),
             camara=("camara", "first"),
             n_votos=("desvio", "size"), n_desvios=("desvio", "sum"))
        .reset_index()
    )
    g["tasa_desvio"] = (g["n_desvios"] / g["n_votos"]).round(4)
    return g


def por_periodo(d: pd.DataFrame) -> pd.DataFrame:
    """Desvío por legislador x período parlamentario (la unidad de análisis correcta:
    cada recambio reconfigura los escaños y cambia la disciplina)."""
    disp = actas_disputadas(d)
    d = d.assign(disputada=d["acta_id"].isin(disp)).dropna(subset=["periodo"])

    def agg(sub: pd.DataFrame) -> pd.Series:
        sd = sub[sub["disputada"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "bloque": sub["bloque_norm"].mode().iat[0],
            "n_votos": len(sub), "n_desvios": int(sub["desvio"].sum()),
            "tasa_desvio": round(sub["desvio"].mean(), 4),
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(sd["desvio"].mean(), 4) if len(sd) else np.nan,
        })

    g = (d.groupby(["legislador_id", "periodo", "camara"], observed=True)
           .apply(agg, include_groups=False).reset_index())
    return g.sort_values(["legislador_id", "periodo"])


def dimensionar_set_pivote(idx: pd.DataFrame, min_votos: int) -> dict:
    """Gate 1: cuántos legisladores superan cada umbral de divergencia (con n suficiente)."""
    base = idx[idx["n_votos"] >= min_votos]
    res = {
        "min_votos": min_votos,
        "legisladores_medibles": int(len(base)),
        "tasa_desvio_mediana": round(float(base["tasa_desvio"].median()), 4),
        "tasa_desvio_p90": round(float(base["tasa_desvio"].quantile(0.90)), 4),
        "por_umbral": {},
    }
    for u in UMBRALES:
        sel = base[base["tasa_desvio"] >= u]
        res["por_umbral"][f">={int(u*100)}%"] = {
            "n_legisladores": int(len(sel)),
            "pct_de_medibles": round(100 * len(sel) / len(base), 1) if len(base) else 0.0,
        }
    disp = base.dropna(subset=["tasa_desvio_disputadas"])
    disp = disp[disp["n_disputadas"] >= max(10, min_votos // 5)]
    res["disputadas"] = {
        f">={int(u*100)}%": int((disp["tasa_desvio_disputadas"] >= u).sum()) for u in UMBRALES
    }
    return res


def main() -> None:
    here = Path(__file__).resolve()
    src = Path(os.environ.get("CANON", here.parents[3] / "datos" / "canonica" / "data" / "clean"))
    out = Path(os.environ.get("OUT", here.parents[1] / "outputs"))
    min_votos = int(os.environ.get("MIN_VOTOS", "50"))
    out.mkdir(parents=True, exist_ok=True)

    d = marcar_desvios(cargar(src))
    idx = indice_por_legislador(d)
    anual = por_anio(d)
    periodos = por_periodo(d)
    gate = dimensionar_set_pivote(idx, min_votos)
    gate["cobertura"] = {
        "n_votos_medidos": int(len(d)),
        "n_actas": int(d["acta_id"].nunique()),
        "anios": f"{int(d['anio'].min())}-{int(d['anio'].max())}" if d["anio"].notna().any() else "s/d",
        "fuentes": sorted(d["fuente"].unique().tolist()),
    }

    idx.to_csv(out / "disciplina_individual.csv", index=False, encoding="utf-8-sig")
    anual.to_csv(out / "disciplina_por_anio.csv", index=False, encoding="utf-8-sig")
    periodos.to_csv(out / "disciplina_por_periodo.csv", index=False, encoding="utf-8-sig")
    (out / "set_pivote.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False, indent=2))
    top = idx[idx["n_votos"] >= min_votos].head(15)
    print("\nTop díscolos (n_votos >= %d):" % min_votos)
    print(top[["nombre", "camaras", "anio_desde", "anio_hasta", "n_votos", "tasa_desvio",
               "tasa_desvio_disputadas"]].to_string(index=False))


if __name__ == "__main__":
    main()
