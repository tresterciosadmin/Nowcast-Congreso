"""Carga y valida el vocabulario controlado de taxonomías.

Uso:
    from loader import cargar, ids_validos, lista_para_prompt
    tx = cargar()                       # dict del JSON
    ids = ids_validos(tx)               # set de ids válidos (subtemas + auxiliares)
    print(lista_para_prompt(tx))        # texto plano para el prompt del agente

CLI:
    python loader.py validar [taxonomias.json]   # chequea ids únicos y formato
    python loader.py prompt  [taxonomias.json]   # imprime la lista para el agente
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

JSON_DEFAULT = Path(__file__).with_name("taxonomias.json")
_ID_RE = re.compile(r"^[A-Z]+(\.[A-Z0-9]+)?$")


def cargar(ruta: str | Path = JSON_DEFAULT) -> dict:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _todas_entradas(tx: dict):
    """Itera (id, nombre, area_id|None) por subtemas y auxiliares."""
    for area in tx.get("areas", []):
        for sub in area.get("subtemas", []):
            yield sub["id"], sub["nombre"], area["id"]
    for aux in tx.get("auxiliares", []):
        yield aux["id"], aux["nombre"], None


def ids_validos(tx: dict) -> set[str]:
    return {i for i, _, _ in _todas_entradas(tx)}


def validar(tx: dict) -> list[str]:
    """Devuelve lista de problemas (vacía = OK)."""
    problemas: list[str] = []
    vistos: set[str] = set()
    area_ids = {a["id"] for a in tx.get("areas", [])}
    for area in tx.get("areas", []):
        if not _ID_RE.match(area["id"]):
            problemas.append(f"id de área con formato raro: {area['id']!r}")
    for tid, nombre, area_id in _todas_entradas(tx):
        if tid in vistos:
            problemas.append(f"id DUPLICADO: {tid!r}")
        vistos.add(tid)
        if not _ID_RE.match(tid):
            problemas.append(f"id con formato inválido: {tid!r}")
        if not (nombre or "").strip():
            problemas.append(f"id sin nombre: {tid!r}")
        if area_id and not tid.startswith(area_id + "."):
            problemas.append(f"id {tid!r} no respeta el prefijo de su área {area_id!r}")
    return problemas


def lista_para_prompt(tx: dict) -> str:
    """Texto compacto Área/subtemas para inyectar en el prompt del agente."""
    lineas = []
    for area in tx.get("areas", []):
        subs = ", ".join(f"{s['id']}={s['nombre']}" for s in area.get("subtemas", []))
        lineas.append(f"[{area['id']}] {area['nombre']}: {subs}")
    aux = ", ".join(f"{a['id']}={a['nombre']}" for a in tx.get("auxiliares", []))
    if aux:
        lineas.append(f"[AUX] Auxiliares: {aux}")
    return "\n".join(lineas)


def _main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validar"
    ruta = sys.argv[2] if len(sys.argv) > 2 else JSON_DEFAULT
    tx = cargar(ruta)
    if cmd == "validar":
        problemas = validar(tx)
        n = len(ids_validos(tx))
        if problemas:
            print(f"PROBLEMAS ({len(problemas)}):")
            for p in problemas:
                print("  -", p)
            return 1
        print(f"OK — {n} ids válidos y únicos, {len(tx.get('areas', []))} áreas.")
        return 0
    if cmd == "prompt":
        print(lista_para_prompt(tx))
        return 0
    print(f"comando desconocido: {cmd!r} (usar 'validar' o 'prompt')")
    return 2


if __name__ == "__main__":
    sys.exit(_main())
