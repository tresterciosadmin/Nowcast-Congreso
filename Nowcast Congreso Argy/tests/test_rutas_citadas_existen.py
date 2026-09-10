# -*- coding: utf-8 -*-
"""Una ruta del repo nombrada en un docstring o un comentario tiene que existir.

Este repo se lee por sus docstrings: `MAPA.md` se arma con ellos y el CLAUDE.md
manda leer el README del modulo antes de tocarlo. Una ruta que quedo vieja no da
error -- manda a alguien a buscar un archivo donde no esta, y el costo se paga en
minutos perdidos, no en un test rojo.

Ya paso, y por eso existe este archivo. El 2026-09-08 se encontraron CINCO
docstrings que prometian el codigo viejo en `Archivos_Borrar/BORRAR_*.py`:
ninguna de las cinco copias existia. El 09-09 aparecieron siete rutas mas, casi
todas por un segmento `data/` o `src/` que se cayo al escribirlas.

QUE MIRA, Y QUE NO
    - SOLO rutas que arrancan en una carpeta de primer nivel del repo
      (`datos/...`, `variables/...`). Una ruta relativa al modulo (`data/x.csv`)
      es correcta desde ahi y no se toca.
    - Se saltea lo truncado con `...`, que es prosa, no una ruta.
    - Se exceptuan los archivos GENERADOS que declara `rutas.py`: son salidas que
      pueden no estar hasta que alguien corra el paso que las produce.

    python -m pytest tests/test_rutas_citadas_existen.py -q
    python tests/test_rutas_citadas_existen.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROYECTO))

import rutas  # noqa: E402

EXCLUIDAS = ("Archivos_Borrar", "Aportes sobre dataset congreso", "__pycache__",
             ".pytest_cache")
EXTS = "py|md|json|csv|parquet|ps1|sh|yml|R|sql|html|js|xlsx|db"
RE_RUTA = re.compile(r"(?<![\w./-])((?:[A-Za-z_][\w.-]*/){1,5}[\w.-]+\.(?:" + EXTS + r"))")


def _carpetas_de_primer_nivel() -> set[str]:
    return {p.name for p in RAIZ_PROYECTO.iterdir()
            if p.is_dir() and p.name not in EXCLUIDAS}


def _generados() -> set[str]:
    """Rutas (relativas al repo) que `rutas.py` marca como salidas generadas."""
    salida = set()
    for nombre, ruta in rutas.inventario().items():
        if nombre in rutas.GENERADOS:
            try:
                salida.add(Path(ruta).resolve().relative_to(RAIZ_PROYECTO).as_posix())
            except ValueError:
                pass
    return salida


def _archivos_py():
    for p in sorted(RAIZ_PROYECTO.rglob("*.py")):
        rel = p.relative_to(RAIZ_PROYECTO).as_posix()
        if any(rel.startswith(e) or f"/{e}/" in f"/{rel}" for e in EXCLUIDAS):
            continue
        yield rel, p


def rutas_rotas() -> dict[str, list[str]]:
    tope, generados = _carpetas_de_primer_nivel(), _generados()
    rotas: dict[str, list[str]] = {}
    for rel, p in _archivos_py():
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for citada in sorted(set(RE_RUTA.findall(texto))):
            if citada.split("/")[0] not in tope:
                continue                                  # URL, libreria, etc.
            if "..." in citada:
                continue                                  # prosa truncada
            if (RAIZ_PROYECTO / citada).exists():
                continue
            if citada in generados or any(citada.startswith(g + "/") for g in generados):
                continue                                  # salida que puede no estar
            # ¿es relativa al modulo? entonces es correcta desde donde se escribio
            if any((d / citada).exists() for d in list(p.parents)[:4]):
                continue
            rotas.setdefault(citada, []).append(rel)
    return rotas


def test_ninguna_ruta_citada_esta_rota():
    rotas = rutas_rotas()
    assert not rotas, (
        "estas rutas se nombran en el codigo y NO existen:\n"
        + "".join(f"  {r}\n" + "".join(f"      <- {q}\n" for q in quienes)
                  for r, quienes in sorted(rotas.items()))
        + "Corregir el texto, no crear el archivo. Si es una salida generada, "
          "declararla en rutas.py y agregarla a GENERADOS.")


def test_el_detector_mira_algo():
    """Sin esto, un cambio en el regex dejaria el control en verde sin controlar."""
    tope = _carpetas_de_primer_nivel()
    citadas = 0
    for _, p in _archivos_py():
        for c in set(RE_RUTA.findall(p.read_text(encoding="utf-8", errors="ignore"))):
            if c.split("/")[0] in tope:
                citadas += 1
    assert citadas > 50, (
        f"solo {citadas} rutas del repo detectadas en los docstrings: el regex o la "
        "lista de carpetas de primer nivel se rompio.")


if __name__ == "__main__":
    fallas = 0
    for nombre, fn in sorted(globals().items()):
        if nombre.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"[OK ] {nombre}")
            except AssertionError as e:
                fallas += 1
                print(f"[FALLA] {nombre}\n  {e}")
    raise SystemExit(1 if fallas else 0)
