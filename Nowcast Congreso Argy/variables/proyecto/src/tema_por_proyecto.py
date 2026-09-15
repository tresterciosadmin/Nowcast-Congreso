"""variables/proyecto - TEMA POR PROYECTO: lectura, no clasificación (Parte A del
prompt multietiqueta, coordinacion/PROMPT-MULTIETIQUETA.md).

EL HALLAZGO QUE ESTO RESUELVE (medido 2026-09-15, ver ESTADO-DEL-PROYECTO.md)
------------------------------------------------------------------------------
`tema` en `nowcast_puertas.nowcast()` es un parámetro `--tema` MANUAL: nunca se
deriva de `proyecto_id`. No existe ningún enganche `proyecto_id -> tema` en la
ruta de producción, así que la rama de condicionamiento por tema no dispara en
NINGUNA corrida automatizada de hoy — sólo cuando un humano lo escribe a mano en
`casos/`. Cualquier regla de combinación de temas (unión, ponderada, ...) que se
construya en `variables/bloque` queda huérfana sin este módulo.

LO QUE ESTE MÓDULO **NO** ES: un clasificador nuevo. Ya existe uno completo y
probado, `variables/proyecto/src/agente_taxonomias.py`:
  - `clasificar_lote(db_path)` baja el PDF de cada proyecto y lo clasifica
    (multietiqueta, vía LLM), escribiendo en `proyecto_taxonomias`
    (`datos/proyectos/data/proyectos.db`) vía `persistir()`.
  - Ese contrato YA es multietiqueta (PK compuesta `(denominador, taxonomia_id)`)
    y YA respeta lo humano por sobre lo del agente.
  - **Hoy tiene 0 filas** — no porque falte código, sino porque nadie corrió
    `clasificar_lote` todavía (necesita `ANTHROPIC_API_KEY` + red; no disponibles
    en esta sesión). Es un pendiente OPERATIVO, no de diseño.

Este módulo es la mitad que SÍ se podía construir sin red: la LECTURA de
`proyecto_taxonomias`, resuelta contra el `proyecto_id` (HCDN) que usa el motor
— que es un identificador DISTINTO del `denominador` (NNNN-X-AAAA) que usa
`proyectos.db`/`docs/taxonomias`. Mezclar esos dos espacios de nombres sin un
cruce explícito es exactamente la trampa de "nombres en formatos distintos" que
ya costó un coeficiente con p=0,88 en este repo (ver CLAUDE.md).

EL CRUCE proyecto_id (HCDN) <-> denominador (NNNN-X-AAAA)
-----------------------------------------------------------
`datos/expedientes/data/clean/expedientes.parquet` ya trae ambos por fila:
`proyecto_id` y `exp_diputados` (que ES el denominador para todo proyecto con
huella en Diputados — verificado 2026-09-15: 114.365/114.365, 100%). Es
DIPUTADOS-CÉNTRICO a propósito (ver README de datos/expedientes): un proyecto
de origen Senado que nunca cruzó a Diputados no tiene fila acá, y por lo tanto
no resuelve `proyecto_id` — limitación documentada, no un bug de este módulo.

CONSUME (contratos de otros módulos; no edita su código):
  datos/proyectos/data/proyectos.db            tabla proyecto_taxonomias
  datos/expedientes/data/clean/expedientes.parquet   proyecto_id <-> exp_diputados
PRODUCE: nada nuevo — es sólo lectura. `temas_de_proyecto()` es la función que
  consume `nowcast_puertas.nowcast()` cuando `TEMA_AUTO=1` (bandera apagada por
  defecto).

4 directivas: errores específicos, parsing defensivo, logging estructurado.
(Sin red: no hace falta backoff.)
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger("proyecto.tema_por_proyecto")

_RAIZ = Path(__file__).resolve().parents[3]
DEFAULT_DB = _RAIZ / "datos" / "proyectos" / "data" / "proyectos.db"
DEFAULT_EXPEDIENTES = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "expedientes.parquet"

_AUX_PREFIX = "AUX"


def cargar_crosswalk(expedientes: Path = DEFAULT_EXPEDIENTES) -> dict:
    """{proyecto_id (HCDN) -> denominador} y su inversa, desde expedientes.parquet.
    Vacío (no rompe) si el contrato no está — degradación limpia, igual que
    `_bancas_padron` en variables/bloque."""
    expedientes = Path(expedientes)
    if not expedientes.exists():
        logger.warning("no está %s: sin cruce proyecto_id<->denominador", expedientes)
        return {"pid_a_denom": {}, "denom_a_pid": {}}
    df = pd.read_parquet(expedientes, columns=["proyecto_id", "exp_diputados"])
    df = df.dropna(subset=["proyecto_id", "exp_diputados"])
    pid_a_denom = dict(zip(df["proyecto_id"].astype(str), df["exp_diputados"].astype(str)))
    denom_a_pid = {v: k for k, v in pid_a_denom.items()}
    return {"pid_a_denom": pid_a_denom, "denom_a_pid": denom_a_pid}


def _resolver_denominador(proyecto_id: Optional[str], denominador: Optional[str],
                          cruce: dict) -> Optional[str]:
    if denominador:
        return str(denominador)
    if proyecto_id:
        d = cruce["pid_a_denom"].get(str(proyecto_id))
        if d is None:
            logger.info("proyecto_id=%s sin denominador cruzado (¿origen Senado sin "
                        "huella en Diputados?): sin tema automático", proyecto_id)
        return d
    return None


def taxonomias_de(denominador: str, db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Todas las filas de `proyecto_taxonomias` para un denominador, tal cual
    están (agente + humano). DataFrame vacío si no hay ninguna (no es error:
    puede no estar clasificado todavía)."""
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"falta la base de proyectos: {db_path}")
    con = sqlite3.connect(str(db_path))
    try:
        return pd.read_sql(
            "SELECT denominador, taxonomia_id, taxonomia, fuente, confianza, asignada_en "
            "FROM proyecto_taxonomias WHERE denominador=?",
            con, params=(str(denominador),))
    finally:
        con.close()


