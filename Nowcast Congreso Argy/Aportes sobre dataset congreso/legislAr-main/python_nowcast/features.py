"""
features.py
===========
Construye la tabla analítica (un registro por legislador-votación) a partir de la
base SQLite generada por `legislar_data.py`, y deriva variables útiles para un
modelo de nowcast de resultados legislativos.

La idea: cada fila es "cómo votó el legislador X en el proyecto Y", enriquecida
con bloque, provincia y fecha. Sobre esa base se calculan:

  - disciplina_bloque : % de veces que el legislador vota igual que la mayoría
                        de su bloque (señal histórica de lealtad partidaria).
  - tasa_afirmativa   : propensión histórica del legislador a votar AFIRMATIVO.
  - tasa_ausencia     : propensión histórica a estar AUSENTE.

Estas features (calculadas SOLO con votaciones anteriores a la fecha del asunto,
para evitar fuga de información) son el insumo típico de un nowcast: dado el
conjunto de legisladores presentes y su comportamiento pasado, estimar la
probabilidad de aprobación de un proyecto.

Uso:
    python features.py --db legislar.db --out features.parquet
"""
from __future__ import annotations

import argparse
import sqlite3

import pandas as pd


def load_long_table(db_path: str) -> pd.DataFrame:
    """Tabla larga: legislador-votación con bloque, provincia y fecha."""
    q = """
    SELECT v.camara, v.asunto_id, v.legis_id, v.bloque_id, v.voto,
           b.nombre_bloque, l.nombre_legislador, l.provincia,
           a.fecha, a.anio, a.mes, a.descripcion
    FROM votaciones v
    LEFT JOIN bloques      b ON b.bloque_id = v.bloque_id AND b.camara = v.camara
    LEFT JOIN legisladores l ON l.legis_id  = v.legis_id  AND l.camara = v.camara
    LEFT JOIN asuntos      a ON a.asunto_id = v.asunto_id AND a.camara = v.camara
    """
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql_query(q, con, parse_dates=["fecha"])
    return df


def add_result_per_bill(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega el resultado agregado de cada votación (target del modelo)."""
    grp = df.groupby(["camara", "asunto_id", "voto"]).size().unstack(fill_value=0)
    for col in ["AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE"]:
        if col not in grp:
            grp[col] = 0
    grp["presentes"] = grp["AFIRMATIVO"] + grp["NEGATIVO"] + grp["ABSTENCION"]
    # aprobado = mayoría simple de los presentes (heurística; ajustar por quórum/tipo de ley)
    grp["aprobado"] = (grp["AFIRMATIVO"] > grp["NEGATIVO"]).astype(int)
    res = grp[["AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE", "presentes", "aprobado"]]
    res = res.rename(columns=str.lower).reset_index()
    return df.merge(res, on=["camara", "asunto_id"], how="left")


def add_legislator_history(df: pd.DataFrame) -> pd.DataFrame:
    """Tasas históricas por legislador, expandidas en el tiempo (sin fuga futura)."""
    df = df.sort_values("fecha").copy()
    df["es_afirm"] = (df["voto"] == "AFIRMATIVO").astype(int)
    df["es_ausente"] = (df["voto"] == "AUSENTE").astype(int)

    g = df.groupby(["camara", "legis_id"], group_keys=False)
    # expanding().mean() usa solo el pasado; shift(1) excluye la fila actual
    df["tasa_afirmativa"] = g["es_afirm"].apply(lambda s: s.shift(1).expanding().mean())
    df["tasa_ausencia"] = g["es_ausente"].apply(lambda s: s.shift(1).expanding().mean())
    return df


def add_party_discipline(df: pd.DataFrame) -> pd.DataFrame:
    """Disciplina: ¿votó igual que la mayoría de su bloque en ese asunto?"""
    voto_mayoria = (
        df[df["voto"].isin(["AFIRMATIVO", "NEGATIVO", "ABSTENCION"])]
        .groupby(["camara", "asunto_id", "bloque_id"])["voto"]
        .agg(lambda s: s.mode().iat[0] if not s.mode().empty else None)
        .rename("voto_mayoria_bloque")
        .reset_index()
    )
    df = df.merge(voto_mayoria, on=["camara", "asunto_id", "bloque_id"], how="left")
    df["sigue_bloque"] = (df["voto"] == df["voto_mayoria_bloque"]).astype(int)
    g = df.sort_values("fecha").groupby(["camara", "legis_id"], group_keys=False)
    df["disciplina_bloque"] = g["sigue_bloque"].apply(lambda s: s.shift(1).expanding().mean())
    return df


def build_features(db_path: str) -> pd.DataFrame:
    df = load_long_table(db_path)
    df = add_result_per_bill(df)
    df = add_legislator_history(df)
    df = add_party_discipline(df)
    return df


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Construir features para el nowcast")
    p.add_argument("--db", default="legislar.db")
    p.add_argument("--out", default="features.parquet")
    args = p.parse_args()

    feats = build_features(args.db)
    if args.out.endswith(".parquet"):
        feats.to_parquet(args.out, index=False)
    else:
        feats.to_csv(args.out, index=False)
    print(f"Features: {len(feats):,} filas -> {args.out}")
    print(feats[["camara", "asunto_id", "nombre_legislador", "voto",
                 "disciplina_bloque", "tasa_afirmativa", "aprobado"]].head(10).to_string())
