# -*- coding: utf-8 -*-
"""D2.0 de la auditoría 2026-09: qué es cada acta de la canónica, desde su TÍTULO (la regla pre-registrada).

    python evaluacion/baseline/src/clasificar_actas_d2_0.py          # conteo por clase y subtipo, por fuente

LA REGLA es el pre-registro de D2.0 (`ESTADO-EJECUCION.md`, «D2.0 — pre-registro»); este archivo es la regla escrita
y se commitea con el pre-registro, ANTES de cruzar ninguna clase con el resultado. Lee SÓLO `acta_id`, `camara`,
`fecha`, `titulo` y `fuente`: nunca `resultado`, `tipo_mayoria` ni los conteos (un control lo verifica: barajar el
resultado no cambia ninguna clase, y la función no recibe esas columnas).

Cuatro clases (las de Franco) y un subtipo que dice por qué. Se aplica la PRIMERA regla que se cumple, en este orden:

  1. MOCION      procedimiento: «moción …», apartamiento del reglamento, habilitación del tratamiento (o «que se trate
                 sobre tablas»), pedido o solicitud de preferencia, de tratamiento, de vuelta o pase a comisión,
                 inclusión en el tratamiento, emplazamiento solicitado, reconsideración, cuarto intermedio, constituir
                 la cámara en comisión, cuestión de privilegio, plan de labor. Los disparadores sueltos «sobre tablas»,
                 «preferencia», «emplazamiento» y «cámara en comisión» NO cuentan: aparecen en títulos de leyes
                 («acuerdo preferencial», «lugar del emplazamiento», «dictamen de la cámara en comisión»).
  2. OTRA        lo que no es votar una ley: acuerdos, pliegos y nombramientos (`acuerdo_pliego`); validez o rechazo
                 de decretos, Bicameral de Trámite Legislativo o de Facultades Delegadas (`decreto`); juicio político,
                 desafuero, comisión acusadora (`juicio_desafuero`); insistencia y aceptación de modificaciones —segunda
                 revisión o veto— (`insistencia`); licencias, secretarios y otros asuntos internos (`interno`).
  3. GENERAL     «en general y en particular» en una sola votación (`general_y_particular`).
  4. GENERAL     «en general» explícito (`general`).
  5. PARTICULAR  «en particular» explícito, o un artículo, capítulo, título, inciso, anexo, planilla o la incorporación
                 de uno nuevo (`particular`). No cuenta la mención de un artículo, título o inciso DE OTRA NORMA
                 («modifica el art. 3º de la ley 25.413», «art. 81 CN»): es el asunto de la ley, no una parte votada.
  6. OTRA        votaciones en conjunto de varios expedientes: «temas varios», «sin disidencias», «… en los
                 siguientes» (`conjunto`); proyectos de resolución, declaración o comunicación
                 (`resolucion_declaracion`); un título que es sólo un recuento, sin el asunto (`sin_titulo`).
  7. fuente `senado`: su marca final `[EN GENERAL]` → GENERAL (`senado_tag_general`). Su marca `[EN PARTICULAR]`
                 aparece en 680 de las 749 actas, también en votaciones únicas de una ley entera, así que sola no
                 alcanza: si en la misma cámara y fecha hay un acta con el mismo título base y marca `[EN GENERAL]` →
                 PARTICULAR (`senado_particular_tras_general`); si no → GENERAL (`senado_votacion_unica`).
  8. resto (un título de ley o de expediente sin ninguna marca): si su título es ÚNICO en esa cámara y fecha →
                 GENERAL (`unica_sin_marca`: una sola votación de la ley); si se repite → OTRA (`repetida_sin_marca`:
                 no se puede saber cuál es la general).

Normalización del título: sin tildes, en mayúsculas, espacios colapsados. La marca `[EN …]` del Senado se saca del
texto antes de las reglas 1 a 6 y se usa sólo en la 7. **Se corta el título en «OBSERVACIONES»** (la cola que
`decada_votada` agrega en el Senado: «OBSERVACIONES: SOBRE TABLAS, SE RECHAZA…»): describe cómo se trató la ley y a
veces trae el RESULTADO, que la regla no puede leer. La regla 8 cuenta repeticiones sobre ese mismo título cortado.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents if (d / "rutas.py").is_file())))
from rutas import RAIZ as REPO  # noqa: E402

CANONICA = REPO / "datos" / "canonica" / "data" / "clean" / "actas_canonico.parquet"
COLUMNAS_QUE_LEE = ["acta_id", "camara", "fecha", "titulo", "fuente"]
CLASES = ("GENERAL", "PARTICULAR", "MOCION", "OTRA")

_TAG_SENADO = re.compile(r"\[\s*(EN GENERAL|EN PARTICULAR)\s*\]\s*$")

MOCION = re.compile(
    r"\bMOCION\b|APARTAMIENTO (DEL|DE) REGLAMENTO|HABILITACION (DEL |DE )?(TRATAMIENTO|TEMARIO|TRAT\b)"
    r"|HABILITAR EL TRATAMIENTO|REQUIRIENDO SU HABILITACION|TRATE SOBRE TABLAS?"
    r"|(PEDIDO|SOLICITUD) DE (PREFERENCIA|TRAT|VUELTA|PASE)|INCLUSION (EN EL |DEL? )?(TRATAMIENTO|PLAN)"
    r"|TRATAMIENTO SOBRE TABLAS?"
    r"|EMPLAZAMIENTO (\d+ )?SOLICITAD|VUELTA A COMISION|PASE A COMISION|RECONSIDERACION|CUARTO INTERMEDIO"
    r"|CONSTITU\w* (LA CAMARA|EL CUERPO|EN COMISION)|CUESTION DE PRIVILEGIO|PLAN DE LABOR")
OTRA_NO_LEY = {
    "acuerdo_pliego": re.compile(
        r"SOLICITA(NDO)? (EL |SU )?ACUERDO|ACUERDOS? PARA (LA |EL |LAS |LOS )?(DESIGNA|PROMOCION|ASCENSO|NOMBRA)"
        r"|\bPLIEGOS?\b|ACUERDOS? PODER JUDICIAL|\bNOMBRAMIENTOS?\b"),
    "decreto": re.compile(
        r"(VALIDEZ|RECHAZO|TOMA DE CONOCIMIENTO|RATIFICA\w*|APROBACION) (DEL? |AL |DE LOS |DE LAS )?(DECRETOS?|DNUS?)\b"
        r"|VALIDEZ DE(L)? (LOS )?DNU|DECRETOS? DE NECESIDAD Y URGENCIA N|TRAMITE LEGISLATIVO"
        r"|FACULTADES DELEGADAS AL (PEN|PODER EJECUTIVO)|DECLARACIONES DE VALIDEZ"),
    "juicio_desafuero": re.compile(
        r"JUICIO POLITICO|DESAFUERO|COMISION ACUSADORA|\b(EXCLUSION|REMOCION) DE(L)? (SENADOR|DIPUTAD)|IMPUGNACION"
        r"|DIPLOMAS?\b"),
    "insistencia": re.compile(r"INSISTENCIA|ACEPTACION DE (LAS )?MODIF|SANCION ORIGINAL"),
    "interno": re.compile(
        r"\bLICENCIA\b|RATIFICACION DE (SECRETARIOS|AUTORIDADES)|DESIGNACION DE (SENADORES|DIPUTADOS)"
        r"|PRESIDENTE PROVISIONAL|VERSION TAQUIGRAFICA|\bRENUNCIA\b|PROSECRETARI"),
}
GENERAL_Y_PARTICULAR = re.compile(
    r"GENERAL Y (EN )?PARTICULAR|\bGRAL\.? Y PART|\bGRAL\.? PART|EN GENERAL Y EN PARTICULAR")
GENERAL = re.compile(r"\bEN GENERAL\b|VOTACION GENERAL|\bVOT\.? (EN )?GRAL\b")
PARTICULAR = re.compile(
    r"EN PARTICULAR|VOTACION PARTICULAR|\bARTICULOS?\b|\bARTS?\.?\s*\d|\bART\.\s*[IVXL\d]|\bCAPITULOS?\b"
    r"|\bCAP\.\s*[IVXL\d]|\bTITULOS?\s+([IVXL]+|\d+)\b|\bINCISOS?\b|\bANEXO\s+[IVXL\d]+\b|\bPLANILLAS?\b"
    r"|INCORPORACION (DE )?(UN )?NUEV|INCORPORACION DE(L)? (ARTICULO|CAPITULO|INCISO)")
# Un artículo, título o capítulo DE OTRA NORMA es el asunto de la ley, no una votación en particular («modifica el
# art. 3º de la ley 25.413», «art. 81 CN»): esas menciones se borran antes de la regla 5.
REF_OTRA_NORMA = re.compile(
    r"\b(ARTICULOS?|ARTS?\.?|TITULOS?|CAPITULOS?|INCISOS?)\s[^.;]{0,40}?"
    r"(DE LA LEY|DEL CODIGO|DE LA CONSTITUCION|\bCN\b|DEL DECRETO|DEL REGLAMENTO)")
OTRA_TARDIA = {
    "conjunto": re.compile(
        r"TEMAS VARIOS|SIN DISIDENCIAS|EN LOS SIGUIENTES|VOTACION DE PROYECTOS|EN CONJUNTO|\bEN BLOQUE\b"),
    "resolucion_declaracion": re.compile(
        r"PROYECTOS? DE (RESOLUCION|DECLARACION|COMUNICACION)|\bDE (RESOLUCION|DECLARACION)\s*[.:-]"
        r"|EXPEDIENTES? (VARIOS )?DE RESOLUCION|-P[DR]\b|\bREPUDIO\b|\bBENEPLACITO\b"),
    # el título es sólo un recuento («AUSENTE OTRA 0 AFIRMATIVOS 0 NEGATIVOS …»), sin el asunto
    "sin_titulo": re.compile(r"\bAFIRMATIVOS\b.*\bNEGATIVOS\b"),
}


def normalizar(titulo) -> str:
    s = unicodedata.normalize("NFKD", "" if titulo is None or titulo is pd.NA else str(titulo))
    s = s.encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", s).strip()


def _sin_tag(t: str) -> tuple[str, str | None]:
    """Saca la marca `[EN …]` del Senado y corta en «OBSERVACIONES» (ver la normalización, arriba)."""
    m = _TAG_SENADO.search(t)
    t, tag = (t[:m.start()].strip(), m.group(1)) if m else (t, None)
    return re.split(r"\bOBSERVACIONES\b", t, maxsplit=1)[0].strip(" .:-"), tag


def _base_senado(t: str) -> str:
    """El título sin la marca y sin la cola de artículos («, Art. 67 , Art. 68 …»): para emparejar general/particular."""
    t, _ = _sin_tag(t)
    return re.sub(r"\s*,?\s*\bART(ICULOS?|S)?\b\.?.*$", "", t).strip(" ,.")


def clasificar_titulo(t_norm: str) -> tuple[str, str] | None:
    """Reglas 1 a 6 sobre un título normalizado, cortado y SIN la marca del Senado. None = no decide (reglas 7 y 8)."""
    if MOCION.search(t_norm):
        return "MOCION", "procedimiento"
    for sub, rx in OTRA_NO_LEY.items():
        if rx.search(t_norm):
            return "OTRA", sub
    if GENERAL_Y_PARTICULAR.search(t_norm):
        return "GENERAL", "general_y_particular"
    if GENERAL.search(t_norm):
        return "GENERAL", "general"
    if PARTICULAR.search(REF_OTRA_NORMA.sub(" ", t_norm)):
        return "PARTICULAR", "particular"
    for sub, rx in OTRA_TARDIA.items():
        if rx.search(t_norm):
            return "OTRA", sub
    return None


def clasificar(actas: pd.DataFrame) -> pd.DataFrame:
    """Una fila por acta: `acta_id`, `clase`, `subtipo`. Sólo mira `COLUMNAS_QUE_LEE`."""
    a = actas[COLUMNAS_QUE_LEE].copy()
    a["acta_id"] = a["acta_id"].astype(str)
    tn = a["titulo"].map(normalizar)
    partes = tn.map(_sin_tag)
    a["t_"], a["tag_"] = partes.str[0], partes.str[1]
    a["base_"] = tn.map(_base_senado)
    a["f_"] = a["fecha"].astype("string").fillna("sin_fecha")
    # pares (cámara, fecha, título base) del Senado que tienen una votación marcada [EN GENERAL]
    sen = a[(a["fuente"] == "senado") & (a["tag_"] == "EN GENERAL")]
    con_general = set(zip(sen["camara"], sen["f_"], sen["base_"]))
    # cuántas veces aparece cada título (cortado) en la misma cámara y fecha (regla 8)
    rep = a.groupby(["camara", "f_", "t_"])["acta_id"].transform("size")
    clase, subtipo = [], []
    for r, n in zip(a.itertuples(index=False), rep):
        res = clasificar_titulo(r.t_)
        if res is None and r.fuente == "senado" and r.tag_ is not None:
            if r.tag_ == "EN GENERAL":
                res = ("GENERAL", "senado_tag_general")
            elif (r.camara, r.f_, r.base_) in con_general:
                res = ("PARTICULAR", "senado_particular_tras_general")
            else:
                res = ("GENERAL", "senado_votacion_unica")
        if res is None:
            res = ("GENERAL", "unica_sin_marca") if n == 1 else ("OTRA", "repetida_sin_marca")
        clase.append(res[0])
        subtipo.append(res[1])
    return pd.DataFrame({"acta_id": a["acta_id"].to_numpy(), "clase": clase, "subtipo": subtipo})


def main() -> int:
    a = pd.read_parquet(CANONICA, columns=COLUMNAS_QUE_LEE)
    c = clasificar(a).merge(a[["acta_id", "fuente"]], on="acta_id")
    pd.set_option("display.width", 200)
    print(pd.crosstab([c["clase"], c["subtipo"]], c["fuente"], margins=True).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
