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
