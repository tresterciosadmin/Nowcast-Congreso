"""Tests offline de `alineacion_individual_por_area` en
modelo/ensemble/src/nowcast_puertas.py — FASE 1 de PROMPT-MULTITEMA-V2.md
(URGENTE 8), validada sobre el censo completo en
`evaluacion/baseline/outputs/fase1_rec_por_tema_censo.json` (11,1% menos
Brier en el subconjunto que toca). Acá sólo la mecánica, con datos sintéticos.

    python modelo/ensemble/tests/test_record_por_tema.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import nowcast_puertas as N  # noqa: E402

fallos: list[str] = []
corridos = 0


def check(cond: bool, msg: str) -> None:
    global corridos
    corridos += 1
    if not cond:
        fallos.append(msg)
        print(f"  FALLA: {msg}")


def _escenario():
    """Un legislador (L1) con récord GENERAL mixto (mitad afirmativo), pero que
    en el área ECON vota siempre NEGATIVO y en TRAB vota siempre AFIRMATIVO —
    el caso que `rec_i^tema` existe para capturar y que el récord general por
    sí solo no puede ver."""
    filas = []
    base = pd.Timestamp("2020-01-01")
    k = 0
    for _ in range(10):  # 10 actas ECON, L1 vota NEGATIVO en todas
        filas.append(dict(acta_id=f"econ{k}", fecha=base + pd.Timedelta(days=k),
                          camara="diputados", bloque_linaje="X",
                          legislador_id="L1", conducta="NEGATIVO"))
        k += 1
    for _ in range(10):  # 10 actas TRAB, L1 vota AFIRMATIVO en todas
        filas.append(dict(acta_id=f"trab{k}", fecha=base + pd.Timedelta(days=k),
                          camara="diputados", bloque_linaje="X",
                          legislador_id="L1", conducta="AFIRMATIVO"))
        k += 1
    votos = pd.DataFrame(filas)
    cond = pd.DataFrame(
        [{"acta_id": f"econ{i}", "todas_ids": "ECON.DEUDA"} for i in range(10)] +
        [{"acta_id": f"trab{i}", "todas_ids": "TRAB.PREV"} for i in range(10, 20)])
    return votos, cond


print("récord por área difiere del general: ECON tira hacia abajo, TRAB hacia arriba")
votos, cond = _escenario()
ind_general = N.alineacion_individual(votos, {}, None, hasta="2021-01-01")
p_general, n_tot, presencia, n_emit = ind_general[("diputados", "L1")]
check(abs(p_general - 0.5) < 1e-9, f"récord general tiene que ser 0.5 (mitad y mitad): {p_general}")

ind_econ = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_general,
    hasta="2021-01-01")
p_econ = ind_econ[("diputados", "L1")][0]
check(p_econ < p_general, f"condicionado a ECON (vota siempre NEGATIVO ahí) tiene que "
                          f"bajar del general: {p_econ} vs {p_general}")

ind_trab = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("TRAB", 1.0)], ind_general=ind_general,
    hasta="2021-01-01")
p_trab = ind_trab[("diputados", "L1")][0]
check(p_trab > p_general, f"condicionado a TRAB (vota siempre AFIRMATIVO ahí) tiene que "
                          f"subir del general: {p_trab} vs {p_general}")
print(f"  OK general={p_general:.4f}  |  ECON={p_econ:.4f}  |  TRAB={p_trab:.4f}")


print("\nn_tot/presencia/n_emit NO cambian: sólo cambia qué récord se usa")
check(ind_econ[("diputados", "L1")][1:] == ind_general[("diputados", "L1")][1:],
      "n_votos/presencia/n_emit tienen que quedar IGUAL que en el récord general")
print("  OK")


print("\nmulti-área combina en LOGIT, no en probabilidad: el resultado cae ENTRE los dos")
ind_multi = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("ECON", 1.0), ("TRAB", 1.0)],
    ind_general=ind_general, hasta="2021-01-01")
p_multi = ind_multi[("diputados", "L1")][0]
check(p_econ < p_multi < p_trab, f"combinado tiene que caer entre ECON y TRAB: "
                                 f"{p_econ} < {p_multi} < {p_trab}")
print(f"  OK combinado(ECON,TRAB)={p_multi:.4f}")


print("\nárea objetivo sin ningún voto de esa persona: cae a su récord general")
ind_otra = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("SALUD", 1.0)], ind_general=ind_general,
    hasta="2021-01-01")
check(abs(ind_otra[("diputados", "L1")][0] - p_general) < 1e-9,
      "sin datos en el área objetivo, tiene que quedar igual al récord general")
print("  OK")


print("\nsin areas_objetivo: devuelve ind_general sin tocar")
ind_vacio = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[], ind_general=ind_general, hasta="2021-01-01")
check(ind_vacio == ind_general, "areas_objetivo vacío tiene que ser no-op")
print("  OK")


print("\nsin cond_por_acta (None): degrada a ind_general, no rompe")
ind_sin_cond = N.alineacion_individual_por_area(
    votos, None, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_general,
    hasta="2021-01-01")
check(ind_sin_cond == ind_general, "sin cond_por_acta tiene que degradar limpio")
print("  OK")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
