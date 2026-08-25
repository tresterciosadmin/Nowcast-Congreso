# -*- coding: utf-8 -*-
"""Baja las Órdenes del Día del SENADO (dictámenes de sus comisiones).

## Por qué hace falta un script aparte

Las Órdenes del Día que baja `ingesta_od.py` son de **Diputados**. El CKAN de
Diputados publica los dictámenes producidos por las comisiones de Diputados —sea
Diputados cámara de origen o revisora—, así que de las 6.854 filas de dictamen de
proyectos de ley, 1.515 ya son de proyectos con origen Senado. **El hueco real es
el sistema de comisiones del Senado**, que publica por su propia vía.

Sin esto, un proyecto que nace en el Senado no tiene Puerta A observable, y uno
que consigue media sanción en Diputados no tiene Puerta C. El circuito bicameral
queda cojo de un lado.

## Lo que se verificó el 21-08-2026 (sonda en PowerShell, no supuestos)

- Listado: `senado.gob.ar/parlamentario/parlamentaria/ordenDelDia`, con **1983 a
  2026** en el selector de período.
- El filtro **NO viaja por query string**: es un POST a `.../ordenDelDiaResultado`
  con `busqueda_orden[ordenDelDiaPeriodo]` (el año) y `tipoExpedientes`.
- Los códigos de `tipoExpedientes` que nos importan: **`PL`** = proyecto de ley,
  **`CD`** = comunicaciones de Diputados, que es como entra un proyecto con media
  sanción. (`AC` = acuerdos, que son pliegos de jueces y NO son leyes.)
- Cada fila trae número/año de OD, el o los expedientes con su ficha
  (`/parlamentario/comisiones/verExp/<num>.<anio>/<origen>/<tipo>`) y el link de
  descarga con un **id interno opaco**: `/parlamentario/parlamentaria/<id>/downloadOrdenDia`.
  El id no se deduce del número de OD: hay que leerlo del listado.
- **Los PDF del Senado traen la lista de firmantes**, con la misma fórmula de
  cierre que Diputados (`Sala de las comisiones, <fecha>.` + nombres separados por
  `–`), así que los parsea el mismo `parser_od.py`. Verificado sobre la OD 1/2026
  (`CD-21/24`, *"proyecto de ley venido en revisión"*) y la OD 2/2026 (`PE-46/24`).

## Cómo se corre

    python datos/expedientes/src/ingesta_od_senado.py --anios 2024-2026 --solo-lista
    python datos/expedientes/src/ingesta_od_senado.py --anios 2008-2026

Reanudable igual que el de Diputados. `OD_SENADO_CACHE=/dir`, `REFRESH=1`.

**Empezá por `--solo-lista` de un año.** La paginación del sitio se sigue leyendo
los enlaces del propio HTML en vez de suponer el patrón, pero si el sitio cambia
el formulario esto se entera acá y no después de 3.000 descargas.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                            if (d / "rutas.py").is_file())))
from rutas import RAIZ  # noqa: E402

logger = logging.getLogger("expedientes.ingesta_od_senado")

BASE = "https://www.senado.gob.ar"
LISTADO = f"{BASE}/parlamentario/parlamentaria/ordenDelDia"
BUSCAR = f"{BASE}/parlamentario/parlamentaria/ordenDelDiaResultado"
HEADERS = {"User-Agent": "nowcast-congreso/0.1 (datos/expedientes; ingesta_od_senado)"}
TIMEOUT = 120
PAUSA = 0.4
MINIMO_PDF = 1500

# Sólo `PL`. Se probó también `CD` y devuelve **cero** en 2025: los expedientes
# venidos en revisión de Diputados aparecen DENTRO del listado de `PL`, con el
# prefijo en el numero de expediente (`CD-33/25-PL`). `tipoExpedientes` es el tipo
# del PROYECTO, no su origen; el origen viaja en el prefijo. Medido el 21-08-2026
# sobre 2025: 40 OD con `PL` (23 de origen PE, 13 de senadores, 4 de Diputados) y
# 0 con `CD`. Se deja el parametro por si alguna vez cambia.
TIPOS_LEY = ("PL",)

RE_TABLA = re.compile(r"<table.*?</table>", re.S | re.I)
RE_FILA = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
RE_CELDA = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
RE_DESCARGA = re.compile(r"/parlamentario/parlamentaria/(\d+)/downloadOrdenDia")
RE_VEREXP = re.compile(r"/parlamentario/comisiones/verExp/([\d.]+)/([A-Z]+)/([A-Z]+)")
RE_PAGINAS = re.compile(r'href="([^"]*ordenDelDia[^"]*?page=(\d+))"')
RE_TAGS = re.compile(r"<[^>]+>")


def cache_dir() -> Path:
    return Path(os.environ.get("OD_SENADO_CACHE", RAIZ / "Archivos_Borrar" / "od_pdf_senado"))


def _texto(html: str) -> str:
    return " ".join(RE_TAGS.sub(" ", html).split())


def _filas_de(html: str) -> list[dict]:
    tabla = RE_TABLA.search(html)
    if not tabla:
        return []
    filas = []
    for cuerpo in RE_FILA.findall(tabla.group(0)):
        celdas = RE_CELDA.findall(cuerpo)
        if len(celdas) < 4:
            continue                       # el <thead> no tiene <td>
        m = RE_DESCARGA.search(cuerpo)
        if not m:
            continue                       # fila sin adjunto: no hay PDF que bajar
        od = _texto(celdas[0])
        num_anio = re.match(r"(\d+)\s*/\s*(\d{4})", od)
        exps = [f"{n}/{o}/{t}" for n, o, t in RE_VEREXP.findall(celdas[1])]
        filas.append({
            "id": m.group(1),
            "od_numero": num_anio.group(1) if num_anio else "",
            "od_anio": num_anio.group(2) if num_anio else "",
            "od_crudo": od,
            "expedientes": ";".join(_texto(celdas[1]).split()) if not exps else ";".join(exps),
            "expedientes_texto": _texto(celdas[1]),
            "tipo_orden": _texto(celdas[2]),
        })
    return filas


def listar(anio: int, tipo: str, ses: requests.Session) -> list[dict]:
    """POST de búsqueda + paginación leída del propio HTML."""
    datos = {"busqueda_orden[ordenDelDiaNumero]": "",
             "busqueda_orden[ordenDelDiaPeriodo]": str(anio),
             "busqueda_orden[palabra]": "",
             "tipoExpedientes": tipo}
    r = ses.post(BUSCAR, data=datos, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    filas = _filas_de(r.text)
    # Se usa el HREF que trae el HTML, NO una URL armada a mano. La primera version
    # capturaba el href y despues pedia `LISTADO?page=N`, que es el listado SIN
    # filtrar: las paginas 2+ devolvian el anio por defecto (2026) en vez del pedido.
    # El sintoma fue que TODOS los anios daban exactamente 20 Ordenes del Dia — el
    # tamanio de una pagina. Ningun dato real sale tan parejo.
    enlaces = {}
    for href, n in RE_PAGINAS.findall(r.text):
        enlaces[int(n)] = href if href.startswith("http") else BASE + href
    vistos = {f["id"] for f in filas}
    for n in sorted(enlaces):
        if n <= 1:
            continue
        time.sleep(PAUSA)
        rp = ses.get(enlaces[n], headers=HEADERS, timeout=TIMEOUT)
        if rp.status_code != 200:
            logger.warning("año %s tipo %s: la página %s dio HTTP %s", anio, tipo, n, rp.status_code)
            continue
        pagina = _filas_de(rp.text)
        # GUARDA REAL: que las filas sean del anio pedido. La guarda anterior sólo
        # miraba si venian filas NUEVAS, y no podia ver que fueran de OTRO anio.
        ajenas = [f for f in pagina if f["od_anio"] and f["od_anio"] != str(anio)]
        if ajenas:
            logger.error("año %s tipo %s: la página %s devolvió filas de %s — la "
                         "paginación perdió el filtro. Se corta este año.",
                         anio, tipo, n, sorted({f["od_anio"] for f in ajenas})[:3])
            break
        nuevas = [f for f in pagina if f["id"] not in vistos]
        for f in nuevas:
            vistos.add(f["id"])
        filas.extend(nuevas)
    for f in filas:
        f["anio_buscado"] = anio
        f["tipo_buscado"] = tipo
    logger.info("año %s tipo %s: %d Órdenes del Día (%d páginas)", anio, tipo, len(filas),
                max(enlaces) if enlaces else 1)
    return filas


def bajar(filas: list[dict], destino: Path, ses: requests.Session, refresh: bool) -> list[dict]:
    destino.mkdir(parents=True, exist_ok=True)
    manifiesto = []
    for i, f in enumerate(filas, start=1):
        nombre = f"senado-{f['od_anio'] or f['anio_buscado']}-{f['od_numero'] or f['id']}.pdf"
        ruta = destino / nombre
        if ruta.exists() and ruta.stat().st_size >= MINIMO_PDF and not refresh:
            estado, detalle = "cache", "ya estaba"
        else:
            url = f"{BASE}/parlamentario/parlamentaria/{f['id']}/downloadOrdenDia"
            try:
                r = ses.get(url, headers=HEADERS, timeout=TIMEOUT)
                if r.status_code != 200:
                    estado, detalle = "FALLA", f"HTTP {r.status_code}"
                elif not r.content.startswith(b"%PDF-"):
                    estado, detalle = "FALLA", f"no es PDF (cabecera {r.content[:8]!r})"
                elif len(r.content) < MINIMO_PDF:
                    estado, detalle = "FALLA", f"PDF muy chico ({len(r.content)} bytes)"
                else:
                    ruta.write_bytes(r.content)
                    estado, detalle = "ok", "ok"
            except requests.RequestException as exc:
                estado, detalle = "FALLA", f"{type(exc).__name__}: {exc}"
            time.sleep(PAUSA)
        manifiesto.append(dict(f, archivo=nombre, estado=estado, detalle=detalle,
                               bytes=ruta.stat().st_size if ruta.exists() else 0))
        if i % 50 == 0 or i == len(filas):
            ok = sum(1 for m in manifiesto if m["estado"] in ("ok", "cache"))
            logger.info("%d/%d  ok+cache=%d  fallas=%d", i, len(filas), ok, len(manifiesto) - ok)
    return manifiesto


def _escribir(filas: list[dict], ruta: Path) -> None:
    if not filas:
        logger.warning("nada que escribir en %s", ruta)
        return
    campos = list(dict.fromkeys(k for f in filas for k in f))
    with ruta.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--anios", default="2008-2026", help="rango AAAA-AAAA o lista con comas")
    ap.add_argument("--tipos", default=",".join(TIPOS_LEY),
                    help="códigos de tipoExpedientes (PL=proyecto de ley, CD=venido en revisión)")
    ap.add_argument("--solo-lista", action="store_true", help="arma el listado y no baja PDF")
    args = ap.parse_args(argv)

    # stream=sys.stdout a propósito: por defecto logging escribe en stderr, y
    # PowerShell pinta de ROJO todo lo que un proceso manda por stderr —incluido
    # un INFO de avance— y encima lo envuelve en un NativeCommandError. Una
    # corrida sana parecía estar fallando. Con stdout, `| Tee-Object` alcanza y
    # no hace falta el `2>&1`.
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

    if "-" in args.anios and "," not in args.anios:
        a, b = args.anios.split("-")
        anios = list(range(int(a), int(b) + 1))
    else:
        anios = [int(x) for x in args.anios.split(",") if x.strip()]
    tipos = [t.strip().upper() for t in args.tipos.split(",") if t.strip()]

    destino = cache_dir()
    destino.mkdir(parents=True, exist_ok=True)

    ses = requests.Session()
    ses.get(LISTADO, headers=HEADERS, timeout=TIMEOUT)     # abre sesión y toma cookies

    filas: list[dict] = []
    for anio in anios:
        for tipo in tipos:
            try:
                filas.extend(listar(anio, tipo, ses))
            except requests.RequestException as exc:
                logger.error("año %s tipo %s: %s", anio, tipo, exc)
            time.sleep(PAUSA)

    # un mismo id puede venir por dos tipos; el PDF es uno solo
    unicas = list({f["id"]: f for f in filas}.values())
    _escribir(unicas, destino / "od_senado_listado.csv")
    logger.info("listado: %d filas, %d Órdenes del Día únicas -> %s",
                len(filas), len(unicas), destino / "od_senado_listado.csv")
    if args.solo_lista:
        return 0

    manifiesto = bajar(unicas, destino, ses, refresh=bool(os.environ.get("REFRESH")))
    _escribir(manifiesto, destino / "od_senado_descargas.csv")
    estados: dict[str, int] = {}
    for m in manifiesto:
        estados[m["estado"]] = estados.get(m["estado"], 0) + 1
    logger.info("RESULTADO %s", estados)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
