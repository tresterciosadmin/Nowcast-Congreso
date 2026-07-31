"""BOT DIARIO — adaptador VOTACIONES (Diputados + Senado).

Tercera pata del bot, junto a `tp_diputados.py` (expedientes de Diputados) y
`dae_senado.py` (expedientes del Senado). Hasta hoy el bot traía **qué se
presenta** pero no **qué se vota**: por eso la base de votaciones quedó parada en
octubre de 2025 mientras los expedientes seguían al día. Este módulo cierra esa
asimetría.

Por qué importa (incidente del 2026-07-31). `P(aprobación) = P(llega al recinto) ×
P(mayoría | recinto)`. El segundo factor lo alimentan las actas. Con la base
detenida antes del recambio del 10-dic-2025, el proyector de posturas devolvía la
Cámara vieja **sin avisar**: 383 bancas sobre 257 y todos los bloques en
AFIRMATIVO. Se habían acumulado **229 actas** sin ingestar. Un nowcast que se
desactualiza en silencio es peor que uno que falta.

Fuente: `api.argentinadatos.com/v1/{diputados,senado}/actas/{anio}`. Es la misma
que usa `datos/argentinadatos/src/to_canonical.py`, así que no se inventa un
contrato nuevo: el bot detecta novedades y **delega la normalización** en ese
módulo (se consume su salida, no se reimplementa su lógica).

Estrategia incremental: a diferencia del DAE (numeración secuencial), las actas se
identifican por `id`/`actaId`. El bot guarda el conjunto de ids ya vistos por
cámara y año en `data/estado_bot.json` y solo actúa si aparecen ids nuevos.
Idempotente: correr dos veces no duplica ni recommitea.

Salida:  data/clean/votaciones_nuevas.parquet  (bitácora de lo detectado: cuándo
         entró cada acta al radar; NO reemplaza a la canónica)
Estado:  data/estado_bot.json -> {"actas_diputados_2026": {"ids": [...], "n": N}, ...}

Correr:
  python datos/bot_recoleccion/src/votaciones.py              # año en curso
  python datos/bot_recoleccion/src/votaciones.py 2025 2026    # años puntuales
  RECONSTRUIR=1 python .../votaciones.py                      # ignora el estado

Tests offline:  python datos/bot_recoleccion/tests/test_votaciones.py

Las 4 directivas: errores específicos, backoff, parsing defensivo (campos por
nombre con alias, tolerante a faltantes), logging estructurado.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from requests.exceptions import ConnectionError as CE, HTTPError, Timeout

logger = logging.getLogger("bot.votaciones")

BASE = "https://api.argentinadatos.com/v1"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/bot_recoleccion)"}
TIMEOUT = 120

DATA = Path(__file__).resolve().parents[1] / "data"
ESTADO = DATA / "estado_bot.json"
SALIDA = DATA / "clean" / "votaciones_nuevas.parquet"

CAMARAS = ("diputados", "senado")


def _pedir(path: str):
    """GET con backoff exponencial. Devuelve [] si la API responde 404 (año sin
    datos todavía), que no es un error sino una respuesta legítima."""
    ultimo = None
    for i in range(4):
        try:
            r = requests.get(BASE + path, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 404:
                logger.info("sin datos en %s (404)", path)
                return []
            r.raise_for_status()
            return r.json()
        except (CE, Timeout, HTTPError) as e:
            ultimo = e
            logger.warning("reintento %d/4 en %s: %s", i + 1, path, type(e).__name__)
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"GET {path}: {ultimo}")


# ------------------------------------------------------------------- parsing
def _campo(d: dict, *nombres, default=None):
    """Primer campo presente y no vacío, buscado POR NOMBRE (no por posición):
    la API usa `id` en Diputados y `actaId` en Senado, y podría cambiar."""
    for n in nombres:
        v = d.get(n)
        if v not in (None, ""):
            return v
    return default


def parse_actas(payload, camara: str, anio: int) -> list[dict]:
    """Normaliza la respuesta a filas mínimas para el radar del bot. Defensivo:
    ignora elementos que no sean dict y actas sin id (no rastreables)."""
    filas = []
    for a in (payload or []):
        if not isinstance(a, dict):
            continue
        aid = _campo(a, "id", "actaId", "acta_id")
        if aid in (None, ""):
            continue
        filas.append({
            "camara": camara,
            "anio": anio,
            "acta_id": f"argentinadatos:{camara}:{aid}",
            "fecha": str(_campo(a, "fecha", default=""))[:10] or None,
            "titulo": str(_campo(a, "titulo", default="")).strip() or "(sin titulo)",
            "resultado": _campo(a, "resultado"),
            "n_afirmativos": _campo(a, "votosAfirmativos", "afirmativos"),
            "n_negativos": _campo(a, "votosNegativos", "negativos"),
            "n_abstenciones": _campo(a, "abstenciones"),
            "n_ausentes": _campo(a, "ausentes"),
            "detectado": date.today().isoformat(),
        })
    return filas


# -------------------------------------------------------------------- estado
def _leer_estado() -> dict:
    if ESTADO.exists():
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error("estado_bot.json ilegible (%s): arranco de cero", e)
    return {}


def _guardar_estado(est: dict) -> None:
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def revisar(anios: list[int]) -> pd.DataFrame:
    """Trae las actas de cada (cámara, año) y devuelve SOLO las que no estaban."""
    est = _leer_estado()
    reconstruir = os.environ.get("RECONSTRUIR") == "1"
    nuevas: list[dict] = []

    for camara in CAMARAS:
        for anio in anios:
            clave = f"actas_{camara}_{anio}"
            vistos = set() if reconstruir else set((est.get(clave) or {}).get("ids", []))
            filas = parse_actas(_pedir(f"/{camara}/actas/{anio}"), camara, anio)
            if not filas:
                continue
            ids = {f["acta_id"] for f in filas}
            faltan = [f for f in filas if f["acta_id"] not in vistos]
            if faltan:
                logger.info("%s %d: %d actas en la fuente, %d NUEVAS",
                            camara, anio, len(filas), len(faltan))
                nuevas.extend(faltan)
            else:
                logger.info("%s %d: sin novedades (%d actas)", camara, anio, len(filas))
            est[clave] = {"ids": sorted(ids), "n": len(ids),
                          "ultima_revision": date.today().isoformat()}

    _guardar_estado(est)
    return pd.DataFrame(nuevas)


def _append_dedup(df: pd.DataFrame) -> int:
    """Suma al parquet histórico sin duplicar (clave: acta_id)."""
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    if SALIDA.exists():
        try:
            viejo = pd.read_parquet(SALIDA)
            df = pd.concat([viejo, df], ignore_index=True)
        except (OSError, ValueError) as e:
            logger.error("no pude leer %s (%s): reescribo", SALIDA, e)
    antes = len(df)
    df = df.drop_duplicates(subset=["acta_id"], keep="first")
    df.to_parquet(SALIDA, index=False)
    return antes - len(df)


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = [a for a in argv[1:] if a.isdigit()]
    anios = [int(a) for a in args] or [date.today().year]
    # el año anterior también: en enero-febrero siguen cargándose actas de diciembre
    if not args and date.today().month <= 3:
        anios.append(date.today().year - 1)

    logger.info("revisando años %s en %s", anios, list(CAMARAS))
    nuevas = revisar(anios)

    if nuevas.empty:
        print("Sin actas nuevas: no se commitea nada.")
        return 0

    dup = _append_dedup(nuevas)
    print(f"\nACTAS NUEVAS: {len(nuevas)}"
          + (f" (descartadas {dup} duplicadas)" if dup else ""))
    print(nuevas.groupby(["camara", "anio"]).size().to_string())
    print(f"\n-> {SALIDA}")
    print("\n⚠️  El bot DETECTA; la canónica no se reconstruye sola. Para incorporarlas:")
    print("     python datos/argentinadatos/src/to_canonical.py")
    print("     python datos/canonica/src/run_pipeline.py")
    print("   (y si hubo recambio, actualizar el padrón:")
    print("     python datos/padron/src/bajar_nomina.py diputados --padron )")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
