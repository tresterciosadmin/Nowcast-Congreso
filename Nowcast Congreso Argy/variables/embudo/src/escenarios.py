"""ESCENARIOS — scorea UN proyecto y sus contrafactuales con el modelo del embudo.

Responde la pregunta de negocio: *"¿cuánto cambia la probabilidad si el mismo
texto lo presenta el Poder Ejecutivo, un jefe de bloque oficialista, o un
diputado de a pie de la oposición?"*. El texto no cambia: cambia QUIÉN firma.

No re-implementa el modelo: importa `variables/embudo/src/embudo.py` (contrato del
equipo), entrena UNA vez sobre la cohorte madura y luego reemplaza los rasgos
`origen_*` / `lider` de la fila del proyecto para leer el efecto marginal puro.

⚠️ COLINEALIDAD (detectada 2026-07-31, ver ESTADO). En el modelo v1 el rasgo
`autor_tasa_hist` (tasa histórica de éxito del autor) correlaciona **0,874** con
`origen_ejecutivo`: el autor del PE ES el presidente, cuya tasa histórica ronda
0,76 contra 0,033 del promedio. La logística le adjudica el crédito a
`autor_tasa_hist` (coef 0,61) y deja `origen_ejecutivo` en 0,04 y `lider` en
−0,03, pese a que las tasas CRUDAS son 78,8% vs 1,4% y 6x respectivamente.
Consecuencia: pisar solo `origen_*` NO produce un contrafactual válido — el
modelo casi no se mueve porque el autor sigue siendo el mismo. Por eso este
script mueve **también** `autor_tasa_hist` a la mediana del grupo destino
(`origen × lider`) en el train. La tabla cruda se imprime siempre al lado, para
que el lector pueda contrastar modelo contra observación.

Uso:
    python variables/embudo/src/escenarios.py HCDN292179
    python variables/embudo/src/escenarios.py HCDN292179 --json salida.json

Salida: tabla por escenario con p_sancion y p_llega_recinto, más el desglose
histórico observado (tasa base por origen/líder) para contrastar modelo vs. crudo.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embudo as E  # noqa: E402  (contrato del equipo)

logger = logging.getLogger("escenarios")

# (origen, lider) por escenario, en el orden en que se muestran.
ESCENARIOS = [
    ("Poder Ejecutivo (real)",            "EJECUTIVO",   0),
    ("Jefe de bloque OFICIALISTA",        "OFICIALISMO", 1),
    ("Diputado común OFICIALISTA",        "OFICIALISMO", 0),
    ("Jefe de bloque OPOSITOR",           "OPOSICION",   1),
    ("Diputado común OPOSITOR",           "OPOSICION",   0),
]


def _modelo_entrenado(c: pd.DataFrame, target: str, feats_proy, madurez: int):
    """Entrena sobre la cohorte madura y devuelve (modelo, columnas, top_com,
    tasa_autor, base_autor) para poder scorear filas sintéticas después."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline

    train = E.cohorte_madura(c, madurez)
    top_com = E._top_comisiones(train)
    tasa_autor, base_autor = E._tasa_autor(train, target)
    Xtr = E.construir_features(train, top_com, tasa_autor, base_autor, feats_proy)
    modelo = make_pipeline(StandardScaler(with_mean=False),
                           LogisticRegression(max_iter=1000))
    modelo.fit(Xtr, train[target].astype(int).values)
    # mediana de autor_tasa_hist por grupo destino, para contrafactuales coherentes
    g = train[["proyecto_id"]].copy()
    if feats_proy is not None:
        f = feats_proy.drop_duplicates("proyecto_id")[["proyecto_id", "origen", "lider"]]
        g = g.merge(f, on="proyecto_id", how="left")
        g["ath"] = Xtr["autor_tasa_hist"].values
        med = g.groupby(["origen", "lider"])["ath"].median().to_dict()
    else:
        med = {}
    return modelo, Xtr.columns, top_com, tasa_autor, base_autor, med


