"""Tests del seguidor de giros.

- Lógica pura (sin red): detección de cámara, normalización de expediente,
  construcción de URLs, inferencia de estado.
- Parsing: fixtures HTML que reconstruyen la estructura real de las fichas
  verificadas (Diputados 2832-D-2026 y Senado 1091/26, jun-2026).
"""
import seguidor_giros as sg


# ── Lógica pura ──────────────────────────────────────────────────────────────

def test_deteccion_camara():
    assert sg.detectar_camara("2832-D-2026") == "diputados"
    assert sg.detectar_camara("2137-D-2026") == "diputados"
    assert sg.detectar_camara("S-1091/26") == "senado"
    assert sg.detectar_camara("1091/26") == "senado"
    assert sg.detectar_camara("1091/2026") == "senado"


def test_normalizacion_dip():
    assert sg.normalizar_dip("2832-d-2026") == "2832-D-2026"
    assert sg.normalizar_dip(" 15-PE-2025 ") == "15-PE-2025"


def test_normalizacion_sen():
    assert sg.normalizar_sen("S-1091/26") == ("1091", "26")
    assert sg.normalizar_sen("1091 / 2026") == ("1091", "2026")


def test_urls():
    assert sg.url_diputados("sajmechet", "2832-D-2026") == \
        "https://www.hcdn.gov.ar/diputados/sajmechet/proyecto.html?exp=2832-D-2026"
    assert sg.url_senado("S-1091/26") == \
        "https://www.senado.gob.ar/parlamentario/comisiones/verExp/1091.26/S/PL"


def test_diputados_exige_slug():
    try:
        sg.url_diputados("", "2832-D-2026")
    except ValueError:
        return
    raise AssertionError("debió exigir slug")


def test_inferir_estado():
    giros = [sg.Giro(comision="DEPORTE")]
    assert sg.inferir_estado([], []) == "INGRESADO"
    assert sg.inferir_estado(giros, []) == "EN_COMISION"
    assert sg.inferir_estado(giros, [sg.Movimiento("dip", "DICTAMEN DE COMISION")]) == "CON_DICTAMEN"
    assert sg.inferir_estado(giros, [sg.Movimiento("dip", "MEDIA SANCION")]) == "MEDIA_SANCION"
    assert sg.inferir_estado(giros, [sg.Movimiento("dip", "SANCION DEFINITIVA")]) == "SANCIONADO"
    # El más avanzado gana, sin importar el orden de los movimientos.
    movs = [sg.Movimiento("dip", "MEDIA SANCION"), sg.Movimiento("sen", "DICTAMEN")]
    assert sg.inferir_estado(giros, movs) == "MEDIA_SANCION"


# ── Fixtures HTML (estructura real reconstruida) ─────────────────────────────

HTML_DIP = """
<html><body>
<h1>PROYECTO DE LEY</h1>
<p>Expediente: <b>2832-D-2026</b></p>
<p>Fecha:<b>16/06/2026</b></p>
<p><b>Sumario:</b> ACTOS DISCRIMINATORIOS - LEY 23592 -. MODIFICACIONES INCORPORANDO EL ANTISEMITISMO.</p>
<a href="https://www.hcdn.gob.ar/proyectos/detalle_tp_adjunto/index.html?id=292542">Ver documento original</a>
<h3>Giro a comisiones en Diputados</h3>
<table><tr><th>Comisión</th></tr>
<tr><td>DERECHOS HUMANOS Y GARANTIAS <b>(Primera Competencia)</b></td></tr>
<tr><td>LEGISLACION PENAL</td></tr>
</table>
<h3>Trámite</h3>
<table><tr><th>Cámara</th><th>Movimiento</th><th>Fecha</th><th>Resultado</th></tr>
<tr><td>Diputados</td><td>SOLICITUD DE SER COFIRMANTE DE LA DIPUTADA AJMECHET</td><td></td><td></td></tr>
</table>
</body></html>
""" * 1 + ("x" * 800)  # padding para superar el umbral anti-bloqueo

HTML_SEN = """
<html><body>
<h1>Número de Expediente 1091/26</h1>
<table><caption>Datos</caption>
<tr><th>N°</th><th>Origen</th><th>Tipo</th><th>Extracto</th></tr>
<tr><td>1091/26</td><td>Senado De La Nación</td><td>Proyecto De Ley</td>
    <td>ABAD: PROYECTO DE LEY QUE CREA EL REGIMEN NACIONAL DE MECENAZGO DEPORTIVO.</td></tr>
</table>
<table><caption>Fechas en Dir. Mesa de Entradas</caption>
<tr><th>MESA DE ENTRADAS</th><th>DADO CUENTA</th><th>DAE</th></tr>
<tr><td>24-06-2026</td><td>SIN FECHA</td><td>46/2026</td></tr>
</table>
<table><caption>Giros del Expediente a Comisiones</caption>
<tr><th>COMISIÓN</th><th>FECHA DE INGRESO</th><th>FECHA DE EGRESO</th></tr>
<tr><td>DE DEPORTE ORDEN DE GIRO: 1</td><td>24-06-2026</td><td></td></tr>
<tr><td>DE PRESUPUESTO Y HACIENDA ORDEN DE GIRO: 2</td><td>24-06-2026</td><td></td></tr>
</table>
<table><caption>Trámite Legislativo</caption>
<tr><th>Movimiento</th></tr>
</table>
<a href="/parlamentario/parlamentaria/497423/downloadPdf">Texto Original</a>
</body></html>
""" + ("x" * 800)


def test_parse_diputados():
    seg = sg.seguir("2832-D-2026", slug_autor="sajmechet", html_text=HTML_DIP)
    assert seg.camara == "diputados"
    assert seg.fecha_ingreso == "16/06/2026"
    assert "ANTISEMITISMO" in (seg.sumario or "")
    assert len(seg.giros) == 2
    assert seg.giros[0].comision == "DERECHOS HUMANOS Y GARANTIAS"
    assert seg.giros[0].primera_competencia is True
    assert seg.giros[1].primera_competencia is False
    assert seg.pdf_url and "detalle_tp_adjunto" in seg.pdf_url
    assert len(seg.movimientos) == 1
    assert seg.estado == "EN_COMISION"


def test_parse_senado():
    seg = sg.seguir("S-1091/26", html_text=HTML_SEN)
    assert seg.camara == "senado"
    assert seg.url.endswith("/verExp/1091.26/S/PL")
    assert "MECENAZGO" in (seg.sumario or "")
    assert seg.fecha_ingreso == "24-06-2026"
    assert len(seg.giros) == 2
    assert seg.giros[0].comision == "DE DEPORTE"
    assert seg.giros[0].orden == 1
    assert seg.giros[0].fecha_ingreso == "24-06-2026"
    assert seg.giros[1].orden == 2
    assert seg.pdf_url == "https://www.senado.gob.ar/parlamentario/parlamentaria/497423/downloadPdf"
    assert seg.estado == "EN_COMISION"


def test_fuente_sospechosa():
    try:
        sg.seguir("S-1091/26", html_text="<html>just a moment...</html>")
    except sg.FuenteSospechosa:
        return
    raise AssertionError("debió detectar fuente sospechosa")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    ok = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        ok += 1
    print(f"\n{ok}/{len(fns)} tests OK")
