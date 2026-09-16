"""variables/proyecto - TEMA POR PROYECTO: lectura + clasificación por TÍTULO
(Parte A del prompt multietiqueta, coordinacion/PROMPT-MULTIETIQUETA.md).

EL HALLAZGO QUE ESTO RESUELVE (medido 2026-09-15, ver ESTADO-DEL-PROYECTO.md)
------------------------------------------------------------------------------
`tema` en `nowcast_puertas.nowcast()` es un parámetro `--tema` MANUAL: nunca se
deriva de `proyecto_id`. No existe ningún enganche `proyecto_id -> tema` en la
ruta de producción, así que la rama de condicionamiento por tema no dispara en
NINGUNA corrida automatizada de hoy — sólo cuando un humano lo escribe a mano en
`casos/`. Cualquier regla de combinación de temas (unión, ponderada, ...) que se
construya en `variables/bloque` queda huérfana sin este módulo.

⚠️ CORRECCIÓN 2026-09-16 (Franco: "revisá bien"). La entrada anterior de este
docstring decía "ANTHROPIC_API_KEY no disponible en esta sesión" — **estaba
mal**: el archivo `.env` de la raíz SÍ la tiene. El error fue de quien escribió
esa entrada: chequeó `os.environ.get(...)` directo en vez de cargar `.env` con
`python-dotenv`, que es como `agente_taxonomias.py` la carga siempre. El agente
SIEMPRE funcionó — lo que faltaba no era la key, era ejecutar el batch.

Ya existe un clasificador completo y probado,
`variables/proyecto/src/agente_taxonomias.py`:
  - `clasificar_lote(db_path)` baja el PDF de cada proyecto y lo clasifica
    (multietiqueta, vía LLM), escribiendo en `proyecto_taxonomias`
    (`datos/proyectos/data/proyectos.db`) vía `persistir()`.
  - Ese contrato YA es multietiqueta (PK compuesta `(denominador, taxonomia_id)`)
    y YA respeta lo humano por sobre lo del agente.

**Pero `clasificar_lote` tiene un cuello de botella real, medido el 16-09:
sólo 71 de 115.495 proyectos (0,06%) tienen `pdf_url` cargado** en
`proyectos.db` — la vía PDF no puede escalar más allá de eso hoy, no importa
cuánto presupuesto de API se le dé. En cambio `sumario` está al **100%**. Por
eso este módulo agrega `clasificar_por_titulo()`: el mismo patrón barato que
`tema_por_acta.py` ya usa para actas (clasificar por TEXTO, sin PDF), aplicado
a `proyectos.sumario`, escribiendo en la MISMA tabla `proyecto_taxonomias` con
`fuente='agente:texto'` (para distinguirla de `fuente='agente'`, la vía PDF).
No compite con `clasificar_lote`: la vía PDF sigue siendo la más profunda
cuando hay PDF; ésta es la que da COBERTURA.

La lectura (`temas_de_proyecto`) sigue siendo el enganche que
`nowcast_puertas.nowcast()` usa cuando `TEMA_AUTO=1` — resuelta contra el
`proyecto_id` (HCDN) que usa el motor, que es un identificador DISTINTO del
`denominador` (NNNN-X-AAAA) que usa `proyectos.db`/`docs/taxonomias`. Mezclar
esos dos espacios de nombres sin un cruce explícito es exactamente la trampa
de "nombres en formatos distintos" que ya costó un coeficiente con p=0,88 en
este repo (ver CLAUDE.md).

EL CRUCE proyecto_id (HCDN) <-> denominador (NNNN-X-AAAA)
-----------------------------------------------------------
`datos/expedientes/data/clean/expedientes.parquet` ya trae ambos por fila:
`proyecto_id` y `exp_diputados` (que ES el denominador para todo proyecto con
huella en Diputados — verificado 2026-09-15: 114.365/114.365, 100%). Es
DIPUTADOS-CÉNTRICO a propósito (ver README de datos/expedientes): un proyecto
de origen Senado que nunca cruzó a Diputados no tiene fila acá, y por lo tanto
no resuelve `proyecto_id` — limitación documentada, no un bug de este módulo.

CONSUME (contratos de otros módulos; no edita su código):
  datos/proyectos/data/proyectos.db            tabla proyectos (sumario) + proyecto_taxonomias
  datos/expedientes/data/clean/expedientes.parquet   proyecto_id <-> exp_diputados
  variables/proyecto/src/agente_taxonomias.clasificar_texto + persistir (reusados, no reimplementados)
PRODUCE: filas nuevas en `proyecto_taxonomias` (fuente='agente:texto'), vía
  `clasificar_por_titulo()`. `temas_de_proyecto()` es la LECTURA que consume
  `nowcast_puertas.nowcast()` cuando `TEMA_AUTO=1` (bandera apagada por defecto).

CLI:
  # clasifica los proyectos VOTADOS (universo acotado y de alto valor: son los
  # únicos con proyecto_id resuelto, y son el insumo real de TEMA_AUTO y de
  # cualquier backtest de multietiqueta):
  python tema_por_proyecto.py clasificar --solo-votados --limite 500
  # o una lista propia de denominadores:
  python tema_por_proyecto.py clasificar --denominadores 100-D-2024,200-S-2023
  # consulta sin clasificar:
  python tema_por_proyecto.py consultar --proyecto-id HCDN272347

4 directivas: errores específicos, parsing defensivo, logging estructurado.
(La llamada al LLM está en `agente_taxonomias`, que ya trae su propio backoff;
acá no se reimplementa.)
"""
from __future__ import annotations

