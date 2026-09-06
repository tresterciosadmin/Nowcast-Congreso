# -*- coding: utf-8 -*-
"""Tests de datos/expedientes/src/parser_od.py — sin red y sin PDF.

Los textos de abajo son **transcripciones literales** de PDF reales (extraídos
con pdfminer el 21-08-2026), recortados a lo que el parser tiene que entender.
Se guardan como texto y no como PDF para que el test corra en cualquier lado y
sin depender del extractor; los PDF completos quedan en el caché descartable.

Lo que fija cada fixture:

- `DIP_DISIDENCIA` (Diputados, O.D. 346 de 2008): dos comisiones, expediente del
  Senado en el sumario, 24 firmantes plenos y 5 **en disidencia parcial**.
- `DIP_EJECUTIVO` (Diputados, O.D. 292 de 2008): la trampa. Después del
  articulado viene la firma del **Poder Ejecutivo** sobre el mensaje —Cobos y los
  dos Fernández—, que NO firmó ningún dictamen. Si aparecen entre los firmantes,
  el parser está leyendo "cosas que parecen nombres" en vez del bloque correcto.
- `SEN_REVISION` (Senado, O.D. 2 de 2026): la misma fórmula de cierre en la otra
  cámara, sobre un expediente `PE-46/24`. Prueba que un solo parser sirve para
  los dos sistemas de comisiones.

    python datos/expedientes/tests/test_parser_od.py
    python -m pytest datos/expedientes/tests/test_parser_od.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parser_od import _clase_del_dictamen, a_filas, parsear  # noqa: E402

DIP_DISIDENCIA = """CAMARA DE DIPUTADOS DE LA NACION

O.D. Nº 346

SESIONES ORDINARIAS

2008

ORDEN DEL DIA Nº 346

COMISIONES DE PREVENCION DE ADICCIONES Y CONTROL DEL NARCOTRAFICO
Y DE ACCION SOCIAL Y SALUD PUBLICA

Impreso el día 6 de junio de 2008
Término del artículo 113: 18 de junio de 2008

SUMARIO: Programa Nacional de Prevención y
Control de los Trastornos Alimentarios en el ám-
bito del Ministerio de Salud. Creación y cuestio-
nes conexas. (160-S.-2007.)

Dictamen de las comisiones

Honorable Cámara:

Las comisiones de Prevención de Adicciones y
Control del Narcotráfico y de Acción Social y Salud
Pública han considerado el proyecto de ley en revi-
sión, y han tenido a la vista los proyectos de ley de
los señores diputados: Bisutti, 444-D.-08; Sesma,
722-D.-08; y, por las razones expuestas en el informe
que se acompaña, aconsejan su sanción.

Sala de las comisiones, 27 de mayo de 2008.

Graciela M. Giannettasio. – Juan H.
Sylvestre Begnis. – María del C. C.
Rico. – Graciela B. Gutiérrez. – Fabián
F. Peralta. – Juan C. Scalesi. – Adela
R. Segarra. – María J. Areta. – Julio E.
Arriaga. – Griselda A. Baldata. – Ivana
M. Bianchi. – Susana M. Canela. –
Susana E. Díaz. – Mónica H. Fein. –
Héctor Flores. – Eva García de
Moreno. – Nancy S. González. –
Eduardo Lorenzo Borocotó. – Mario H.
Martiarena. – Marta L. Osorio. –
Guillermo A. Pereyra. – Agustín A.
Portela. – Carmen Román. – Pablo V.
Zancada.

En disidencia parcial:

Juan E. Acuña Kunz. – Paula M. Bertol.
– Leonardo A. Gorbacz. – Silvia Storni.
– Mónica L. Torfe.

Buenos Aires, 28 de noviembre de 2007.

Al señor presidente de la Honorable Cámara de
Diputados de la Nación.
"""

DIP_EJECUTIVO = """CAMARA DE DIPUTADOS DE LA NACION

