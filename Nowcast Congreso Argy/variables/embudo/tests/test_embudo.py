"""Tests offline de variables/embudo con fixture sintetica (imita el contrato
de datos/expedientes). No toca disco ni red. Correr:  python tests/test_embudo.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import embudo as E  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def fixture():
    """500 proyectos de ley 2010-2021 con un embudo realista y senal aprendible:
    los girados a 1 comision con autor 'productivo' sancionan mas."""
    rng = np.random.default_rng(7)
    n = 600
    anios = rng.integers(2010, 2022, n)
    autores = rng.choice([f"A{i}" for i in range(20)], n)
    # autores 'productivos' (A0..A4) empujan la sancion
    prod = np.isin(autores, [f"A{i}" for i in range(5)])
    n_giros = rng.choice([1, 1, 2, 3], n)
    # probabilidad de dictamen y sancion dependen de rasgos reales (senal)
    p_dict = 0.10 + 0.15 * (n_giros == 1) + 0.20 * prod
    con_dict = rng.random(n) < p_dict
    p_sanc = np.where(con_dict, 0.25 + 0.30 * prod, 0.01)
    sanc = rng.random(n) < p_sanc
    recinto = con_dict & (rng.random(n) < 0.6) | sanc

    ids = [f"{i}-D-{anios[i]}" for i in range(n)]
    exp = pd.DataFrame({
        "proyecto_id": ids,
        "titulo": ["proyecto " + x for x in ids],
        "fecha_publicacion": [f"{a}-06-15" for a in anios],
        "camara_origen": rng.choice(["Diputados", "Senado"], n),
        "tipo": "PROYECTO DE LEY",
        "autor": autores,
    })
    giros = pd.DataFrame({
        "proyecto_id": np.repeat(ids, n_giros),
        "comision": [rng.choice(["PRESUPUESTO", "SALUD", "TRABAJO", "JUSTICIA"])
                     for _ in range(int(n_giros.sum()))],
        "orden": 1,
    })
    dicts = pd.DataFrame({"proyecto_id": [ids[i] for i in range(n) if con_dict[i]]})
    res = pd.DataFrame({
        "proyecto_id": ids,
        "resultado": [("MEDIA SANCION" if recinto[i] else None) for i in range(n)],
    })
    leyes = pd.DataFrame({"proyecto_id": [ids[i] for i in range(n) if sanc[i]]})
    return {"expedientes": exp, "giros": giros, "dictamenes": dicts,
            "resultados": res, "leyes": leyes}


def main():
    dfs = fixture()

    # --- cohorte ---
    c = E.construir_cohorte(dfs)
    chk(len(c) == 600, "cohorte = 600 proyectos de ley")
    chk(set(["proyecto_id", "anio", "n_giros", "con_dictamen", "llega_recinto",
             "sancionado", "etapa_actual"]).issubset(c.columns), "columnas del contrato")
    chk(c["n_giros"].min() >= 1, "n_giros >= 1 (todos girados)")
    chk(bool((c["sancionado"] <= c["llega_recinto"]).all()),
        "monotonia: sancionado => llega_recinto")

    # --- solo proyectos de LEY (filtra otros tipos) ---
    dfs2 = fixture()
    dfs2["expedientes"].loc[0, "tipo"] = "PROYECTO DE RESOLUCION"
    chk(len(E.construir_cohorte(dfs2)) == 599, "filtra tipos no-LEY")

    # --- embudo ---
    m = E.medir_embudo(c)
    chk(m["n_presentados"] == 600, "embudo cuenta presentados")
    chk(0 < m["pct_sancionado"] < m["pct_llega_recinto"] < 100,
        "embudo: sancionado < llega_recinto (achica)")
    chk(m["trans_sancion_dado_recinto"] >= m["pct_sancionado"],
        "transicion condicional > tasa absoluta")

    # --- por dimension y comision ---
    pa = E.embudo_por_dimension(c, "anio")
    chk(len(pa) >= 8 and "pct_sancionado" in pa.columns, "embudo por anio")
    pc = E.embudo_por_comision(c)
    chk("comision" in pc.columns and len(pc) >= 1, "embudo por comision")

    # --- cohorte madura (caducidad) ---
    mad = E.cohorte_madura(c, madurez=2)
    chk(mad["anio"].max() <= c["anio"].max() - 2, "cohorte madura excluye recientes")

    # --- features SIN LEAKAGE ---
    train = mad[mad["anio"] < 2019]
    top = E._top_comisiones(train)
    ta, base = E._tasa_autor(train, "sancionado")
    X = E.construir_features(train, top, ta, base)
    chk("autor_tasa_hist" in X.columns and "anio_electoral" in X.columns,
        "features incluyen historia de autor y anio electoral")
    chk(not X.isna().any().any(), "features sin NaN")
    chk("sancionado" not in X.columns and "con_dictamen" not in X.columns,
        "features NO incluyen el target (sin leakage)")

    # --- backtest temporal (si hay sklearn) ---
    try:
        import sklearn  # noqa: F401
        bt = E.backtest_temporal(c, target="sancionado", madurez=1, min_train=100)
        chk("global" in bt and bt["global"]["n"] > 0, "backtest produce metricas")
        chk(bt["global"]["auc"] > 0.5, "backtest AUC > 0.5 (aprende senal)")
        chk(bt["skill_score"] > 0, "backtest skill > 0 (mejora vs tasa base)")
        s = E.entrenar_y_scorear(c, "sancionado", None, madurez=1)
        chk(s.between(0, 1).all() and len(s) == len(c), "scoring en [0,1] para todos")
    except ImportError:
        print("  (sklearn no instalado: salteo backtest; se corre local)")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
