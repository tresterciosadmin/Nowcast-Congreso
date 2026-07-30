"""Test OFFLINE del scraper de jefes de bloque (fixture del HTML oficial)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scrape_jefes_bloque import parse_jefes

HTML = """<html><body>
<h2>LA LIBERTAD AVANZA95</h2>
<p>bornoroni gabrielPresidente</p><p>ajmechet sabrina</p>
<h2>PRO12</h2>
<p>ritondo cristian a.Presidente</p><p>yeza martín</p>
<h2>COALICION CIVICA2</h2>
<p>ferraro maximilianoPresidente</p>
<h2>SECCION SIN NUMERO</h2><p>texto suelto</p>
</body></html>"""
OK = 0
def check(c, m):
    global OK
    assert c, f"FALLO: {m}"
    OK += 1; print("  ok:", m)

f = parse_jefes(HTML, "2026-07-30")
check(len(f) == 3, "3 bloques con presidente (ignora sección sin número)")
check(f[0]["nombre"] == "BORNORONI GABRIEL", "nombre sin el sufijo 'Presidente'")
check(f[0]["bloque"] == "LA LIBERTAD AVANZA", "bloque sin el número de bancas")
check("95 bancas" in f[0]["nota"], "bancas en la nota")
check(f[1]["nombre"] == "RITONDO CRISTIAN A.", "segundo bloque")
check(f[2]["bloque"] == "COALICION CIVICA" and f[2]["confianza"] == "ALTA", "tercero + confianza")
check(all(x["camara"] == "diputados" and x["desde"] == "2026-07-30" for x in f), "cámara y snapshot")
check(parse_jefes("<html><body><h2>ALGO5</h2><p>nadie</p></body></html>", "2026-07-30") == [],
      "sin marca Presidente -> no inventa")
print(f"\nTODOS LOS CHEQUEOS OK ({OK})")
