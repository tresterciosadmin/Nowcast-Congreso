# -*- coding: utf-8 -*-
"""D2.0 (auditoría 2026-09): la revisión de las actas de la canónica.

QUÉ FIJA (pre-registro de D2.0 en `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`):
  1. LA REGLA DE CLASIFICACIÓN (`clasificar_actas_d2_0.py`), commiteada con el pre-registro antes de cruzar ninguna
     clase con el resultado:
     - lee sólo título, fuente, cámara, fecha y acta_id: barajar `resultado`, `tipo_mayoria` y los conteos no cambia
       ninguna clase, y la función corre con un DataFrame que sólo trae esas columnas;
     - casos sintéticos de cada regla (el orden, la cola «OBSERVACIONES», la marca del Senado, los títulos repetidos,
       el artículo de otra norma);
     - los conteos por clase y subtipo sobre la canónica de la medición (sha256/16 `fda52f44d2f51240`). Si la
       canónica cambió, el ancla no aplica y se dice (no falla: la medición quedó fijada a esa canónica).
  2. (cuando exista) la validación con la muestra etiquetada, la revisión de las actas y la relectura de C2 y D2,
     recalculadas desde lo que viaja por git.

    python evaluacion/baseline/tests/test_d2_0_actas.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "evaluacion" / "baseline" / "src"))
import clasificar_actas_d2_0 as C  # noqa: E402

FALLOS: list[str] = []
SHA_CANONICA = "fda52f44d2f51240"
# La regla congelada el 2026-10-05, antes de cruzarla con el resultado.
ANCLA_CLASES = {"GENERAL": 3223, "PARTICULAR": 1803, "MOCION": 425, "OTRA": 547}
ANCLA_SUBTIPOS = {
    "general": 812, "general_y_particular": 1570, "senado_tag_general": 30, "senado_votacion_unica": 332,
    "unica_sin_marca": 479, "procedimiento": 425, "acuerdo_pliego": 140, "conjunto": 162, "decreto": 67,
    "insistencia": 48, "interno": 17, "juicio_desafuero": 24, "repetida_sin_marca": 55, "resolucion_declaracion": 29,
    "sin_titulo": 5, "particular": 1792, "senado_particular_tras_general": 11}


def check(cond: bool, msg: str) -> None:
    print(("  ok    " if cond else "  FALLA ") + msg)
    if not cond:
        FALLOS.append(msg)


def _sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def sinteticas() -> pd.DataFrame:
    f = [  # (acta_id, camara, fecha, titulo, fuente, clase esperada, subtipo esperado)
        ("x:1", "diputados", "2010-01-01", "Apartamiento del Reglamento solicitado por el Dip. X.", "ckan_diputados",
         "MOCION", "procedimiento"),
        ("x:2", "diputados", "2010-01-01", "MOCIÓN SOLICITADA POR LA DIP. Y.", "argentinadatos", "MOCION", "procedimiento"),
        ("x:3", "senado", "2006-01-01", "Dictamen en el proyecto de ley X. Votacion en general. OBSERVACIONES: SOBRE TABLAS.",
         "decada_votada", "GENERAL", "general"),
        ("x:4", "senado", "2006-01-01", "Proyecto de ley Z. Votacion en particular Artículo 3. OBSERVACIONES : SOBRE TABLAS,"
         " SE RECHAZA.", "decada_votada", "PARTICULAR", "particular"),
        ("x:5", "diputados", "2007-01-01", "Expediente 1-S-07. Acuerdo preferencial de comercio. Votación en General y "
         "Particular.", "decada_votada", "GENERAL", "general_y_particular"),
        ("x:6", "senado", "2007-01-01", "Proyecto de ley respecto al lugar del emplazamiento del monumento. Votacion en "
         "general y en particular", "decada_votada", "GENERAL", "general_y_particular"),
        ("x:7", "senado", "2009-01-01", "Proyecto de ley W. HABILITACION DEL TRATAMIENTO SOBRE TABLAS", "decada_votada",
         "MOCION", "procedimiento"),
        ("x:8", "senado", "2022-09-01", "Acuerdo para designar vocal. O.D. 63/2023 [EN PARTICULAR]", "senado",
         "OTRA", "acuerdo_pliego"),
        ("x:9", "senado", "2016-06-29", "Ley A. O.D. 1/2016 [EN GENERAL]", "senado", "GENERAL", "senado_tag_general"),
        ("x:10", "senado", "2016-06-29", "Ley A. O.D. 1/2016 [EN PARTICULAR]", "senado", "PARTICULAR",
         "senado_particular_tras_general"),
        ("x:11", "senado", "2016-06-29", "Ley B. O.D. 2/2016 [EN PARTICULAR]", "senado", "GENERAL", "senado_votacion_unica"),
        ("x:12", "senado", "2016-06-29", "Ley C. O.D. 3/2016 , Art. 4 [EN PARTICULAR]", "senado", "PARTICULAR", "particular"),
        ("x:13", "diputados", "2026-01-01", "Inviolabilidad de la Propiedad Privada.", "argentinadatos", "OTRA",
         "repetida_sin_marca"),
        ("x:14", "diputados", "2026-01-01", "Inviolabilidad de la Propiedad Privada.", "argentinadatos", "OTRA",
         "repetida_sin_marca"),
        ("x:15", "diputados", "2026-01-02", "Ley Federal de Trabajo Social.", "argentinadatos", "GENERAL", "unica_sin_marca"),
        ("x:16", "diputados", "2014-01-01", "Proyecto de ley estableciendo un sistema de resolución de conflictos", "decada_votada",
         "GENERAL", "unica_sin_marca"),
        ("x:17", "senado", "2025-01-01", "Rechazo al decreto 681/25 del Poder Ejecutivo Nacional. S-1692/25-PD", "argentinadatos",
         "OTRA", "decreto"),
        ("x:18", "senado", "2016-01-01", "Temas Varios O.D. ( S-784/16-PL , O.D. 605/2016 [EN GENERAL]", "senado", "OTRA",
         "conjunto"),
        ("x:19", "diputados", "2024-04-30", "INCORPORACION NUEVO CAPITULO.", "argentinadatos", "PARTICULAR", "particular"),
        ("x:20", "senado", "2022-10-27", "Incorporación de prestaciones al Programa Médico Obligatorio. O.D. 373/2022 "
         "[EN PARTICULAR]", "senado", "GENERAL", "senado_votacion_unica"),
        ("x:21", "senado", "2019-01-01", "AUSENTE OTRA 0 AFIRMATIVOS 0 NEGATIVOS 0 ABSTENCIONES 33 AUSENTES", "senado",
         "OTRA", "sin_titulo"),
        ("x:22", "diputados", "2006-01-01", "Exp. 0056-PE-03 - Insistencia de la HCDN en la sanción original", "decada_votada",
         "OTRA", "insistencia"),
        ("x:23", "diputados", "2024-05-01", "Modificación del art. 139 del Código Penal tipificando la sustracción de menores."
         " O.D. 39/2024", "argentinadatos", "GENERAL", "unica_sin_marca"),
        ("x:24", "senado", "2016-01-01", "Proyecto de ley que modifica el Art. 3º de la Ley 25.413. O.D. 5/2016 [EN PARTICULAR]",
         "senado", "GENERAL", "senado_votacion_unica"),
        ("x:25", "diputados", "2004-01-01", "Expediente 195-S-04 Orden del Día 1788 * Artículo 2. Prórroga de la Ley 25.561",
         "argentinadatos", "PARTICULAR", "particular"),
        ("x:26", "senado", "2024-12-01", "Remoción del Senador X en los términos del artículo 66 de la Constitución Nacional.",
         "argentinadatos", "OTRA", "juicio_desafuero"),
        ("x:27", "diputados", "2006-01-01", "Pedido de trat. sobre tablas del Dip. X de los Expedientes 1-D-06", "argentinadatos",
         "MOCION", "procedimiento"),
    ]
    return pd.DataFrame(f, columns=["acta_id", "camara", "fecha", "titulo", "fuente", "clase_esp", "subtipo_esp"])


def main() -> int:
    print("1. La regla de clasificación")
    s = sinteticas()
    r = C.clasificar(s[C.COLUMNAS_QUE_LEE]).merge(s, on="acta_id")
    for x in r.itertuples(index=False):
        check((x.clase, x.subtipo) == (x.clase_esp, x.subtipo_esp),
              f"{x.acta_id}: {x.clase}/{x.subtipo} (esperado {x.clase_esp}/{x.subtipo_esp}) · {x.titulo[:60]}")

    a = pd.read_parquet(C.CANONICA)
    base = C.clasificar(a)
    check(set(base["clase"]) <= set(C.CLASES) and len(base) == len(a) and base["acta_id"].is_unique,
          f"una clase de las cuatro por acta ({len(base)} actas)")
    rng = np.random.default_rng(0)
    b = a.copy()
    for col in ("resultado", "tipo_mayoria", "n_afirmativos", "n_negativos", "n_abstenciones", "n_ausentes",
                "expediente", "periodo"):
        b[col] = b[col].to_numpy()[rng.permutation(len(b))]
    check(C.clasificar(b).equals(base), "barajar resultado, tipo, conteos y expediente no cambia ninguna clase")
    check(C.clasificar(a[C.COLUMNAS_QUE_LEE]).equals(base), "corre sólo con acta_id, cámara, fecha, título y fuente")
    check(C.clasificar(a).equals(base), "determinista: dos corridas, la misma salida")

    sha = _sha16(C.CANONICA)
    if sha != SHA_CANONICA:
        print(f"  (la canónica cambió: sha256/16 {sha}, la medición usa {SHA_CANONICA}; el ancla de conteos no aplica)")
    else:
        cl = base["clase"].value_counts().to_dict()
        st = base["subtipo"].value_counts().to_dict()
        check(cl == ANCLA_CLASES, f"conteo por clase: {cl}")
        check(st == ANCLA_SUBTIPOS, "conteo por subtipo (anclado)")

    print(f"\n{'TODO OK' if not FALLOS else f'{len(FALLOS)} FALLAS'}")
    return 1 if FALLOS else 0


if __name__ == "__main__":
    raise SystemExit(main())
