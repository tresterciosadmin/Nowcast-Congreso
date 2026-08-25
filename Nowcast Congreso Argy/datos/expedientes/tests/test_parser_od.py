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

from parser_od import a_filas, parsear  # noqa: E402

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
