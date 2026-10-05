# -*- coding: utf-8 -*-
"""D2 (auditoría 2026-09): los brazos de `calibracion_declarada.py --simular` y la regla de `medir_d2_capa2.py`.

QUÉ FIJA (pre-registro de D2 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. EL BRAZO: ε₀, τ y el piso aceptan un número o `{año: valor}`; un año que falta falla (no se adivina).
  2. LA REGLA, sobre tablas sintéticas:
     - la elección anual: el mínimo; empate < 1e-12 relativo con V0 → V0; sin V0 entre los empatados → el más bajo;
     - la selección sólo mira el entrenamiento: lo que pasa en las actas de fecha ≥ 1-ene-Y y en las leyes con actas
       de test en Y no cambia el valor elegido para Y (y lo de antes sí);
     - el Δ de cobertura: |c_alt − 0,90| − |c_base − 0,90| en pp, con las dos coberturas recalculadas por réplica;
     - el árbol (sin F, que es de la capa 1): Z, C, A, B, D y el veto E —recalibrar daña a un subgrupo; apagar el
       mecanismo daña donde el mecanismo es mejor—, y sin veto cuando la acción no es un cambio;
     - la salida del mecanismo desde sus dos contrastes (pre-registro 3.8): A y B → E; E en uno → E; A con C/D/Z → A…;
     - si el mecanismo termina en E, no se aplica nada (tampoco el piso); Holm con m = 5.
  3. EL VEREDICTO DE D2, recalculado desde `d2_capa2.json` y `d2_curvas.json` (lo que viaja por git), cuando exista.
No lee el detalle del censo: corre en el CI.

    python evaluacion/baseline/tests/test_d2_capa2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import calibracion_declarada as CD  # noqa: E402
import medir_d2_capa2 as D  # noqa: E402

FALLOS: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  ok    " if cond else "  FALLA ") + msg)
    if not cond:
        FALLOS.append(msg)


def falla(f) -> bool:
    try:
        f()
    except (KeyError, ValueError):
        return True
    return False


def curvas_sinteticas(objetivo_por_anio: dict, n_por_anio: int = 40, seed: int = 0) -> pd.DataFrame:
    """Actas de Diputados 2001–2012: la log-loss de cada acta es mínima en el ε₀ objetivo de su año; momentos de τ
    con sobredispersión creciente por año (para que τ dependa de lo que se mira)."""
    rng = np.random.default_rng(seed)
    filas = []
    for anio, obj in objetivo_por_anio.items():
        for i in range(n_por_anio):
            n = 60
            sp = rng.uniform(25, 35)
            sp2 = sp * sp / n + rng.uniform(1, 3)
            A = round(sp + rng.normal(0, 2 + 0.5 * (anio - 2000)))
            fila = {"acta_id": f"{anio}-{i}", "fecha": f"{anio}-06-01", "camara": "diputados",
                    "ley": f"L{anio}-{i // 2}", "n": n, "A": float(A), "sp": sp, "sp2": sp2, "dmin": 0.1}
            for e in D.GRILLA_EPS:
                fila[f"ll::{D.etiqueta(e)}"] = 10.0 + (e - obj) ** 2
            filas.append(fila)
    return pd.DataFrame(filas)


def r_falso(tipo: str, delta: float, ic_ley: list, ic_mes: list, final=None, v0=None, sub: dict | None = None,
            identico: bool = False, perdida: str = "brier") -> dict:
    sg = {k: {"actas": 10, "por_ley": {"ic95": v}} for k, v in (sub or {}).items()}
    return {"tipo": tipo, "perdida": perdida, "identico_en_el_panel": identico, "valor_wf_final": final, "v0": v0,
            "primario": {"actas": 100, "por_ley": {"delta": delta, "ic95": ic_ley}, "por_mes": {"ic95": ic_mes}},
            "subgrupos": sg}


def main() -> int:
    print("1. el brazo de --simular")
    check(CD.valor_brazo("0.02") == 0.02, "un número")
    v = CD.valor_brazo('{"2006": 0.04, "2007": 0.05}')
    check(v == {2006: 0.04, 2007: 0.05}, "un valor por año (claves enteras)")
    check(CD._del_anio(v, 2007, "x") == 0.05 and CD._del_anio(0.3, 1999, "x") == 0.3, "el valor del año del acta")
    check(falla(lambda: CD._del_anio(v, 2008, "x")), "un año que falta falla")

    print("2. la regla")
    check(D.elegir([0.0, 0.02, 0.04], np.array([1.0, 1.0, 1.0]), 0.02) == 0.02, "empate exacto → V0")
    check(D.elegir([0.0, 0.02, 0.04], np.array([1.0, 1.0 + 1e-14, 2.0]), 0.02) == 0.02, "empate < 1e-12 relativo → V0")
    check(D.elegir([0.0, 0.01, 0.02], np.array([1.0, 1.0, 2.0]), 0.02) == 0.0, "V0 fuera del empate → el más bajo")
    check(D.elegir([0.0, 0.01, 0.02], np.array([3.0, 1.0, 2.0]), 0.02) == 0.01, "el mínimo estricto")

    obj = {a: (0.05 if a < 2006 else 0.20) for a in range(2001, 2013)}
    c = curvas_sinteticas(obj)
    s = D.seleccion(c, None, D.GRILLA_PISO, D.EPS_BASE_MAX)
    check(s["anios"][2006]["epsilon0"] == 0.05, f"2006 elige con 2001–2005 (0,05): {s['anios'][2006]['epsilon0']}")
    check(s["anios"][2012]["epsilon0"] not in (0.05,), "2012 ya ve los años con objetivo 0,20")
    c2 = c.copy()
    m = pd.to_datetime(c2["fecha"]) >= "2006-01-01"
    for e in D.GRILLA_EPS:                    # lo de 2006 en adelante, absurdo: no puede mover la elección de 2006
        c2.loc[m, f"ll::{D.etiqueta(e)}"] = 1e6 * (e - 0.3) ** 2
    c2.loc[m, "A"] = c2.loc[m, "A"] + 30
    s2 = D.seleccion(c2, None, D.GRILLA_PISO, D.EPS_BASE_MAX, solo=[2006])
    check(s2["anios"][2006]["epsilon0"] == s["anios"][2006]["epsilon0"] and s2["anios"][2006]["tau"] == s["anios"][2006]["tau"],
          "corromper el test (fecha ≥ 2006) no cambia ε₀ ni τ de 2006")
    c3 = c.copy()
    m3 = pd.to_datetime(c3["fecha"]) < "2006-01-01"
    for e in D.GRILLA_EPS:
        c3.loc[m3, f"ll::{D.etiqueta(e)}"] = 10.0 + (e - 0.15) ** 2
    s3 = D.seleccion(c3, None, D.GRILLA_PISO, D.EPS_BASE_MAX, solo=[2006])
    check(s3["anios"][2006]["epsilon0"] == 0.15, "corromper el entrenamiento sí la cambia (control positivo)")
    lt = D.leyes_de_test(c)
    check(all(l.startswith("L2006") for l in lt[2006]), "las leyes de test de 2006 son las de sus actas OOS")

    n = np.full(50, 10.0)
    r = D.boot_cobertura(n, np.full(50, 9.0), np.full(50, 6.0))
    check(abs(r["delta"] + 30.0) < 1e-9 and abs(r["ic95"][0] + 30) < 1e-9 and abs(r["ic95"][1] + 30) < 1e-9,
          f"cobertura 90% contra 60%: Δ = −30 pp ({r['delta']}, {r['ic95']})")
    r = D.boot_cobertura(n, np.full(50, 6.0), np.full(50, 6.0))
    check(r["delta"] == 0 and r["ic95"] == [0.0, 0.0], "coberturas iguales: Δ = 0")
    rng = np.random.default_rng(1)
    d0 = rng.binomial(10, 0.6, 50).astype(float)
    r = D.boot_cobertura(n, np.minimum(d0 + 3, 10), d0)
    check(r["ic95"][1] < 0 and r["p"] < 0.01, f"cobertura que sube hacia 0,90: Δ < 0 con IC que excluye 0 ({r['ic95']})")
    d1 = np.full(50, 10.0)                    # 100%: se pasa de 0,90 por 10 pp; la base en 80% le erra por 10: Δ = 0
    r = D.boot_cobertura(n, d1, np.full(50, 8.0))
    check(abs(r["delta"]) < 1e-9, "el error es simétrico: 100% y 80% están a 10 pp de 0,90")

    ar = D.arbol
    check(ar(r_falso("hiper", 0, [0, 0], [0, 0], identico=True), False)["salida"] == "Z", "idéntico → Z")
    check(ar(r_falso("hiper", 0.2, [-0.5, 0.8], [-0.9, 0.9]), False)["salida"] == "C", "IC dentro de ±1% → C")
    check(ar(r_falso("hiper", 0.2, [-0.5, 1.8], [-0.9, 0.9]), False)["salida"] == "D", "IC fuera del margen, sin Holm → D")
    check(ar(r_falso("hiper", -3, [-5, -1.5], [-6, -1.2], final=0.0, v0=0.02), True)["salida"] == "A", "mejora → A")
    e = ar(r_falso("hiper", -3, [-5, -1.5], [-6, -1.2], final=0.0, v0=0.02, sub={"senado": [0.5, 4]}), True)
    check(e["salida"] == "E" and e["danio_en"] == ["senado"], "recalibrar daña al Senado → E")
    check(ar(r_falso("hiper", -3, [-5, -1.5], [-6, -1.2], final=0.02, v0=0.02, sub={"senado": [0.5, 4]}), True)["salida"]
          == "A", "si el WF final es V0 no hay cambio: sin veto")
    check(ar(r_falso("coef_ii", 3, [1.5, 5], [1.2, 6], final=0.05, v0=0.035), True)["salida"] == "B", "empeora → B")
    check(ar(r_falso("mec_i", 30, [15, 45], [12, 50]), True)["salida"] == "B", "el mecanismo empeora → B (apagar)")
    e = ar(r_falso("mec_i", 30, [15, 45], [12, 50], sub={"diputados": [-8, -2]}), True)
    check(e["salida"] == "E", "apagar daña donde el mecanismo es mejor → E")
    check(ar(r_falso("mec_i", -45, [-55, -35], [-56, -33], sub={"senado": [2, 6]}, perdida="cobertura"), True)["salida"]
          == "A", "el mecanismo mejora → A sin veto (seguir prendido no es un cambio)")
    check(ar(r_falso("mec_i", -0.5, [-0.8, -0.2], [-0.9, -0.1], perdida="cobertura"), True)["salida"] == "C",
          "cobertura dentro de ±1 pp → C")

    sm = D.salida_mecanismo
    casos = {("A", "B"): "E", ("B", "A"): "E", ("E", "A"): "E", ("D", "E"): "E", ("A", "D"): "A", ("Z", "A"): "A",
             ("B", "C"): "B", ("C", "C"): "C", ("Z", "Z"): "Z", ("C", "D"): "D", ("A", "A"): "A", ("D", "Z"): "D"}
    check(all(sm(a, b) == v for (a, b), v in casos.items()), "la salida del mecanismo (pre-registro 3.8)")

    def res_falso(salidas: dict) -> dict:
        out = {}
        for c_, s_ in salidas.items():
            perd, _, _, tipo = D.CONTRASTES[c_]
            ident = s_ == "Z"
            sig = {"A": (-3, [-5, -1.5], [-6, -1.2]), "B": (3, [1.5, 5], [1.2, 6]), "C": (0.1, [-0.5, 0.5], [-0.5, 0.5]),
                   "D": (0.5, [-2, 3], [-2, 3]), "Z": (0, [0, 0], [0, 0])}[s_]
            fin = {"piso": 0.0, "epsilon0": 0.05, "tau": 1.3}.get(c_)
            r_ = r_falso(tipo, *sig, final=fin, v0=D.V0.get(c_), identico=ident, perdida=perd)
            r_["primario"]["p_estrella"] = 0.0001 if s_ in "AB" else 0.5
            out[c_] = r_
        return out

    v = D.veredicto(res_falso({"piso": "A", "epsilon0": "D", "tau": "D", "mec_i": "B", "mec_i2": "A"}))
    check(v["mecanismo"] == "E" and all(x.startswith("no se aplica") for x in v["acciones"].values()),
          "el mecanismo en E (A y B cruzados): no se aplica nada, tampoco el piso")
    v = D.veredicto(res_falso({"piso": "A", "epsilon0": "A", "tau": "D", "mec_i": "A", "mec_i2": "D"}))
    check(v["mecanismo"] == "A" and v["acciones"]["epsilon0"].startswith("recalibrar") and v["acciones"]["tau"] == "conservar V0"
          and v["confirmacion_conjunta_necesaria"], f"mecanismo A: recalibra ε₀ y el piso → confirmación conjunta ({v['cambian']})")
    v = D.veredicto(res_falso({"piso": "D", "epsilon0": "A", "tau": "A", "mec_i": "D", "mec_i2": "D"}))
    check(v["acciones"]["epsilon0"] == "conservar V0" and v["acciones"]["tau"] == "conservar V0",
          "mecanismo D: (ii) en A no recalibra ((i) no es A)")
    v = D.veredicto(res_falso({"piso": "D", "epsilon0": "D", "tau": "D", "mec_i": "B", "mec_i2": "D"}))
    check(v["mecanismo"] == "B" and "apagar" in v["acciones"]["mecanismo"], "mecanismo B → apagar la bandera")
    check(D.holm({"a": 0.009, "b": 0.011, "c": 0.5, "d": 0.6, "e": 0.7}, 0.05, 5) == {"a": True, "b": True, "c": False,
          "d": False, "e": False}, "Holm con m = 5")

    print("3. el veredicto de D2, desde git")
    if not D.SALIDA.is_file():
        print(f"  (todavía no se midió: falta {D.SALIDA.name})")
    else:
        r = D.recalcular_desde_json()
        g = r["guardado"]
        sal = {k: v["salida"] for k, v in r["veredicto"]["por_contraste"].items()}
        check(sal == {k: v["salida"] for k, v in g["veredicto"]["por_contraste"].items()},
              f"el recálculo da lo mismo que lo guardado ({sal})")
        check({k: v for k, v in r["seleccion"]["anios"].items()} == g["seleccion"]["anios"],
              "la selección anual se reproduce desde las curvas y la tabla")
    print(f"\n{'TODO OK' if not FALLOS else f'{len(FALLOS)} FALLAS'}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