O.D. Nº 292

SESIONES ORDINARIAS

2008

ORDEN DEL DIA Nº 292

COMISIONES DE DERECHOS HUMANOS
Y GARANTIAS Y DE PRESUPUESTO Y HACIENDA

Impreso el día 30 de mayo de 2008
Término del artículo 113: 10 de junio de 2008

SUMARIO: Convenio entre el Estado nacional y la
Ciudad Autónoma de Buenos Aires. Ratifica-
ción. (1-P.E.-2008.)

Dictamen de las comisiones

Honorable Cámara:

Las comisiones de Derechos Humanos y Garan-
tías y de Presupuesto y Hacienda han considerado
el proyecto del Poder Ejecutivo, mensaje 352, y
aconsejan su sanción.

Sala de las comisiones, 21 de mayo de 2008.

Remo G. Carlotto. – Walter A. Agosto. –
Hugo R. Perié. – Miguel A. Giubergia.
– Juan C. D. Gullo. – César A. Albrisi.
– Laura G. Montero. – Fabián F.
Peralta. – María J. Acosta.

PROYECTO DE LEY

El Senado y Cámara de Diputados,…

Artículo 1° – Ratifícase el Convenio celebrado el
20 de noviembre de 2007.

Art. 2° – Comuníquese al Poder Ejecutivo.

JULIO C. COBOS.
Alberto A. Fernández. – Aníbal D.

Fernández.
"""

SEN_REVISION = """CONGRESO NACIONAL

CÁMARA DE SENADORES

SESIONES ORDINARIAS DE 2026

ORDEN DEL DÍA Nº 2

10 de marzo de 2026

SUMARIO

COMISIÓN DE RELACIONES EXTERIORES Y CULTO
Y DE PRESUPUESTO Y HACIENDA

Dictamen en el mensaje y proyecto de ley del Poder Ejecutivo Nacional
que aprueba el Protocolo de Enmienda al Convenio con el Gobierno de
la República Francesa. (PE-46/24)

DICTAMEN DE COMISIÓN

Honorable Senado:

Las Comisiones de Relaciones Exteriores y Culto y de
Presupuesto y Hacienda han considerado el proyecto de ley del Poder
Ejecutivo Nacional, registrado bajo expediente PE-46/24, y aconsejan
su aprobación.

Sala de las comisiones, 10 de marzo de 2026.

Francisco M. Paoltroni – Ezequiel Atauche – Luis A. Juez – Agustín A.
Monteverde – Eduardo A. Vischi – Patricia Bullrich – Sonia E. Rojas
Decut – Ivanna M. Arrascaeta – Mariana Juri – Bartolomé E. Abdala –
María V. Huala – Flavio S. Fama – Maximiliano Abad – Carlos M.
Espínola – Daniel R. Kroneberger – Edith E. Terenzi – Gonzalo Guzmán
Coraita – Beatriz L. Ávila – María B. Monte de Oca – Mario P. Cervi –
Guillermo E. Andrada.
"""


# Transcripción literal de `senado-2008-1168.pdf` (SIPA/AFJP), recortada. Es EL
# testigo del bug del 04-09-2026: el sumario dice "Dictamen de mayoría" y el
# cuerpo abre con la genérica "DICTAMEN DE COMISION". Con la regla vieja —la
# última cabecera gana— la genérica pisaba al rótulo y el parquet lo guardaba
# como `unico`. Cero mayorías en 18.105 filas del Senado salían de acá.
SEN_MAYORIA_EN_SUMARIO = """CONGRESO NACIONAL

CAMARA  DE  SENADORES

SESIONES ORDINARIAS DE 2008

ORDEN DEL DIA Nº 1168

Impreso el día 12 de noviembre de 2008

SUMARIO

COMISION DE PRESUPUESTO Y HACIENDA Y DE TRABAJO Y
PREVISIÓN SOCIAL

