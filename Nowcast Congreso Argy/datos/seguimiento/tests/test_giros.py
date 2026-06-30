"""Tests del parser de giros contra fixtures HTML que replican las tablas reales.

Corre sin red: `python tests/test_giros.py` (desde datos/seguimiento/).
Valida la LÓGICA de parseo. La validación de selectores en vivo se hace en una
PC con internet vía el CLI de giros.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import giros  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def _ok(cond, msg):
    print(("PASS" if cond else "FAIL"), "-", msg)
    assert cond, msg


def test_diputados():
    html = (FIX / "diputados_2832-D-2026.html").read_text(encoding="utf-8")
    f = giros.parse_diputados(html, "2832-D-2026", "http://x")
    _ok(f.fuente_ok, "dip: fuente reconocida")
    _ok(f.expediente == "2832-D-2026", "dip: expediente")
    _ok(f.fecha_ingreso == "2026-06-16", f"dip: fecha_ingreso = {f.fecha_ingreso}")
    _ok(f.sumario and "ANTISEMITISMO" in f.sumario, "dip: sumario")
    _ok(f.pdf_url and f.pdf_url.startswith("http") and "detalle_tp_adjunto" in f.pdf_url,
        "dip: pdf_url absoluta")
    _ok(len(f.firmantes) == 4, f"dip: 4 firmantes ({len(f.firmantes)})")
    _ok(f.firmantes[0].bloque == "PRO", "dip: bloque firmante")
    _ok(len(f.giros) == 2, f"dip: 2 giros ({len(f.giros)})")
    _ok(f.giros[0].comision == "DERECHOS HUMANOS Y GARANTIAS",
        f"dip: comision limpia = {f.giros[0].comision!r}")
    _ok(f.giros[0].competencia_primaria, "dip: primera competencia detectada")
    _ok(not f.giros[1].competencia_primaria, "dip: segunda sin competencia primaria")
    _ok(len(f.tramite) == 2, f"dip: 2 movimientos ({len(f.tramite)})")
    _ok(f.estado == "en_comision", f"dip: estado = {f.estado}")
    print(" --> ficha diputados OK\n")


def test_senado():
    html = (FIX / "senado_1091.26.html").read_text(encoding="utf-8")
    f = giros.parse_senado(html, "1091-S-2026", "http://x")
    _ok(f.fuente_ok, "sen: fuente reconocida")
    _ok(f.sumario and "MECENAZGO" in f.sumario, "sen: sumario/extracto")
    _ok(f.fecha_ingreso == "2026-06-24", f"sen: fecha_ingreso = {f.fecha_ingreso}")
    _ok(len(f.firmantes) == 1 and "Abad" in f.firmantes[0].nombre, "sen: autor (1, sin duplicar)")
    _ok(f.firmantes[0].nombre == "Abad, Maximiliano", f"sen: autor normalizado = {f.firmantes[0].nombre!r}")
    _ok(f.pdf_url and f.pdf_url.startswith("http") and "downloadPdf" in f.pdf_url,
        "sen: pdf_url absoluta (urljoin)")
    _ok(len(f.giros) == 2, f"sen: 2 giros ({len(f.giros)})")
    _ok(f.giros[0].comision == "DE DEPORTE", f"sen: comision = {f.giros[0].comision!r}")
    _ok(f.giros[0].orden == 1, f"sen: orden de giro = {f.giros[0].orden}")
    _ok(f.giros[1].orden == 2, "sen: orden de giro 2")
    _ok(f.giros[0].fecha_ingreso == "2026-06-24", "sen: fecha ingreso giro")
    _ok(f.estado == "en_comision", f"sen: estado = {f.estado}")
    print(" --> ficha senado OK\n")


def test_denominadores():
    _ok(giros.normalizar_denominador_dip(" 2832-d-2026 ") == "2832-D-2026", "denom dip normaliza")
    _ok(giros.denominador_senado(1091, 26) == "1091-S-2026", "denom senado año corto")
    _ok(giros.denominador_senado("1040", "2026") == "1040-S-2026", "denom senado año largo")
    try:
        giros.normalizar_denominador_dip("basura")
        _ok(False, "denom dip inválido debe fallar")
    except ValueError:
        _ok(True, "denom dip inválido lanza ValueError")
    print(" --> denominadores OK\n")


if __name__ == "__main__":
    test_denominadores()
    test_diputados()
    test_senado()
    print("TODOS LOS TESTS PASARON")
