# -*- coding: utf-8 -*-
"""El dictamen entra POR LEGISLADOR (ADR-0016, S:III.A.2 de FORMULA-COMPLETA.md).

    logit(P_i^dict) = logit(P_i) + beta1*F_i + beta2*(1-d_i)*J_l

      F_i       firmo el propio legislador el dictamen (favorable: mayoria/unico)
      J_l       firmo el jefe de SU bloque (persona concreta, vigente a la fecha)
      (1-d_i)   su lealtad: cuanto le pesa lo que hizo su jefe (d_i = su desvio)

NO SE REIMPLEMENTA el cruce firmante<->jefe: se REUSA
`estimar_beta_dictamen.firmas_por_acta` / `jefes`, las mismas funciones con las
que se estimaron los coeficientes (M6_sin_caracter en
`modelo/ensemble/outputs/beta_dictamen.json`). Calcularlo distinto aca que en la
estimacion seria estimar con una definicion y aplicar con otra.

POR QUE SIN EL CARACTER DEL DICTAMEN (14-09-2026, cambio respecto de la
formulacion original de ADR-0016). La primera version de este modulo (M5)
agregaba `+ delta(caracter)` -- UNICO/DISPUTADO/mayoria/solo_minoria -- y
prendida medida sobre proyectos reales hacia colapsar P (0,98 -> 0,01) en la
mayoria de los casos con dictamen no-unanime. Pedido de Franco: "miralo con mas
casos antes de decidir". Un backtest walk-forward (entrenar con el 70% de actas
MAS VIEJO, medir Brier en el 30% MAS NUEVO, nunca visto al ajustar --
`modelo/ensemble/src/validar_beta_dictamen_walkforward.py`) mostro que **el
caracter NO GENERALIZA**: empeora el Brier held-out (0,1725 -> 0,1793 total;
mayoria 0,1934 -> 0,2533). El termino estaba sobreajustando una particularidad
de la muestra de entrenamiento -- exactamente el tipo de "hallazgo" que
`verificar_regeneracion.py` pide sospechar. **F_i y lealtad_x_jefe SOLOS, sin
caracter, SI generalizan**: Brier held-out 0,1725 -> 0,1591 (skill 0,1929 ->
0,2672). Por eso M6 (sin caracter) es la formulacion de produccion desde hoy, y
NO M5. `puerta_a.delta_caracter` (el condicionante AGREGADO del carácter, item 9
de la fórmula) sigue en 0 e intacto: la evidencia de arriba es sobre ESTE
mecanismo, per-legislador, no dice nada sobre ese.

POR QUE SIN EL 'const' DEL MODELO. `logit(P_i) + b1 F_i + b2 lealtad_x_jefe`,
sin termino independiente: el offset (logit(P_i), coeficiente fijado en 1 en la
regresion) ya absorbe quien es cada legislador. El `const` que devuelve el GLM
es una recalibracion agregada del offset, no algo que el dictamen "agregue" --
sumarlo aplicaria un corrimiento parejo a CUALQUIER voto, tenga o no dictamen
leido. (Medido igual en el walk-forward: con const el held-out mejora un poco
mas -- Brier 0,1566 -- pero se prefiere la version sin const por lo anterior;
la diferencia entre las dos es chica y las dos generalizan.)

BANDERA APAGADA POR DEFECTO: BETA_DICTAMEN=1 (o pasar `activo=True`) para prender.
Con la bandera apagada, `ajuste(...)` siempre devuelve delta=0 y no toca nada.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger("beta_dictamen")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

# BANDERA APAGADA POR DEFECTO (revision metodologica 25-08, item B / ADR-0016).
# Coeficientes estimados y validados walk-forward (ver M6_sin_caracter en
# beta_dictamen.json); lo que falta es que Franco decida prenderla.
BETA_DICTAMEN = os.environ.get("BETA_DICTAMEN") == "1"

SALIDA = RAIZ / "modelo" / "ensemble" / "outputs" / "beta_dictamen.json"

TERMINOS = ("F_i", "lealtad_x_jefe")


@lru_cache(maxsize=1)
def _coeficientes() -> dict:
    """Coeficientes de M6_sin_caracter. {} si el archivo falta o el modelo no ajusto."""
    if not SALIDA.exists():
        logger.warning("no encontre %s: corre estimar_beta_dictamen.py. "
                       "El condicionante por legislador queda en 0.", SALIDA)
        return {}
    d = json.loads(SALIDA.read_text(encoding="utf-8"))
    m6 = d.get("M6_sin_caracter", {})
    if "error" in m6 or not m6.get("coef"):
        logger.warning("M6_sin_caracter no se pudo estimar (%s): el condicionante "
                       "por legislador queda en 0.", m6.get("error", "sin coef"))
        return {}
    faltan = [t for t in TERMINOS if t not in m6["coef"]]
    if faltan:
        logger.warning("a M6_sin_caracter le faltan terminos %s: el condicionante "
                       "por legislador queda en 0.", faltan)
        return {}
    return m6["coef"]


@lru_cache(maxsize=1)
def _datos_dictamen():
    """Carga pesada (firmas de las dos camaras + roster de jefes), UNA vez por proceso."""
    from estimar_beta_dictamen import firmas_por_acta, jefes as _jefes

    firmas, _mapa_acta, _mapa_nombre = firmas_por_acta(RAIZ)
    firmantes_por_proyecto = firmas.groupby("proyecto_id")["legislador_id"].apply(set).to_dict()
    j = _jefes(RAIZ)
    return firmas, firmantes_por_proyecto, j


def contexto_de(proyecto_id: str, camara: str, fecha) -> dict:
    """Contexto del dictamen de UN (proyecto_id, camara) a `fecha`: firmantes
    favorables (para F_i) y linajes cuyo jefe firmo (para J_l).

    F_i y J_l se resuelven por `proyecto_id` SOLO, sin filtrar por camara -- igual
    que en `estimar_beta_dictamen.construir_panel`: el roster de cada camara ya
    esta separado por legislador_id, asi que mezclar firmantes de las dos camaras
    bajo el mismo proyecto_id es inocuo, y hacerlo distinto aca rompería la
    correspondencia entre como se estimo el coeficiente y como se aplica.
    """
    pid = str(proyecto_id or "")
    if not pid:
        return {"firmantes": frozenset(), "lin_jefe": frozenset()}
    firmas, firmantes_por_proyecto, jefes_df = _datos_dictamen()
    firm = firmantes_por_proyecto.get(pid, set())

    import pandas as pd
    f = pd.to_datetime(fecha) if fecha is not None else pd.Timestamp.today()
    jefes_hoy = jefes_df[(jefes_df["camara"] == camara) & (jefes_df["desde"] <= f)
                         & (jefes_df["hasta"] >= f) & jefes_df["legislador_id"].notna()]
    ids_jefes_firmantes = set(jefes_hoy["legislador_id"]) & firm
    lin_de_este = firmas[firmas["proyecto_id"] == pid]
    lin_jefe = set(lin_de_este[lin_de_este["legislador_id"].isin(ids_jefes_firmantes)]
                  ["bloque_linaje"].astype(str))

    return {"firmantes": frozenset(firm), "lin_jefe": frozenset(lin_jefe)}


def delta_legislador(bloque_linaje: str, legislador_id: str, desvio: float,
                     contexto: dict, coef: dict | None = None) -> float:
    """El corrimiento en logit para ESTE legislador, dado el contexto de su proyecto.

    0.0 si no hay coeficientes o no hay contexto de dictamen (proyecto hipotetico,
    o sin dictamen leido): F_i y J_l son 0 por construccion cuando no hay contexto,
    asi que ni siquiera hace falta un caso aparte.
    """
    c = _coeficientes() if coef is None else coef
    if not c or contexto is None:
        return 0.0
    f_i = int(str(legislador_id) in contexto.get("firmantes", ()))
    j_l = int(str(bloque_linaje) in contexto.get("lin_jefe", ()))
    d_i = float(min(max(desvio, 0.0), 1.0))
    delta = (c.get("F_i", 0.0) * f_i
            + c.get("lealtad_x_jefe", 0.0) * (1.0 - d_i) * j_l)
    return float(delta)


def ajuste(p0: float, bloque_linaje: str, legislador_id: str, desvio: float,
          contexto: dict | None, *, activo: bool | None = None) -> float:
    """P(afirmativo) de este legislador, con el dictamen aplicado si la bandera
    esta prendida y hay contexto. Reusa `puerta_d.ajuste_paso_origen`: mismo
    mecanismo de logit que el resto del motor, no uno nuevo."""
    from puerta_d import ajuste_paso_origen

    prende = BETA_DICTAMEN if activo is None else activo
    if not prende or contexto is None:
        return float(p0)
    delta = delta_legislador(bloque_linaje, legislador_id, desvio, contexto)
    return ajuste_paso_origen(float(p0), delta, 1.0)