import logging
import sqlite3
import sys
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
    el proyecto no tiene taxonomías cargadas todavía (la cobertura real, 16-09,
    es el universo VOTADO — ver `clasificar_por_titulo`; el resto sigue vacío),
    y el llamador debe degradar a incondicional, igual que hace
    `variables/bloque` cuando `tema=None`.

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


# --------------------------------------------------------------------------- #
# Clasificación por TÍTULO (sumario) — el que da COBERTURA (16-09-2026)       #
# --------------------------------------------------------------------------- #
def denominadores_votados(db_path: Path = DEFAULT_DB,
                          acta_exp: Optional[Path] = None) -> list[str]:
    """El universo de proyectos que alguna vez llegaron a una VOTACIÓN (tienen
    `proyecto_id` resuelto en `acta_expediente_todas.parquet`), cruzado a
    denominador. Acotado y de alto valor a propósito: son los únicos proyectos
    para los que `TEMA_AUTO` puede llegar a servir HOY (necesita el cruce
    proyecto_id<->denominador, que sólo existe para éstos) y son el insumo real
    para validar multietiqueta contra votos reales — no es una muestra al azar
    del universo de 115.495, es el subconjunto que efectivamente importa."""
    p = Path(acta_exp) if acta_exp else (
        _RAIZ / "datos" / "expedientes" / "data" / "clean" / "acta_expediente_todas.parquet")
    if not p.exists():
        raise FileNotFoundError(f"falta {p}")
    ae = pd.read_parquet(p, columns=["proyecto_id"]).dropna(subset=["proyecto_id"])
    cruce = cargar_crosswalk()
    denoms = {cruce["pid_a_denom"][pid] for pid in ae["proyecto_id"].astype(str)
             if pid in cruce["pid_a_denom"]}
    return sorted(denoms)


def denominadores_desde(fecha: str, db_path: Path = DEFAULT_DB, sin_clasificar: bool = True) -> list[str]:
    """El universo de proyectos con `fecha_ingreso >= fecha` — proyectos
    RECIENTES/en trámite, que es justo el que más necesita el nowcast
    (`denominadores_votados` es el opuesto: ya se votaron, es el pasado).
    `sin_clasificar=True` (default) excluye los que ya tienen alguna fila en
    `proyecto_taxonomias` — mismo criterio de idempotencia que
    `clasificar_por_titulo(solo_faltantes=True)`, para no pedir un cálculo que
    esa función va a saltear igual."""
    con = sqlite3.connect(str(db_path))
    try:
        q = "SELECT denominador FROM proyectos WHERE fecha_ingreso >= ?"
        if sin_clasificar:
            q += " AND NOT EXISTS (SELECT 1 FROM proyecto_taxonomias t WHERE t.denominador = proyectos.denominador)"
        filas = con.execute(q, (fecha,)).fetchall()
    finally:
        con.close()
    return sorted({r[0] for r in filas if r[0]})


