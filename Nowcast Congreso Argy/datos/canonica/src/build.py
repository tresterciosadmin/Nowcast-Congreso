"""datos/canonica/src/build.py
Une las fuentes canonicas disponibles en la base canonica unica del proyecto.
Deduplica solapamientos (precedencia: fuente oficial > agregador > semilla),
valida contra docs/schemas y escribe la base.

Uso: SOURCES=/dir CLEAN=/out SCHEMAS=/dir python build.py
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

import pandas as pd
try:
    from jsonschema import Draft202012Validator as _Validator
except ImportError:  # entornos con jsonschema viejo
    from jsonschema import Draft7Validator as _Validator

# Precedencia de fuentes para deduplicar periodos solapados (mayor = gana).
PRECEDENCIA = {"decada_votada": 1, "argentinadatos": 2, "senado": 2, "ckan_diputados": 3, "manual_2026": 4}
VOTOS_OK = {"AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE"}

def _load(sources: Path, kind: str) -> pd.DataFrame:
    files = sorted(sources.glob(f"*_{kind}.parquet"))
    if not files:
        print(f"[warn] sin fuentes *_{kind}.parquet en {sources}")
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    print(f"  {kind}: {len(df)} filas desde {[f.name for f in files]}")
    return df

def _checks(df: pd.DataFrame, required: list[str], name: str) -> None:
    miss = [c for c in required if c not in df.columns]
    assert not miss, f"{name}: faltan columnas {miss}"
    for c in required:
        nn = df[c].isna().sum()
        assert nn == 0, f"{name}: {nn} nulos en columna requerida '{c}'"
    assert df["acta_id"].str.match(r"^[a-z0-9_]+:.+").all(), f"{name}: acta_id con formato inválido"

def _sample_jsonschema(df: pd.DataFrame, schema: dict, n: int = 500) -> None:
    v = _Validator(schema)
    s = df.sample(min(n, len(df)), random_state=0).where(pd.notna(df), None)
    errs = 0
    for rec in s.to_dict("records"):
        rec = {k: (int(x) if isinstance(x, bool) is False and hasattr(x, "item") else x) for k, x in rec.items()}
        rec = {k: (None if (isinstance(x, float) and pd.isna(x)) else x) for k, x in rec.items()}
        for _ in v.iter_errors(rec):
            errs += 1; break
    assert errs == 0, f"validación json-schema falló en {errs} filas de muestra"

def main() -> None:
    sources = Path(os.environ.get("SOURCES", "."))
    clean = Path(os.environ.get("CLEAN", Path(__file__).resolve().parents[1] / "data" / "clean"))
    schemas = Path(os.environ.get("SCHEMAS", "schemas"))
    clean.mkdir(parents=True, exist_ok=True)

    actas, votos = _load(sources, "actas"), _load(sources, "votos")
    if actas.empty or votos.empty:
        sys.exit("Nada que construir: faltan fuentes.")

    # Dedup actas por acta_id segun precedencia de fuente.
    actas["_p"] = actas["fuente"].map(PRECEDENCIA).fillna(0)
    actas = (actas.sort_values("_p", ascending=False)
                   .drop_duplicates("acta_id", keep="first").drop(columns="_p"))
    # Dedup votos por (acta_id, legislador) segun precedencia.
    votos["_p"] = votos["fuente"].map(PRECEDENCIA).fillna(0)
    votos = (votos.sort_values("_p", ascending=False)
                   .drop_duplicates(["acta_id", "legislador_nombre"], keep="first").drop(columns="_p"))

    # Integridad: todo voto referencia un acta existente; voto en enum.
    assert votos["voto"].isin(VOTOS_OK).all(), "hay votos fuera del enum canónico"
    huerfanos = (~votos["acta_id"].isin(set(actas["acta_id"]))).sum()
    assert huerfanos == 0, f"{huerfanos} votos sin acta (FK rota)"

    _checks(actas, ["schema_version", "acta_id", "camara", "titulo", "fuente"], "actas")
    _checks(votos, ["schema_version", "acta_id", "legislador_nombre", "bloque", "voto", "fuente"], "votos")
    _sample_jsonschema(actas, json.load(open(schemas / "acta.schema.json")))
    _sample_jsonschema(votos, json.load(open(schemas / "voto.schema.json")))

    actas.to_parquet(clean / "actas_canonico.parquet", index=False)
    votos.to_parquet(clean / "votos_canonico.parquet", index=False)
    print(f"OK canónica: {len(actas)} actas, {len(votos)} votos -> {clean}")
    print("  cámaras:", actas['camara'].value_counts().to_dict())
    print("  fuentes:", actas['fuente'].value_counts().to_dict())

if __name__ == "__main__":
    main()
