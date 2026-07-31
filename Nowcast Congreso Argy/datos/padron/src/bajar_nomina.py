"""datos/padron/src/bajar_nomina.py
Baja la NÓMINA de legisladores con su mandato y bloque, y la deja en el formato
que consume `ingesta_padron.py` (Apellido, Nombre, Distrito, IniciaMandato,
FinalizaMandato, Bloque).

Por qué existe (2026-07-31). El proyector de `variables/bloque` cae al "conteo por
ventana" cuando no hay padrón, y ese conteo **suma las cámaras de antes y después
de un recambio**: al 31-07-2026 devolvía **383 bancas de Diputados sobre 257
reales**, porque la ventana de 730 días abarca el recambio del 10-dic-2025. Sin
padrón, cualquier `P(mayoría)` está mal.

Fuente: `api.argentinadatos.com/v1/diputados/diputados` — trae `periodoBloque`
{inicio, fin} POR BLOQUE, así que un diputado que cambia de bloque genera varias
filas con ventanas distintas (justo lo que necesita un padrón point-in-time). Es
la misma fuente que `datos/argentinadatos/src/to_canonical.py` usa para resolver
el bloque de cada voto, así que padrón y votos quedan consistentes por
construcción.

⚠️ SENADO: esta fuente **no da el bloque parlamentario** (solo la alianza por la
que ingresó, que no es lo mismo: p.ej. Atauche entra por el Partido Renovador
Federal y bloquea en LLA). El padrón del Senado se mantiene a mano en
`datos/senado/data/padron_bloques_senado.csv` y hoy **llega al 2025-12-09**: los
senadores que asumieron el 10-dic-2025 no tienen bloque. Ver URGENTE.md.

Uso:
  python datos/padron/src/bajar_nomina.py diputados          # -> nomina_diputados.csv
  python datos/padron/src/bajar_nomina.py diputados --padron # + corre ingesta_padron

CALIDAD DE FUENTE — por qué el padrón da 256 y no 257 (investigado 2026-07-31).
Cruzando contra quiénes votaron de verdad en junio-2026 (257 votantes únicos en 13
sesiones) faltan del padrón:
  • PITROLA, Néstor (Buenos Aires, PO) — la API le carga el tramo
    `2026-04-27 -> 2026-04-27`: asumió y le pusieron fin el mismo día. Es la banca
    70 de Buenos Aires, el único distrito que no cierra (69 de 70).
  • MATZKIN, Martín — directamente no figura en la nómina.
  (ALI, Ernesto "Pipi" sí está: el cruce fallaba por las comillas del apodo.)
Hay 22 tramos con `fin <= inicio`, casi todos de quienes asumieron el 10-dic-2025
con fin 09-dic-2025.

**Se probó repararlos y NO funciona.** Abrirlos a ciegas da 278 bancas (duplica a
quien tiene un tramo posterior); cerrarlos con el inicio del siguiente da 263 y
Buenos Aires 74 sobre 70 — porque parte de esos tramos rotos pertenece a gente que
efectivamente cesó. La fuente no permite distinguir un caso del otro.
**Criterio adoptado: no reparar.** Se detecta, se avisa y se deja como viene: falta
una banca real (99,6%) en vez de inventar seis falsas. El arreglo de fondo es la
nómina oficial de HCDN, no esta API. Anotado en ESTADO.

4 directivas: errores específicos, backoff, parsing defensivo, logging estructurado.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import ConnectionError as CE, HTTPError, Timeout

logger = logging.getLogger("padron.nomina")

BASE = "https://api.argentinadatos.com/v1"
H = {"User-Agent": "nowcast-congreso/0.1 (datos/padron)"}
DATA = Path(__file__).resolve().parents[1] / "data"

# Centinela de "mandato en curso". OJO: NO usar 9999-12-31 — pandas.Timestamp
# solo llega a 2262-04-11, así que to_datetime("9999-12-31") devuelve NaT y el
# legislador desaparece de cualquier filtro por fecha (nos escondió una banca).
_ABIERTO = "2099-12-31"


def _get(path: str):
    ultimo = None
    for i in range(4):
        try:
            r = requests.get(BASE + path, headers=H, timeout=120)
            r.raise_for_status()
            return r.json()
        except (CE, Timeout, HTTPError) as e:
            ultimo = e
            logger.warning("reintento %d en %s: %s", i + 1, path, type(e).__name__)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET {path}: {ultimo}")


def nomina_diputados() -> pd.DataFrame:
    """Una fila por (diputado, tramo de bloque). Defensivo: campos por nombre,
    tolerante a faltantes; descarta filas sin fecha de inicio (no ubicables)."""
    filas = []
    invalidos = 0
    for r in _get("/diputados/diputados/"):
        pb = r.get("periodoBloque") or {}
        desde = str(pb.get("inicio") or "")[:10]
        hasta = str(pb.get("fin") or "")[:10]
        if not desde:
            continue
        # TRAMOS DEGENERADOS de la fuente (detectado 2026-07-31, 11 casos).
        # Para altas recientes la API carga `fin` ANTES o IGUAL que `inicio`
        # (p.ej. Pitrola 2026-04-27 -> 2026-04-27, o los que asumieron el
        # 10-dic-2025 con fin 09-dic-2025: el fin quedó pegado al mandato
        # anterior). Un tramo así se descarta en silencio al filtrar por fecha
        # y la banca desaparece del padrón: así se perdía la banca 70 de
        # Buenos Aires. Interpretación: fin inválido = MANDATO EN CURSO.
        if hasta and hasta <= desde:
            # NO se "arregla": ver nota de CALIDAD DE FUENTE en el docstring.
            # Se cuenta y se avisa; el tramo queda como viene y el filtro por
            # fecha lo descarta (criterio conservador: preferimos que falte una
            # banca real a inventar varias falsas).
            invalidos += 1
        filas.append({
            "Apellido": (r.get("apellido") or "").strip(),
            "Nombre": (r.get("nombre") or "").strip(),
            "Distrito": (r.get("provincia") or "").strip(),
            "IniciaMandato": desde,
            "FinalizaMandato": hasta or _ABIERTO,
            "Bloque": (r.get("bloque") or "SIN BLOQUE").strip(),
        })
    if invalidos:
        logger.warning("%d tramos con fin <= inicio en la fuente (se dejan como "
                       "vienen; ver CALIDAD DE FUENTE en el docstring)", invalidos)
    df = pd.DataFrame(filas)
    if df.empty:
        raise RuntimeError("la nómina vino vacía: revisar el contrato de la API")
    return df.drop_duplicates()


def _vigentes(df: pd.DataFrame, fecha: str) -> pd.DataFrame:
    d = pd.to_datetime(df["IniciaMandato"], errors="coerce")
    h = pd.to_datetime(df["FinalizaMandato"], errors="coerce")
    f = pd.Timestamp(fecha)
    return df[(d <= f) & (h >= f)]


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("camara", choices=["diputados"])
    ap.add_argument("--padron", action="store_true",
                    help="además, corre ingesta_padron.py para generar el contrato")
    ap.add_argument("--fecha", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)

    DATA.mkdir(parents=True, exist_ok=True)
    df = nomina_diputados()
    salida = DATA / f"nomina_{a.camara}.csv"
    df.to_csv(salida, index=False, encoding="utf-8")

    vig = _vigentes(df, a.fecha)
    logger.info("nómina %s: %d filas (%d personas) -> %s",
                a.camara, len(df), df[["Apellido", "Nombre"]].drop_duplicates().shape[0], salida)
    logger.info("bancas vigentes al %s: %d", a.fecha, len(vig))
    if len(vig) != 257:
        logger.warning("¡ATENCIÓN! %d bancas vigentes, se esperaban 257. "
                       "Revisar solapamientos de tramos antes de usar el padrón.", len(vig))
    print("\ncomposición vigente al", a.fecha)
    print(vig["Bloque"].value_counts().head(15).to_string())

    if a.padron:
        import subprocess
        raiz = Path(__file__).resolve().parents[3]
        dest = DATA / f"padron_{a.camara}.csv"
        subprocess.run([sys.executable, str(Path(__file__).parent / "ingesta_padron.py"),
                        a.camara, str(salida), str(dest)], check=True)
        logger.info("padrón -> %s", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