Dictamen  de  mayoría  en  el  proyecto  de  ley  venido  en  revisión  por  el
que se dispone la unificación del Sistema Integrado de Jubilaciones y
Pensiones en un único régimen previsional público. (CD-70/08)

DICTAMEN DE COMISION

Honorable Senado:

Vuestras Comisiones de PRESUPUESTO Y HACIENDA y de TRABAJO Y
PREVISIÓN SOCIAL, han considerado el proyecto de ley en revisión
registrado bajo el número CD-70/08 y os aconsejan la aprobación del mismo.

Sala de las Comisiones, 12 de Noviembre de 2008

Roberto F. Ríos.- Julio A. Miranda.- Isabel J. Viudes.- Eric Calcagno y
Maillman.- Marcel A. H. Guinle.- Nicolás A. Fernández.-

EN DISIDENCIA PARCIAL:

Roxana I. Latorre.
"""

# Transcripción literal de `senado-2009-485.pdf`: la OTRA forma del Senado, la
# calificada en el cuerpo — "DICTAMEN DE COMISIÓN EN MAYORIA". El regex viejo la
# leía por la rama genérica ("Dictamen de comisión") y devolvía `unico`.
SEN_COMISION_EN_MAYORIA = """CONGRESO NACIONAL

CAMARA DE SENADORES

ORDEN DEL DIA Nº 485

Impreso el día 24 de septiembre de 2009

SUMARIO

COMISION DE PRESUPUESTO Y HACIENDA

Dictamen de mayoría en el proyecto de ley venido en revisión por el que
se modifican las leyes de impuestos internos y al valor agregado.(CD-31/09)

DICTAMEN DE COMISIÓN EN MAYORIA

Honorable Senado:

Vuestra Comisión de PRESUPUESTO Y HACIENDA ha considerado el
proyecto de ley en revisión registrado bajo el número CD-31/09.

Sala de la comisión, 24 de septiembre de 2009

Carlos A. Verna.- Roberto G. Basualdo.- José M. A. Mayans.- Elena M.
Corregido.- Nicolás A. Fernández.
"""

# Transcripción literal de `senado-2018-16.pdf` (Parque Nacional Aconquija): el
# MISMO dictamen impreso dos veces, con la misma fecha de sala y los mismos
# firmantes, y con un ANEXO catastral en el medio. Antes del 04-09 esto producía
# (1) un "dictamen de minoría" que no existe —las únicas 19 minorías del Senado
# en todo el parquet— y (2) nombres inventados leídos del padrón catastral.
SEN_REIMPRESO = """CONGRESO NACIONAL

CÁMARA DE SENADORES

ORDEN DEL DÍA Nº 16

Impreso el día 4 de abril de 2018

SUMARIO

COMISIÓN DE ASUNTOS ADMINISTRATIVOS Y MUNICIPALES

Dictamen en el proyecto de ley venido en revisión por el que se acepta la
cesión de la jurisdicción efectuada por la provincia de Tucumán. (CD-68/17)

DICTAMEN DE COMISIÓN

Honorable Senado de la Nación:

Art. 8º.- Comuníquese al Poder Ejecutivo Nacional.

Sala de la comision, 4 de abril de 2018

Julio C. Martínez.- Fernando E. Solanas.- Esteban J. Bullrich.- José A.
Ojeda.- Julio C. Cobos.-

En disidencia parcial: Beatriz G. Mirkin.-

ANEXO I

1) Padrón denominado "QUEBRADA DEL PORTUGUES" Matrícula 35234, Orden
398, Circunscripción 1, Sección D, Lámina 287.

Sala de la comision , 4 de abril de 2018

Julio C. Martínez.- Fernando E. Solanas.- Esteban J. Bullrich.- José A.
Ojeda.- Julio C. Cobos.-

