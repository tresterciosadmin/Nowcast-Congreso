"""Tests OFFLINE del adaptador de votaciones (sin red).

Cubre lo que rompe en producción: alias de campos entre cámaras, actas sin id,
payloads corruptos y el dedup del solapamiento diciembre/enero (el endpoint del
año N devuelve actas de fin del año N-1).

Correr:  python datos/bot_recoleccion/tests/test_votaciones.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import votaciones as V  # noqa: E402

ok = fail = 0


def check(cond, msg):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print(f"  FALLA: {msg}")


# --- 1. Diputados usa `id`; Senado usa `actaId`: ambos deben parsearse ---
dip = [{"id": 5793, "fecha": "2026-06-25T02:33:00.000Z", "titulo": "Proyecto X",
        "resultado": "AFIRMATIVO", "votosAfirmativos": 130, "votosNegativos": 100,
        "abstenciones": 2, "ausentes": 25}]
sen = [{"actaId": "1234", "fecha": "2026-07-16T17:55:54.000Z", "titulo": "Proyecto Y",
        "resultado": "APROBADO", "afirmativos": 40, "negativos": 20}]

fd = V.parse_actas(dip, "diputados", 2026)
fs = V.parse_actas(sen, "senado", 2026)
check(len(fd) == 1 and len(fs) == 1, "no parseó una acta por cámara")
check(fd[0]["acta_id"] == "argentinadatos:diputados:5793", "acta_id de Diputados mal armado")
check(fs[0]["acta_id"] == "argentinadatos:senado:1234", "acta_id de Senado mal armado")
check(fd[0]["fecha"] == "2026-06-25", "la fecha debe recortarse a YYYY-MM-DD")
check(fd[0]["n_afirmativos"] == 130, "alias votosAfirmativos no resuelto (Diputados)")
check(fs[0]["n_afirmativos"] == 40, "alias afirmativos no resuelto (Senado)")
check(fs[0]["n_abstenciones"] is None, "campo ausente debe quedar None, no romper")

# --- 2. Parsing defensivo: basura en el payload no debe tirar el bot ---
sucio = [None, "no soy un dict", 42, {}, {"id": ""}, {"titulo": "sin id"},
         {"id": 1, "titulo": ""}]
fx = V.parse_actas(sucio, "diputados", 2026)
check(len(fx) == 1, f"debe quedar solo el acta con id válido, quedaron {len(fx)}")
check(fx[0]["titulo"] == "(sin titulo)", "título vacío debe caer al placeholder")
check(V.parse_actas(None, "senado", 2026) == [], "payload None debe dar lista vacía")
check(V.parse_actas([], "senado", 2026) == [], "payload vacío debe dar lista vacía")

# --- 3. El campo se busca por NOMBRE, con orden de preferencia ---
check(V._campo({"a": None, "b": "x"}, "a", "b") == "x", "no saltea el campo vacío")
check(V._campo({}, "a", default="z") == "z", "no aplica el default")

# --- 4. Solapamiento dic/ene: la misma acta en dos años NO se duplica ---
#     (el endpoint /senado/actas/2026 devuelve actas del 27-dic-2025)
dic = {"actaId": "999", "fecha": "2025-12-27T00:44:08.000Z", "titulo": "Extraordinarias"}
a25 = V.parse_actas([dic], "senado", 2025)
a26 = V.parse_actas([dic], "senado", 2026)
check(a25[0]["acta_id"] == a26[0]["acta_id"],
      "la misma acta en dos años debe tener el MISMO acta_id (si no, se duplica)")

# --- 5. La fecha de detección se estampa (trazabilidad del radar) ---
check(fd[0]["detectado"] and len(fd[0]["detectado"]) == 10, "falta la fecha de detección")

print(f"\n{ok} chequeos OK, {fail} fallas")
raise SystemExit(1 if fail else 0)