def scorear_escenarios(pid: str, madurez: int = E.MADUREZ_ANIOS) -> dict:
    clean, out, feats_path = E._rutas()
    dfs = E.cargar(Path(clean))
    c = E.construir_cohorte(dfs)
    feats = pd.read_parquet(feats_path) if feats_path else None

    fila = c[c["proyecto_id"].astype(str) == pid]
    if fila.empty:
        raise SystemExit(f"proyecto_id {pid} no está en la cohorte de LEY")
    i = fila.index[0]

    res: dict = {"proyecto_id": pid,
                 "titulo": str(fila.iloc[0].get("titulo", ""))[:200],
                 "anio": int(fila.iloc[0]["anio"]),
                 "comisiones": list(fila.iloc[0].get("comisiones") or []),
                 "escenarios": {}}

    for target in ("sancionado", "llega_recinto"):
        modelo, cols, top_com, tasa_autor, base_autor, med = _modelo_entrenado(
            c, target, feats, madurez)
        for nombre, origen, lider in ESCENARIOS:
            X = E.construir_features(fila, top_com, tasa_autor, base_autor, feats)
            X = X.reindex(columns=cols, fill_value=0.0)
            # contrafactual: quién firma = origen + liderazgo + su tasa histórica
            for cat in ("ejecutivo", "oficialismo", "oposicion"):
                if "origen_" + cat in X.columns:
                    X.loc[i, "origen_" + cat] = 1.0 if cat == origen.lower() else 0.0
            if "lider" in X.columns:
                X.loc[i, "lider"] = float(lider)
            # sin esto el contrafactual es falso: ver nota de COLINEALIDAD arriba
            ath = med.get((origen, bool(lider)))
            if ath is not None and "autor_tasa_hist" in X.columns:
                X.loc[i, "autor_tasa_hist"] = float(ath)
            p = float(modelo.predict_proba(X)[0, 1])
            res["escenarios"].setdefault(nombre, {})[target] = round(p, 4)
            res["escenarios"][nombre]["autor_tasa_hist"] = round(float(ath or 0), 4)
    return res


def tasas_observadas(madurez: int = E.MADUREZ_ANIOS) -> pd.DataFrame:
    """Tasa histórica CRUDA por (origen × líder): el contraste sin modelo."""
    clean, _, feats_path = E._rutas()
    c = E.construir_cohorte(E.cargar(Path(clean)))
    c = E.cohorte_madura(c, madurez)
    if not feats_path:
        return pd.DataFrame()
    f = pd.read_parquet(feats_path).drop_duplicates("proyecto_id")
    m = c.merge(f[["proyecto_id", "origen", "lider"]], on="proyecto_id", how="left")
    g = m.groupby(["origen", "lider"], dropna=False).agg(
        n=("proyecto_id", "size"),
        pct_dictamen=("con_dictamen", lambda s: round(100 * s.mean(), 2)),
        pct_recinto=("llega_recinto", lambda s: round(100 * s.mean(), 2)),
        pct_sancion=("sancionado", lambda s: round(100 * s.mean(), 2)),
    ).reset_index()
    return g.sort_values("pct_sancion", ascending=False)


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("proyecto_id")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv[1:])

    obs = tasas_observadas()
    print("\n=== TASA HISTÓRICA OBSERVADA (cohorte madura, sin modelo) ===")
    print(obs.to_string(index=False))

    r = scorear_escenarios(a.proyecto_id)
    print(f"\n=== {r['proyecto_id']} · {r['titulo']}")
    print(f"    girado a: {', '.join(r['comisiones'])}\n")
    print(f"{'ESCENARIO':<34} {'P(recinto)':>11} {'P(sanción)':>11}  {'tasa_autor':>10}")
    for k, v in r["escenarios"].items():
        rec, san, ath = v["llega_recinto"], v["sancionado"], v["autor_tasa_hist"]
        print(f"{k:<34} {100*rec:>10.1f}% {100*san:>10.1f}%  {ath:>10.3f}")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"scoring": r, "observado": obs.to_dict("records")},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main(sys.argv)
