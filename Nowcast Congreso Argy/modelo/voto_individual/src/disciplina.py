"""modelo/voto_individual/src/disciplina.py
Índice de disciplina individual + set pivote — DESVÍO v2 (definición de Valle, ADR-0004).

MODELO (bottom-up): la línea del bloque EMERGE de sus miembros, no baja de afuera.
En cada votación, cada miembro tiene una de tres CONDUCTAS:
  AFIRMATIVO · NEGATIVO · NO_ACOMPANA (abstenerse o ausentarse — usar el escaño es una decisión).
La BAJADA DE LÍNEA del bloque = la conducta con mayoría simple sobre TODOS sus escaños
en esa acta (incluidos los ausentes). DESVÍO = tu conducta ≠ la línea (regla ESTRICTA:
abstenerse cuando la línea es rechazar también computa; votar cuando el bloque se
ausenta en masa, también).

Sin mayoría en el bloque (ej. 2-2):
  1) si el bloque pertenece a un espacio político real (linaje ≠ "OTRO / PROVINCIAL"),
     se desempata con la línea del ESPACIO entero en esa acta (metodo="linaje");
  2) si no hay espacio real o el espacio también empata: DESVÍO PARCIAL =
     1 − (fracción de escaños del bloque con tu misma conducta) (metodo="parcial").
Pendiente anotado: reclasificar los partidos de la bolsa OTRO/PROVINCIAL hacia linajes.

EXCLUSIONES (falso desvío estructural, decisión de Valle 2026-07-02): presidentes de la
Cámara de Diputados (no votan por costumbre), SUSPENDIDOS (anotados en el nombre por la
fuente) y placeholders. Las LICENCIAS no están en los datos: dependen de la herramienta
de licencias/suspensiones (PLAN — datos/licencias_suspensiones, a crear).

DISPUTADA: misma definición que datos/export (resultado a ±5% de los votos emitidos
respecto del umbral de la mayoría requerida). Mantener sincronizadas.

Salidas (outputs/):
  - disciplina_individual.csv    (una fila por legislador)
  - disciplina_por_periodo.csv   (legislador × período parlamentario × cámara)
  - disciplina_por_anio.csv      (legislador × año)
  - desvios_por_voto.parquet     (una fila por VOTO: conducta, línea, método, desvío —
                                  contrato para la columna `desvio` de datos/export)
  - set_pivote.json              (dimensionamiento del set pivote)

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

CONDUCTAS = ["AFIRMATIVO", "NEGATIVO", "NO_ACOMPANA"]
LINAJE_BOLSA = "OTRO / PROVINCIAL"   # no es un espacio político real: no sirve para desempatar
MARGEN_DISPUTADA = 0.05              # ±5% de los emitidos (igual que datos/export)
MIEMBROS = {"diputados": 257, "senado": 72}
UMBRALES = [0.02, 0.05, 0.10, 0.15]

# Presidentes de la Cámara de Diputados: por costumbre NO votan (solo desempatan), así
# que computarles "no acompaña" sería falso desvío. Se excluyen sus filas durante su
# presidencia (hallazgo de la validación v2: dominaban el top con 85-95% de "desvío").
# Lista curada — mantener al día en cada recambio. El Senado no lo necesita: lo preside
# el vicepresidente de la Nación, que no es senador.
PRESIDENCIAS_DIPUTADOS = [
    ("PASCUAL",    "1999-12-10", "2001-12-20"),
    ("CAMAÑO",     "2001-12-21", "2005-12-09"),   # Eduardo Camaño
    ("BALESTRINI", "2005-12-10", "2007-12-09"),
    ("FELLNER",    "2007-12-10", "2011-12-09"),
    ("DOMINGUEZ",  "2011-12-10", "2015-12-09"),   # Julián Domínguez
    ("MONZO",      "2015-12-10", "2019-12-09"),   # Emilio Monzó
    ("MASSA",      "2019-12-10", "2022-08-02"),   # Sergio Massa
    ("MOREAU",     "2022-08-02", "2023-12-09"),   # Cecilia Moreau
    ("MENEM",      "2023-12-10", None),           # Martín Menem
]


def _sin_acentos(s: pd.Series) -> pd.Series:
    return (s.astype(str).str.upper()
             .str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii"))


def excluir_no_medibles(v: pd.DataFrame) -> pd.DataFrame:
    """Saca (1) filas placeholder de las fuentes (bancas no incorporadas), (2) suspendidos
    (Art. 70 C.N., anotados en el nombre: no votar no es una decisión) y (3) al presidente
    de Diputados durante su presidencia. Las LICENCIAS quedan pendientes de la herramienta
    de licencias/suspensiones (ver PLAN)."""
    antes = len(v)
    nombre = _sin_acentos(v["legislador_nombre"])
    v = v[~nombre.str.contains("NO INCORPORADO", na=False)]
    nombre = _sin_acentos(v["legislador_nombre"])
    v = v[~nombre.str.contains("SUSPENDID", na=False)]
    f = pd.to_datetime(v["fecha"], errors="coerce")
    nombre = _sin_acentos(v["legislador_nombre"])
    fuera = pd.Series(False, index=v.index)
    for apellido, desde, hasta in PRESIDENCIAS_DIPUTADOS:
        m = (v["camara"] == "diputados") & nombre.str.contains(apellido, na=False)
        m &= f >= pd.Timestamp(desde)
        if hasta:
            m &= f <= pd.Timestamp(hasta)
        # solo si su conducta dominante en el período es NO votar (evita homónimos:
        # p.ej. otro MASSA que sí vota no debe excluirse)
        if m.any():
            for lid in v.loc[m, "legislador_id"].unique():
                mi = m & (v["legislador_id"] == lid)
                if (v.loc[mi, "conducta"] == "NO_ACOMPANA").mean() > 0.8:
                    fuera |= mi
    v = v[~fuera]
    log.info("excluidos no medibles: %d filas (placeholders + suspendidos + presidencias)", antes - len(v))
    return v


def periodo_parlamentario(fecha: pd.Series, anio: pd.Series) -> pd.Series:
    """Recambios del 10-dic de años impares (sincronizada con variables/legislador y datos/export)."""
    f = pd.to_datetime(fecha, errors="coerce")
    ini = f.dt.year.where(f.dt.year % 2 == 1, f.dt.year - 1)
    antes = (f.dt.year % 2 == 1) & ((f.dt.month < 12) | ((f.dt.month == 12) & (f.dt.day < 10)))
    ini = ini.where(~antes, ini - 2)
    a = pd.to_numeric(anio, errors="coerce")
    ini = ini.fillna(a.where(a % 2 == 1, a - 1))
    out = ini.astype("Int64").astype("string")
    return (out + "-" + (ini + 2).astype("Int64").astype("string")).where(ini.notna())


def normalizar_mayoria(tipo: pd.Series) -> pd.Series:
    """Sincronizada con datos/export/src/export_base.py."""
    t = tipo.fillna("").astype(str).str.upper()

    def clas(s: str) -> str:
        if "TERCIO" in s:
            return "DOS_TERCIOS_CUERPO" if "CUERPO" in s else "DOS_TERCIOS"
        if "CUARTO" in s:
            return "TRES_CUARTOS"
        if s == "ABSOLUTA" or "CUERPO" in s or "MITAD MÁS UNO" in s or "MITAD MAS UNO" in s:
            return "ABSOLUTA"
        return "SIMPLE"

    return t.map(clas).astype("string")


def actas_disputadas(actas: pd.DataFrame, v: pd.DataFrame) -> set:
    """Disputada = resultado a ±5% de los emitidos respecto del umbral (def. de Valle,
    sincronizada con datos/export)."""
    a = actas.copy()
    cnt = v.pivot_table(index="acta_id", columns="voto", aggfunc="size", fill_value=0)
    for col, nc in [("AFIRMATIVO", "n_afirmativos"), ("NEGATIVO", "n_negativos")]:
        calc = a["acta_id"].map(cnt[col]) if col in cnt.columns else np.nan
        a[nc] = pd.to_numeric(a.get(nc), errors="coerce").fillna(calc)
    afirm, neg = a["n_afirmativos"], a["n_negativos"]
    emitidos = afirm + neg
    miembros = a["camara"].map(MIEMBROS)
    tipo = normalizar_mayoria(a.get("tipo_mayoria", pd.Series(index=a.index, dtype=object)))
    umbral = pd.Series(np.nan, index=a.index, dtype=float)
    umbral[tipo == "SIMPLE"] = emitidos[tipo == "SIMPLE"] / 2
    umbral[tipo == "ABSOLUTA"] = (miembros[tipo == "ABSOLUTA"] // 2 + 1).astype(float)
    umbral[tipo == "DOS_TERCIOS"] = np.ceil(emitidos[tipo == "DOS_TERCIOS"] * 2 / 3)
    umbral[tipo == "DOS_TERCIOS_CUERPO"] = np.ceil(miembros[tipo == "DOS_TERCIOS_CUERPO"] * 2 / 3)
    umbral[tipo == "TRES_CUARTOS"] = np.ceil(emitidos[tipo == "TRES_CUARTOS"] * 3 / 4)
    disp = (afirm - umbral).abs() <= MARGEN_DISPUTADA * emitidos
    return set(a.loc[disp.fillna(False), "acta_id"])


def cargar(src: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    fv, fa = src / "votos_resuelto.parquet", src / "actas_canonico.parquet"
    for f in (fv, fa):
        if not f.exists():
            raise FileNotFoundError(
                f"No existe {f}. Reconstruí la base primero: python datos/canonica/src/run_pipeline.py"
            )
    v = pd.read_parquet(fv)
    actas = pd.read_parquet(fa)
    a = actas[["acta_id", "camara", "fecha"]].rename(columns={"fecha": "fecha_acta"})
    v = v.merge(a, on="acta_id", how="left")
    v["fecha"] = v["fecha"].fillna(v["fecha_acta"])
    v["anio"] = pd.to_datetime(v["fecha"], errors="coerce").dt.year.astype("Int64")
    v.loc[v["anio"].isna() & (v["fuente"] == "manual_2026"), "anio"] = 2026
    v["periodo"] = periodo_parlamentario(v["fecha"], v["anio"])
    # v2: TODOS los votos cuentan (la ausencia/abstención es una conducta), solo se
    # excluye lo que no tiene bloque asignable y los no-medibles estructurales.
    v = v[v["bloque_norm"].notna() & (v["bloque_norm"] != "SIN BLOQUE")].copy()
    v["conducta"] = np.where(v["voto"].isin(["AFIRMATIVO", "NEGATIVO"]), v["voto"], "NO_ACOMPANA")
    v = excluir_no_medibles(v)
    if v.empty:
        raise ValueError("Base sin votos con bloque resuelto; nada que medir.")
    log.info("votos con bloque (todas las conductas): %d (%d actas)", len(v), v["acta_id"].nunique())
    return v, actas


def _linea(df: pd.DataFrame, nivel: str) -> pd.DataFrame:
    """Conducta con >50% de los escaños del nivel (bloque o linaje) en cada acta."""
    cnt = (df.groupby(["acta_id", nivel, "conducta"], observed=True).size()
             .unstack(fill_value=0).reindex(columns=CONDUCTAS, fill_value=0))
    total = cnt.sum(axis=1)
    top = cnt.max(axis=1)
    linea = cnt.idxmax(axis=1).where(top * 2 > total)  # mayoría simple estricta, si no NA
    out = linea.rename("linea").reset_index()
    out["n_total"] = total.values
    return out


def marcar_desvios(v: pd.DataFrame) -> pd.DataFrame:
    """Desvío v2 por voto: línea del bloque → desempate por linaje → desvío parcial."""
    lb = _linea(v, "bloque_norm").rename(columns={"linea": "linea_bloque", "n_total": "n_bloque"})
    d = v.merge(lb, on=["acta_id", "bloque_norm"], how="left")

    # cuántos pares del bloque comparten mi conducta (para el desvío parcial)
    mismos = (v.groupby(["acta_id", "bloque_norm", "conducta"], observed=True).size()
                .rename("n_misma_conducta").reset_index())
    d = d.merge(mismos, on=["acta_id", "bloque_norm", "conducta"], how="left")

    # línea del espacio político (solo linajes reales)
    vreal = v[v["bloque_linaje"].notna() & (v["bloque_linaje"] != LINAJE_BOLSA)]
    ll = _linea(vreal, "bloque_linaje").rename(columns={"linea": "linea_linaje"})[
        ["acta_id", "bloque_linaje", "linea_linaje"]]
    d = d.merge(ll, on=["acta_id", "bloque_linaje"], how="left")

    con_linea = d["linea_bloque"].notna()
    linaje_ok = ~con_linea & d["linea_linaje"].notna() & (d["bloque_linaje"] != LINAJE_BOLSA)
    parcial = ~con_linea & ~linaje_ok

    d["metodo"] = np.select([con_linea, linaje_ok, parcial], ["bloque", "linaje", "parcial"], default="parcial")
    d["desvio"] = np.select(
        [con_linea, linaje_ok, parcial],
        [(d["conducta"] != d["linea_bloque"]).astype(float),
         (d["conducta"] != d["linea_linaje"]).astype(float),
         1.0 - d["n_misma_conducta"] / d["n_bloque"]],
    )
    d["linea"] = d["linea_bloque"].fillna(d["linea_linaje"].where(linaje_ok))
    log.info("desvíos v2 — método: %s | desvío medio: %.4f",
             d["metodo"].value_counts().to_dict(), d["desvio"].mean())
    return d


def indice_por_legislador(d: pd.DataFrame, disputadas: set) -> pd.DataFrame:
    d = d.assign(disputada=d["acta_id"].isin(disputadas))

    def agg(sub: pd.DataFrame) -> pd.Series:
        anio_max = sub["anio"].max()
        reciente = sub[sub["anio"] >= (anio_max - 1)] if pd.notna(anio_max) else sub.iloc[0:0]
        sd = sub[sub["disputada"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "camaras": "+".join(sorted(sub["camara"].dropna().unique())),
            "bloques": "; ".join(sorted(sub["bloque_norm"].dropna().unique())[:4]),
            "anio_desde": sub["anio"].min(), "anio_hasta": anio_max,
            "n_votos": len(sub), "n_desvios": round(float(sub["desvio"].sum()), 1),
            "tasa_desvio": round(float(sub["desvio"].mean()), 4),
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(float(sd["desvio"].mean()), 4) if len(sd) else np.nan,
            "n_reciente": len(reciente),
            "tasa_desvio_reciente": round(float(reciente["desvio"].mean()), 4) if len(reciente) else np.nan,
            "pct_metodo_linaje": round(float((sub["metodo"] == "linaje").mean()), 4),
            "pct_metodo_parcial": round(float((sub["metodo"] == "parcial").mean()), 4),
            "tam_bloque_mediano": float(sub["n_bloque"].median()),
        })

    idx = d.groupby("legislador_id", observed=True).apply(agg, include_groups=False).reset_index()
    return idx.sort_values("tasa_desvio", ascending=False)


def por_anio(d: pd.DataFrame) -> pd.DataFrame:
    g = (d.dropna(subset=["anio"])
           .groupby(["legislador_id", "anio"], observed=True)
           .agg(nombre=("legislador_nombre", lambda s: s.mode().iat[0]),
                camara=("camara", "first"),
                n_votos=("desvio", "size"), n_desvios=("desvio", "sum"))
           .reset_index())
    g["n_desvios"] = g["n_desvios"].round(1)
    g["tasa_desvio"] = (g["n_desvios"] / g["n_votos"]).round(4)
    return g


def por_periodo(d: pd.DataFrame, disputadas: set) -> pd.DataFrame:
    d = d.assign(disputada=d["acta_id"].isin(disputadas)).dropna(subset=["periodo"])

    def agg(sub: pd.DataFrame) -> pd.Series:
        sd = sub[sub["disputada"]]
        return pd.Series({
            "nombre": sub["legislador_nombre"].mode().iat[0],
            "bloque": sub["bloque_norm"].mode().iat[0],
            "n_votos": len(sub), "n_desvios": round(float(sub["desvio"].sum()), 1),
            "tasa_desvio": round(float(sub["desvio"].mean()), 4),
            "n_disputadas": len(sd),
            "tasa_desvio_disputadas": round(float(sd["desvio"].mean()), 4) if len(sd) else np.nan,
        })

    g = (d.groupby(["legislador_id", "periodo", "camara"], observed=True)
           .apply(agg, include_groups=False).reset_index())
    return g.sort_values(["legislador_id", "periodo"])


def dimensionar_set_pivote(idx: pd.DataFrame, min_votos: int) -> dict:
    base = idx[idx["n_votos"] >= min_votos]
    res = {
        "definicion": "desvío v2 (ADR-0004): conducta vs línea del bloque (mayoría de TODOS los escaños); "
                      "estricta con abstenciones/ausencias; desempate por linaje; parcial en OTRO/PROVINCIAL; "
                      "excluidos presidentes de Diputados y suspendidos",
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
    disp = disp[disp["n_disputadas"] >= 5]
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

    v, actas = cargar(src)
    d = marcar_desvios(v)
    disputadas = actas_disputadas(actas, v)
    log.info("actas disputadas (±5%% emitidos): %d", len(disputadas))

    idx = indice_por_legislador(d, disputadas)
    anual = por_anio(d)
    periodos = por_periodo(d, disputadas)
    gate = dimensionar_set_pivote(idx, min_votos)
    gate["cobertura"] = {
        "n_votos_medidos": int(len(d)),
        "n_actas": int(d["acta_id"].nunique()),
        "anios": f"{int(d['anio'].min())}-{int(d['anio'].max())}" if d["anio"].notna().any() else "s/d",
        "fuentes": sorted(d["fuente"].unique().tolist()),
        "metodo": {k: int(n) for k, n in d["metodo"].value_counts().items()},
    }

    idx.to_csv(out / "disciplina_individual.csv", index=False, encoding="utf-8-sig")
    anual.to_csv(out / "disciplina_por_anio.csv", index=False, encoding="utf-8-sig")
    periodos.to_csv(out / "disciplina_por_periodo.csv", index=False, encoding="utf-8-sig")
    d[["acta_id", "legislador_id", "conducta", "linea", "metodo", "desvio"]].to_parquet(
        out / "desvios_por_voto.parquet", index=False)
    (out / "set_pivote.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(gate, ensure_ascii=False, indent=2))
    top = idx[idx["n_votos"] >= min_votos].head(15)
    print("\nTop díscolos v2 (n_votos >= %d):" % min_votos)
    print(top[["nombre", "camaras", "anio_desde", "anio_hasta", "n_votos", "tasa_desvio",
               "tasa_desvio_disputadas"]].to_string(index=False))


if __name__ == "__main__":
    main()
