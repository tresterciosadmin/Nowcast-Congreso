# -*- coding: utf-8 -*-
"""Saca los FIRMANTES del dictamen del texto de una Orden del Día.

## Qué extrae

Por Orden del Día: número, fecha de impresión, comisiones, expedientes del
sumario, y **un bloque por dictamen** (mayoría, minoría, o el único cuando no
hay disputa) con sus firmantes y quién firmó **en disidencia** (parcial o total).

## El ancla, y por qué es la misma en las dos cámaras

Todo cuelga de una frase que cierra el dictamen antes de las firmas:

    Sala de las comisiones, 27 de mayo de 2008.
    Graciela M. Giannettasio. – Juan H. Sylvestre Begnis. – ...
    En disidencia parcial:
    Juan E. Acuña Kunz. – Paula M. Bertol. – ...

Diputados y Senado usan **la misma fórmula y el mismo separador** (guión medio
`–`), así que un solo parser sirve para los dos sistemas de comisiones. Eso no
era obvio: se verificó el 21-08-2026 sobre OD reales de Diputados 2008-2013 y
del Senado 2026.

## Por qué el ancla y no "buscar nombres"

Un PDF de Orden del Día trae **más de una lista de personas**. Después del
articulado aparece la firma del Poder Ejecutivo sobre el mensaje —"JULIO C.
COBOS. Alberto A. Fernández. – Aníbal D. Fernández."— que NO firmó ningún
dictamen. Buscar "cosas que parecen nombres" mete al Ejecutivo adentro de la
comisión. El ancla acota la lectura al bloque que sigue a la fórmula de cierre.

## Falla ruidoso

Si no encuentra el ancla, o si el bloque de firmas no parece una lista de
nombres, la OD sale con `parseo_ok=False` y `motivo`, **y entra igual a la
salida**. Un OD que no se pudo leer tiene que quedar marcado, no desaparecer del
conteo: si desaparece, la cobertura se ve mejor de lo que es.

## Lo que este módulo NO hace

**No resuelve el bloque de cada firmante.** El PDF da el nombre y casi nunca el
bloque, y por decisión de Valle (21-08) el bloque se resuelve contra
`datos/padron`, que es mandate-aware y sabe qué bloque tenía cada legislador a
esa fecha. Sacarlo del PDF daría una segunda fuente contradictoria para un dato
que ya tenemos bien. El emparejamiento nombre→legislador vive aparte.

    python datos/expedientes/src/parser_od.py Archivos_Borrar/od_pdf/126-346.pdf
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ─────────────────────────── patrones ───────────────────────────

RE_OD = re.compile(r"ORDEN\s+DEL\s+D[IÍ]A\s*N[º°o]\s*([\d.]+)", re.I)
RE_IMPRESO = re.compile(r"Impreso\s+el\s+d[ií]a\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", re.I)
RE_COMISIONES = re.compile(r"^\s*(COMISI[OÓ]N(?:ES)?\s+DE\s+.+?)(?=\n\s*(?:Impreso|SUMARIO|$))",
                           re.I | re.M | re.S)
# expedientes tal como salen del sumario: (160-S.-2007.) (1-P.E.-2008.) (444-D.-08)
RE_EXPEDIENTE = re.compile(r"(\d{1,4}(?:\.\d{3})?)\s*-\s*([A-Z]{1,3}(?:\.[A-Z])?\.?)\s*-\s*(\d{2,4})")

# El Senado ANTES de ~2018 escribe la fórmula distinto: **"Sala de Comisión,"**
# — singular y SIN el artículo — y cierra con `.-`. Ejemplo real:
#   "Sala de Comisión, Agosto 17 de 2010.-"
# El regex viejo exigía "de la(s) comisión(es)" y por eso 662 Órdenes del Día del
# Senado quedaban sin leer, casi todas anteriores a 2018.
# Y muchas veces NO hay punto al final: la fecha se pega directo al primer
# firmante — "Sala de la comisión, 16 de noviembre de 2016 Liliana T. Negre de
# Alonso.-". Por eso la captura termina en el AÑO (cuatro dígitos, que toda fecha
# tiene) y el punto queda opcional, en vez de exigirlo como cierre.
RE_ANCLA = re.compile(
    r"Sala\s+de\s+(?:la\s+|las\s+)?comisi[oó]n(?:es)?\s*,\s*"
    r"([^\n]{0,45}?\d{4})\s*\.?\s*-?", re.I)
# Cómo rotula cada cámara el carácter del dictamen. Verificado el 04-09-2026
# sobre 193 Órdenes del Día reales del Senado (2008-2026) y las de Diputados:
#
#   Diputados — la cabecera va pegada al cuerpo del dictamen:
#       "Dictamen de mayoría" / "Dictamen de minoría" / "Dictamen de las comisiones"
#
#   Senado — el carácter se rotula en el SUMARIO, no en el cuerpo:
#       "Dictamen de mayoría en el proyecto de ley venido en revisión ..."
#     y el cuerpo lleva SIEMPRE la genérica "DICTAMEN DE COMISIÓN"; a veces
#     además calificada: "DICTAMEN DE COMISIÓN EN MAYORIA" (senado-2009-485.pdf).
#     Sin la segunda alternativa, esa forma caía en la rama genérica.
#
#   Senado, cuarta forma (06-09-2026) — sin "de comisión" ni calificativo:
#       "Dictamen EN el proyecto de ley de la señora senadora Latorre, por el ..."
#       "Dictamen EN el mensaje y proyecto de ley ..."
#     Es un dictamen a secas. Se encontraron leyendo las 39 Órdenes del Día del
#     Senado que quedaban en `desconocido`: las 39 usan esta forma, sin una sola
#     excepción, y ninguna tiene un segundo dictamen que pudiera confundirse.
#     Entra como GENÉRICA (dice "hay un dictamen", no de qué carácter es).
#
# El orden de las alternativas importa: "comisión EN mayoría" tiene que probarse
# ANTES que la genérica "comisión", o la genérica se la come. Y la forma nueva va
# ÚLTIMA por lo mismo: "Dictamen de mayoría en el proyecto..." tiene que caer en la
# primera alternativa, no en ésta.
RE_CABECERA_DICTAMEN = re.compile(
    r"Dictamen\s+de\s+(?:la\s+)?(mayor[ií]a|minor[ií]a)"
    r"|Dictamen\s+de\s+(?:las?\s+)?comisi[oó]n(?:es)?\s+en\s+(mayor[ií]a|minor[ií]a)"
    r"|Dictamen\s+de\s+(?:las?\s+)?(comisi[oó]n(?:es)?)"
    r"|Dictamen(?:es)?\s+(en)\s+(?:el|los|la|las)\s+"
    r"(?:proyecto|mensaje|expediente|proyectos)\b", re.I)
# Hasta dónde se busca hacia ADELANTE cuando no hubo cabecera antes del ancla.
# Ver el "rescate hacia adelante" en `_clase_del_dictamen`.
RESCATE_ADELANTE = 3000
RE_DISIDENCIA = re.compile(r"En\s+disidencia(\s+parcial|\s+total)?\s*:", re.I)

# dónde termina el bloque de firmas
CORTES = re.compile(
    r"(?:^|\n)\s*(?:"
    r"Buenos\s+Aires\s*,"
    r"|PROYECTO\s+DE\s+(?:LEY|RESOLUCI[OÓ]N|DECLARACI[OÓ]N)"
    r"|INFORME\b"
    r"|FUNDAMENTOS\b"
    r"|ANTECEDENTE"
    # `ANEXO` cierra el bloque de firmas y no estaba: en `senado-2018-16.pdf` el
    # bloque seguía leyendo el ANEXO I —un padrón catastral— y le sacaba **18
    # nombres inventados** ("Quebrada del Portugués", "Estancia El Mollar"), 37
    # firmantes donde el documento tiene 19. Va anclado a principio de línea, que
    # es como aparece el encabezado.
    r"|ANEXO\b"
    r"|Dictamen\s+de\b"
    r"|El\s+Senado\s+y\s+C[áa]mara\s+de\s+Diputados"
    r"|Honorable\s+C[áa]mara\s*:"
    r"|Art[íi]culo\s+1"
    r")", re.I)

MAX_PALABRAS_NOMBRE = 7
MAX_LARGO_NOMBRE = 60
MIN_NOMBRES = 3        # cuántos nombres tiene que rendir un bloque sin ancla

# Cortes para la búsqueda SIN ancla. No se puede reusar `CORTES`: incluye
# `Honorable Cámara:`, que aparece UNA LÍNEA DESPUÉS de la cabecera del
# dictamen, así que la región a mirar quedaba vacía y no se encontraba nada.
CORTES_SIN_ANCLA = re.compile(
    r"(?:^|\n)\s*(?:"
    r"INFORME\b"
    r"|FUNDAMENTOS\b"
    r"|ANTECEDENTE"
    r"|PROYECTO\s+DE\s+(?:LEY|RESOLUCI[OÓ]N|DECLARACI[OÓ]N)"
    r"|El\s+Senado\s+y\s+C[áa]mara\s+de\s+Diputados"
    r")")
# SIN `re.I` a propósito: los encabezados de sección van en MAYÚSCULA, y con
# `re.I` el corte saltaba en un "informe" en minúscula metido en la prosa
# ("por las razones expuestas en el informe que se acompaña"), dejando la región
# vacía justo antes de las firmas.


@dataclass
class Dictamen:
    clase: str                       # 'mayoria' | 'minoria' | 'unico' | 'desconocido'
    orden: int                       # 1, 2, 3... en el orden en que aparecen
    fecha_sala: str = ""
    firmantes: list[dict] = field(default_factory=list)


@dataclass
class OrdenDelDia:
    archivo: str = ""
    od_numero: str = ""
    fecha_impresion: str = ""
    comisiones: list[str] = field(default_factory=list)
    expedientes: list[str] = field(default_factory=list)
    dictamenes: list[Dictamen] = field(default_factory=list)
    parseo_ok: bool = False
    motivo: str = ""
    # De dónde salieron las firmas: "ancla" (la fórmula de cierre) o "sin_ancla"
    # (reconocidas por su forma, como en las Órdenes del Día de 2020-2021).
    # Viaja al parquet: una firma leída sin ancla es más frágil que una leída
    # con la fórmula, y hay que poder separarlas al medir.
    origen_firmas: str = ""
    # Cuántos bloques de firmas se descartaron por ser el MISMO dictamen impreso
    # dos veces (misma fecha de sala y la misma lista de firmantes). Ver
    # `_sin_repetidos`. Viaja al parquet para que la deduplicación se pueda medir
    # en vez de tener que confiar en ella.
    dictamenes_repetidos: int = 0


# ─────────────────────────── ayudas ───────────────────────────

def _normalizar(texto: str) -> str:
    """Colapsa los espacios que mete la extracción de PDF, sin tocar los saltos."""
    texto = texto.replace("\xa0", " ").replace("\u2010", "-").replace("\u2011", "-")
    return re.sub(r"[ \t]+", " ", texto)


def _sin_acentos_mayus(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").upper()


def _parece_nombre(candidato: str) -> bool:
    """Filtro conservador: preferimos perder un nombre raro a inventar uno."""
    c = candidato.strip(" .,;")
    if not c or len(c) > MAX_LARGO_NOMBRE:
        return False
    if any(ch.isdigit() for ch in c):
        return False
    palabras = c.split()
    if not (1 < len(palabras) <= MAX_PALABRAS_NOMBRE):
        return False
    # al menos dos "piezas" arrancan en mayúscula (nombre y apellido)
    mayusculas = sum(1 for p in palabras if p[:1].isupper())
    return mayusculas >= 2


# Separadores de firmas. Diputados usa el guión medio `–`; el Senado viejo usa
# `.-` pegado al apellido ("Escudero.- Luis A. Juez.-") y a veces un guión suelto
# entre espacios. Se unifican a `–` ANTES de partir, y sólo dentro del bloque de
# firmas: en el resto del documento un guión no significa lo mismo.
_SEPARADORES = re.compile(r"\.\s*-|\s+-\s+")


def _firmantes_de(bloque: str, disidencia: str) -> list[dict]:
    bloque = re.sub(r"\s*\n\s*", " ", bloque).strip()
    bloque = _SEPARADORES.sub(" – ", bloque)
    salida: list[dict] = []
    for pieza in bloque.split("–"):
        crudo = " ".join(pieza.split())
        # El asterisco marca a quien integra LAS DOS comisiones que firman en
        # conjunto. Si se deja pegado al nombre ("Paola Vessvessian.*"), el
        # emparejamiento contra el padrón falla; si se tira, se pierde el único
        # dato del PDF sobre a qué comisión pertenece cada firma. Se separa.
        dos_comisiones = "*" in crudo
        nombre = crudo.replace("*", "").strip(" .,;")
        if not _parece_nombre(nombre):
            continue
        salida.append({
            "firmante_raw": nombre,
            "orden_firma": len(salida) + 1,
            "disidencia": disidencia,
            "primer_firmante": disidencia == "none" and len(salida) == 0,
            "dos_comisiones": dos_comisiones,
        })
    return salida


def _bloque_de_firmas(texto: str, desde: int) -> str:
    resto = texto[desde:]
    corte = CORTES.search(resto)
    return resto[: corte.start()] if corte else resto[:2000]


CLASE_DESCONOCIDA = "desconocido"


def _etiqueta_de(m: 're.Match') -> str:
    """La etiqueta capturada por `RE_CABECERA_DICTAMEN`, sin acentos y en mayúscula."""
    return _sin_acentos_mayus(m.group(1) or m.group(2) or m.group(3) or m.group(4) or "")


def _clase_del_dictamen(texto: str, pos_ancla: int, vistos: int,
                        fin: int | None = None) -> str:
    """La cabecera de dictamen más cercana ANTES del ancla manda, con dos reglas.

    **1. Una cabecera GENÉRICA no pisa a una calificada.** El Senado rotula
    "Dictamen de mayoría" en el sumario y después abre el cuerpo con la genérica
    "DICTAMEN DE COMISIÓN". Con la regla vieja —la última cabecera gana, sin
    importar cuál— la genérica del cuerpo borraba el rótulo del sumario **en
    todas** las Órdenes del Día del Senado. Testigo: `senado-2008-1168.pdf` dice
    literalmente *"Dictamen de mayoría en el proyecto de ley venido en revisión
    por el que se dispone la unificación del Sistema Integrado de Jubilaciones y
    Pensiones"* y el parquet lo tenía como `unico`.
    En Diputados esto no cambia nada: sus cabeceras calificadas se siguen pisando
    entre sí en orden (mayoría, después minoría), que es lo que hace falta para
    que cada ancla reciba la suya.

    **2. Si no hay NINGUNA cabecera, la clase es `desconocido`, no `unico`.**
    Arrancar en "unico" convertía "no encontré el rótulo" en una afirmación
    positiva sobre el documento. Son dos cosas distintas y los consumidores tienen
    que poder separarlas: `desconocido` es sin dato, no "despacho único".
    """
    clase = None
    for m in RE_CABECERA_DICTAMEN.finditer(texto, 0, pos_ancla):
        e = _etiqueta_de(m)
        if e.startswith("MAYOR"):
            clase = "mayoria"
        elif e.startswith("MINOR"):
            clase = "minoria"
        elif clase is None:
            # genérica: informa "hay un dictamen", no su carácter. Sólo cuenta
            # cuando no hubo antes una cabecera calificada que decir.
            clase = "unico"
    if clase is None:
        # RESCATE HACIA ADELANTE. La búsqueda hacia atrás falla en dos casos que
        # medimos el 06-09 sobre las 56 Órdenes del Día de Diputados que quedaban
        # en `desconocido`:
        #
        #   1. La cabecera arranca EXACTAMENTE en `pos_ancla`. Pasa en la rama
        #      `sin_ancla` (2020-2021), donde el "ancla" es el arranque del bloque
        #      de firmas y la cabecera abre ese mismo bloque. `finditer(t, 0, pos)`
        #      es medio abierto y la excluye por un carácter. `131-2469.pdf` dice
        #      "Dictamen de mayoría" en la posición 627 y el bloque también empieza
        #      en 627: se perdía una MAYORÍA entera por un off-by-one.
        #   2. La cabecera está DESPUÉS del ancla. Pasa cuando el documento cierra
        #      con "Sala de la comisión" antes de abrir el cuerpo del dictamen
        #      (`126-445.pdf`: ancla en 657, cabecera en 1030).
        #
        # Sólo corre cuando la respuesta habría sido `desconocido`, así que no
        # puede cambiar ninguna clase que hoy sale bien. Y toma la PRIMERA
        # cabecera, no la última: hacia adelante, la primera es la que ABRE este
        # dictamen; las de más allá son del siguiente.
        tope = len(texto) if fin is None else min(fin, len(texto))
        tope = min(tope, pos_ancla + RESCATE_ADELANTE)
        m = RE_CABECERA_DICTAMEN.search(texto, pos_ancla, tope)
        if m is not None:
            e = _etiqueta_de(m)
            clase = ("mayoria" if e.startswith("MAYOR")
                     else "minoria" if e.startswith("MINOR") else "unico")
    if clase is None:
        return CLASE_DESCONOCIDA
    # un segundo dictamen sin cabecera propia es, por construcción, de minoría
    if vistos > 0 and clase == "unico":
        clase = "minoria"
    return clase


# ─────────────────────────── parser ───────────────────────────

def _bloques_sin_ancla(texto: str) -> list[tuple[int, str]]:
    """Encuentra las firmas cuando NO está la fórmula de cierre.

    **Por qué hace falta.** En las Órdenes del Día de 2020 y 2021 —las de las
    sesiones remotas— la fórmula `Sala de las comisiones, <fecha>.` simplemente
    no está: la palabra "sala" aparece CERO veces y los firmantes van pegados al
    final del dictamen. Son 165 de 2.517 (6,6%), y el 79% de ellas cae en esos
    dos períodos.

    **Cómo se las reconoce sin el ancla.** Por la forma: una lista de firmas es
    un tramo de líneas seguidas separadas por `–`. Para no confundirla con el
    articulado —que también usa `–`, como en `Art. 2° – Comuníquese`— la búsqueda
    se limita a lo que hay **entre una cabecera de dictamen y el primer corte**
    (INFORME, PROYECTO DE LEY, ANTECEDENTE...), que es donde el articulado
    todavía no empezó, y se exige que el tramo rinda al menos `MIN_NOMBRES`
    nombres válidos.

    Devuelve [(posición, bloque)], una por dictamen encontrado.
    """
    salida = []
    cabeceras = list(RE_CABECERA_DICTAMEN.finditer(texto))
    for k, cab in enumerate(cabeceras):
        fin = cabeceras[k + 1].start() if k + 1 < len(cabeceras) else len(texto)
        corte = CORTES_SIN_ANCLA.search(texto, cab.end(), fin)
        region = texto[cab.end(): corte.start() if corte else fin]
        lineas = region.split("\n")
        # tramos de líneas consecutivas con guión medio (se tolera una línea sin
        # guión en el medio: un nombre largo parte en dos renglones)
        mejor, actual, huecos = [], [], 0
        for j, linea in enumerate(lineas):
            if "–" in linea:
                actual.append(j)
                huecos = 0
            elif actual and huecos == 0 and linea.strip():
                huecos = 1
            else:
                if len(actual) >= 2:
                    mejor = actual
                actual, huecos = [], 0
        if len(actual) >= 2:
            mejor = actual
        if not mejor:
            continue
        bloque = "\n".join(lineas[mejor[0]: mejor[-1] + 1])
        if len(_firmantes_de(bloque, "none")) >= MIN_NOMBRES:
            salida.append((cab.start(), bloque))
    return salida


def _sin_repetidos(crudos: list[tuple[int, str, str]]) -> tuple[list, int]:
    """Saca los bloques de firmas que son el MISMO dictamen impreso dos veces.

    **Por qué hace falta.** `senado-2018-16.pdf` (Parque Nacional Aconquija)
    imprime el dictamen dos veces: misma fecha de sala —"4 de abril de 2018"— y
    exactamente los mismos 19 firmantes, de Julio C. Martínez a Beatriz G. Mirkin.
    El parser veía dos anclas, y la regla "un segundo dictamen sin cabecera propia
    es de minoría" lo rotulaba como **dictamen de minoría**. Esas 19 filas eran
    LAS ÚNICAS 19 "minorías" del Senado en todo el parquet (18.105 filas): un
    fenómeno entero que no existía, nacido de una reimpresión.

    Se compara por (fecha de sala, conjunto de firmantes). Dos despachos distintos
    con exactamente la misma lista de firmas y la misma fecha no son dos despachos.
    """
    salida, vistos, repetidos = [], set(), 0
    for pos, bloque, fecha in crudos:
        clave = (fecha.strip().lower(),
                 tuple(f["firmante_raw"] for f in _firmantes_de(bloque, "none")))
        if clave[1] and clave in vistos:
            repetidos += 1
            continue
        vistos.add(clave)
        salida.append((pos, bloque, fecha))
    return salida, repetidos


def parsear(texto: str, archivo: str = "") -> OrdenDelDia:
    t = _normalizar(texto)
    od = OrdenDelDia(archivo=archivo)

    m = RE_OD.search(t)
    if m:
        od.od_numero = m.group(1).replace(".", "")
    m = RE_IMPRESO.search(t)
    if m:
        od.fecha_impresion = " ".join(m.group(1).split())
    m = RE_COMISIONES.search(t)
    if m:
        crudo = " ".join(m.group(1).split())
        crudo = re.sub(r"^COMISI[OÓ]N(?:ES)?\s+DE\s+", "", crudo, flags=re.I)
        od.comisiones = [c.strip(" .") for c in re.split(r"\s+Y\s+DE\s+", crudo, flags=re.I) if c.strip()]

    # expedientes: sólo los del SUMARIO (los del cuerpo son "tenidos a la vista")
    sumario = t[: t.find("Honorable")] if "Honorable" in t else t[:3000]
    od.expedientes = sorted({f"{a}-{b.rstrip('.')}-{c}" for a, b, c in RE_EXPEDIENTE.findall(sumario)})

    if len(t.strip()) < MIN_CHARS_SONDA:
        od.motivo = ("el PDF no tiene capa de texto (escaneado): no hay nada que "
                     "parsear sin OCR")
        return od

    anclas = list(RE_ANCLA.finditer(t))
    if anclas:
        od.origen_firmas = "ancla"
        crudos = [(a.start(), _bloque_de_firmas(t, a.end()),
                   " ".join(a.group(1).split())) for a in anclas]
    else:
        # 2020-2021: sin fórmula de cierre. Se buscan las firmas por su forma.
        od.origen_firmas = "sin_ancla"
        crudos = [(pos, bloque, "") for pos, bloque in _bloques_sin_ancla(t)]
        if not crudos:
            od.motivo = "no aparece la fórmula 'Sala de las comisiones, <fecha>.' y "
            od.motivo += "tampoco un bloque de firmas reconocible"
            return od

    crudos, od.dictamenes_repetidos = _sin_repetidos(crudos)

    for i, (pos, bloque, fecha_sala) in enumerate(crudos):
        sig = crudos[i + 1][0] if i + 1 < len(crudos) else None
        dic = Dictamen(clase=_clase_del_dictamen(t, pos, i, sig),
                       orden=i + 1,
                       fecha_sala=fecha_sala)
        # el bloque se parte en tramos: firmas plenas y tramos "En disidencia ...:"
        cortes = list(RE_DISIDENCIA.finditer(bloque))
        tramos: list[tuple[str, str]] = []
        if not cortes:
            tramos.append((bloque, "none"))
        else:
            tramos.append((bloque[: cortes[0].start()], "none"))
            for j, c in enumerate(cortes):
                fin = cortes[j + 1].start() if j + 1 < len(cortes) else len(bloque)
                tipo = (c.group(1) or "").strip().lower()
                tramos.append((bloque[c.end(): fin], tipo if tipo else "sin_especificar"))
        for tramo, tipo in tramos:
            dic.firmantes.extend(_firmantes_de(tramo, tipo))
        od.dictamenes.append(dic)

    total = sum(len(d.firmantes) for d in od.dictamenes)
    if total == 0:
        od.motivo = "encontré el ancla pero ningún nombre debajo"
        return od
    od.parseo_ok = True
    return od


def a_filas(od: OrdenDelDia) -> list[dict]:
    """Aplana a una fila por firmante — el grano del contrato de salida.

    **Siempre devuelve al menos una fila.** Una Orden del Día que no se pudo leer
    tiene que quedar en la tabla marcada con su motivo; si devolviera una lista
    vacía, desaparecería del conteo y la cobertura se vería mejor de lo que es.

    Eso pasó de verdad el 21-08-2026: cuando el parser encontraba el ancla pero
    ningún nombre debajo, `od.dictamenes` quedaba poblado y el `for` de abajo no
    agregaba nada. **115 Órdenes del Día de 2.517 se evaporaron** — el resumen
    decía 2.402 leídas y nadie las echaba de menos. Por eso el guardacoches del
    final, y por eso hay un test que lo fija.
    """
    filas = []
    base = {"archivo": od.archivo, "od_numero": od.od_numero,
            "fecha_impresion": od.fecha_impresion,
            "comisiones": ";".join(od.comisiones),
            "expedientes_sumario": ";".join(od.expedientes),
            "parseo_ok": od.parseo_ok, "motivo": od.motivo,
            "origen_firmas": od.origen_firmas,
            "dictamenes_repetidos": od.dictamenes_repetidos}
    vacia = dict(base, dictamen_orden=0, dictamen_clase="", fecha_sala="",
                 firmante_raw="", orden_firma=0, disidencia="", primer_firmante=False,
                 dos_comisiones=False)
    if not od.dictamenes:
        return [vacia]
    for d in od.dictamenes:
        for f in d.firmantes:
            filas.append(dict(base, dictamen_orden=d.orden, dictamen_clase=d.clase,
                              fecha_sala=d.fecha_sala, **f))
    if not filas:
        return [dict(vacia, parseo_ok=False,
                     motivo=od.motivo or "hay dictamen pero no se leyó ningún firmante")]
    return filas


TOPE_PAGINAS = 20          # cuántas páginas lee pdfminer antes de rendirse
SONDA_PAGINAS = 3          # sonda barata para detectar un PDF escaneado
MIN_CHARS_SONDA = 100      # menos que esto en 3 páginas = no hay capa de texto
TOPE_RESCATE = 120         # páginas máximas que lee pypdf en el rescate

# Sonda del ancla, a propósito MÁS SUELTA que `RE_ANCLA`. `texto_de_pdf` mira el
# texto CRUDO —sin pasar por `_normalizar`—, donde la extracción deja espacios
# dobles y corta renglones en cualquier lado; el regex estricto no matcheaba y el
# archivo caía al rescate de pypdf sin necesidad. En `senado-2018-521.pdf` (75 MB,
# 300 páginas) eso significaba recorrerlo entero para nada.
RE_SONDA_ANCLA = re.compile(r"Sala\s+de\s+(?:la\s+|las\s+)?comisi", re.I)

# Reparaciones del texto de pypdf. pypdf saca las palabras pegadas o con espacios
# de más —"Juan C.Scalesi", "Héctor P . Recalde", "Alberto CanteroGutiérrez"— y
# eso rompe el emparejamiento con el padrón, que trabaja por tokens. pdfminer no
# las necesita, así que se aplican SÓLO al texto de pypdf.
_REPARACIONES = [
    (re.compile(r"([A-ZÁÉÍÓÚÑ])\s+\."), r"\1."),                        # 'P .'  -> 'P.'
    (re.compile(r"\.(?=[A-ZÁÉÍÓÚÑ])"), ". "),                           # 'C.Scalesi'
    (re.compile(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])"), " "),   # 'CanteroGutiérrez'
    (re.compile(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ]\.)"), " "),            # 'FabiánF. Peralta'
]


def _reparar_espacios(texto: str) -> str:
    for patron, reemplazo in _REPARACIONES:
        texto = patron.sub(reemplazo, texto)
    return texto


def texto_de_pdf(ruta, tope_paginas: int = TOPE_PAGINAS) -> str:
    """Extrae el texto de una Orden del Día, sin poder colgarse.

    **Por qué no es un `extract_text()` y ya.** pdfminer se cuelga —para siempre,
    no lento— en PDF con muchas fuentes embebidas y sus CMaps. El 21-08-2026
    `139-1.pdf` (2,2 MB, 72 páginas, 58 fuentes, 38 CMaps) frenó dos corridas
    enteras en la misma posición. Medido: 12 páginas en 1,1 s, 20 páginas en
    1,6 s, **30 páginas no termina nunca**.

    La estrategia, entonces:

    1. **pdfminer con tope de páginas.** Es el mejor extractor y el ancla vive
       cerca del principio en casi todas las Órdenes del Día.
    2. **Si no aparece el ancla, pypdf sobre el archivo completo.** pypdf no tiene
       esa patología: el mismo archivo son 2 segundos. Saca peor el espaciado, y
       por eso su texto pasa por `_reparar_espacios`.

    No hay timeouts ni procesos aparte: en Windows eso es caro y frágil. El tope
    de páginas es determinista y hace el mismo trabajo.
    """
    texto = ""
    try:
        from pdfminer.high_level import extract_text
        # Sonda barata de 3 páginas. Sirve para dos cosas: la mayoría de las
        # Órdenes del Día tienen el ancla ahí y se sale enseguida, y las
        # ESCANEADAS se detectan sin pagar el precio completo. `senado-2014-30.pdf`
        # son 21 MB y 85 páginas de imágenes: pdfminer tarda **21 segundos** en
        # sacarle 20 caracteres, y después pypdf recorrería las 85 para no
        # encontrar nada tampoco. Con la sonda son 3 segundos y queda marcada.
        sonda = extract_text(str(ruta), maxpages=SONDA_PAGINAS)
        if len(sonda.strip()) < MIN_CHARS_SONDA:
            return sonda          # sin capa de texto: `parsear` lo marca
        # ⚠️ La sonda NO devuelve el texto aunque encuentre el ancla. Se probó y
        # rompía: una lista de 64 firmantes sigue en la página 4, así que devolver
        # las 3 primeras la cortaba al medio — `139-410.pdf` pasó de 64 firmas a 34
        # sin que nada fallara. La sonda sirve para UNA cosa: detectar el PDF
        # escaneado barato. Leer las 20 páginas cuesta un segundo más y no miente.
        texto = extract_text(str(ruta), maxpages=tope_paginas)
        if RE_SONDA_ANCLA.search(texto):
            return texto
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 - un PDF roto no puede tumbar la corrida
        texto = ""

    try:
        from pypdf import PdfReader
    except ImportError as exc:                                  # pragma: no cover
        if texto:
            return texto
        raise ImportError(
            "hace falta un extractor de PDF: pip install pdfminer.six Y pip install pypdf "
            "(el segundo es el rescate para los PDF que cuelgan al primero)"
        ) from exc
    # el rescate también va con tope: hay Órdenes del Día de 300 páginas y 75 MB
    paginas = PdfReader(str(ruta)).pages
    completo = "\n".join((pag.extract_text() or "") for pag in paginas[:TOPE_RESCATE])
    reparado = _reparar_espacios(completo)
    # si el rescate tampoco encuentra el ancla, se devuelve lo que más prometa
    return reparado if RE_SONDA_ANCLA.search(reparado) else (texto or reparado)


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys

    if len(sys.argv) < 2:
        print("uso: python parser_od.py <archivo.pdf> [...]")
        raise SystemExit(2)
    for ruta in sys.argv[1:]:
        od = parsear(texto_de_pdf(ruta), archivo=str(ruta).split("\\")[-1].split("/")[-1])
        print(json.dumps({
            "archivo": od.archivo, "od_numero": od.od_numero,
            "fecha_impresion": od.fecha_impresion, "comisiones": od.comisiones,
            "expedientes": od.expedientes, "parseo_ok": od.parseo_ok, "motivo": od.motivo,
            "dictamenes": [{"orden": d.orden, "clase": d.clase, "fecha_sala": d.fecha_sala,
                            "n_firmantes": len(d.firmantes),
                            "disidencias": sorted({f["disidencia"] for f in d.firmantes}),
                            "firmantes": [f["firmante_raw"] for f in d.firmantes]}
                           for d in od.dictamenes],
        }, ensure_ascii=False, indent=2))