def temas_de_proyecto(proyecto_id: Optional[str] = None, denominador: Optional[str] = None,
                      db_path: Path = DEFAULT_DB, expedientes: Path = DEFAULT_EXPEDIENTES,
                      cruce: Optional[dict] = None) -> list[tuple[str, float]]:
    """La multietiqueta SUSTANTIVA (no AUX) de un proyecto, como
    `[(área, confianza), ...]`, ordenada por confianza descendente. Acepta
    `proyecto_id` (HCDN, el que usa el motor) o `denominador` (NNNN-X-AAAA, el
    de `proyectos.db`) — al menos uno de los dos. Lista vacía (no excepción) si
    el proyecto no tiene taxonomías cargadas todavía: es el caso NORMAL hoy
    (`clasificar_lote` no corrió), y el llamador debe degradar a incondicional,
    igual que hace `variables/bloque` cuando `tema=None`.

    Cuando hay VARIAS filas para el mismo taxonomia_id (agente + humano
    corregido a mano), gana la de fuente 'humano' — mismo criterio que
    `agente_taxonomias.persistir()` ya aplica al escribir."""
    if not proyecto_id and not denominador:
        raise ValueError("hace falta proyecto_id o denominador")
    cruce = cruce if cruce is not None else cargar_crosswalk(expedientes)
    denom = _resolver_denominador(proyecto_id, denominador, cruce)
    if not denom:
        return []
    try:
        df = taxonomias_de(denom, db_path)
    except FileNotFoundError as e:
        logger.warning("%s", e)
        return []
    if df.empty:
        return []
    # el humano gana: si un taxonomia_id tiene fila 'humano' Y 'agente', se queda con la humana
    df = df.sort_values("fuente", key=lambda s: s.eq("humano"), ascending=False)
    df = df.drop_duplicates("taxonomia_id", keep="first")
    df = df[~df["taxonomia_id"].astype(str).str.upper().str.startswith(_AUX_PREFIX)]
    if df.empty:
        return []
    df["area"] = df["taxonomia_id"].astype(str).str.split(".").str[0].str.upper()
    por_area = df.groupby("area")["confianza"].max()
    return sorted(((a, float(c)) for a, c in por_area.items()), key=lambda t: -t[1])


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Consulta la multietiqueta de un proyecto "
                                            "(sólo lectura; no clasifica).")
    p.add_argument("--proyecto-id", default=None, help="HCDN..., el que usa el motor")
    p.add_argument("--denominador", default=None, help="NNNN-X-AAAA, el de proyectos.db")
    args = p.parse_args(argv)
    try:
        temas = temas_de_proyecto(proyecto_id=args.proyecto_id, denominador=args.denominador)
    except ValueError as e:
        print(f"error: {e}")
        return 1
    print(json.dumps({"proyecto_id": args.proyecto_id, "denominador": args.denominador,
                      "temas": temas}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
