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

# Mínimo de votos para que una coincidencia de recuento signifique algo. Con 20 votos
# emitidos, dos actas distintas pueden dar el mismo reparto por casualidad; con 250, no.
MIN_VOTOS_GEMELA = 40


def _cruzar(g: pd.DataFrame, evidencia: str) -> list[dict]:
    """Todos los pares de FUENTES DISTINTAS dentro de un grupo ya agrupado."""
    if g["fuente"].nunique() < 2:
        return []                    # misma fuente: puede ser votacion en particular
    g = g.sort_values(["fuente", "acta_id"]).drop_duplicates("acta_id")
    out = []
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            a, b = g.iloc[i], g.iloc[j]
            if a["fuente"] == b["fuente"]:
                continue
            out.append({"camara": a["camara"], "n_votos": int(a["_total"]),
                        "evidencia": evidencia,
                        "acta_a": a["acta_id"], "fuente_a": a["fuente"],
                        "acta_b": b["acta_id"], "fuente_b": b["fuente"]})
    return out


def actas_gemelas(actas: pd.DataFrame, votos: pd.DataFrame) -> pd.DataFrame:
    """Actas de FUENTES DISTINTAS que son la misma votación con otro `acta_id`.

    **Por qué existe.** El dedup de arriba es por `acta_id`, así que dos fuentes que le
    ponen distinto id a la MISMA votación pasan las dos. El 06-09-2026 se encontró que
    las 17 actas de `manual_2026` son las mismas votaciones que 17 de `argentinadatos`:
    12 coinciden voto por voto al 100% y las 5 restantes tienen el recuento IDÉNTICO
    (139/97/21, 130/106/14/7, ...) y difieren sólo en el `legislador_id` de algunas
    personas, que es la costura de identidades entre las dos ingestas. O sea: 3.072
    votos entrando dos veces, **2,7% de la era vigente**.

    Nadie lo vio durante meses porque no da error: son dos actas legítimas con dos ids
    legítimos. La huella que las delata es el RECUENTO — dos votaciones distintas de la
    misma cámara no dan el mismo reparto exacto de afirmativos, negativos, abstenciones
    y ausentes por casualidad.

    **Y no era sólo `manual_2026`.** El mismo control, corrido sobre toda la canónica,
    encontró que **259 de las 999 actas de `ckan_diputados` (26%) son la misma votación
    que una de `argentinadatos`**: mismo día, mismo reparto y 249 de ellas idénticas voto
    por voto. Son 66.563 votos, **6,6% de la canónica**. Los ids se prefijan distinto
    (`ckan_diputados:361` contra `argentinadatos:diputados:361` — el mismo 361), así que
    el dedup por `acta_id` no los ve.

    **Dos niveles de evidencia, y la diferencia importa:**

    - *misma fecha + mismo recuento*: es evidencia. Dos votaciones distintas de la misma
      cámara **el mismo día** no dan el mismo reparto exacto por casualidad.
    - *sólo mismo recuento* (cuando una de las dos no tiene fecha, como `manual_2026`):
      es un INDICIO y hay que mirarlo a mano. Sin el día, el recuento solo coincide por
      casualidad seguido: la primera versión de este control, que agrupaba sólo por
      recuento, devolvía 12.469 pares y casi todos eran ruido.

    Devuelve un DataFrame con los pares sospechosos. NO borra nada: quién manda entre
    dos fuentes es una decisión de precedencia, no de este control.
    """
    r = (votos.groupby(["acta_id", "voto"]).size().unstack(fill_value=0))
    r["_total"] = r.sum(axis=1)
    r = r[r["_total"] >= MIN_VOTOS_GEMELA]
    cols = [c for c in r.columns if c != "_total"]
    r["_huella"] = [tuple(x) for x in r[cols].to_numpy()]
    d = (r.reset_index()[["acta_id", "_huella", "_total"]]
           .merge(actas[["acta_id", "camara", "fuente", "titulo"]], on="acta_id", how="left"))
    d["fecha"] = pd.to_datetime(
        actas.set_index("acta_id")["fecha"].reindex(d["acta_id"]).values, errors="coerce")
    pares = []
    # CON FECHA: (camara, fecha, huella). Es la evidencia fuerte — dos actas de la misma
    # camara, el MISMO DIA y con el mismo reparto exacto son la misma votacion.
    con = d[d["fecha"].notna()]
    for _, g in con.groupby(["camara", "fecha", "_huella"]):
        pares += _cruzar(g, "misma fecha + mismo recuento")
    # SIN FECHA: (camara, huella) y se marca como indicio, no como evidencia. Es el caso
    # de `manual_2026`, que entra sin fecha; sin el dia, el recuento solo puede coincidir
    # por casualidad y hay que mirarlo a mano.
    sin = d[d["fecha"].isna()]
    if len(sin):
        todos = pd.concat([sin, d])
        for _, g in todos.groupby(["camara", "_huella"]):
            if not g["acta_id"].isin(sin["acta_id"]).any():
                continue
            pares += _cruzar(g, "sin fecha: solo mismo recuento (INDICIO)")
    return pd.DataFrame(pares)


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

    # ACTAS GEMELAS: la misma votación entrando dos veces con dos `acta_id`.
    #
    # Se DESCARTA la copia de menor PRECEDENCIA, y sólo cuando la evidencia es fuerte
    # (misma cámara, misma fecha y mismo recuento). Los indicios sin fecha se reportan y
    # NO se tocan: sin el día, el recuento coincide por casualidad seguido.
    #
    # La precedencia que ya estaba escrita da el resultado correcto y está verificado
    # campo por campo sobre las 250 actas duplicadas (06-09-2026):
    #
    #                      tipo_mayoria   expediente   temas ya clasificados
    #   ckan_diputados         100%          88%              248
    #   argentinadatos           0%           0%                0
    #
    # De esas 250, **12 no son de mayoría simple** (10 "Dos tercios", 2 "La mitad más
    # uno"): con la copia de argentinadatos ganando, esas 12 caerían al default SIMPLE y
    # el umbral del recuento sería el equivocado. Y las 248 clasificaciones de tema
    # cuestan llamadas de API: tirarlas es tirar trabajo pago.
    gem = actas_gemelas(actas, votos)
    sobran = set()
    if len(gem):
        prec = gem["fuente_a"].map(PRECEDENCIA).fillna(0) < gem["fuente_b"].map(PRECEDENCIA).fillna(0)
        gem["sobra"] = gem["acta_a"].where(prec, gem["acta_b"])
        fuerte = gem[gem["evidencia"].str.startswith("misma fecha")]
        indicio = gem[~gem["evidencia"].str.startswith("misma fecha")]
        sobran = set(fuerte["sobra"])
        n = int(votos["acta_id"].isin(sobran).sum())
        print(f"  actas GEMELAS: {len(fuerte)} pares con evidencia fuerte -> se descartan "
              f"{len(sobran)} actas ({n:,} votos que entraban dos veces).")
        for f, sub in fuerte.groupby(["fuente_a", "fuente_b"]):
            gana = max(f, key=lambda x: PRECEDENCIA.get(x, 0))
            print(f"       {f[0]} vs {f[1]}: {len(sub)} pares, gana {gana}")
        if len(indicio):
            print(f"  !! {len(indicio)} pares SIN FECHA (sólo mismo recuento): son INDICIO, "
                  f"NO se descartan. Miralos a mano.")
            for _, r in indicio.head(4).iterrows():
                print(f"       {r.camara}: {r.acta_a} ({r.fuente_a}) == {r.acta_b} ({r.fuente_b})")
        actas = actas[~actas["acta_id"].isin(sobran)]
        votos = votos[~votos["acta_id"].isin(sobran)]

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