En disidencia parcial: Beatriz G. Mirkin
"""


# ── 06-09-2026: las tres formas que caían en `desconocido` sin tener por qué ──
# Salieron de leer las 95 Órdenes del Día (39 del Senado + 56 de Diputados) que el
# parquet regenerado dejaba en `desconocido`. Las tres FALLAN con el parser del 04-09.

# 1. El Senado tiene una CUARTA forma: dictamen a secas, sin "de comisión" ni
#    calificativo. Las 39 del Senado usan ésta, sin una sola excepción.
SEN_DICTAMEN_EN_EL = """CONGRESO NACIONAL

CÁMARA DE SENADORES

ORDEN DEL DÍA Nº 876

SUMARIO

Dictamen en el proyecto de ley de la señora senadora Latorre, por el que se
declara de interés el aniversario de la ciudad. (S-1234/14)

Honorable Senado:

Vuestra comisión ha considerado el proyecto y aconseja su aprobación.

Sala de la comisión, 12 de noviembre de 2014

Ada R. del Valle Iturrez de Cappellini.- Marta Varela.
"""

# 3. La cabecera está DESPUÉS del ancla: el documento cierra con "Sala de la
#    comisión" antes de abrir el cuerpo del dictamen (`126-445.pdf`).
DIP_CABECERA_DESPUES = """ORDEN DEL DÍA Nº 445

Sala de la comisión, 15 de septiembre de 2008

Dictamen de comisión

Honorable Cámara:

Las comisiones han considerado el proyecto y aconsejan su aprobación.

Sala de las comisiones, 15 de septiembre de 2008

Juan C. Perez.- Maria L. Gonzalez.
"""

# 4. CONTROL: la forma nueva NO puede pisar a una calificada. Si "Dictamen de
#    mayoría en el proyecto..." cayera en la alternativa genérica, el arreglo del
#    04-09 (ADR-0017) se desharía en silencio.
SEN_MAYORIA_CON_EN_EL = """ORDEN DEL DÍA Nº 1168

SUMARIO

Dictamen de mayoría en el proyecto de ley venido en revisión por el que se
dispone la unificación del Sistema Integrado de Jubilaciones y Pensiones.

DICTAMEN DE COMISIÓN

Honorable Senado:

Sala de la comisión, 20 de noviembre de 2008

Nicolas A. Fernandez.- Carlos A. Rossi.
"""

# Un dictamen SIN ninguna cabecera reconocible: no se puede afirmar que sea único.
SEN_SIN_CABECERA = """CONGRESO NACIONAL

CÁMARA DE SENADORES

ORDEN DEL DÍA Nº 999

Impreso el día 3 de mayo de 2017

SUMARIO

Honorable Senado:

Las comisiones han considerado el asunto y aconsejan su aprobación.

Sala de la comisión, 3 de mayo de 2017

