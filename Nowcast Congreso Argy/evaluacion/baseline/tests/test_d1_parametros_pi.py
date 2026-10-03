# -*- coding: utf-8 -*-
"""D1 (auditoría 2026-09): el mecanismo `brazo` del harness y la regla del veredicto de `medir_d1_parametros_pi.py`.

QUÉ FIJA (pre-registro de D1 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. EL BRAZO: claves desconocidas y orígenes inválidos fallan; un valor por año da el del año del acta y un año que
     falta falla; `era_desde` (el argumento de C3) y `brazo['era_desde']` no pueden contradecirse; sin brazo = {}.
  2. LA REGLA, sobre tablas por acta sintéticas (el mismo camino que recorre la medición real):
     - una alternativa idéntica a V0 → la selección elige V0 (empate) y la salida es Z;
     - una alternativa mejor en todas las actas → el WF la elige todos los años y la salida es A (con el panel chico
       frente al global, sin alarma F); con el mismo efecto sobre todo el global, F;
     - una alternativa peor → el WF elige V0 todos los años → Z;
     - el borde: si algún año elige el máximo de la grilla, `toca_borde` pide la extensión de arriba (y no la de
       abajo cuando no existe);
     - Holm con m = 7 (los que faltan cuentan como p = 1) y el veto E cuando la alternativa daña a una cámara
       (y no cuando el valor WF final es V0: ahí la acción es conservar, no un cambio);
     - el contraste fijo del guard (la simplificación de C3): desde 2015-12-10, denominador = el Brier de V0 sobre
       todos los votos, con IC por ley y por mes; informativo, no entra a Holm.
No lee el detalle del censo: corre en el CI.

    python evaluacion/baseline/tests/test_d1_parametros_pi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import medir_d1_parametros_pi as D  # noqa: E402
from baseline_voto_individual import normalizar_brazo, valor_del_brazo  # noqa: E402

FALLOS: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  ok    " if cond else "  FALLA ") + msg)
    if not cond:
        FALLOS.append(msg)


def falla(f) -> bool:
    try:
        f()
    except (ValueError, KeyError):
        return True
    return False


def tabla(par: str, efecto: dict, n_actas: int = 400, e0_todos: float = 100.0, efecto_senado: dict | None = None,
          seed: int = 3) -> pd.DataFrame:
    """Una tabla por acta sintética: actas de 2004 a 2026 en las dos cámaras, una ley por acta, `e::<valor>` = la suma
    de Brier de V0 (con ruido) por el factor de `efecto` (1 = igual que V0)."""
    rng = np.random.default_rng(seed)
    fechas = pd.to_datetime("2004-03-01") + pd.to_timedelta(np.sort(rng.integers(0, 365 * 22, n_actas)), unit="D")
    cam = np.where(np.arange(n_actas) % 2 == 0, "diputados", "senado")
    t = pd.DataFrame({"acta_id": [f"a{i}" for i in range(n_actas)], "fecha": fechas.strftime("%Y-%m-%d"),
                      "camara": cam, "ley": [f"l{i}" for i in range(n_actas)]})
    base = rng.uniform(5, 15, n_actas)
    t["n_panel"], t["n_todos"] = 50, 500
    t["e0_todos"], t["e_orig"] = e0_todos * base, base
    for v in D.GRILLAS[par]["grilla"]:
        lab = D.etiqueta(v)
        f = np.full(n_actas, efecto.get(lab, 1.0))
        if efecto_senado:
            f = np.where(cam == "senado", efecto_senado.get(lab, f), f)
        t[f"e::{lab}"] = base * f * (1 + 0.01 * rng.standard_normal(n_actas)) if lab in efecto else base
        t[f"a::{lab}"] = 1.0 if lab in efecto else 0.0     # |Δp| contra V0: sólo las que tienen efecto difieren
    return t


def main() -> int:
    print("1. el brazo del harness")
    check(normalizar_brazo(None) == {}, "sin brazo = {}")
    check(falla(lambda: normalizar_brazo({"k": 1})), "una clave desconocida falla")
    check(falla(lambda: normalizar_brazo({"origen": "medio"})), "un origen que no es 'fino' ni 'lado' falla")
    check(falla(lambda: normalizar_brazo({"era_desde": "1900-01-01"}, "2000-01-01")), "era_desde contradictoria falla")
    b = normalizar_brazo({"k_postura": {"2020": 10.0, 2021: 2.5}, "ventana_postura": None}, "1900-01-01")
    check(b == {"k_postura": {2020: 10.0, 2021: 2.5}, "era_desde": "1900-01-01"}, f"normaliza años y vacíos: {b}")
    check(valor_del_brazo(b, "k_postura", "2021-05-01") == 2.5, "valor por año: el del año del acta")
    check(valor_del_brazo(b, "origen", "2021-05-01") is None, "clave ausente = el motor (None)")
    check(falla(lambda: valor_del_brazo(b, "k_postura", "2019-05-01")), "un año que falta falla")
    check(D.brazo_de("ventana_postura=365") == ("ventana_postura", 365, {"ventana_postura": 365}), "brazo_de entero")
    check(D.brazo_de("k_postura=2.5")[2] == {"k_postura": 2.5} and D.brazo_de("origen=lado")[1] == "lado",
          "brazo_de real y texto")
    check(len(D.brazos_de_la_grilla()) == 9, f"nueve brazos de censo: {D.brazos_de_la_grilla()}")

    print("2. la regla del veredicto, sobre tablas sintéticas")
    par = "k_record"
    vals = D.GRILLAS[par]["grilla"]
    t = tabla(par, {})
    sel = D.seleccion_anual(t, par, vals)
    check(set(sel["por_anio"].values()) == {5.0} and sel["final"] == 5.0, "todas iguales: el empate lo gana V0")
    r = D.medir_parametro(t, par, vals)
    check(D.arbol(r, False)["salida"] == "Z", "todas iguales → Z")

    t = tabla(par, {"10": 0.9})
    sel = D.seleccion_anual(t, par, vals)
    check(set(sel["por_anio"].values()) == {10.0}, f"una mejor en todas las actas: el WF la elige siempre ({set(sel['por_anio'].values())})")
    r = D.medir_parametro(t, par, vals)
    check(r["primario"]["por_ley"]["dBrier_rel_%"] < 0 and r["primario"]["por_ley"]["ic95"][1] < 0, "Δ < 0 con IC < 0")
    check(r["global_oos"]["dBrier_rel_%"] > -2, f"global chico: {r['global_oos']['dBrier_rel_%']}")
    check(D.arbol(r, True)["salida"] == "A", "mejor, Holm rechaza → A")
    check(D.arbol(r, False)["salida"] == "D", "mejor, Holm no rechaza → D")
    tF = tabla(par, {"10": 0.9}, e0_todos=1.0)
    check(D.arbol(D.medir_parametro(tF, par, vals), True)["salida"] == "F", "la misma mejora sobre todo el global → F")

    tE = tabla(par, {"10": 0.85}, efecto_senado={"10": 1.06})
    rE = D.medir_parametro(tE, par, vals)
    salE = D.arbol(rE, True)
    check(salE["salida"] == "E" and "senado" in salE.get("danio_en", []), f"mejora global que daña al Senado → E ({salE})")
    rE["valor_wf_final"] = rE["v0"]
    salE0 = D.arbol(rE, True)
    check(salE0["salida"] == "A" and "es V0" in salE0["accion"],
          f"con el valor WF final en V0 la acción es conservar: sin veto E ({salE0})")

    tG = tabla("guard", {"sin_corte": 1.1})
    rG = D.medir_parametro(tG, "guard", D.GRILLAS["guard"]["grilla"])
    cf = rG.get("contraste_fijo_simplificacion", {})
    fG = pd.to_datetime(tG["fecha"])
    mG = D.es_oos(tG) & (fG >= pd.Timestamp("2015-12-10")).to_numpy()
    esperado = 100 * (tG["e::sin_corte"] - tG["e::prendido"])[mG].sum() / tG["e0_todos"][mG].sum()
    check(cf.get("informativo") and abs(cf["por_ley"]["dBrier_rel_%"] - round(esperado, 4)) < 1e-9
          and "por_mes" in cf and cf["votos_todos"] == int(tG["n_todos"][mG].sum()),
          f"guard: contraste fijo desde 2015-12-10 con denominador e0_todos ({cf.get('por_ley', {}).get('dBrier_rel_%')} "
          f"contra {esperado:.4f}), con IC por mes")
    vG = D.veredicto({"guard": rG})["por_parametro"]["guard"]
    check(vG["p_estrella_holm"] == rG["primario"]["p_estrella"], "el contraste fijo no entra a Holm")
    check("contraste_fijo_simplificacion" not in D.medir_parametro(t, par, vals), "sólo el guard lo lleva")

    t = tabla(par, {"10": 1.2})
    sel = D.seleccion_anual(t, par, vals)
    check(set(sel["por_anio"].values()) == {5.0}, "una peor: el WF elige V0 siempre")
    check(D.arbol(D.medir_parametro(t, par, vals), False)["salida"] == "Z", "peor → Z (el compuesto es V0)")

    t = tabla(par, {"40": 0.9})
    sel = D.seleccion_anual(t, par, vals)
    check(D.toca_borde(par, sel, vals) == ["arriba"], "elige el máximo → extensión de arriba (80)")
    t = tabla(par, {"0": 0.9})
    check(D.toca_borde(par, D.seleccion_anual(t, par, vals), vals) == [], "k = 0 es borde sin extensión de abajo")

    rech = D.holm({"a": 0.001, "b": 0.008, "c": 0.02})
    check(rech == {"a": True, "b": True, "c": False}, f"Holm con m = 7: 0,001 ≤ 0,05/7; 0,008 ≤ 0,05/6; 0,02 > 0,05/5 ({rech})")
    rech = D.holm({"a": 0.001, "b": 0.013, "c": 0.002, "d": 0.0001})
    check(rech == {"d": True, "a": True, "c": True, "b": False}, f"Holm: el 4.º, 0,013 > 0,05/4 = 0,0125, se frena ({rech})")
    print(f"\n{'TODO OK' if not FALLOS else f'{len(FALLOS)} FALLAS'}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
