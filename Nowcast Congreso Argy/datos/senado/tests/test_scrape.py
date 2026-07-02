"""Tests OFFLINE del scraper de votaciones del Senado (sin red).

Corre contra fixtures sintéticos que replican la estructura observada del
sitio (jul-2026). Correr:  python datos/senado/tests/test_scrape.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scrape_votaciones import (  # noqa: E402
    _form_payload, _parse_listado, _resultado_lista, _voto, parse_detalle)

FIX = Path(__file__).parent / "fixtures"
OK = 0


def check(cond: bool, msg: str) -> None:
    global OK
    assert cond, f"FALLO: {msg}"
    OK += 1
    print(f"  ok: {msg}")


def test_form_payload() -> None:
    soup = BeautifulSoup((FIX / "listado_2018.html").read_text(encoding="utf-8"),
                         "html.parser")
    action, payload = _form_payload(soup, 2018)
    check(action.endswith("/votaciones/actas"), "action del form resuelto")
    check(payload["busqueda_actas[anio]"] == "2018", "año pisado en el payload")
    check(payload.get("busqueda_actas[_token]") == "tok123",
          "hidden _token preservado")
    check("busqueda_actas[palabra]" in payload, "resto de campos incluidos")


def test_parse_listado() -> None:
    rows = _parse_listado((FIX / "listado_2018.html").read_text(encoding="utf-8"))
    check(len(rows) == 2, "listado: 2 filas")
    check(rows[0]["detalle_id"] == "1000" and rows[1]["detalle_id"] == "999",
          "listado: detalle_id extraídos")
    check(rows[0]["fecha_lista"] == "14/11/2018", "listado: fecha")
    check(rows[0]["nro_acta_lista"] == "7", "listado: nro de acta")
    check(rows[0]["resultado_lista"] == "AFIRMATIVO", "listado: resultado")
    check(rows[0]["mayoria_lista"] == "MAYORIA ABSOLUTA"
          and rows[1]["mayoria_lista"] == "SIMPLE", "listado: mayoría requerida")


def test_parse_detalle() -> None:
    html = (FIX / "detalle_1000.html").read_text(encoding="utf-8")
    acta, votos = parse_detalle(html, "1000")
    check(acta["acta_id"] == "senado:1000" and acta["camara"] == "senado",
          "detalle: acta_id canónico")
    check(acta["fecha"] == "2018-11-14", "detalle: fecha ISO")
    check(acta["tipo_mayoria"] == "MAYORIA ABSOLUTA", "detalle: tipo de mayoría")
    check(acta["resultado"] == "AFIRMATIVO", "detalle: resultado")
    check(acta["expediente"] == "PE-50/18-PL", "detalle: expediente")
    check("instancia" not in acta, "detalle: sin columnas extra (schema estricto)")
    check(acta["titulo"].endswith("[EN GENERAL]"),
          "detalle: instancia plegada al título")
    check((acta["n_afirmativos"], acta["n_negativos"],
           acta["n_abstenciones"], acta["n_ausentes"]) == (3, 2, 1, 1),
          "detalle: totales")
    check(len(votos) == 7, "detalle: 7 filas nominales")
    v0 = votos[0]
    check(v0["legislador_nombre"] == "PEREZ, JUAN"
          and v0["bloque"] == "FRENTE PARA LA VICTORIA"
          and v0["distrito"] == "BUENOS AIRES"
          and v0["voto"] == "AFIRMATIVO"
          and v0["fuente"] == "senado", "detalle: fila nominal completa")
    check(sum(1 for v in votos if v["voto"] == "AFIRMATIVO") == 3
          and sum(1 for v in votos if v["voto"] == "NEGATIVO") == 2
          and sum(1 for v in votos if v["voto"] == "ABSTENCION") == 1
          and sum(1 for v in votos if v["voto"] == "AUSENTE") == 1,
          "detalle: nominal cuadra con totales")


def test_voto_mapping() -> None:
    check(_voto("Afirmativo") == "AFIRMATIVO" and _voto("SI") == "AFIRMATIVO",
          "voto: afirmativo")
    check(_voto("negativo") == "NEGATIVO" and _voto("NO") == "NEGATIVO",
          "voto: negativo")
    check(_voto("Abstención") == "ABSTENCION", "voto: abstención (con tilde)")
    check(_voto("ausente") == "AUSENTE" and _voto("PRESIDENTE") == "AUSENTE"
          and _voto("") == "AUSENTE", "voto: residuales -> AUSENTE")


def test_resultado_lista() -> None:
    check(_resultado_lista("POSITIVO AFIRMATIVO") == "AFIRMATIVO",
          "resultado: positivo -> AFIRMATIVO")
    check(_resultado_lista("NEGATIVO NEGATIVO") == "NEGATIVO",
          "resultado: negativo simple")
    check(_resultado_lista("NEGATIVO CANCELADA LEV.VOT.")
          == "NEGATIVO - CANCELADA LEV.VOT.", "resultado: detalle preservado")
    check(_resultado_lista("AFIRMATIVO") == "AFIRMATIVO"
          and _resultado_lista("") is None, "resultado: casos borde")


if __name__ == "__main__":
    test_form_payload()
    test_parse_listado()
    test_parse_detalle()
    test_voto_mapping()
    test_resultado_lista()
    print(f"\nTODOS LOS CHEQUEOS OK ({OK})")