Ada R. del Valle Iturrez de Cappellini.- Marta Varela.- Julio C. Cobos.
"""


def _correr() -> int:
    fallos: list[str] = []
    corridos = 0

    def check(cond: bool, msg: str) -> None:
        nonlocal corridos
        corridos += 1
        if not cond:
            fallos.append(msg)
            print(f"  FALLA: {msg}")

    # ─────────────── Diputados con disidencia parcial ───────────────
    print("Diputados O.D. 346/2008 — dos comisiones y disidencia parcial")
    od = parsear(DIP_DISIDENCIA, "126-346.pdf")
    check(od.parseo_ok, f"tendría que parsear ok, dijo: {od.motivo}")
    check(od.od_numero == "346", f"número de OD: {od.od_numero!r}")
    check(od.fecha_impresion == "6 de junio de 2008", f"fecha de impresión: {od.fecha_impresion!r}")
    check(len(od.comisiones) == 2, f"dos comisiones, encontró {od.comisiones}")
    check("160-S-2007" in od.expedientes, f"expediente del sumario: {od.expedientes}")
    check("444-D-08" not in od.expedientes,
          "los expedientes 'tenidos a la vista' del cuerpo NO son los del sumario")
    check(len(od.dictamenes) == 1, f"un solo dictamen, encontró {len(od.dictamenes)}")
    d = od.dictamenes[0]
    check(d.fecha_sala == "27 de mayo de 2008", f"fecha de sala: {d.fecha_sala!r}")
    plenos = [f for f in d.firmantes if f["disidencia"] == "none"]
    disidentes = [f for f in d.firmantes if f["disidencia"] == "parcial"]
    check(len(plenos) == 24, f"24 firmantes plenos, contó {len(plenos)}")
    check(len(disidentes) == 5, f"5 en disidencia parcial, contó {len(disidentes)}")
    check(plenos[0]["firmante_raw"] == "Graciela M. Giannettasio", f"primer firmante: {plenos[0]}")
    check(plenos[0]["primer_firmante"] is True, "el primero queda marcado como primer firmante")
    nombres = [f["firmante_raw"] for f in d.firmantes]
    check("Eva García de Moreno" in nombres, "un nombre partido en dos líneas se rearma entero")
    check("Juan E. Acuña Kunz" in [f["firmante_raw"] for f in disidentes],
          "el primero de la disidencia entra como disidente")
    check(not any(f["primer_firmante"] for f in disidentes),
          "un disidente NO puede ser el primer firmante del dictamen")

    # ─────────────── la trampa: la firma del Poder Ejecutivo ───────────────
    print("Diputados O.D. 292/2008 — la firma del Ejecutivo no es del dictamen")
    od2 = parsear(DIP_EJECUTIVO, "126-292.pdf")
    check(od2.parseo_ok, f"tendría que parsear ok, dijo: {od2.motivo}")
    firmas = [f["firmante_raw"] for f in od2.dictamenes[0].firmantes]
    check(len(firmas) == 9, f"9 firmantes del dictamen, contó {len(firmas)}: {firmas}")
    for intruso in ("Alberto A. Fernández", "Aníbal D. Fernández", "JULIO C. COBOS"):
        check(intruso not in firmas, f"{intruso} firmó el mensaje del Ejecutivo, NO el dictamen")
    check("Remo G. Carlotto" in firmas, "el primer firmante real sí está")

    # ─────────────── Senado, mismo parser ───────────────
    print("Senado O.D. 2/2026 — la otra cámara con el mismo ancla")
    od3 = parsear(SEN_REVISION, "senado-2026-2.pdf")
    check(od3.parseo_ok, f"tendría que parsear ok, dijo: {od3.motivo}")
    check(od3.od_numero == "2", f"número de OD: {od3.od_numero!r}")
    f3 = od3.dictamenes[0].firmantes
    check(len(f3) == 21, f"21 senadores firmantes, contó {len(f3)}")
    check(f3[0]["firmante_raw"] == "Francisco M. Paoltroni", f"primer firmante: {f3[0]}")
    check(f3[-1]["firmante_raw"] == "Guillermo E. Andrada", f"último firmante: {f3[-1]}")
    check(all(f["disidencia"] == "none" for f in f3), "este dictamen no tiene disidencias")

    # ─────────────── el carácter del dictamen en el Senado (04-09-2026) ───────────────
    print("Senado O.D. 1168/2008 — 'Dictamen de mayoría' va en el SUMARIO")
    od4 = parsear(SEN_MAYORIA_EN_SUMARIO, "senado-2008-1168.pdf")
    check(od4.parseo_ok, f"tendría que parsear ok, dijo: {od4.motivo}")
    check(od4.dictamenes[0].clase == "mayoria",
          "el rótulo del sumario manda: la genérica 'DICTAMEN DE COMISION' del "
          f"cuerpo NO puede pisarlo. Dio {od4.dictamenes[0].clase!r}")
    check({f["disidencia"] for f in od4.dictamenes[0].firmantes} == {"none", "parcial"},
          "y la disidencia parcial se sigue leyendo")

    print("Senado O.D. 485/2009 — 'DICTAMEN DE COMISIÓN EN MAYORIA'")
    od5 = parsear(SEN_COMISION_EN_MAYORIA, "senado-2009-485.pdf")
    check(od5.dictamenes[0].clase == "mayoria",
          f"la forma calificada del cuerpo también es mayoría, dio {od5.dictamenes[0].clase!r}")

    print("Senado O.D. 16/2018 — el mismo dictamen impreso dos veces")
    od6 = parsear(SEN_REIMPRESO, "senado-2018-16.pdf")
    check(len(od6.dictamenes) == 1,
          f"una reimpresión no es un segundo despacho, dio {len(od6.dictamenes)}")
    check(od6.dictamenes_repetidos == 1,
          f"y la reimpresión queda contada, no escondida: {od6.dictamenes_repetidos}")
    check(od6.dictamenes[0].clase != "minoria",
          "y sobre todo NO puede inventar un dictamen de minoría")
    nombres = {f["firmante_raw"] for f in od6.dictamenes[0].firmantes}
    check(not any("QUEBRADA" in n.upper() or "Matrícula" in n for n in nombres),
          f"el ANEXO catastral no es una lista de firmas: {sorted(nombres)}")
    check(len(od6.dictamenes[0].firmantes) == 6,
          f"5 firmas plenas + 1 en disidencia, dio {len(od6.dictamenes[0].firmantes)}")

    print("sin cabecera de dictamen → 'desconocido', nunca 'unico'")
    od7 = parsear(SEN_SIN_CABECERA, "sin-cabecera.pdf")
    check(od7.parseo_ok, f"las firmas se leen igual, dijo: {od7.motivo}")
    check(od7.dictamenes[0].clase == "desconocido",
          "no encontrar el rótulo NO es lo mismo que 'despacho único': "
          f"dio {od7.dictamenes[0].clase!r}")

    print("las tres formas que caían en 'desconocido' y no tenían por qué (06-09)")
    o1 = parsear(SEN_DICTAMEN_EN_EL, "senado-2014-876.pdf")
    check(o1.dictamenes[0].clase == "unico",
          "el Senado tiene una CUARTA forma, 'Dictamen EN el proyecto de ley': es un "
          f"dictamen a secas, o sea unico. Dio {o1.dictamenes[0].clase!r}")
    # La cabecera arranca EXACTAMENTE donde arranca el bloque. Se chequea la función
    # directamente y no un documento entero, porque la posición la elige
    # `_bloques_sin_ancla` y un fixture sintético no la reproduce: el primer intento de
    # este test PASABA con el parser viejo, o sea que no probaba nada. En el documento
    # real (`131-2469.pdf`) el bloque y "Dictamen de mayoría" arrancan los dos en 627 y
    # se perdía una MAYORÍA entera por el intervalo medio abierto.
    check(_clase_del_dictamen("Dictamen de mayoría\nHonorable Cámara:", 0, 0) == "mayoria",
          "con la cabecera en la misma posición que el ancla, `finditer(t, 0, pos)` la "
          "excluye por un carácter: tiene que rescatarla hacia adelante")
    check(_clase_del_dictamen("Dictamen de las comisiones\nHonorable Cámara:", 0, 0) == "unico",
          "lo mismo con la cabecera genérica")
    # y el rescate NO puede robarle la cabecera al dictamen siguiente
    dos = "xxxx\nDictamen de minoría\nfirmas"
    check(_clase_del_dictamen(dos, 0, 0, 4) == "desconocido",
          "con `fin` en 4, el rescate no puede llegar a la cabecera del que sigue: "
          f"dio {_clase_del_dictamen(dos, 0, 0, 4)!r}")
    o3 = parsear(DIP_CABECERA_DESPUES, "126-445.pdf")
    check(o3.dictamenes[0].clase == "unico",
          "la cabecera puede estar DESPUÉS del ancla cuando el documento cierra antes "
          f"de abrir el cuerpo. Dio {o3.dictamenes[0].clase!r}")

    print("y el control: la forma nueva NO pisa a una calificada (ADR-0017)")
    o4 = parsear(SEN_MAYORIA_CON_EN_EL, "senado-2008-1168.pdf")
    check(o4.dictamenes[0].clase == "mayoria",
          "'Dictamen de mayoría EN el proyecto...' tiene que caer en la alternativa "
          f"calificada, no en la genérica nueva. Dio {o4.dictamenes[0].clase!r}")

    print("Diputados: la cabecera genérica sigue dando 'unico'")
    check(od.dictamenes[0].clase == "unico",
          f"'Dictamen de las comisiones' es único, dio {od.dictamenes[0].clase!r}")

    # ─────────────── falla ruidosa ───────────────
    print("un PDF escaneado (sin capa de texto)")
    # Un PDF de imágenes devuelve un puñado de caracteres. `senado-2014-30.pdf` son
    # 21 MB y 85 páginas y pdfminer le saca 20 caracteres en 21 segundos.
    escaneado = parsear("O.D. 30\n\x0c\x0c", "escaneado.pdf")
    check(escaneado.parseo_ok is False, "un PDF sin texto no puede dar parseo_ok=True")
    check("capa de texto" in escaneado.motivo,
          f"el motivo tiene que distinguirlo de un parseo fallido: {escaneado.motivo!r}")

    print("un texto largo que NO es una Orden del Día")
    ajeno = parsear("Esto no es una Orden del Día, es cualquier cosa. " * 8, "roto.pdf")
    check(ajeno.parseo_ok is False, "un texto sin el ancla no puede dar parseo_ok=True")
    check("Sala de las comisiones" in ajeno.motivo,
          f"acá el motivo SÍ tiene que ser el del ancla: {ajeno.motivo!r}")
    filas = a_filas(ajeno)
    check(len(filas) == 1 and filas[0]["parseo_ok"] is False,
          "una OD ilegible entra igual a la salida, marcada; no desaparece del conteo")

    # ─────────────── una OD con ancla pero sin nombres NO puede desaparecer ───────────────
    print("ancla presente, ningún nombre debajo")
    hueca = parsear("""ORDEN DEL DIA Nº 999

