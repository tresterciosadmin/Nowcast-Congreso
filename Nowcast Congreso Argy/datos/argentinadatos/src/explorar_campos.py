"""SONDA: qué campos devuelve realmente la API de argentinadatos por acta.

POR QUÉ EXISTE
--------------
`to_canonical.py` escribe **`expediente=None` fijo** para las dos cámaras
(líneas 132 y 147): nunca se intenta leerlo. Consecuencia medida el 2026-08-08:
las 369 actas de Diputados de 2024-2026 y las 311 del Senado entran a la
canónica sin saber qué proyecto se votó, y el enlace entre cámaras —que es el
corazón del nowcast desde el cambio de enfoque— se sostiene sólo con lo que se
pueda rescatar del título.

La pregunta es simple y no se puede contestar desde el sandbox, que no tiene
red: **¿la API expone el expediente y lo estamos tirando, o directamente no lo
publica?** Si lo expone, el arreglo son dos líneas y cubre el flujo vivo. Si no,
el rescate por título/O.D. es lo mejor disponible y hay que dejarlo dicho.

Esta sonda no cambia nada: baja UNA acta de cada cámara e imprime sus campos.

CORRER EN LA PC DE VALLE (necesita internet)
    python datos/argentinadatos/src/explorar_campos.py

QUÉ MIRAR EN LA SALIDA
    Cualquier clave que suene a expediente: `expediente`, `expedientes`,
    `numeroExpediente`, `exp`, `proyecto`, `asunto`, `ordenDelDia`, `od`...
    Si aparece, pegá la salida y se enchufa en `to_canonical.py`.

Módulo: datos/argentinadatos · creado 2026-08-08 (línea Revisión de Comisiones)
"""
from __future__ import annotations

import json
import logging
import sys

try:
    import requests
except ImportError:
    raise SystemExit("falta requests: pip install requests")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE = "https://api.argentinadatos.com/v1"
UA = {"User-Agent": "nowcast-congreso/0.1 (investigacion legislativa)"}
TIMEOUT = 60

# Cómo se llamaría el campo si existiera. Se busca sin distinguir mayúsculas ni
# acentos, y también dentro de los votos, por si viniera anidado.
PISTAS = ("expediente", "exped", "proyecto", "asunto", "orden", "\bod\b",
          "sumario", "tramite", "numero", "camara")


def _get(path: str):
    r = requests.get(BASE + path, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _interesantes(claves) -> list[str]:
    return [k for k in claves if any(p.strip("\\b") in str(k).lower() for p in PISTAS)]


def sondear(nombre: str, path: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {nombre}   GET {BASE}{path}")
    print("=" * 72)
    try:
        datos = _get(path)
    except requests.RequestException as e:
        logger.error("no se pudo consultar %s: %s", path, e)
        return
    if not isinstance(datos, list) or not datos:
        logger.warning("respuesta inesperada o vacía")
        return

    # La última suele ser la más reciente: es la que interesa para el flujo vivo.
    acta = datos[-1]
    print(f"\nactas devueltas: {len(datos)}")
    print(f"\nCAMPOS del acta ({len(acta)}):")
    for k, v in acta.items():
        if k == "votos":
            print(f"  {k:24} <lista de {len(v) if isinstance(v, list) else '?'} votos>")
            continue
        s = str(v)
        print(f"  {k:24} {s[:80]}")

    cand = _interesantes(acta.keys())
    print(f"\n>>> CANDIDATOS a expediente en el acta: {cand or 'NINGUNO'}")

    votos = acta.get("votos") or []
    if isinstance(votos, list) and votos and isinstance(votos[0], dict):
        print(f"\nCAMPOS de un voto: {list(votos[0].keys())}")

    print("\nEl acta completa, por si el campo tiene un nombre inesperado:")
    recorte = {k: v for k, v in acta.items() if k != "votos"}
    print(json.dumps(recorte, ensure_ascii=False, indent=2)[:1800])


def main() -> int:
    print(__doc__.split("CORRER EN")[0])
    sondear("SENADO", "/senado/actas/")
    sondear("DIPUTADOS", "/diputados/actas/")
    print("\n" + "=" * 72)
    print("""  QUÉ HACER CON ESTO

  · Si aparece un campo de expediente -> se enchufa en to_canonical.py, que hoy
    tiene `expediente=None` fijo en las líneas 132 (Diputados) y 147 (Senado).
    Queda cubierto el flujo vivo 2024-2026 en la fuente, sin rescates.

  · Si NO aparece -> el rescate desde el título (Senado) y desde la O.D.
    (Diputados) de `datos/expedientes/src/enlace_senado.py` es lo mejor
    disponible, y conviene anotarlo en el README para que nadie lo vuelva a
    buscar. Pegá igual la salida en el ESTADO: una fuente que NO trae un dato
    también es un hallazgo, y este ya se buscó dos veces.""")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
