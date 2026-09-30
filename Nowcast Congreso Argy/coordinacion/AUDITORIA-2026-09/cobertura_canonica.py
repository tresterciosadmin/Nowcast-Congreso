# -*- coding: utf-8 -*-
"""Cobertura de la canónica por año y cámara (auditoría 2026-09, ítem A4 / recomendación d4-a).

QUÉ MIDE. Cuántas actas y cuántos votos individuales tiene la base canónica en cada año y
cámara, si el voto individual está completo DENTRO de cada acta, y cuántas de esas actas entran
al censo del skill. Es un inventario: NO dice si "faltan" actas (no hay un número oficial de
sesiones contra el cual comparar); dice dónde la base es anómalamente chica.

CRITERIO, fijado antes de calcular (2026-09-30):
  1. actas de la canónica; 2. actas con votos individuales; 3. cobertura individual = votos
  emitidos (afirmativo + negativo + abstención) ÷ los que el propio acta declara
  (`n_afirmativos + n_negativos + n_abstenciones`); 4. actas que entran al censo del 28-09;
  5. % de votos del censo sin ley identificable.
  Un año-cámara es SOSPECHOSO si tiene menos de la mitad de las actas de la mediana de sus ±2
  años vecinos, o si su cobertura individual es < 90%.

DOS CORRECCIONES QUE SE HICIERON MIENTRAS SE MEDÍA (quedan escritas porque la primera corrida
las mostró con números absurdos, que es la señal que este repo manda mirar):
  a. la cobertura individual daba > 1 (hasta 1,71) porque el denominador incluía actas SIN
     conteo declarado (`n_*` nulos); ahora sólo entran las actas con conteo declarado > 0;
  b. el % de votos sin ley daba 0 en todos los años porque el censo marca "sin ley" con el id del
     acta (`acta:...`), no con un nulo.

    python coordinacion/AUDITORIA-2026-09/cobertura_canonica.py
Salida: coordinacion/AUDITORIA-2026-09/resultados/cobertura_canonica.json
(JSON y no CSV: `*.csv` y `*.parquet` están ignorados por git y el resultado tiene que viajar)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())
sys.path.insert(0, str(RAIZ))
from rutas import BASELINE_OUT, CANONICA_ACTAS, CANONICA_VOTOS_RESUELTO  # noqa: E402

CENSO = BASELINE_OUT / "censo_detalle_2026-09-28.parquet"
SALIDA = Path(__file__).resolve().parent / "resultados" / "cobertura_canonica.json"
EMITIDOS = ("AFIRMATIVO", "NEGATIVO", "ABSTENCION")


def medir() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(tabla por año y cámara, actas con su motivo de exclusión del censo)"""
    a = pd.read_parquet(CANONICA_ACTAS)
    v = pd.read_parquet(CANONICA_VOTOS_RESUELTO, columns=["acta_id", "voto"])
    censo = pd.read_parquet(CENSO, columns=["acta_id", "ley"])

    a["anio"] = pd.to_datetime(a["fecha"], errors="coerce").dt.year
    v["emitido"] = v["voto"].isin(EMITIDOS)
    v["afneg"] = v["voto"].isin(("AFIRMATIVO", "NEGATIVO"))
    por_acta = v.groupby("acta_id").agg(n_filas=("voto", "size"), n_emitidos=("emitido", "sum"),
                                        n_afneg=("afneg", "sum"))
    a = a.merge(por_acta, on="acta_id", how="left")
    for c in ("n_filas", "n_emitidos", "n_afneg"):
        a[c] = a[c].fillna(0)
    a["declarados"] = (a["n_afirmativos"].fillna(0) + a["n_negativos"].fillna(0)
                       + a["n_abstenciones"].fillna(0)).astype(float)
    a["en_censo"] = a["acta_id"].isin(set(censo["acta_id"]))

    censo["sin_ley"] = censo["ley"].isna() | censo["ley"].astype(str).str.startswith("acta:")
    sl = censo.groupby("acta_id")["sin_ley"].agg(["size", "sum"])
    a = a.merge(sl, left_on="acta_id", right_index=True, how="left")

    filas = []
    for (anio, cam), g in a.groupby(["anio", "camara"]):
        con_votos = g[g["n_filas"] > 0]
        con_decl = con_votos[con_votos["declarados"] > 0]
        decl = con_decl["declarados"].sum()
        filas.append({
            "anio": int(anio), "camara": cam, "actas": len(g), "actas_con_votos": len(con_votos),
            "votos_individuales": int(g["n_filas"].sum()),
            "actas_con_conteo_declarado": len(con_decl),
            "cobertura_individual": (con_decl["n_emitidos"].sum() / decl) if decl else np.nan,
            "filas_por_acta": (g["n_filas"].sum() / len(con_votos)) if len(con_votos) else np.nan,
            "actas_en_censo": int(g["en_censo"].sum()),
            "pct_votos_sin_ley": (g["sum"].sum() / g["size"].sum()) if g["size"].sum() else np.nan})
    t = pd.DataFrame(filas)

    def _mediana_vecinos(r):
        m = t[(t.camara == r.camara) & (t.anio != r.anio) & ((t.anio - r.anio).abs() <= 2)]["actas"]
        return m.median() if len(m) else np.nan

    t["mediana_vecinos"] = t.apply(_mediana_vecinos, axis=1)
    t["flag_pocas_actas"] = t["actas"] < 0.5 * t["mediana_vecinos"]
    t["flag_cobertura"] = t["cobertura_individual"] < 0.90
    t["sospechoso"] = t["flag_pocas_actas"] | t["flag_cobertura"]

    a["motivo_fuera_del_censo"] = np.where(
        a["en_censo"], "", np.where(a["anio"].isna(), "sin fecha valida",
        np.where(a["n_filas"] == 0, "sin votos individuales",
        np.where(a["n_afneg"] == 0, "solo abstenciones o ausentes", "con afirmativos/negativos: motivo no auditado"))))
    return t, a


def main() -> int:
    t, a = medir()
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    t.round(4).to_json(SALIDA, orient="records", indent=1, force_ascii=False)
    pd.set_option("display.width", 200)
    print(f"canonica: {len(a)} actas | en el censo: {int(a['en_censo'].sum())} | sin fecha valida: {int(a['anio'].isna().sum())}")
    print("fuera del censo:", int((~a["en_censo"]).sum()))
    print(a.loc[~a["en_censo"], "motivo_fuera_del_censo"].value_counts().to_string())
    print("\nSOSPECHOSOS (regla del criterio):")
    print(t[t["sospechoso"]][["anio", "camara", "actas", "mediana_vecinos", "cobertura_individual"]]
          .round(3).to_string(index=False))
    d = t[(t.camara == "diputados") & t.anio.between(2020, 2023)]
    print(f"\nDiputados 2020-2023: {int(d['actas'].sum())} actas, {int(d['votos_individuales'].sum())} votos individuales")
    print(f"-> {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
