# -*- coding: utf-8 -*-
"""`rutas.py` tiene que decir la verdad, y tiene que estar COMPLETO.

Dos controles, y el segundo es el que importa:

1. **Lo declarado existe.** Lo que no esta marcado como generado tiene que estar
   en disco. Una ruta declarada que apunta a la nada es peor que no declararla:
   parece un contrato y no lo es.

2. **Lo que el codigo usa esta declarado.** Se escanean todos los .py buscando
   rutas armadas a mano que cruzan de un modulo a otro (`parents[3] / "datos" /
   ...`, `RAIZ / "variables" / ...`). Cada una tiene que corresponder a algo de
   `rutas.py`. Sin esto, `rutas.py` seria una lista optimista que se queda vieja
   sola — que es exactamente el modo de falla del repo.

El test NO exige que los modulos IMPORTEN `rutas.py` (la migracion va modulo por
modulo, con su claim en TABLERO). Exige que el inventario este completo, que es
lo que lo hace util desde el dia uno.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("_rutas_nowcast", RAIZ / "rutas.py")
rutas = importlib.util.module_from_spec(spec)
sys.modules["_rutas_nowcast"] = rutas
spec.loader.exec_module(rutas)

CAPAS = ("datos", "variables", "modelo", "evaluacion", "producto", "docs")

# Carpetas que no son codigo del proyecto (ver .mapa/indexar.py, mismo criterio).
EXCLUIR = ("Archivos_Borrar", "Aportes sobre dataset congreso", "__pycache__",
           ".pytest_cache", ".mapa")

# `X / "modulo" / "sub" / ...` con X = RAIZ/ROOT/root/raiz/_RAIZ o parents[N]
RE_RUTA = re.compile(
    r"""(?:parents\[[0-9]\]|RAIZ|ROOT|root|raiz|_RAIZ|_ROOT)\s*/\s*"""
    r"""("(?:[^"\n]+)"(?:\s*/\s*"(?:[^"\n]+)")*)""")
RE_TROZO = re.compile(r'"([^"\n]+)"')


def _archivos_py():
    for f in sorted(RAIZ.rglob("*.py")):
        rel = f.relative_to(RAIZ).as_posix()
        if any(e in rel for e in EXCLUIR) or rel == "rutas.py":
            continue
        yield f, rel


def test_lo_declarado_existe():
    """Si algo declarado no esta y no es generado, el contrato miente."""
    hay_raiz_git = (rutas.RAIZ_GIT / ".git").is_dir()
    faltan = []
    for nombre, ruta in sorted(rutas.inventario().items()):
        if nombre in rutas.GENERADOS:
            continue
        if nombre in rutas.SOLO_EN_RAIZ_GIT and not hay_raiz_git:
            continue                      # se esta mirando solo la subcarpeta
        if not ruta.exists():
            faltan.append(f"{nombre} -> {ruta}")
    assert not faltan, (
        "rutas declaradas que NO estan en disco (y no estan marcadas como "
        "generadas en GENERADOS):\n  " + "\n  ".join(faltan))


def test_el_codigo_no_usa_rutas_entre_modulos_sin_declarar():
    """Cada ruta cruzada que el codigo arma a mano tiene que figurar en rutas.py."""
    declaradas = {r.resolve() for r in rutas.inventario().values()}

    huerfanas: dict[str, set[str]] = {}
    for f, rel in _archivos_py():
        modulo_propio = "/".join(rel.split("/")[:2]) if rel.split("/")[0] in CAPAS else rel.split("/")[0]
        texto = f.read_text(encoding="utf-8", errors="replace")
        for m in RE_RUTA.finditer(texto):
            trozos = RE_TROZO.findall(m.group(1))
            if not trozos or trozos[0] not in CAPAS or len(trozos) < 2:
                continue                                   # ruta interna del modulo
            destino = "/".join(trozos[:2])
            if destino == modulo_propio:
                continue                                   # se referencia a si mismo
            p = (RAIZ.joinpath(*trozos)).resolve()
            if p in declaradas or any(d in p.parents for d in declaradas):
                continue
            huerfanas.setdefault("/".join(trozos), set()).add(rel)

    if huerfanas:
        detalle = "\n".join(
            f"  {ruta}\n      usada en: {', '.join(sorted(usos))}"
            for ruta, usos in sorted(huerfanas.items()))
        pytest.fail(
            "hay rutas ENTRE MODULOS armadas a mano que no estan en `rutas.py`.\n"
            "Declaralas ahi (es el mapa de conexiones del repo) o, si son "
            "internas, no las armes desde la raiz:\n" + detalle)


def test_la_raiz_es_la_del_proyecto_no_la_de_git():
    """Trampa historica del repo: la raiz git esta UN NIVEL ARRIBA del proyecto."""
    assert (rutas.RAIZ / "CLAUDE.md").exists(), "RAIZ no apunta al proyecto"
    assert rutas.RAIZ_GIT == rutas.RAIZ.parent
    assert rutas.WORKFLOWS == rutas.RAIZ_GIT / ".github" / "workflows", (
        "los workflows van en la RAIZ GIT; lo que se escriba en la subcarpeta "
        "GitHub no lo lee nunca")
