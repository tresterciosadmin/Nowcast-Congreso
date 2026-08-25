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
    # --- la formulacion v1 esta DADA DE BAJA (2026-08-22, ADR-0012) ---
    # No se borraron las funciones: levantan SystemExit con el motivo y a donde ir.
    # Este bloque falla si alguien las revive sin pasar por el ADR.
    for nombre in ('componer', '_p_llega_de_embudo', 'nowcast_proyecto',
                   'nowcast_auto', 'imprimir_tarjeta', 'main'):
        try:
            getattr(E, nombre)([]) if nombre == 'main' else getattr(E, nombre)()
            chk(False, f'{nombre} deberia estar dado de baja y no lo esta')
        except SystemExit as e:
            chk('ADR-0012' in str(e) and 'nowcast_puertas' in str(e),
                f'{nombre}: dado de baja, y el mensaje dice el ADR y a donde ir')
        except TypeError:
            chk(False, f'{nombre} sigue con la firma vieja: no se dio de baja')

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

    # --- la simulacion con guardas (lo que sobrevivio de la v1) ---
    # Estos chequeos eran de `nowcast_proyecto`, que se dio de baja. La cobertura NO
    # se pierde: se mudan a `simular_con_guardas`, que es donde vive ahora la cuenta
    # y lo que consumen la Puerta B y la Puerta D.
    lin_si = np.array(['AFIRMATIVO'] * 200 + ['NEGATIVO'] * 57)
    lin_no = np.array(['NEGATIVO'] * 200 + ['AFIRMATIVO'] * 57)
    dev_chico = np.full(257, 0.02)
    dev_cero = np.zeros(257)

    a_favor = E.simular_con_guardas(lin_si, dev_chico, 'SIMPLE', 'diputados', n_sims=300)
    en_contra = E.simular_con_guardas(lin_no, dev_chico, 'SIMPLE', 'diputados', n_sims=300)
    chk(a_favor['p_aprobacion'] > 0.9, 'roster holgado a favor -> P(mayoria) ~1')
    chk(en_contra['p_aprobacion'] < 0.1, 'roster en contra -> P(mayoria) ~0')

    g = E.simular_con_guardas(lin_si, dev_cero, 'SIMPLE', 'diputados', n_sims=300,
                              desvio_min=0.0)
    chk(g['p_aprobacion'] == 1.0 - E.P_INCERTIDUMBRE,
        'goleada total NO da 100%: se clampa a 99% (riesgo sistemico)')
    d = E.simular_con_guardas(lin_no, dev_cero, 'SIMPLE', 'diputados', n_sims=300,
                              desvio_min=0.0)
    chk(d['p_aprobacion'] == E.P_INCERTIDUMBRE, 'derrota total NO da 0%: piso 1%')
    crudo = E.simular_con_guardas(lin_si, dev_cero, 'SIMPLE', 'diputados', n_sims=300,
                                  desvio_min=0.0, p_incertidumbre=0.0)
    chk(crudo['p_aprobacion'] == 1.0, 'con los topes en 0, la goleada vuelve a 1 (crudo)')

    lin_justa = np.array(['AFIRMATIVO'] * 130 + ['NEGATIVO'] * 127)
    dev_bisagra = np.concatenate([np.full(20, 0.45), np.full(237, 0.01)])
    disciplinados = E.simular_con_guardas(lin_justa, np.full(257, 0.01), 'SIMPLE',
                                          'diputados', n_sims=600)
    con_bisagras = E.simular_con_guardas(lin_justa, dev_bisagra, 'SIMPLE', 'diputados',
                                         n_sims=600)
    chk(con_bisagras['p_aprobacion'] < disciplinados['p_aprobacion'],
        '20 bisagras en una votacion justa BAJAN P(mayoria): el individuo pesa')
    chk(a_favor['afirm_p5'] <= a_favor['afirm_medio'] <= a_favor['afirm_p95'],
        'banda 5-95 contiene la media')

    # (los chequeos de topes y bisagras se mudaron arriba, a simular_con_guardas)

    # --- lo que MURIO con la v1, y por que no hay reemplazo ---
    # 'mas P(llega) -> mas P(aprobacion)' y 'falla si no hay p_llega' probaban el
    # factor del embudo. Ese factor salio de la cadena (ADR-0012): medía la mortandad
    # en el cajon, que es agenda politica. No se reemplazan por otra cosa: se van.
    # El numero de hoy es CONDICIONAL a que las camaras voten, y eso se prueba en
    # modelo/ensemble/tests/test_nowcast_puertas.py.

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
