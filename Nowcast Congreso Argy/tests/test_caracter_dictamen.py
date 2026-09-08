# -*- coding: utf-8 -*-
"""El caracter del dictamen se decide en UN solo lugar, y la tabla no cambia sola.

`definiciones.caracter_de_dictamen` (ADR-0021) parte en dos cosas distintas la
misma poblacion: el panel con el que `modelo/ensemble` estima el beta del
dictamen, y el corte con el que `evaluacion/baseline` lo evalua. Hasta el
2026-09-08 estaba COPIADA en los dos, identica caracter por caracter.

Por que importa que no diverja, y por que un test y no un docstring: si las dos
copias se separan, el beta se estima sobre una particion y se lo mide sobre otra,
y **nada da error**. El control 5 de `verificar_regeneracion.py` seguiria en verde,
porque mira que las categorias existan, no como se asignan.

La unificacion se hizo despues de verificar que las dos implementaciones daban lo
mismo en las 16 entradas posibles. Esa tabla es la de abajo, y es lo que este
archivo defiende.

    python -m pytest tests/test_caracter_dictamen.py -q
    python tests/test_caracter_dictamen.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROYECTO))

from definiciones import CARACTERES_DICTAMEN, caracter_de_dictamen  # noqa: E402

EXCLUIDAS = ("Archivos_Borrar", "Aportes sobre dataset congreso", "__pycache__",
             ".pytest_cache", "fase0")

# La tabla completa, medida el 2026-09-08 sobre las DOS implementaciones que
# habia, antes de unificarlas. Las 16 combinaciones del vocabulario.
TABLA = {
    frozenset(): None,
    frozenset({"desconocido"}): None,
    frozenset({"unico"}): "UNICO",
    frozenset({"mayoria"}): "mayoria",
    frozenset({"minoria"}): "solo_minoria",
    frozenset({"desconocido", "unico"}): "UNICO",
    frozenset({"desconocido", "mayoria"}): "mayoria",
    frozenset({"desconocido", "minoria"}): "solo_minoria",
    frozenset({"mayoria", "unico"}): "mayoria",
    frozenset({"minoria", "unico"}): "DISPUTADO",
    frozenset({"mayoria", "minoria"}): "DISPUTADO",
    frozenset({"mayoria", "minoria", "unico"}): "DISPUTADO",
    frozenset({"desconocido", "mayoria", "unico"}): "mayoria",
    frozenset({"desconocido", "minoria", "unico"}): "DISPUTADO",
    frozenset({"desconocido", "mayoria", "minoria"}): "DISPUTADO",
    frozenset({"desconocido", "mayoria", "minoria", "unico"}): "DISPUTADO",
}

# La forma que tenian las dos copias. Si vuelve a aparecer, alguien la reescribio.
RE_COPIA = re.compile(r'"minoria"\s+in\s+\w+\s+and\s*\(')


def _archivos_py():
    for p in sorted(RAIZ_PROYECTO.rglob("*.py")):
        rel = p.relative_to(RAIZ_PROYECTO).as_posix()
        if any(rel.startswith(e) or f"/{e}/" in f"/{rel}" for e in EXCLUIDAS):
            continue
        yield rel, p


def test_la_tabla_completa_no_cambio():
    """Las 16 entradas posibles, con el resultado que daban las dos copias."""
    malas = []
    for entrada, esperado in sorted(TABLA.items(), key=lambda kv: sorted(kv[0])):
        obtenido = caracter_de_dictamen(entrada)
        if obtenido != esperado:
            malas.append(f"{sorted(entrada) or '(vacio)'}: esperaba {esperado!r}, "
                         f"dio {obtenido!r}")
    assert not malas, ("la tabla del caracter del dictamen cambio:\n  "
                       + "\n  ".join(malas)
                       + "\nSi el cambio es querido, va con ADR: parte el panel del "
                         "beta y el corte del baseline a la vez.")


def test_desconocido_no_es_despacho_unico():
    """El caso que motivo el rotulo: 'no encontre el rotulo' != 'despacho unico'."""
    assert caracter_de_dictamen(frozenset({"desconocido"})) is None
    assert caracter_de_dictamen(frozenset({"desconocido", "unico"})) == "UNICO"


def test_todo_lo_que_devuelve_esta_declarado():
    salidas = {v for v in TABLA.values() if v is not None}
    assert salidas <= set(CARACTERES_DICTAMEN), (
        f"devuelve {salidas - set(CARACTERES_DICTAMEN)}, que no esta en "
        "CARACTERES_DICTAMEN")


def test_nadie_reimplementa_la_regla():
    """Una segunda copia no da error: da un numero distinto y nadie se entera."""
    culpables = []
    aca = Path(__file__).relative_to(RAIZ_PROYECTO).as_posix()
    for rel, p in _archivos_py():
        if rel in (aca, "definiciones.py"):
            continue
        for n, linea in enumerate(p.read_text(encoding="utf-8", errors="ignore")
                                  .splitlines(), 1):
            if RE_COPIA.search(linea):
                culpables.append(f"{rel}:{n}")
    assert not culpables, (
        "estos archivos vuelven a decidir el caracter del dictamen por su cuenta:\n  "
        + "\n  ".join(culpables)
        + "\nUsa `from definiciones import caracter_de_dictamen` (ADR-0021).")


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