COMISION DE PRESUPUESTO Y HACIENDA

Impreso el día 1 de junio de 2010

Dictamen de comisión

Honorable Cámara:

Sala de la comisión, 20 de mayo de 2010.

PROYECTO DE LEY

Artículo 1° - Lo que sea.
""", "hueca.pdf")
    check(hueca.parseo_ok is False, "sin nombres no puede dar parseo_ok=True")
    filas_h = a_filas(hueca)
    check(len(filas_h) == 1,
          f"tiene que devolver UNA fila marcada, no cero: dio {len(filas_h)}")
    check(filas_h[0]["parseo_ok"] is False, "y esa fila va marcada como no leída")
    check(bool(filas_h[0]["motivo"]), "y con motivo")
    check(filas_h[0]["archivo"] == "hueca.pdf",
          "con el archivo, para que se pueda contar en la cobertura")

    # ─────────────── el aplanado ───────────────
    print("aplanado a filas")
    filas = a_filas(od)
    check(len(filas) == 29, f"29 filas (24 + 5), dio {len(filas)}")
    check(all(f["od_numero"] == "346" for f in filas), "todas las filas llevan el número de OD")
    check({f["disidencia"] for f in filas} == {"none", "parcial"}, "los dos estados de disidencia")

    print(f"\n{corridos - len(fallos)}/{corridos} OK")
    if fallos:
        print(f"\n{len(fallos)} FALLAS:")
        for f in fallos:
            print(f"  - {f}")
    return len(fallos)


def test_parser_od() -> None:
    assert _correr() == 0


if __name__ == "__main__":
    sys.exit(1 if _correr() else 0)
