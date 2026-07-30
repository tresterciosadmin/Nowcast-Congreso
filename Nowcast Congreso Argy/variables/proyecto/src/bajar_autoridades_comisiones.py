"""Baja "Comisiones Permanentes Autoridades" del CKAN de Diputados.

Responde el pendiente de Valle (nota 12-07): `comisiones_integrantes` NO trae
el rol → la señal `lider_pdte_comision` queda en 0. Este dataset sí publica las
AUTORIDADES (presidente / vicepresidentes / secretarios) de cada comisión
permanente. Salida al contrato de datos/expedientes para que origen_lider la
consuma sin tocar otros módulos.

Correr (PC con internet):
  python variables/proyecto/src/bajar_autoridades_comisiones.py

Salida: datos/expedientes/data/clean/comisiones_autoridades.parquet
LIMITACIÓN esperada: el CKAN publica la composición VIGENTE (no la serie
histórica). Sirve para el nowcast de hoy; para el histórico hay que archivar
snapshots (el bot puede hacerlo mensualmente) o curar a mano.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger("proyecto.autoridades")
CKAN = "https://datos.hcdn.gob.ar/api/3/action/package_show"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (variables/proyecto)"}
SALIDA = (Path(__file__).resolve().parents[3] / "datos" / "expedientes" /
          "data" / "clean" / "comisiones_autoridades.parquet")


def _get(url, **kw):
    ultimo = None
    for i in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=120, **kw)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            ultimo = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"GET {url}: {ultimo}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    pkg = _get(CKAN, params={"id": "comisiones"}).json()["result"]
    url = next((r["url"] for r in pkg["resources"]
                if r.get("format", "").upper() == "CSV"
                and "autoridades" in (r.get("name") or "").lower()), None)
    if not url:
        raise SystemExit("no encontré el recurso CSV de autoridades")
    logger.info("bajando %s", url[:90])
    df = pd.read_csv(url, dtype=str, encoding="utf-8-sig")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(SALIDA, index=False)
    print(f"OK autoridades={len(df)} -> {SALIDA}")
    print("  columnas:", list(df.columns))
    for c in df.columns:
        if "cargo" in c or "rol" in c:
            print(f"  {c}:", df[c].value_counts().head(8).to_dict())


if __name__ == "__main__":
    main()
