"""datos/expedientes - VOTACIÓN POR ARTÍCULO (contrato B1, PARTE B del prompt
multietiqueta/disgregación, coordinacion/PROMPT-MULTIETIQUETA.md).

PROBLEMA QUE RESUELVE
----------------------
`enlace_senado.elegir_votacion` reduce todas las votaciones de un proyecto en
una cámara a UNA SOLA: la decisiva (la de "EN GENERAL", o la primera si ninguna
lo dice). Eso es correcto para lo que `elegir_votacion` hace (alimentar
`cadena_camaras.parquet`, que el motor usa para P(revisora | aprobó origen)) —
NO SE TOCA ESE COMPORTAMIENTO ACÁ.

Pero las votaciones DESCARTADAS —la votación en particular, artículo por
artículo, que sigue a la general— no son ruido: son el único insumo que
tenemos, SIN PARSEAR UNA PALABRA DE ARTICULADO, para medir qué sobrevive de
una ley y qué se cae en el recinto. Ley Bases "se aprobó" habiendo perdido
buena parte de su articulado en la primera ronda (06-02-2024) antes de
retirarse y volver recortada (30-04-2024); el modelo de hoy no lo ve.

Este módulo AGREGA un contrato nuevo con UNA FILA POR ACTA (no una por
proyecto): quién es la decisiva, cuáles son "en particular", y el resultado de
cada una. No reemplaza `cadena_camaras.parquet` ni cambia `elegir_votacion`.

CONSUME (contrato de este mismo módulo, sin tocar su código):
  datos/expedientes/data/clean/acta_expediente_todas.parquet
    (acta_id, camara, proyecto_id, fecha, resultado, titulo)
PRODUCE (contrato nuevo, estable):
  datos/expedientes/data/clean/votacion_por_articulo.parquet
    proyecto_id, camara, acta_id, fecha, titulo, resultado, resultado_clase,
    es_decisiva, tipo_votacion, es_particular, titulo_num, capitulo_num,
    n_actas_grupo

  resultado_clase in {AFIRMATIVO, NEGATIVO, EMPATE, OTRO} — normaliza los
    9 valores crudos de `resultado` (mayúsculas/minúsculas/variantes con
    "- CANCELADA"/"- AUSENTE"/"- EMPATE" que trae la fuente).
  es_decisiva: True en la fila que `elegir_votacion` elegiría para esa
    (proyecto_id, camara) — idéntica función, importada, no reimplementada.
  tipo_votacion: el mismo vocabulario que ya usa `construir_cadena`
    (unica | general | primera | primera_particular), para la fila decisiva;
    None en las demás.
  es_particular: matchea `_RE_PARTICULAR` (mismo regex que `elegir_votacion`) —
    "en particular", artículos, incisos, capítulos, títulos.
  titulo_num, capitulo_num (B2, 2026-09-16): el numeral romano que el propio
    título del acta declara ("TITULO VIII. CAPITULO VIII. ARTS. 208 AL 214."),
    como TEXTO (no se convierten a entero: alcanza con agrupar por igualdad).
    None cuando el título no lo declara (la votación EN GENERAL no pertenece a
    ningún capítulo: es la ley entera). No hace falta bajar el PDF de la Orden
    del Día para esto — se probó que el PDF SÍ trae el articulado completo con
    sus encabezados de capítulo (útil para el NOMBRE del capítulo, no para
    agruparlo), pero la numeración ya está en el título de cada acta.
  n_actas_grupo: cuántas actas tiene el (proyecto_id, camara) en total —
    permite filtrar sin recomputar el groupby.

Sobre la granularidad: cada fila es UN VOTO REGISTRADO, que a veces cubre un
artículo y a veces un bloque ("ARTS. 24 AL 51") según cómo la cámara agrupó
la votación ese día. Este módulo NO reparte esos rangos en artículos
individuales — eso es B2 (agrupamiento en capítulos), que depende de tener el
TEXTO del articulado y queda para después.

QUÉ NO HACE (a propósito, ADR-0016 y "no reemplaces, agregá"):
  - No cambia `elegir_votacion` ni `cadena_camaras.parquet`.
  - No calcula P(sobrevive) ni ningún número publicado: es sólo el contrato
    de datos. La composición (simulación con shock común) es un consumidor
    futuro, detrás de bandera, que se decide aparte.

4 directivas: errores específicos, parsing defensivo, logging estructurado.
(No hay I/O de red: no hace falta backoff.)
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger("expedientes.votacion_por_articulo")

_RAIZ = Path(__file__).resolve().parents[3]
DEFAULT_ACTA_EXP = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "acta_expediente_todas.parquet"
OUT_DEFAULT = _RAIZ / "datos" / "expedientes" / "data" / "clean" / "votacion_por_articulo.parquet"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enlace_senado import elegir_votacion, _RE_PARTICULAR  # noqa: E402

# B2 (2026-09-16): a qué TÍTULO/CAPÍTULO pertenece un tramo, SIN parsear un solo
# PDF. Descubrimiento: el título del acta YA declara la posición del tramo en
# la ley — "TITULO VIII. CAPITULO VIII. ARTS. 208 AL 214." (Ley Bases, O.D. 7),
# "TÍTULO II, CAP. I ART. 5 INCISO E." (Ley Bases, O.D. 1: nota la coma y la
# abreviatura "CAP.", los dos formatos aparecen en la práctica). Verificado
# además que el PDF de la Orden del Día SÍ trae el articulado completo con sus
# encabezados de capítulo ("Capítulo II — Declaración de emergencia pública…",
# 141-1.pdf, 106.008 caracteres extraídos) — es la vía para el NOMBRE del
# capítulo si algún día hace falta; para la NUMERACIÓN, que es lo que agrupa,
# el título del acta alcanza y no hace falta bajar nada.
_RE_TITULO_NUM = re.compile(r"T[IÍ]TULO\s+([IVXLCDM]+)\b", re.I)
_RE_CAPITULO_NUM = re.compile(r"CAP(?:[IÍ]TULO)?\.?\s+([IVXLCDM]+)\b", re.I)


def extraer_titulo_capitulo(titulo: str) -> tuple[Optional[str], Optional[str]]:
    """(título_num, capítulo_num) como numerales romanos EN TEXTO (no se
    convierten a entero: sólo hace falta agrupar por igualdad, no ordenar ni
    sumar, y un romano mal formado sigue sirviendo como clave de agrupamiento
    aunque no se pueda convertir). `None` en lo que el título no declara —
    "VOT. EN GRAL." no declara ninguno de los dos, y es lo esperable: la
    votación en general no pertenece a un capítulo, es la ley entera."""
    t = str(titulo or "")
    m_tit = _RE_TITULO_NUM.search(t)
    m_cap = _RE_CAPITULO_NUM.search(t)
    return (m_tit.group(1).upper() if m_tit else None,
            m_cap.group(1).upper() if m_cap else None)


def _resultado_clase(valor: object) -> str:
    """Normaliza los 9 valores crudos de `resultado` a 4 clases. Parsing
    defensivo: cualquier variante no reconocida (incluida vacía) cae en OTRO,
    nunca se adivina."""
    s = str(valor).strip().upper()
    if s.startswith("AFIRMATIV"):
        return "AFIRMATIVO"
    if s.startswith("NEGATIV"):
        return "NEGATIVO"
    if s == "EMPATE" or s.endswith("EMPATE"):
        return "EMPATE"
    return "OTRO"


def cargar_actas(acta_exp: Path = DEFAULT_ACTA_EXP) -> pd.DataFrame:
    """Lee acta_expediente_todas y devuelve sólo las actas con proyecto_id
    resuelto (sin eso no hay a qué proyecto atribuir el tramo)."""
    acta_exp = Path(acta_exp)
    if not acta_exp.exists():
        raise FileNotFoundError(f"falta contrato de expedientes: {acta_exp}")
    df = pd.read_parquet(acta_exp)
    need = {"acta_id", "camara", "proyecto_id", "fecha", "resultado", "titulo"}
    faltan = need - set(df.columns)
    if faltan:
        raise KeyError(f"acta_expediente_todas sin columnas {faltan}; hay {list(df.columns)}")
    df = df.dropna(subset=["proyecto_id"]).copy()
    if df.empty:
        raise ValueError("ninguna acta con proyecto_id resuelto")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df


def construir(actas: pd.DataFrame) -> pd.DataFrame:
    """Une, por (proyecto_id, camara), la fila DECISIVA (misma función que ya
    usa el motor) con el resto marcado como tal. No descarta nada."""
    need = {"acta_id", "camara", "proyecto_id", "fecha", "resultado", "titulo"}
    faltan = need - set(actas.columns)
    if faltan:
        raise KeyError(f"cargar_actas sin columnas {faltan}")

    filas = []
    for (pid, cam), sub in actas.groupby(["proyecto_id", "camara"], sort=False):
        n_grupo = len(sub)
        try:
            decisiva = elegir_votacion(sub)
        except (KeyError, ValueError) as e:
            logger.warning("proyecto=%s camara=%s: no pude elegir decisiva (%s); "
                           "marco todas es_decisiva=False", pid, cam, e)
            decisiva = None
        decisiva_acta = str(decisiva["acta_id"]) if decisiva is not None else None
        tipo_decisiva = decisiva.get("tipo_votacion") if decisiva is not None else None

        for _, r in sub.iterrows():
            aid = str(r["acta_id"])
            titulo = str(r.get("titulo") or "")
            es_dec = aid == decisiva_acta
            titulo_num, capitulo_num = extraer_titulo_capitulo(titulo)
            filas.append({
                "proyecto_id": pid,
                "camara": cam,
                "acta_id": aid,
                "fecha": r.get("fecha"),
                "titulo": titulo,
                "resultado": r.get("resultado"),
                "resultado_clase": _resultado_clase(r.get("resultado")),
                "es_decisiva": bool(es_dec),
                "tipo_votacion": tipo_decisiva if es_dec else None,
                "es_particular": bool(_RE_PARTICULAR.search(titulo)) if titulo else False,
                "titulo_num": titulo_num,
                "capitulo_num": capitulo_num,
                "n_actas_grupo": int(n_grupo),
            })
    out = pd.DataFrame(filas)
    if out.empty:
        raise ValueError("no se construyó ninguna fila (¿actas vacías?)")
    return out.sort_values(["proyecto_id", "camara", "fecha"]).reset_index(drop=True)


def correr(acta_exp: Path = DEFAULT_ACTA_EXP, out: Path = OUT_DEFAULT) -> pd.DataFrame:
    actas = cargar_actas(acta_exp)
    res = construir(actas)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out, index=False)
    n_proy_multi = res[res["n_actas_grupo"] > 1]["proyecto_id"].nunique()
    logger.info("votacion_por_articulo: %d filas, %d proyectos con >1 acta -> %s",
                len(res), n_proy_multi, out)
    return res


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Construye votacion_por_articulo.parquet "
                                            "(B1: no descarta las votaciones en particular).")
    p.add_argument("--acta-exp", default=str(DEFAULT_ACTA_EXP))
    p.add_argument("--out", default=str(OUT_DEFAULT))
    args = p.parse_args(argv)
    try:
        correr(Path(args.acta_exp), Path(args.out))
    except (FileNotFoundError, KeyError, ValueError) as e:
        logger.error("%s: %s", type(e).__name__, e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
