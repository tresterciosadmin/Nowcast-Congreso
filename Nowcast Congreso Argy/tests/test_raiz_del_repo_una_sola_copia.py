# -*- coding: utf-8 -*-
"""La raiz del repo se busca de UNA sola forma: la que documenta `rutas.py`.

Hasta el 2026-09-08 convivian dos criterios para la misma pregunta:

  A. `rutas.py` (el bueno, y explica por que): subir por los padres hasta
     encontrar el propio `rutas.py`. Sobrevive a que un modulo cambie de
     profundidad, *"que es justo lo que rompia antes"*.
  B. Siete copias de `_hallar_repo()` / `_repo()`: subir hasta una carpeta que
     tenga `coordinacion/` **y** `variables/`. Cuatro de las siete en
     `modelo/ensemble`, o sea en el motor.

Las dos daban lo mismo, y esta medido (ver el primer test, que se escribio ANTES
de unificar, como pide el plan de limpieza). Pero B se apoya en que dos carpetas
concretas no cambien de nombre ni de lugar: una limpieza que mueva
`coordinacion/` deja a los siete buscando una raiz que no existe, y el error no
aparece donde esta la causa.

Es la misma forma que el ADR-0014 (definiciones compartidas viven una sola vez),
un nivel mas abajo: no una definicion del dominio, sino la de "donde estoy".

    python -m pytest tests/test_raiz_del_repo_una_sola_copia.py -q
    python tests/test_raiz_del_repo_una_sola_copia.py
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
EXCLUIDAS = ("Archivos_Borrar", "Aportes sobre dataset congreso", "__pycache__",
             ".pytest_cache", "fase0")

# El criterio viejo, escrito como lo escribian las siete copias. Se conserva aca
# -- y SOLO aca -- para poder seguir comparandolo contra el bueno.
RE_CRITERIO_VIEJO = re.compile(r'"coordinacion"\s*\)\s*\.is_dir\(\)')


def _archivos_py():
    for p in sorted(RAIZ_PROYECTO.rglob("*.py")):
        rel = p.relative_to(RAIZ_PROYECTO).as_posix()
        if any(rel.startswith(e) or f"/{e}/" in f"/{rel}" for e in EXCLUIDAS):
            continue
        yield rel, p


def _raiz_por_rutas(desde: Path) -> Path | None:
    """El criterio de `rutas.py`: subir hasta encontrarlo."""
    for d in [desde, *desde.parents]:
        if (d / "rutas.py").is_file():
            return d
    return None


def _raiz_por_carpetas(desde: Path) -> Path | None:
    """El criterio viejo: subir hasta `coordinacion/` + `variables/`."""
    for d in [desde, *desde.parents]:
        if (d / "coordinacion").is_dir() and (d / "variables").is_dir():
            return d
    return None


def test_los_dos_criterios_dan_la_misma_raiz():
    """Escrito ANTES de unificar: si difieren en algun lado, la fusion mueve algo.

    Se evalua desde la carpeta de CADA archivo .py del repo, no desde una muestra.
    """
    difieren, sin_raiz = [], []
    carpetas = sorted({p.parent for _, p in _archivos_py()})
    assert carpetas, "no se encontro ningun .py: revisar el test, no el repo"
    for d in carpetas:
        a, b = _raiz_por_rutas(d), _raiz_por_carpetas(d)
        if a is None or b is None:
            sin_raiz.append(f"{d.relative_to(RAIZ_PROYECTO)}: rutas={a} carpetas={b}")
        elif a != b:
            difieren.append(f"{d.relative_to(RAIZ_PROYECTO)}: rutas={a} carpetas={b}")
    assert not sin_raiz, "desde estas carpetas algun criterio no encuentra raiz:\n  " + \
        "\n  ".join(sin_raiz)
    assert not difieren, (
        "los dos criterios de raiz NO coinciden desde:\n  " + "\n  ".join(difieren)
        + "\nSi esto falla, unificar `_hallar_repo` con el criterio de rutas.py "
          "CAMBIA a que archivos apunta alguien. No es una limpieza.")


def test_nadie_reimplementa_la_busqueda_de_la_raiz():
    """Despues de unificar, el criterio viejo no vuelve por la ventana."""
    culpables = []
    for rel, p in _archivos_py():
        if rel == Path(__file__).relative_to(RAIZ_PROYECTO).as_posix():
            continue          # este archivo lo conserva a proposito, para comparar
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for n, linea in enumerate(texto.splitlines(), 1):
            if RE_CRITERIO_VIEJO.search(linea):
                culpables.append(f"{rel}:{n}")
    assert not culpables, (
        "estos archivos vuelven a buscar la raiz por `coordinacion/` + `variables/`:\n  "
        + "\n  ".join(culpables)
        + "\nUsa el bootstrap que documenta rutas.py:\n"
          '    sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents\n'
          '                                if (d / "rutas.py").is_file())))\n'
          "    from rutas import RAIZ as REPO\n"
          "Se apoya en `rutas.py`, no en que dos carpetas no cambien de nombre.")


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
