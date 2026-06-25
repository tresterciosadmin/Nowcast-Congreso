"""
legislar_data.py
================
Ingesta de los datos de "La Década Votada" (Andy Tow) -- los mismos que usa el
paquete R {legislAr} -- a una base de datos SQLite propia, en Python.

Fuente real de los datos (CSV crudos):
    https://github.com/PoliticaArgentina/data_warehouse/tree/master/legislAr/data_raw

Bases por cámara ('diputados' | 'senadores'):
    bloques-{camara}.csv      -> partidos/bloques        (id, nombre, color)
    diputados-{camara}.csv    -> legisladores            (id, nombre, provincia, color)
    votaciones-{camara}.csv   -> voto individual         (id_asunto, legis_id, bloque_id, voto)
    asuntos-{camara}.csv      -> proyectos votados        (id, ..., fecha=col5, ..., descripcion=col17)

Mapeo del voto (igual que en {legislAr}):
    0 -> AFIRMATIVO   1 -> NEGATIVO   2 -> ABSTENCION   3 -> AUSENTE   otro -> PRESIDENTE

Uso rápido:
    python legislar_data.py                 # baja ambas cámaras -> legislar.db
    python legislar_data.py --db mi.db
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

BASE_URL = (
    "https://raw.githubusercontent.com/PoliticaArgentina/"
    "data_warehouse/master/legislAr/data_raw"
)

CHAMBERS = ("diputados", "senadores")

VOTO_MAP = {0: "AFIRMATIVO", 1: "NEGATIVO", 2: "ABSTENCION", 3: "AUSENTE"}


def _url(base: str, chamber: str) -> str:
    return f"{BASE_URL}/{base}-{chamber}.csv"


def load_bloques(chamber: str) -> pd.DataFrame:
    df = pd.read_csv(_url("bloques", chamber), header=0,
                     names=["bloque_id", "nombre_bloque", "color_bloque"])
    df["camara"] = chamber
    return df


def load_legisladores(chamber: str) -> pd.DataFrame:
    df = pd.read_csv(_url("diputados", chamber), header=0,
                     usecols=[0, 1, 2, 3],
                     names=["legis_id", "nombre_legislador", "provincia", "color_bloque"])
    df["camara"] = chamber
    return df


def load_votaciones(chamber: str) -> pd.DataFrame:
    df = pd.read_csv(_url("votaciones", chamber), header=0,
                     usecols=[0, 1, 2, 3],
                     names=["asunto_id", "legis_id", "bloque_id", "voto_cod"])
    df["voto"] = df["voto_cod"].map(VOTO_MAP).fillna("PRESIDENTE")
    df["camara"] = chamber
    return df


def load_asuntos(chamber: str) -> pd.DataFrame:
    # asuntos tiene muchas columnas; fecha=col 5 (idx 4), descripcion=col 17 (idx 16)
    df = pd.read_csv(_url("asuntos", chamber), header=0,
                     usecols=[0, 4, 16],
                     names=["asunto_id", "fecha", "descripcion"])
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["camara"] = chamber
    return df


def build_database(db_path: str = "legislar.db") -> None:
    bloques, legisladores, votaciones, asuntos = [], [], [], []
    for ch in CHAMBERS:
        print(f"Descargando cámara: {ch} ...")
        bloques.append(load_bloques(ch))
        legisladores.append(load_legisladores(ch))
        votaciones.append(load_votaciones(ch))
        asuntos.append(load_asuntos(ch))

    dfs = {
        "bloques": pd.concat(bloques, ignore_index=True),
        "legisladores": pd.concat(legisladores, ignore_index=True),
        "votaciones": pd.concat(votaciones, ignore_index=True),
        "asuntos": pd.concat(asuntos, ignore_index=True),
    }

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        for name, df in dfs.items():
            df.to_sql(name, con, if_exists="replace", index=False)
            print(f"  -> tabla '{name}': {len(df):,} filas")
        # índices para acelerar los joins del nowcast
        cur = con.cursor()
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vot_asunto ON votaciones(asunto_id, camara)")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_vot_legis  ON votaciones(legis_id, camara)")
        con.commit()
    print(f"\nBase lista en: {db_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Ingesta La Década Votada -> SQLite")
    p.add_argument("--db", default="legislar.db", help="ruta de la base SQLite de salida")
    args = p.parse_args()
    build_database(args.db)
