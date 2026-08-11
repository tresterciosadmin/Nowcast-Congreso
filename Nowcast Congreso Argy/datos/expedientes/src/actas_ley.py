"""Qué actas de votación corresponden a un PROYECTO DE LEY.

EL NORTE DEL MODELO (decisión de Valle, 2026-08-09)
---------------------------------------------------
Toda medición probabilística del tratamiento de un proyecto de ley se calcula
**sólo sobre actas de ley** — proyectos de ley y mensajes del Ejecutivo (que en
la práctica son proyectos de ley). Los tratados, pliegos, homenajes,
declaraciones y resoluciones se aprueban por consenso y NO informan la postura
política de ningún bloque: meterlos en el promedio lava justo la señal que
buscamos (el subconjunto DISPUTADO, donde están las bisagras).

Medido el 2026-08-09, share afirmativo del kirchnerismo en el Senado 2024-2026:
  - sobre TODO el temario: 55,8%  -> dirección sale AFIRMATIVO (degenerado)
  - sobre SÓLO leyes:      29,0%  -> NEGATIVO, que es la realidad
El mismo efecto en Diputados (53,7% -> 27,1%). No es un problema de una cámara:
es el filtro que faltaba, uniforme para las dos.

CÓMO SE SABE EL TIPO
    El enlace acta→expediente (`acta_expediente_senado.parquet`) da el
    `proyecto_id`, y el maestro `expedientes.parquet` da el `tipo`. Este módulo
    los cruza y devuelve el conjunto de `acta_id` que son de ley.

LÍMITE HONESTO
    El enlace cubre ~47% de las actas; de una acta NO enlazada no se sabe el
    tipo. `actas_de_ley` devuelve sólo las CONFIRMADAS de ley. Para el uso
    aguas abajo (calcular la postura de bloque) eso es lo correcto: mejor
    computar sobre 88 leyes seguras que ensuciar con 130 actas de tipo
    desconocido. La cobertura sube sola a medida que mejora el enlace.

Módulo: datos/expedientes · creado 2026-08-09 (reconstrucción por puertas)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

logger = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parents[3]
CLEAN = RAIZ / "datos" / "expedientes" / "data" / "clean"

# Un proyecto de ley, en la tipología de HCDN. MENSAJE = mensaje del Ejecutivo,
# que en la práctica es un proyecto de ley (decisión de Valle).
TIPOS_LEY = ("LEY", "MENSAJE Y PROYECTO DE LEY", "MENSAJE")


def actas_de_ley(
    tipos: Iterable[str] = TIPOS_LEY,
    enlace_path: Optional[Path] = None,
    expedientes_path: Optional[Path] = None,
) -> set[str]:
    """Conjunto de `acta_id` cuyo expediente es de ley (LEY/MENSAJE).

    Sólo las CONFIRMADAS: una acta sin enlace no entra (no se sabe su tipo).
    """
    enl_p = Path(enlace_path or CLEAN / "acta_expediente_senado.parquet")
    exp_p = Path(expedientes_path or CLEAN / "expedientes.parquet")
    for p, q in ((enl_p, "el enlace acta→expediente"), (exp_p, "el maestro de expedientes")):
        if not p.exists():
            raise FileNotFoundError(
                f"falta {q}: {p}\n  corré datos/expedientes/src/enlace_senado.py "
                "y datos/expedientes/src/ingesta_ckan.py")

    enl = pd.read_parquet(enl_p, columns=["acta_id", "proyecto_id"]).dropna(subset=["proyecto_id"])
    exp = pd.read_parquet(exp_p, columns=["proyecto_id", "tipo"])
    tset = {str(t).upper() for t in tipos}
    ley_pid = set(exp.loc[exp["tipo"].astype(str).str.upper().isin(tset), "proyecto_id"])
    actas = set(enl.loc[enl["proyecto_id"].isin(ley_pid), "acta_id"])
    logger.info("actas de ley: %d (de %d enlazadas)", len(actas), enl["acta_id"].nunique())
    return actas


def filtrar_votos_a_ley(votos: pd.DataFrame, actas_ley: Optional[set[str]] = None,
                        **kwargs) -> pd.DataFrame:
    """Deja en `votos` sólo las filas de actas de ley. Si `actas_ley` es None,
    lo calcula. No toca `votos` si el filtro dejaría el DataFrame vacío (se
    prefiere el comportamiento viejo antes que una serie sin datos: se avisa)."""
    if "acta_id" not in votos.columns:
        raise KeyError(f"votos sin columna 'acta_id'; hay {list(votos.columns)}")
    if actas_ley is None:
        actas_ley = actas_de_ley(**kwargs)
    filtrado = votos[votos["acta_id"].isin(actas_ley)]
    if filtrado.empty:
        logger.warning("el filtro de ley deja 0 votos; devuelvo los votos sin filtrar "
                       "(revisá la cobertura del enlace)")
        return votos
    logger.info("filtro de ley: %d de %d votos quedan (%.1f%%)",
                len(filtrado), len(votos), 100 * len(filtrado) / len(votos))
    return filtrado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = actas_de_ley()
    print(f"actas de ley (LEY/MENSAJE): {len(s)}")
