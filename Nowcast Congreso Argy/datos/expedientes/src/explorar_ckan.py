"""Explorador de fuentes para datos/expedientes (paso 0 del módulo).

Consulta el CKAN de Diputados (datos.hcdn.gob.ar) y descarga:
  1. El inventario de datasets relevantes (proyectos, expedientes, firmantes,
     giros, dictámenes, órdenes del día) con sus recursos (nombre/URL/formato).
  2. Una MUESTRA (primeras ~200 KB) de cada CSV relevante, para diseñar el
     contrato del módulo sobre la estructura real y no sobre supuestos.

Todo va a datos/Archivos_Borrar/expedientes_ckan/ (régimen de descartables).

Correr en PC con internet:
  python datos/expedientes/src/explorar_ckan.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

CKAN = "https://datos.hcdn.gob.ar/api/3/action/"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/expedientes)"}
QUERIES = ["proyectos", "expediente", "firmante", "giro", "dictamen", "orden del dia"]
MUESTRA_BYTES = 200_000

OUT = Path(__file__).resolve().parents[3] / "datos" / "Archivos_Borrar" / "expedientes_ckan"
OUT.mkdir(parents=True, exist_ok=True)


def _get(url: str, **kw) -> requests.Response:
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60, **kw)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if i == 2:
                raise
            print(f"  reintento {i+1} ({e})")
            time.sleep(3 * (i + 1))


def main() -> None:
    vistos, inventario = set(), []
    for q in QUERIES:
        r = _get(CKAN + "package_search", params={"q": q, "rows": 20}).json()
        for pkg in r["result"]["results"]:
            if pkg["name"] in vistos:
                continue
            vistos.add(pkg["name"])
            item = {"dataset": pkg["name"], "titulo": pkg.get("title"),
                    "notas": (pkg.get("notes") or "")[:200], "recursos": []}
            for res in pkg.get("resources", []):
                item["recursos"].append({
                    "nombre": res.get("name"), "formato": res.get("format"),
                    "url": res.get("url"), "size": res.get("size"),
                    "modificado": res.get("last_modified")})
            inventario.append(item)
    (OUT / "inventario.json").write_text(
        json.dumps(inventario, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"inventario: {len(inventario)} datasets -> {OUT/'inventario.json'}")

    # muestras de los CSV con pinta de proyectos/firmantes/giros
    CLAVES = ("proyecto", "expedient", "firmante", "giro", "dictam", "orden")
    n = 0
    for item in inventario:
        for res in item["recursos"]:
            nom = (res.get("nombre") or "").lower()
            if res.get("formato", "").upper() != "CSV" or not any(k in nom for k in CLAVES):
                continue
            try:
                r = _get(res["url"], stream=True)
                chunk = next(r.iter_content(MUESTRA_BYTES))
                dest = OUT / f"muestra_{item['dataset']}_{nom[:40].replace('/','_').replace(' ','_')}.csv"
                dest.write_bytes(chunk)
                print(f"  muestra: {dest.name} ({len(chunk)//1024} KB)")
                n += 1
            except (requests.RequestException, StopIteration) as e:
                print(f"  FALLO muestra {nom}: {e}")
            time.sleep(0.5)
    print(f"OK: {n} muestras. Sincronizá y avisale a Claude.")


if __name__ == "__main__":
    main()
