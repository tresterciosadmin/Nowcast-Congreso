"""Tests offline de modelo/ensemble (v3 roster nominal). Usan el agregador real
(simular_votacion) pero NINGÚN dato del repo: padrón y fichas sintéticos en tmp.
Correr:  python modelo/ensemble/tests/test_ensemble.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ensemble as E  # noqa: E402

OK = 0


def chk(cond, msg):
    global OK
    assert cond, "FALLO: " + msg
    OK += 1
    print("  ok:", msg)


def _armar_padron_y_fichas(tmp: Path):
    """Padrón sintético de 6 legisladores (uno con mandato vencido) + fichas."""
    pad = pd.DataFrame([
        # con ficha reciente suficiente
        {"legislador": "Uno", "legislador_id": "leg:1", "bloque_linaje": "AZUL",
         "desde": "2023-12-10", "hasta": "2027-12-09"},
        # con ficha global (reciente corta)
        {"legislador": "Dos", "legislador_id": "leg:2", "bloque_linaje": "AZUL",
         "desde": "2023-12-10", "hasta": "2027-12-09"},
        # camada nueva sin ficha -> fallback bloque
        {"legislador": "Tres", "legislador_id": "leg:3", "bloque_linaje": "AZUL",
         "desde": "2025-12-10", "hasta": "2029-12-09"},
        # bloque ROJO con ficha reciente
        {"legislador": "Cuatro", "legislador_id": "leg:4", "bloque_linaje": "ROJO",
         "desde": "2023-12-10", "hasta": "2027-12-09"},
        # linaje sin línea proyectada
        {"legislador": "Cinco", "legislador_id": "leg:5", "bloque_linaje": "VERDE",
         "desde": "2023-12-10", "hasta": "2027-12-09"},
        # mandato VENCIDO: no debe entrar
        {"legislador": "Seis", "legislador_id": "leg:6", "bloque_linaje": "AZUL",
         "desde": "2019-12-10", "hasta": "2023-12-09"},
    ])
    (tmp / "padron_diputados.csv").write_text(
        pad.to_csv(index=False), encoding="utf-8-sig")
    fichas = pd.DataFrame([
        {"legislador_id": "leg:1", "n_votos": 500, "tasa_desvio": 0.10,
         "n_reciente": 60, "tasa_desvio_reciente": 0.30},
        {"legislador_id": "leg:2", "n_votos": 400, "tasa_desvio": 0.08,
         "n_reciente": 5, "tasa_desvio_reciente": 0.90},
        {"legislador_id": "leg:4", "n_votos": 300, "tasa_desvio": 0.02,
         "n_reciente": 50, "tasa_desvio_reciente": 0.05},
    ])
    fcsv = tmp / "disciplina_individual.csv"
    fcsv.write_text(fichas.to_csv(index=False), encoding="utf-8-sig")
    return tmp, fcsv


BLOQUES = [
    {"bloque": "AZUL", "linea": "AFIRMATIVO", "desvio": 0.20},
    {"bloque": "ROJO", "linea": "NEGATIVO", "desvio": 0.04},
]


def main():
    # --- componer ---
    chk(abs(E.componer(0.5, 0.4) - 0.20) < 1e-9, "componer = producto de los dos factores")
    chk(E.componer(1.0, 0.9) == 0.9, "componer con p_llega=1 devuelve p_mayoria")
    for bad in [(-0.1, 0.5), (0.5, 1.2)]:
        try:
            E.componer(*bad); chk(False, "componer rechaza fuera de [0,1]")
        except ValueError:
            chk(True, f"componer rechaza fuera de [0,1] {bad}")

    # --- roster nominal ---
    tmp = Path(tempfile.mkdtemp())
    pdir, fcsv = _armar_padron_y_fichas(tmp)
    lin, dev, det = E.roster_nominal("diputados", "2026-07-14", BLOQUES,
                                     padron_dir=pdir, disciplina_path=fcsv)
    chk(det["n"] == 5, "roster: entra el padrón VIGENTE (5 de 6; excluye mandato vencido)")
    filas = {f["legislador_id"]: f for f in det["filas"]}
    chk(filas["leg:1"]["desvio_de"] == "ficha_reciente" and abs(filas["leg:1"]["desvio"] - 0.30) < 1e-9,
        "escalera 1: usa tasa reciente si la muestra reciente alcanza")
    chk(filas["leg:2"]["desvio_de"] == "ficha_global" and abs(filas["leg:2"]["desvio"] - 0.08) < 1e-9,
        "escalera 2: reciente corta -> cae a la tasa global (no a la reciente ruidosa)")
    chk(filas["leg:3"]["desvio_de"] == "bloque" and abs(filas["leg:3"]["desvio"] - 0.20) < 1e-9,
        "escalera 3: camada sin ficha -> desvío promedio de SU bloque (única excepción)")
    chk(filas["leg:1"]["linea"] == "AFIRMATIVO" and filas["leg:4"]["linea"] == "NEGATIVO",
        "roster: cada legislador hereda la línea proyectada de su linaje")
    chk(filas["leg:5"]["linea"] == "NO_ACOMPANA" and det["sin_linea_proyectada"] == 1,
        "roster: linaje sin línea proyectada entra NO_ACOMPANA y queda trazado")
    chk(len(lin) == len(dev) == det["n"], "roster: arrays alineados con el detalle")
    chk(det["ficha_reciente"] == 2 and det["ficha_global"] == 1 and det["fallback_bloque"] == 2,
        "roster: conteo por fuente de desvío correcto (trazabilidad)")

    # línea inválida en el proyector -> error específico
    try:
        E.roster_nominal("diputados", "2026-07-14",
                         [{"bloque": "AZUL", "linea": "SI", "desvio": 0.1}],
                         padron_dir=pdir, disciplina_path=fcsv)
        chk(False, "roster rechaza línea inválida")
    except ValueError:
        chk(True, "roster rechaza línea inválida del proyector")
    # fecha fuera de todo mandato -> error claro
    try:
        E.roster_nominal("diputados", "1990-01-01", BLOQUES,
                         padron_dir=pdir, disciplina_path=fcsv)
        chk(False, "roster falla si no hay mandatos vigentes")
    except ValueError:
        chk(True, "roster falla claro si no hay mandatos vigentes a la fecha")

    # --- nowcast sobre roster nominal: mayorías claras ---
    dummy = Path("/no/existe")
    lin_si = np.array(["AFIRMATIVO"] * 200 + ["NEGATIVO"] * 57)
    lin_no = np.array(["NEGATIVO"] * 200 + ["AFIRMATIVO"] * 57)
    dev_chico = np.full(257, 0.02)
    a_favor = E.nowcast_proyecto("P1", lin_si, dev_chico, "SIMPLE", "diputados",
                                 dummy, p_llega=0.5)
    en_contra = E.nowcast_proyecto("P2", lin_no, dev_chico, "SIMPLE", "diputados",
                                   dummy, p_llega=0.5)
    chk(a_favor["p_mayoria_recinto"] > 0.95, "roster holgado a favor -> P(mayoría) ~1")
    chk(en_contra["p_mayoria_recinto"] < 0.05, "roster en contra -> P(mayoría) ~0")
    chk(abs(a_favor["p_aprobacion"] - a_favor["p_llega_recinto"] * a_favor["p_mayoria_recinto"]) < 0.02,
        "p_aprobacion = p_llega × p_mayoría")
    chk(a_favor["p_aprobacion"] <= a_favor["p_llega_recinto"] + 1e-9,
        "el embudo es techo: P(aprobación) <= P(llega al recinto)")

    # --- incertidumbre irreducible: P(mayoría) nunca 0%/100% (pedido de Valle) ---
    goleada = np.array(["AFIRMATIVO"] * 257)          # todos leales, colchón enorme
    dev_cero = np.zeros(257)                            # desvío 0: sin piso serían locks
    g = E.nowcast_proyecto("PG", goleada, dev_cero, "SIMPLE", "diputados", dummy, p_llega=1.0)
    chk(g["p_mayoria_recinto"] <= 0.99 + 1e-9,
        "goleada total NO da 100%: se clampa a 99% (riesgo sistémico)")
    chk(g["p_mayoria_recinto"] >= 0.99 - 1e-9,
        "y queda EN el techo 0,99 (no menos: es una goleada)")
    derrota = np.array(["NEGATIVO"] * 257)
    d = E.nowcast_proyecto("PD", derrota, dev_cero, "SIMPLE", "diputados", dummy, p_llega=1.0)
    chk(d["p_mayoria_recinto"] >= 0.01 - 1e-9, "derrota total NO da 0%: piso 1%")
    # apagar los topes (=0) recupera el comportamiento crudo (para el backtest del agregador)
    crudo = E.nowcast_proyecto("PC", goleada, dev_cero, "SIMPLE", "diputados", dummy,
                               p_llega=1.0, desvio_min=0.0, p_incertidumbre=0.0)
    chk(crudo["p_mayoria_recinto"] >= 0.999, "con topes en 0, la goleada vuelve a ~1 (crudo)")

    # --- el desvío individual MUEVE el resultado (las bisagras pesan) ---
    lin_justa = np.array(["AFIRMATIVO"] * 130 + ["NEGATIVO"] * 127)
    disciplinados = E.nowcast_proyecto("P5", lin_justa, np.full(257, 0.01),
                                       "SIMPLE", "diputados", dummy, p_llega=1.0)
    dev_bisagra = np.full(257, 0.01)
    dev_bisagra[:20] = 0.45  # 20 afirmativos poco confiables
    con_bisagras = E.nowcast_proyecto("P6", lin_justa, dev_bisagra,
                                      "SIMPLE", "diputados", dummy, p_llega=1.0)
    chk(con_bisagras["p_mayoria_recinto"] < disciplinados["p_mayoria_recinto"],
        "20 bisagras en una votación justa BAJAN P(mayoría): el individuo pesa")

    # --- monotonía en el embudo ---
    bajo = E.nowcast_proyecto("P3", lin_si, dev_chico, "SIMPLE", "diputados", dummy, p_llega=0.10)
    alto = E.nowcast_proyecto("P4", lin_si, dev_chico, "SIMPLE", "diputados", dummy, p_llega=0.80)
    chk(alto["p_aprobacion"] > bajo["p_aprobacion"], "más P(llega) -> más P(aprobación)")

    # --- banda de votos presente y ordenada ---
    b = a_favor["afirmativos_banda_5_95"]
    chk(b[0] <= a_favor["afirmativos_medio"] <= b[1], "banda 5-95 contiene la media")

    # --- error claro si no hay p_llega por ningún lado ---
    try:
        E.nowcast_proyecto("PX", lin_si, dev_chico, "SIMPLE", "diputados", dummy)
        chk(False, "sin p_llega debe fallar")
    except ValueError:
        chk(True, "falla claro si no hay p_llega (ni embudo ni override)")

    # --- roster PREFIERE la columna de CONDUCTA (URGENTE 1, 2026-08-13) ---
    tmpc = Path(tempfile.mkdtemp())
    padc = pd.DataFrame([
        {"legislador": "Ausente", "legislador_id": "leg:A", "bloque_linaje": "AZUL",
         "desde": "2023-12-10", "hasta": "2027-12-09"},
    ])
    (tmpc / "padron_diputados.csv").write_text(padc.to_csv(index=False), encoding="utf-8-sig")
    # ausente crónico: desvío MEZCLADO alto (0.80) pero desvío de CONDUCTA bajo (0.05).
    # El roster debe usar 0.05 (cuando vota, vota con el bloque; no es bisagra).
    fc = pd.DataFrame([
        {"legislador_id": "leg:A", "n_votos": 500, "n_reciente": 60, "n_presente": 90,
         "tasa_desvio": 0.80, "tasa_desvio_reciente": 0.80,
         "tasa_desvio_conducta": 0.05, "tasa_desvio_reciente_conducta": 0.05}])
    fcc = tmpc / "disciplina_individual.csv"
    fcc.write_text(fc.to_csv(index=False), encoding="utf-8-sig")
    _, _, dc = E.roster_nominal("diputados", "2026-07-14", BLOQUES, padron_dir=tmpc, disciplina_path=fcc)
    fA = {f["legislador_id"]: f for f in dc["filas"]}["leg:A"]
    chk(abs(fA["desvio"] - 0.05) < 1e-9,
        "roster PREFIERE tasa_desvio_reciente_conducta (0.05) sobre la mezclada (0.80)")

    # --- fallback: ficha VIEJA sin columnas de conducta -> usa la mezclada (compat) ---
    fv = pd.DataFrame([
        {"legislador_id": "leg:A", "n_votos": 500, "n_reciente": 60,
         "tasa_desvio": 0.80, "tasa_desvio_reciente": 0.30}])
    fcv = tmpc / "disciplina_vieja.csv"
    fcv.write_text(fv.to_csv(index=False), encoding="utf-8-sig")
    _, _, dv2 = E.roster_nominal("diputados", "2026-07-14", BLOQUES, padron_dir=tmpc, disciplina_path=fcv)
    fA2 = {f["legislador_id"]: f for f in dv2["filas"]}["leg:A"]
    chk(abs(fA2["desvio"] - 0.30) < 1e-9,
        "fallback: sin columnas de conducta usa la mezclada (0.30) — compat")

    # --- conducta faltante (NaN) no rompe y cae a la mezclada (guarda pd.isna) ---
    fn = pd.DataFrame([
        {"legislador_id": "leg:A", "n_votos": 500, "n_reciente": 60, "n_presente": 90,
         "tasa_desvio": 0.80, "tasa_desvio_reciente": 0.30,
         "tasa_desvio_conducta": np.nan, "tasa_desvio_reciente_conducta": np.nan}])
    fcn = tmpc / "disciplina_nan.csv"
    fcn.write_text(fn.to_csv(index=False), encoding="utf-8-sig")
    _, _, dn = E.roster_nominal("diputados", "2026-07-14", BLOQUES, padron_dir=tmpc, disciplina_path=fcn)
    fA3 = {f["legislador_id"]: f for f in dn["filas"]}["leg:A"]
    chk(abs(fA3["desvio"] - 0.30) < 1e-9,
        "conducta NaN: guarda pd.isna no rompe y cae a la mezclada")

    # --- lo eliminado quedó eliminado ---
    chk(not hasattr(E, "_expandir_roster"), "el atajo _expandir_roster ya no existe")
    chk(not hasattr(E, "_demo"), "la demo hardcodeada ya no existe")

    # --- resolver denominador -> proyecto_id interno ---
    tmp2 = Path(tempfile.mkdtemp()) / "expedientes.parquet"
    pd.DataFrame({
        "proyecto_id": ["HCDN283397", "HCDN990001"],
        "exp_diputados": ["1167-D-2025", "None"],
        "exp_senado": ["None", "45-S-2024"],
    }).to_parquet(tmp2)
    chk(E._resolver_proyecto_id("1167-D-2025", tmp2) == "HCDN283397",
        "resolver: denominador Diputados -> id interno")
    chk(E._resolver_proyecto_id("45-S-2024", tmp2) == "HCDN990001",
        "resolver: denominador Senado -> id interno")
    chk(E._resolver_proyecto_id(" 1167 - D - 2025 ", tmp2) == "HCDN283397",
        "resolver: tolera espacios y mayúsculas en el denominador")
    chk(E._resolver_proyecto_id("HCDN283397", tmp2) == "HCDN283397",
        "resolver: un id interno pasa sin tocar")
    chk(E._resolver_proyecto_id("9999-D-2025", tmp2) == "9999-D-2025",
        "resolver: denominador inexistente vuelve tal cual (el embudo avisará)")

    print(f"\n{OK} chequeos OK")


if __name__ == "__main__":
    main()
