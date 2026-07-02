"""Baja los anexos de Wikipedia "Senadores nacionales de Argentina (AAAA-AAAA)"
a datos/Archivos_Borrar/wiki_senadores/ (HTML crudo, régimen de descartables).

Son el insumo para reconstruir el BLOQUE HISTÓRICO por senador (2015-2023),
decisión de fuente tomada el 2026-07-01 (Franco): Wikipedia + validación
contra snapshots propios. Correr en PC con internet:

  python datos/senado/src/bajar_anexos_wiki.py
"""
from __future__ import annotations

import time
from pathlib import Path

import requests

# los títulos usan a veces guion (-) y a veces guion largo (–): probamos ambos
PERIODOS = ["2013-2015", "2015-2017", "2017-2019",
            "2019-2021", "2021-2023", "2023-2025"]
BASE = "https://es.wikipedia.org/wiki/Anexo:Senadores_nacionales_de_Argentina_({p})"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/senado; contacto repo)"}

OUT = Path(__file__).resolve().parents[3] / "datos" / "Archivos_Borrar" / "wiki_senadores"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    for p in PERIODOS:
        dest = OUT / f"anexo_{p}.html"
        if dest.exists():
            print(f"ya está: {dest.name}")
            continue
        ok = False
        for variante in (p, p.replace("-", "–")):  # guion / guion largo
            url = BASE.format(p=variante)
            try:
                r = requests.get(url, headers=HEADERS, timeout=60,
                                 allow_redirects=True)
                if r.status_code == 200 and "Senadores" in r.text:
                    dest.write_text(r.text, encoding="utf-8")
                    print(f"OK {p} <- {url} ({len(r.text)//1024} KB)")
                    ok = True
                    break
            except requests.RequestException as e:
                print(f"  error {url}: {e}")
        if not ok:
            print(f"FALLÓ {p}: revisar el título del anexo a mano")
        time.sleep(0.5)


if __name__ == "__main__":
    main()
