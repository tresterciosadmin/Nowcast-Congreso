# -*- coding: utf-8 -*-
"""datos/taxonomias — EL REGISTRO ÚNICO de taxonomías asignadas.

## Por qué existe

El 06-09-2026 Franco preguntó por las taxonomías históricas y dijo que el equipo las
había hecho. Yo contesté que la tabla estaba vacía. **Las dos cosas eran ciertas**, y ése
es exactamente el problema: había cuatro lugares distintos donde podían estar y ninguno
era EL lugar.

    variables/proyecto/data/tema_por_acta.parquet   3.083 clasificaciones  <- el trabajo real
    datos/proyectos/data/taxonomias.csv                 0 filas           <- respaldo, nunca se lleno
    proyecto_taxonomias (en proyectos.db)               0 filas           <- la base no viaja a git
    variables/proyecto/outputs/muestra_manual_...csv   88 filas           <- validacion a mano

Buscar en el lugar equivocado y concluir "no hay nada" es el modo de fallar de este repo,
y esta vez me tocó a mí. Este archivo lo cierra: **una sola tabla, versionada, en texto.**

## Qué guarda, y qué NO

GUARDA las ASIGNACIONES: qué taxonomía le corresponde a cada objeto, con su procedencia.
Un objeto puede tener varias (multitaxonomía, ADR-0006): una fila por par.

NO guarda el VOCABULARIO. Ése vive en `docs/taxonomias/taxonomias.json` (16 áreas +
3 auxiliares, con reglas de frontera) y es otra cosa: la lista de qué existe, no de qué
se asignó. Separarlos es correcto y no hay que "unificarlos".

## Por qué CSV y no parquet

Porque tiene que sobrevivir. `*.parquet` está en `.gitignore`, es binario y no diffea; la
clasificación **cuesta llamadas de API** y ya se perdió una vez por quedarse sólo en una
base que no viaja. Un CSV de kilobytes, versionado y legible, es la forma de que no vuelva
a pasar. `tema_por_acta.parquet` pasa a ser una **caché derivada**: se regenera de acá.

## Esquema

    nivel        acta | proyecto     (a qué se le asignó)
    objeto       acta_id o denominador del proyecto
    taxonomia_id ECON.TRIB, AUX.TRAMITE, ...   (id del vocabulario)
    area         ECON, AUX, ...                (el área del id; derivable, se guarda por comodidad)
    principal    1 si es la taxonomía principal del objeto, 0 si es secundaria
    confianza    0..1
    fuente       agente:haiku | manual | ...
    asignada_en  ISO-8601 UTC

La clave es (nivel, objeto, taxonomia_id). Al mergear gana la de MAYOR confianza; a
igualdad de confianza, la más reciente.

    python datos/taxonomias/src/registro.py consolidar   # barre todo y arma el registro
    python datos/taxonomias/src/registro.py estado       # que hay, de donde salio
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("taxonomias.registro")

_RAIZ = Path(__file__).resolve().parents[3]
REGISTRO = Path(__file__).resolve().parents[1] / "data" / "asignaciones.csv"
VOCABULARIO = _RAIZ / "docs" / "taxonomias" / "taxonomias.json"

COLS = ["nivel", "objeto", "taxonomia_id", "area", "principal", "confianza",
        "fuente", "asignada_en"]
NIVELES = ("acta", "proyecto")

# De dónde se barre al consolidar. Cada entrada dice CÓMO leer ese formato.
FUENTES = {
    "tema_por_acta": _RAIZ / "variables" / "proyecto" / "data" / "tema_por_acta.parquet",
    "muestra_manual": _RAIZ / "variables" / "proyecto" / "outputs" / "muestra_manual_taxonomias.csv",
    "respaldo_proyectos": _RAIZ / "datos" / "proyectos" / "data" / "taxonomias.csv",
}


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def area_de(taxonomia_id: str) -> str:
    """'ECON.TRIB' -> 'ECON'. El área es el prefijo antes del primer punto."""
    return str(taxonomia_id).split(".")[0].strip().upper()


def ids_validos() -> set[str]:
    """Los ids que el vocabulario declara. Vacío si no está el JSON (no explota)."""
    if not VOCABULARIO.exists():
        logger.warning("no está %s: no se puede validar contra el vocabulario", VOCABULARIO)
        return set()
    j = json.loads(VOCABULARIO.read_text(encoding="utf-8"))
    out = set()
    for grupo in ("areas", "auxiliares"):
        for a in j.get(grupo, []):
            out.add(a["id"])
            for s in a.get("subtemas", []):
                out.add(s["id"] if isinstance(s, dict) else s)
    return out


def cargar(ruta: Path = REGISTRO) -> list[dict]:
    """El registro como lista de dicts. Sin archivo, lista vacía — no es un error."""
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _clave(r: dict) -> tuple:
    return (r["nivel"], r["objeto"], r["taxonomia_id"])


def _mejor(a: dict, b: dict) -> dict:
    """Gana la de MAYOR confianza; a igualdad, la más reciente."""
    ca, cb = float(a.get("confianza") or 0), float(b.get("confianza") or 0)
    if ca != cb:
        return a if ca > cb else b
    return a if str(a.get("asignada_en", "")) >= str(b.get("asignada_en", "")) else b


def merge(existentes: list[dict], nuevas: list[dict]) -> tuple[list[dict], dict]:
    """Une dos listas por (nivel, objeto, taxonomia_id). Devuelve (filas, conteos)."""
    idx = {_clave(r): r for r in existentes}
    n = {"agregadas": 0, "reemplazadas": 0, "sin_cambio": 0}
    for r in nuevas:
        k = _clave(r)
        if k not in idx:
            idx[k] = r
            n["agregadas"] += 1
            continue
        g = _mejor(idx[k], r)
        if g is r and g != idx[k]:
            idx[k] = r
            n["reemplazadas"] += 1
        else:
            n["sin_cambio"] += 1
    filas = sorted(idx.values(), key=lambda r: (r["nivel"], r["objeto"], r["taxonomia_id"]))
    return filas, n


def guardar(filas: list[dict], ruta: Path = REGISTRO) -> int:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    tmp.replace(ruta)
    return len(filas)


# ─────────────────────────── lectores de cada formato ───────────────────────────

# Etiquetas que la revisión MANUAL usó y el vocabulario NO tiene. No se inventan aquí:
# se mapean a lo más cercano que sí existe y se deja dicho, porque las dos nombran algo
# real que el vocabulario no distingue.
#
#   PROCEDIMENTAL  -> AUX.TRAMITE    (apartamiento de reglamento, cuestiones de privilegio)
#   OPACO          -> AUX.SINCLASIF  ("Temas Varios", "Votación en General y Particular":
#                                     el TÍTULO no alcanza y hace falta el PDF)
#
# ⚠️ OPACO merece su propio id y no lo tiene. `AUX.SINCLASIF` dice "no encaja en ninguna,
# revisar"; OPACO dice algo más preciso y más útil: **el clasificador por título no puede
# saberlo**. Es justamente el techo de la vía `texto`. Decisión pendiente de Franco:
# agregarlo al vocabulario (`docs/taxonomias/taxonomias.json`) o dejarlo mapeado.
ALIAS_FUERA_DEL_VOCABULARIO = {"PROCEDIMENTAL": "AUX.TRAMITE", "OPACO": "AUX.SINCLASIF"}

def _de_tema_por_acta(p: Path) -> list[dict]:
    """`tema_por_acta.parquet`: una fila por acta, con `tema_id` y `todas_ids`."""
    import pandas as pd
    d = pd.read_parquet(p)
    out = []
    for r in d.itertuples():
        todas = [x for x in str(getattr(r, "todas_ids", "") or "").split(";") if x.strip()]
        principal = str(r.tema_id).strip()
        if principal and principal not in todas:
            todas.insert(0, principal)
        for t in todas:
            t = t.strip()
            if not t:
                continue
            out.append({"nivel": "acta", "objeto": r.acta_id, "taxonomia_id": t,
                        "area": area_de(t), "principal": int(t == principal),
                        "confianza": round(float(getattr(r, "confianza", 0) or 0), 3),
                        "fuente": "agente:texto",
                        "asignada_en": str(getattr(r, "clasificado_en", "") or "")})
    return out


def _de_muestra_manual(p: Path) -> list[dict]:
    """La muestra revisada a mano: `taxonomias` separadas por `|`, confianza en palabras."""
    escala = {"alta": 0.99, "media": 0.75, "baja": 0.5}
    out = []
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            todas = [x.strip() for x in str(r.get("taxonomias", "")).split("|") if x.strip()]
            todas = [ALIAS_FUERA_DEL_VOCABULARIO.get(x, x) for x in todas]
            for i, t in enumerate(todas):
                out.append({"nivel": "acta", "objeto": r["acta_id"], "taxonomia_id": t,
                            "area": area_de(t), "principal": int(i == 0),
                            "confianza": escala.get(str(r.get("confianza", "")).lower(), 0.75),
                            "fuente": "manual", "asignada_en": _ahora()})
    return out


def _de_respaldo_proyectos(p: Path) -> list[dict]:
    """El respaldo viejo de `proyecto_taxonomias` (nivel PROYECTO)."""
    out = []
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            t = str(r.get("taxonomia_id", "")).strip()
            if not t:
                continue
            out.append({"nivel": "proyecto", "objeto": r.get("denominador", ""),
                        "taxonomia_id": t, "area": area_de(t), "principal": 1,
                        "confianza": r.get("confianza") or 0.9,
                        "fuente": r.get("fuente") or "respaldo",
                        "asignada_en": r.get("asignada_en") or _ahora()})
    return out


LECTORES = {"tema_por_acta": _de_tema_por_acta,
            "muestra_manual": _de_muestra_manual,
            "respaldo_proyectos": _de_respaldo_proyectos}


def consolidar(ruta: Path = REGISTRO) -> dict:
    """Barre todas las fuentes conocidas y las une al registro. Idempotente."""
    filas = cargar(ruta)
    resumen = {"antes": len(filas), "por_fuente": {}}
    for nombre, p in FUENTES.items():
        if not p.exists():
            resumen["por_fuente"][nombre] = "no existe"
            logger.info("%s: no está (%s)", nombre, p)
            continue
        try:
            nuevas = LECTORES[nombre](p)
        except Exception as e:  # noqa: BLE001 — una fuente rota no puede tumbar el barrido
            resumen["por_fuente"][nombre] = f"ERROR {type(e).__name__}: {e}"
            logger.error("%s: no se pudo leer: %s", nombre, e)
            continue
        filas, n = merge(filas, nuevas)
        resumen["por_fuente"][nombre] = {"leidas": len(nuevas), **n}
    validos = ids_validos()
    if validos:
        fuera = sorted({r["taxonomia_id"] for r in filas if r["taxonomia_id"] not in validos})
        resumen["ids_fuera_del_vocabulario"] = fuera
        if fuera:
            logger.error("%d taxonomia_id no están en el vocabulario: %s",
                         len(fuera), fuera[:8])
    resumen["despues"] = guardar(filas, ruta)
    return resumen


def estado(ruta: Path = REGISTRO) -> dict:
    filas = cargar(ruta)
    por = lambda k: {v: sum(1 for r in filas if r.get(k) == v) for v in sorted({r.get(k) for r in filas})}
    return {"archivo": str(ruta), "existe": ruta.exists(), "filas": len(filas),
            "objetos": len({(r["nivel"], r["objeto"]) for r in filas}),
            "por_nivel": por("nivel"), "por_fuente": por("fuente"),
            "areas": len({r["area"] for r in filas})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("accion", choices=["consolidar", "estado"])
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(levelname)s %(name)s: %(message)s")
    r = consolidar() if a.accion == "consolidar" else estado()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
