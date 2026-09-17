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


# ────────────────────────────────────────────────────────────────────────────
# FASE 3 de PROMPT-GUARD-DE-ERA-POR-TEMA.md (2026-09-17): el fallback dejó de
# ser silencioso. ADR-0030 midió 0,0% de legisladores con dato condicionado
# real sobre Ley Bases y nadie se enteró hasta que alguien lo midió a
# propósito -- `devolver_stats=True` expone la fracción, y cada salida de la
# función lo loguea (una línea agregada, no una por fila).
# ────────────────────────────────────────────────────────────────────────────
print("\ndevolver_stats=True -- fallback TOTAL (0 áreas matchean) reporta 0/N, no lo esconde")
_, stats_cero = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("SALUD", 1.0)], ind_general=ind_general,
    hasta="2021-01-01", devolver_stats=True)
check(stats_cero["n_con_dato_real"] == 0, f"nadie tiene SALUD: {stats_cero}")
check(stats_cero["n_total"] == len(ind_general), f"n_total tiene que ser el universo completo: {stats_cero}")
check(stats_cero["frac_condicionado_real"] == 0.0, f"fracción tiene que ser exactamente 0: {stats_cero}")
print(f"  OK {stats_cero}")


print("\ndevolver_stats=True -- con dato real reporta la fracción correcta, no 0 ni 1 falsos")
_, stats_real = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_general,
    hasta="2021-01-01", devolver_stats=True)
check(stats_real["n_con_dato_real"] == 1, f"L1 tiene ECON: {stats_real}")
check(stats_real["frac_condicionado_real"] == 1.0, f"único legislador del universo, con dato: {stats_real}")
print(f"  OK {stats_real}")


print("\ndevolver_stats=True -- sin cond_por_acta también reporta stats (0/N), no sólo el dict")
res_sin_cond = N.alineacion_individual_por_area(
    votos, None, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_general,
    hasta="2021-01-01", devolver_stats=True)
check(isinstance(res_sin_cond, tuple) and len(res_sin_cond) == 2,
     f"tiene que devolver (dict, stats) igual que el resto de las salidas: {type(res_sin_cond)}")
check(res_sin_cond[1]["n_con_dato_real"] == 0, f"stats: {res_sin_cond[1]}")
print("  OK")


print("\ndevolver_stats=False (default): sigue devolviendo sólo el dict -- retrocompatible")
solo_dict = N.alineacion_individual_por_area(
    votos, cond, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_general,
    hasta="2021-01-01")
check(isinstance(solo_dict, dict) and not isinstance(solo_dict, tuple),
     f"sin devolver_stats no puede cambiar el contrato de siempre: {type(solo_dict)}")
print("  OK")


# ────────────────────────────────────────────────────────────────────────────
# "El caso Pichetto": un legislador con historial temático REAL de una era
# ANTERIOR, nowcasteado ya entrada la era NUEVA. FASE 1 (medir_estabilidad_
# record_por_tema.py, censo completo: correlación temática -0,12 a 0,05 según
# recambio, nunca cerca de 0,50) NO encontró señal para privilegiar ese
# historial viejo -- el diseño A (resetear en cada recambio) queda como
# estaba. Este test confirma que el comportamiento actual es ESE, a propósito
# -- no que "debería" conservar la historia.
# ────────────────────────────────────────────────────────────────────────────
print("\ncaso Pichetto -- historial ECON real ANTES del recambio no cuenta DESPUÉS (guard de era, diseño A vigente)")
filas_pichetto = [
    dict(acta_id=f"vieja{i}", fecha=pd.Timestamp("2019-01-01") + pd.Timedelta(days=i),
        camara="senado", bloque_linaje="OTRO / PROVINCIAL",
        legislador_id="PICHETTO", conducta="AFIRMATIVO")
    for i in range(20)  # 20 actas ECON, todas AFIRMATIVO, TODAS antes del recambio 2023-12-10
]
votos_p = pd.concat([votos.assign(camara="diputados"),  # L1 de arriba, para tener universo >1
                     pd.DataFrame(filas_pichetto)], ignore_index=True)
cond_p = pd.concat([cond, pd.DataFrame(
    [{"acta_id": f"vieja{i}", "todas_ids": "ECON.DEUDA"} for i in range(20)])], ignore_index=True)

ind_gen_post = N.alineacion_individual(votos_p, {}, None, hasta="2024-02-01", guard_era=True)
check(("senado", "PICHETTO") not in ind_gen_post or ind_gen_post[("senado", "PICHETTO")][3] == 0,
     f"con guard de era prendido, la ventana walk-forward arranca en 2023-12-10: "
     f"20 actas de 2019 no pueden aparecer como récord GENERAL: {ind_gen_post.get(('senado','PICHETTO'))}")

_, stats_pichetto = N.alineacion_individual_por_area(
    votos_p, cond_p, {}, None, areas_objetivo=[("ECON", 1.0)], ind_general=ind_gen_post,
    hasta="2024-02-01", guard_era=True, devolver_stats=True)
check(stats_pichetto["n_con_dato_real"] == 0 or ("senado", "PICHETTO") not in ind_gen_post,
     f"tampoco el récord POR TEMA ve esas 20 actas viejas -- diseño A, sin cambios: {stats_pichetto}")
print(f"  OK (confirma diseño A vigente): {stats_pichetto}")


print(f"\n{corridos - len(fallos)}/{corridos} OK")
if fallos:
    print(f"\n{len(fallos)} FALLAS:")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("todos los tests pasaron")
