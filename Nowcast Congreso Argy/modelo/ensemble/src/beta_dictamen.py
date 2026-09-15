# -*- coding: utf-8 -*-
"""El dictamen entra POR LEGISLADOR (ADR-0016, S:III.A.2 de FORMULA-COMPLETA.md).

    logit(P_i^dict) = logit(P_i) + beta1*F_i + beta2*(1-d_i)*J_l + delta(caracter)

      F_i       firmo el propio legislador el dictamen (favorable: mayoria/unico)
      J_l       firmo el jefe de SU bloque (persona concreta, vigente a la fecha)
      (1-d_i)   su lealtad: cuanto le pesa lo que hizo su jefe (d_i = su desvio)
      caracter  UNICO (referencia) / DISPUTADO / mayoria / solo_minoria

NO SE REIMPLEMENTA el cruce firmante<->jefe<->caracter: se REUSA
`estimar_beta_dictamen.firmas_por_acta` / `jefes` / `_caracter_por_proyecto_camara`,
las mismas funciones con las que se estimaron los coeficientes (M5_produccion en
`modelo/ensemble/outputs/beta_dictamen.json`). Calcularlo distinto aca que en la
estimacion seria estimar con una definicion y aplicar con otra -- el bug clasico
de este repo (ver la nota de `definiciones.caracter_de_dictamen`).

POR QUE SIN W_OTROS. El M4 de `estimar_beta_dictamen.py` mostro que W_otros cambia
de signo al agregar el caracter (colinealidad, no efecto): "APROBADO 03-09
(Franco): beta_3 W_-l SALE y lo reemplaza el caracter" (FORMULA-COMPLETA S:III.A.2).
Este modulo usa M5_produccion, que se estima SIN W_otros.

POR QUE SIN EL 'const' DEL MODELO. La formulacion aprobada (FORMULA-COMPLETA,
"Formulacion resultante") es `logit(P_i) + b1 F_i + b2 lealtad_x_jefe + delta(caracter)`,
sin termino independiente: el offset (logit(P_i), coeficiente fijado en 1 en la
regresion) ya absorbe quien es cada legislador. El `const` que devuelve el GLM es
una recalibracion agregada del offset, no algo que el dictamen "agregue" -- sumarlo
aplicaria un corrimiento parejo a CUALQUIER voto, tenga o no dictamen leido, que es
exactamente lo que la Puerta A (delta_caracter en sin_dato) evita a proposito.

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
# Coeficientes ya estimados y medidos (ver M5_produccion en beta_dictamen.json); lo
# que falta es que Franco decida prenderla despues de ver cuanto mueve P.
BETA_DICTAMEN = os.environ.get("BETA_DICTAMEN") == "1"

SALIDA = RAIZ / "modelo" / "ensemble" / "outputs" / "beta_dictamen.json"

TERMINOS = ("F_i", "lealtad_x_jefe", "dict_DISPUTADO", "dict_mayoria", "dict_solo_minoria")


@lru_cache(maxsize=1)
def _coeficientes() -> dict:
    """Coeficientes de M5_produccion. {} si el archivo falta o el modelo no ajusto."""
    if not SALIDA.exists():
        logger.warning("no encontre %s: corre estimar_beta_dictamen.py. "
                       "El condicionante por legislador queda en 0.", SALIDA)
        return {}
    d = json.loads(SALIDA.read_text(encoding="utf-8"))
    m5 = d.get("M5_produccion", {})
    if "error" in m5 or not m5.get("coef"):
        logger.warning("M5_produccion no se pudo estimar (%s): el condicionante "
                       "por legislador queda en 0.", m5.get("error", "sin coef"))
        return {}
    faltan = [t for t in TERMINOS if t not in m5["coef"]]
    if faltan:
        logger.warning("a M5_produccion le faltan terminos %s: el condicionante "
                       "por legislador queda en 0.", faltan)
        return {}
    return m5["coef"]


@lru_cache(maxsize=1)
def _datos_dictamen():
    """Carga pesada (firmas de las dos camaras + roster de jefes), UNA vez por proceso."""
    from estimar_beta_dictamen import firmas_por_acta, jefes as _jefes

    firmas, _mapa_acta, _mapa_nombre = firmas_por_acta(RAIZ)
    firmantes_por_proyecto = firmas.groupby("proyecto_id")["legislador_id"].apply(set).to_dict()
    j = _jefes(RAIZ)
    return firmas, firmantes_por_proyecto, j


@lru_cache(maxsize=1)
def _tabla_caracter():
    """(proyecto_id, camara) -> caracter, la MISMA tabla que arma el estimador."""
    from estimar_beta_dictamen import _caracter_por_proyecto_camara, firmas_por_acta

    # firmas_por_acta ya filtro parseo_ok; se necesita el frame CRUDO (con
    # dictamen_clase de las dos camaras) para _caracter_por_proyecto_camara, asi
    # que se rearma igual que adentro de firmas_por_acta.
    import pandas as pd
    from rutas import EXPEDIENTES_FIRMAS as FIRMAS_DIP, EXPEDIENTES_FIRMAS_SENADO as FIRMAS_SEN
    partes = []
    for p in (Path(FIRMAS_DIP), Path(FIRMAS_SEN)):
        if p.exists():
            d = pd.read_parquet(p)
            partes.append(d[d["parseo_ok"]].copy())
    if not partes:
        return pd.DataFrame(columns=["proyecto_id", "camara", "caracter"])
    f = pd.concat(partes, ignore_index=True)
    return _caracter_por_proyecto_camara(f)


def contexto_de(proyecto_id: str, camara: str, fecha) -> dict:
    """Contexto del dictamen de UN (proyecto_id, camara) a `fecha`: firmantes
    favorables (para F_i), linajes cuyo jefe firmo (para J_l) y el caracter.

    F_i y J_l se resuelven por `proyecto_id` SOLO, sin filtrar por camara -- igual
    que en `estimar_beta_dictamen.construir_panel`: el roster de cada camara ya
    esta separado por legislador_id, asi que mezclar firmantes de las dos camaras
    bajo el mismo proyecto_id es inocuo, y hacerlo distinto aca rompería la
    correspondencia entre como se estimo el coeficiente y como se aplica.
    """
    import pandas as pd

    pid = str(proyecto_id or "")
    if not pid:
        return {"firmantes": frozenset(), "lin_jefe": frozenset(), "caracter": None}
    firmas, firmantes_por_proyecto, jefes_df = _datos_dictamen()
    firm = firmantes_por_proyecto.get(pid, set())

    f = pd.to_datetime(fecha) if fecha is not None else pd.Timestamp.today()
    jefes_hoy = jefes_df[(jefes_df["camara"] == camara) & (jefes_df["desde"] <= f)
                         & (jefes_df["hasta"] >= f) & jefes_df["legislador_id"].notna()]
    ids_jefes_firmantes = set(jefes_hoy["legislador_id"]) & firm
    lin_de_este = firmas[firmas["proyecto_id"] == pid]
    lin_jefe = set(lin_de_este[lin_de_este["legislador_id"].isin(ids_jefes_firmantes)]
                  ["bloque_linaje"].astype(str))

    car = _tabla_caracter()
    fila = car[(car["proyecto_id"] == pid) & (car["camara"] == camara)]
    caracter = fila["caracter"].iloc[0] if len(fila) else None
    return {"firmantes": frozenset(firm), "lin_jefe": frozenset(lin_jefe), "caracter": caracter}


def _delta_caracter(caracter: str | None, coef: dict) -> float:
    if caracter is None or caracter == "UNICO":
        return 0.0
    clave = {"DISPUTADO": "dict_DISPUTADO", "mayoria": "dict_mayoria",
             "solo_minoria": "dict_solo_minoria"}.get(caracter)
    return float(coef.get(clave, 0.0)) if clave else 0.0


def delta_legislador(bloque_linaje: str, legislador_id: str, desvio: float,
                     contexto: dict, coef: dict | None = None) -> float:
    """El corrimiento en logit para ESTE legislador, dado el contexto de su proyecto.

    0.0 si no hay coeficientes o no hay contexto de dictamen (proyecto hipotetico,
    o sin dictamen leido) -- el mismo fallback-por-encogimiento-a-cero que la
    Puerta A, salvo que aca no hace falta un factor de encogimiento: F_i y J_l ya
    son 0 cuando no hay dictamen, y eso alcanza.
    """
    c = _coeficientes() if coef is None else coef
    if not c or contexto is None:
        return 0.0
    f_i = int(str(legislador_id) in contexto.get("firmantes", ()))
    j_l = int(str(bloque_linaje) in contexto.get("lin_jefe", ()))
    d_i = float(min(max(desvio, 0.0), 1.0))
    delta = (c.get("F_i", 0.0) * f_i
            + c.get("lealtad_x_jefe", 0.0) * (1.0 - d_i) * j_l
            + _delta_caracter(contexto.get("caracter"), c))
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
