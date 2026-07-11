"""Tests OFFLINE del adaptador TP de Diputados (sin red).
Fixture recortada de una página real. Correr: python datos/bot_recoleccion/tests/test_tp.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tp_diputados import parse_tp, _firmantes, _fecha_iso

FIX = Path(__file__).parent / "fixtures"
OK = 0
def check(c, m):
    global OK
    assert c, f"FALLO: {m}"
    OK += 1; print("  ok:", m)

html = (FIX / "tp_87_144.html").read_text(encoding="utf-8")
ident, filas = parse_tp(html)
check(ident == {"numero": 87, "fecha": "2026-07-07"}, "identidad: nº 87, fecha ISO")
check(len(filas) == 3, "3 proyectos en la fixture")
f0, f1, f2 = filas
check(f0["expediente"] == "3276-D-2026", "expediente")
check(f0["seccion"] == "DIPUTADOS", "sección")
check(f0["n_firmantes"] == 4 and "HERRERA AHUAD, OSCAR A." in f0["firmantes"],
      "4 cofirmantes, el último separado del 'Y'")
check(f0["tipo"] == "DE RESOLUCIÓN", "tipo")
check("ENCUENTRO PROVINCIAL" in f0["sumario"], "sumario sin firmantes ni expediente")
check(f0["giros"] == "EDUCACION", "giro simple")
check(f0["pdf_url"].endswith(".pdf"), "link al PDF")
check(f2["expediente"] == "3278-D-2026" and f2["n_firmantes"] == 1, "proyecto unipersonal")
check("INDUSTRIA" in f2["giros"] and "LEGISLACION DEL TRABAJO" in f2["giros"],
      "giros múltiples")
check(_firmantes("PEREZ, JUAN; GOMEZ, ANA Y LOPEZ, MARIO A.:") ==
      ["PEREZ, JUAN", "GOMEZ, ANA", "LOPEZ, MARIO A."], "separador de firmantes")
check(_fecha_iso("7 DE JULIO DE 2026") == "2026-07-07", "fecha en castellano")
print(f"\nTODOS LOS CHEQUEOS OK ({OK})")
