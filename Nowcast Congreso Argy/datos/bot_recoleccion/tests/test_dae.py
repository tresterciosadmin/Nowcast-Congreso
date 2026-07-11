"""Tests OFFLINE del adaptador DAE del Senado (sin red).
Correr:  python datos/bot_recoleccion/tests/test_dae.py"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dae_senado import parse_dae, _form_dae

FIX = Path(__file__).parent / "fixtures"
OK = 0
def check(c, m):
    global OK
    assert c, f"FALLO: {m}"
    OK += 1; print("  ok:", m)

html = (FIX / "dae_32_2026.html").read_text(encoding="utf-8")
ident, filas = parse_dae(html)
check(ident == {"numero": 32, "anio": 2026}, "identidad del DAE (generarPdf)")
check(len(filas) == 2, "2 expedientes en la tabla")
f0 = filas[0]
check(f0["expediente"] == "PE-129/26-DC", "expediente normalizado sin espacios")
check(f0["fecha_mesa"] == "2026-04-30", "fecha ISO")
check(f0["dae_numero"] == 32 and f0["dae_anio"] == 2026, "nro/año del DAE por fila")
check("BICAMERAL" in f0["giros"], "giros capturados")
check("JEFATURA" in f0["extracto"], "extracto capturado")
check(f0["expediente_url"].endswith("/verExp/129.26/PE/DC"), "URL verExp limpia (sin query)")
check(f0["texto_url"].endswith("/verPDFdaedigital/201067"), "URL del texto")
check(filas[1]["expediente"] == "S-450/26-PL", "expediente de senador")
accion = _form_dae(BeautifulSoup(html, "html.parser"), 30, 2026)
check(accion is not None, "form del buscador encontrado")
url, payload = accion
check(payload["busqueda_dae[numero]"] == "30" and payload["busqueda_dae[anio]"] == "2026",
      "payload pisa numero y año")
check(payload["busqueda_dae[_token]"] == "tok9", "token preservado")
print(f"\nTODOS LOS CHEQUEOS OK ({OK})")