def clasificar_por_titulo(db_path: Path = DEFAULT_DB, denominadores: Optional[list[str]] = None,
                          limite: Optional[int] = None, solo_faltantes: bool = True,
                          clasificar=None, checkpoint_cada: int = 25) -> dict:
    """Clasifica cada proyecto por su `sumario` (mismo patrón barato que
    `tema_por_acta.py` usa para actas: sin PDF, sin visión) y persiste en
    `proyecto_taxonomias` con `fuente='agente:texto'`, reusando
    `agente_taxonomias.clasificar_texto` + `persistir` — no reimplementa el
    prompt ni la validación contra el vocabulario.

    `denominadores`: la lista a clasificar. `None` = TODOS los de `proyectos`
    (115K+, no recomendado sin acotar antes con `--limite` o con
    `denominadores_votados()`). `solo_faltantes=True` (default) saltea los que
    ya tienen alguna fila `fuente LIKE 'agente%'` (idempotente, mismo criterio
    que `_ya_clasificado_por_agente`, pero sin filtrar por vía).

    `clasificar` se inyecta en tests; por defecto usa el agente real (API key)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import agente_taxonomias as AT  # type: ignore  # noqa: E402

    if clasificar is None:
        clasificar = lambda texto: AT.clasificar_texto(texto)  # noqa: E731

    con = sqlite3.connect(str(db_path))
    try:
        if denominadores is None:
            filas = con.execute(
                "SELECT denominador, sumario FROM proyectos "
                "WHERE sumario IS NOT NULL AND TRIM(sumario) <> '' "
                "ORDER BY fecha_ingreso DESC").fetchall()
        else:
            qs = ",".join("?" * len(denominadores))
            filas = con.execute(
                f"SELECT denominador, sumario FROM proyectos WHERE denominador IN ({qs})",
                list(denominadores)).fetchall()
        ya_clasificados = set()
        if solo_faltantes:
            ya_clasificados = {r[0] for r in con.execute(
                "SELECT DISTINCT denominador FROM proyecto_taxonomias "
                "WHERE fuente LIKE 'agente%'").fetchall()}
    finally:
        con.close()

    resumen = {"total": len(filas), "clasificados": 0, "guardados_tax": 0,
              "saltados_ya": 0, "sin_sumario": 0, "errores": 0}
    hechos = 0
    for denom, sumario in filas:
        if limite is not None and hechos >= limite:
            break
        if solo_faltantes and denom in ya_clasificados:
            resumen["saltados_ya"] += 1
            continue
        texto = str(sumario or "").strip()
        if len(texto) < 8:
            resumen["sin_sumario"] += 1
            hechos += 1
            continue
        try:
            res = clasificar(texto)
            res.denominador = denom
            if not res.clasificado:
                resumen["errores"] += 1
                logger.warning("%s: no clasificado (%s)", denom, res.comentario)
                hechos += 1
                continue
            n = AT.persistir(db_path, denom, res, fuente="agente:texto")
            resumen["clasificados"] += 1
            resumen["guardados_tax"] += n
            if resumen["clasificados"] % checkpoint_cada == 0:
                logger.info("  %d/%d clasificados (último: %s -> %s)",
                           resumen["clasificados"], min(len(filas), limite or len(filas)),
                           denom, [a.taxonomia_id for a in res.asignaciones])
        except Exception as e:  # resiliencia: un proyecto roto no corta el lote
            resumen["errores"] += 1
            logger.error("%s: error al clasificar (%s): %s", denom, type(e).__name__, e)
        hechos += 1
    logger.info("clasificar_por_titulo: %s", resumen)
    return resumen


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import json
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Multietiqueta por proyecto: consulta o clasifica.")
    sub = p.add_subparsers(dest="accion", required=True)

    pc = sub.add_parser("consultar", help="sólo lectura, no clasifica")
    pc.add_argument("--proyecto-id", default=None, help="HCDN..., el que usa el motor")
    pc.add_argument("--denominador", default=None, help="NNNN-X-AAAA, el de proyectos.db")

    pcl = sub.add_parser("clasificar", help="clasifica por título (sumario), sin PDF")
    pcl.add_argument("--solo-votados", action="store_true",
                     help="acota a denominadores_votados() en vez de TODOS los proyectos")
    pcl.add_argument("--desde-fecha", default=None,
                     help="acota a proyectos con fecha_ingreso >= esta fecha (AAAA-MM-DD), "
                          "vía denominadores_desde() -- el universo RECIENTE/en trámite")
    pcl.add_argument("--denominadores", default=None,
                     help="lista separada por comas; si no se pasa, usa --solo-votados/"
                          "--desde-fecha o TODOS")
    pcl.add_argument("--limite", type=int, default=None)
    pcl.add_argument("--todos", action="store_true", help="reclasificar aunque ya tengan")

    args = p.parse_args(argv)
    if args.accion == "consultar":
        try:
            temas = temas_de_proyecto(proyecto_id=args.proyecto_id, denominador=args.denominador)
        except ValueError as e:
            print(f"error: {e}")
            return 1
        print(json.dumps({"proyecto_id": args.proyecto_id, "denominador": args.denominador,
                          "temas": temas}, ensure_ascii=False, indent=2))
        return 0

    denoms = None
    if args.denominadores:
        denoms = [d.strip() for d in args.denominadores.split(",") if d.strip()]
    elif args.solo_votados:
        denoms = denominadores_votados()
        logger.info("universo votado: %d denominadores", len(denoms))
    elif args.desde_fecha:
        denoms = denominadores_desde(args.desde_fecha)
        logger.info("universo desde %s (sin clasificar todavía): %d denominadores",
                    args.desde_fecha, len(denoms))
    res = clasificar_por_titulo(denominadores=denoms, limite=args.limite,
                                solo_faltantes=not args.todos)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
