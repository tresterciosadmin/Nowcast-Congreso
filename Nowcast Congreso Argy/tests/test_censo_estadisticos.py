# -*- coding: utf-8 -*-
"""Los estadísticos del censo que viajan por git dan LO MISMO que el detalle voto a voto.

Auditoría 2026-09, ítem A2. El detalle del censo (37 MB) está ignorado por git; en su lugar
viaja `censo_estadisticos_*.json` (una fila por acta + la curva de ε₀). Este archivo fija tres
cosas, y las tres corren en un checkout limpio (sin el detalle):

1. **Equivalencia** (datos sintéticos): ε₀, τ, el skill con su IC por ley y el ΔBrier pareado
   salen IGUAL por el camino voto a voto (`estimar_epsilon`, `estimar_tau`,
   `skill_ic_por_ley`, `dif_brier_ic_por_ley`) que por el camino de los estadísticos.
2. **Lo versionado reproduce lo publicado**: el JSON del repo da el skill y el IC que ya
   figuran en `baseline_voto_individual.json`, y con él se recalculan ε₀ y τ (los valores que
   midió la auditoría: ε₀ 0,055 y τ 1,197 con el motor de hoy).
3. **Frescura** (sólo donde existe el detalle): el JSON corresponde al parquet que hay en
   disco (mismo sha256). Si alguien regenera el censo y no los estadísticos, falla.

Desde D1.0 de la auditoría (2026-10-02) hay dos JSON versionados: el del censo del 28-09
(`CE.ESTADISTICOS_2026_09_28`), que es el que publicó lo que fija el punto 2 y se conserva
como continuidad, y el del motor de hoy (`CE.ESTADISTICOS`, la ficha de desvío al día), cuyo
ε₀ y τ quedan anclados en `ESPERADO_HOY` (fijado DESPUÉS de medir, citando la medición).

    python -m pytest tests/test_censo_estadisticos.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import rutas  # noqa: E402

sys.path.insert(0, str(rutas.ENSEMBLE_OUT.parent / "src"))
import estimar_epsilon_tau as EET  # noqa: E402  (agrega evaluacion/baseline/src al path)
import censo_estadisticos as CE  # noqa: E402
import baseline_voto_individual as B  # noqa: E402

BINS = [pd.Timestamp("1990-01-01"), pd.Timestamp("2010-01-01"), pd.Timestamp("2030-01-01")]
ETIQ = ["antes", "despues"]


def _detalle_sintetico(seed: int = 3, n_actas: int = 150) -> pd.DataFrame:
    """Un censo de juguete con la forma del real: actas de 25-70 votos, dos cámaras, dos
    eras, leyes que se repiten (algunas sin ley), P_i con 0 y 1 exactos y dos variantes."""
    rng = np.random.default_rng(seed)
    filas = []
    for k in range(n_actas):
        camara = "diputados" if k % 3 else "senado"
        fecha = pd.Timestamp("2005-03-01") + pd.Timedelta(days=int(k * 60))
        ley = None if k % 5 == 0 else f"ley:{k // 2}"
        n = int(rng.integers(25, 71))
        p_gen = rng.beta(0.6, 0.15, n)
        p_gen[rng.random(n) < 0.15] = 1.0
        p_gen[rng.random(n) < 0.03] = 0.0
        p_tema = np.clip(p_gen + rng.normal(0, 0.03, n) * (p_gen < 1), 0, 1)
        shock = rng.normal(0, 0.25)          # un corrimiento comun por acta: sobredispersion, tau > 0
        y = (rng.random(n) < np.clip(p_gen * 0.9 + shock, 0.01, 0.99)).astype(int)
        for i in range(n):
            filas.append({"acta_id": f"a{k}", "fecha": fecha, "camara": camara,
                          "legislador": f"l{i}", "y": int(y[i]), "ley": ley,
                          "p__estricta__general": float(p_gen[i]),
                          "p__estricta__tema": float(p_tema[i]), "p": float(p_tema[i])})
    return pd.DataFrame(filas)


def _igual(a, b, ruta=""):
    """Igualdad recursiva con tolerancia de redondeo de punto flotante (1e-9)."""
    if isinstance(a, dict):
        assert set(a) == set(b), f"{ruta}: claves distintas {set(a) ^ set(b)}"
        for k in a:
            _igual(a[k], b[k], f"{ruta}/{k}")
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b), f"{ruta}: largos {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            _igual(x, y, f"{ruta}[{i}]")
    elif isinstance(a, (int, float, np.integer, np.floating)) and a is not None:
        assert b == pytest.approx(a, abs=1e-9), f"{ruta}: {a} != {b}"
    else:
        assert a == b, f"{ruta}: {a!r} != {b!r}"


@pytest.fixture(scope="module")
def sintetico():
    d = _detalle_sintetico()
    est = CE.generar(d, ("estricta__general", "estricta__tema"), era_bins=BINS, era_labels=ETIQ)
    a = CE.tabla_actas(est)
    ley = d["ley"].fillna("acta:" + d["acta_id"].astype(str))
    return d.assign(ley=ley), est, a


# ───────────────────────────── 1. equivalencia con el voto a voto ─────────────────────────────

@pytest.mark.parametrize("col,var", [("p__estricta__general", "estricta__general"),
                                     ("p", "p")])
@pytest.mark.parametrize("camara", ["", "diputados", "senado"])
def test_epsilon_y_tau_salen_igual_desde_los_estadisticos(sintetico, col, var, camara):
    d, est, a = sintetico
    votos = d[d["camara"] == camara] if camara else d
    panel = votos[["acta_id", "camara", "fecha", "y"]].assign(p_motor=votos[col].astype(float))
    eps_ref = EET.estimar_epsilon(panel)
    eps = EET.estimar_epsilon_curvas(*CE.curvas_epsilon(est, var, camara or None)[:3])
    _igual(eps_ref, eps, "epsilon")
    for e0 in (0.0, 0.035, eps_ref["eps0_optimo_logloss"]):
        ref = EET.estimar_tau(panel, e0)
        got = EET.estimar_tau_actas(CE.panel_actas(est, var, camara or None, a), e0)
        assert "error" not in ref, "el panel sintético es muy chico para tau"
        assert ref["tau_mediana"] > 0, "sin sobredispersion el test de tau no discrimina"
        _igual(ref, got, f"tau(eps0={e0})")


def test_skill_ic_y_dbrier_salen_igual_en_todos_los_cortes(sintetico):
    d, est, a = sintetico
    d = d.assign(era=pd.cut(d["fecha"], bins=BINS, labels=ETIQ).astype(str))
    cortes = {"global": np.ones(len(d), bool),
              **{f"era={e}": (d["era"] == e).to_numpy() for e in ETIQ},
              **{f"camara={c}": (d["camara"] == c).to_numpy() for c in ("diputados", "senado")}}
    assert set(cortes) == set(CE.cortes(a))
    for nombre, m in cortes.items():
        s = d[m]
        col = "p__estricta__general"
        ref = B._metricas(s[col].values, s["y"].values)["skill"]
        got = CE.skill(est, "estricta__general", nombre, a=a)
        assert got["skill"] == ref, nombre
        assert got["skill_ic95_ley"] == B.skill_ic_por_ley(s[col], s["y"], s["ley"]), nombre
        assert got["n_leyes"] == s["ley"].nunique() and got["n_votos"] == len(s)
        assert CE.dif_brier(est, "estricta__tema", "estricta__general", nombre, a=a) == \
            B.dif_brier_ic_por_ley(s["p__estricta__tema"], s["p__estricta__general"],
                                   s["y"], s["ley"]), nombre


def test_generar_rechaza_un_alias_que_ya_no_vale():
    """`p` tiene que ser igual a p__estricta__tema; si un censo futuro cambia eso, no se
    guarda un alias falso."""
    d = _detalle_sintetico()
    d["p"] = d["p"] * 0.99
    with pytest.raises(ValueError, match="alias"):
        CE.generar(d, era_bins=BINS, era_labels=ETIQ)


def test_pedir_una_variante_que_no_esta_da_un_error_que_dice_que_hacer(sintetico):
    _d, est, _a = sintetico
    with pytest.raises(KeyError, match="regenerar"):
        CE.variante(est, "dia_incluido__tema")


# ───────────────────────── 2. lo versionado reproduce lo publicado ─────────────────────────

def test_los_estadisticos_versionados_existen_y_estan_ordenados_por_git():
    """El archivo tiene que viajar (`.gitignore` ignora *.parquet y *.csv, no este JSON)."""
    ruta = RAIZ / CE.ESTADISTICOS
    assert ruta.is_file(), f"falta {CE.ESTADISTICOS}: regenerar con censo_estadisticos.py"
    est = CE.cargar()
    assert est["formato"] == CE.FORMATO
    a = CE.tabla_actas(est)
    assert len(a) == est["fuente"]["n_actas"]
    assert int(a["n"].sum()) == est["fuente"]["n_votos"]
    assert a["ley"].nunique() == est["fuente"]["n_leyes"]


def test_lo_versionado_reproduce_el_skill_publicado():
    """`baseline_voto_individual.json` es lo que publicó el censo del 28-09 para la
    variante que ES el motor (RECORD_POR_TEMA apagado). Los estadísticos, sin el detalle,
    dan el mismo skill, el mismo IC por ley y los mismos votos y leyes."""
    pub = json.loads((rutas.BASELINE_OUT / "baseline_voto_individual.json")
                     .read_text(encoding="utf-8"))
    assert pub["variante"] == "p__estricta__general", "cambió la variante publicada"
    est = CE.cargar(RAIZ / CE.ESTADISTICOS_2026_09_28)      # el censo que lo publicó
    a = CE.tabla_actas(est)
    g = pub["global"]
    got = CE.skill(est, "estricta__general", "global", a=a)
    assert got["skill"] == g["skill"]
    assert got["skill_ic95_ley"] == g["skill_ic95_ley"]
    assert got["n_votos"] == g["n"] and got["n_leyes"] == g["n_leyes"]
    for era, fila in pub["por_era"].items():
        e = CE.skill(est, "estricta__general", f"era={era}", a=a)
        assert (e["skill"], e["skill_ic95_ley"]) == (fila["skill"], fila["skill_ic95_ley"]), era
    for cam, fila in pub["por_camara"].items():
        e = CE.skill(est, "estricta__general", f"camara={cam}", a=a)
        assert (e["skill"], e["skill_ic95_ley"]) == (fila["skill"], fila["skill_ic95_ley"]), cam


def test_epsilon_y_tau_se_recalculan_sin_el_detalle():
    """El estimador corre en un checkout limpio y da lo que midió la auditoría: con el
    offset del motor de hoy (RECORD_POR_TEMA apagado) ε₀ = 0,055 y τ = 1,197; con `p` (el
    offset con el que se corrió por defecto, RECORD_POR_TEMA prendido) ε₀ = 0,05 y τ = 1,2249.
    Ver `URGENTE.md` (U2) y ADR-0034. Si una re-estimación de la fase D cambia el censo,
    este test se actualiza junto con el JSON: es la barandilla de que nadie lo cambió sin ver."""
    for ruta, esperado in ((RAIZ / CE.ESTADISTICOS_2026_09_28,
                            {"estricta__general": (0.055, 1.197, 1.1521), "p": (0.05, 1.2249, 1.1734)}),
                           (RAIZ / CE.ESTADISTICOS, ESPERADO_HOY)):
        assert esperado, f"falta el ancla de ε₀ y τ de {ruta.name} (fijarla citando la medición)"
        _eps_tau(CE.cargar(ruta), esperado)


# El motor de hoy (lote de D1: la ventana de la postura en 2190 días), fijado DESPUÉS de medir: (ε₀ log-loss, τ sin ε₀,
# τ con ε₀). Medido el 2026-10-05 sobre `censo_estadisticos_2026-10-03.json` (ESTADO-EJECUCION.md, «D1 — lote»): ε₀
# 0,055 → 0,035; τ 1,201 → 1,1882; τ con ε₀ 1,1535 → 1,156 (D1.0: (0,055; 1,201; 1,1535)). En este censo `p` es la
# variante del motor (RECORD_POR_TEMA apagado).
ESPERADO_HOY = {"estricta__general": (0.035, 1.1882, 1.156), "p": (0.035, 1.1882, 1.156)}


def _eps_tau(est, esperado):
    for col, (e0, tau0, tau_e) in esperado.items():
        r = EET._resultado_desde_estadisticos(est, col, "")
        assert r["n_votos"] == est["fuente"]["n_votos"] and r["n_actas"] == est["fuente"]["n_actas"]
        assert r["epsilon"]["eps0_optimo_logloss"] == e0, col
        assert r["tau_sin_epsilon"]["tau_mediana"] == tau0, col
        assert r["tau_con_epsilon"]["tau_mediana"] == tau_e, col
        assert set(r["por_camara"]) == {"diputados", "senado"}


# ───────────────────────────── 3. frescura frente al detalle local ─────────────────────────────

def test_el_json_corresponde_al_detalle_que_hay_en_disco():
    """Sólo corre donde existe el parquet (la PC que regenera el censo). Si se regeneró el
    detalle y no los estadísticos, avisa: los estimadores leerían números viejos."""
    est = CE.cargar()
    rel = est["fuente"].get("detalle")
    detalle = RAIZ / rel if rel else None
    if detalle is None or not detalle.is_file():
        pytest.skip("el detalle del censo no está en este disco (es lo esperado en CI)")
    assert CE._sha16(detalle) == est["fuente"]["detalle_sha256_16"], (
        f"{rel} cambió desde que se generó {CE.ESTADISTICOS}: correr "
        "`python evaluacion/baseline/src/censo_estadisticos.py`")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
