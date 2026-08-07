"""Tests del padrón del Senado que usa la ingesta de argentinadatos.

POR QUÉ EXISTEN (2026-08-06). El bloque de cada voto del Senado no viene en la
fuente: lo resuelve `to_canonical._padron_senado()` cruzando padrones
versionados. Ese cruce ya falló en silencio dos veces:

  1. 2026-07-11: no se cruzaba nada y TODO el Senado entraba 'SIN BLOQUE'.
  2. 2026-07-31 → 2026-08-06: se cruzaba sólo contra el padrón histórico, que
     termina el 2025-12-09. Los 6.192 votos del Senado 2026 (posteriores al
     recambio del 10-dic) volvieron a entrar 'SIN BLOQUE' — y el síntoma se
     diagnosticó mal dos veces antes de encontrar la causa.

La falla es silenciosa: no rompe nada, sólo degrada el nowcast de una cámara
entera. De ahí el test de COBERTURA (el punto 3), que es el que avisa.

Corren offline, contra los CSV versionados. Desde la raíz del repo, de las dos
formas (la segunda es la convención del resto del repo, la que usa el runbook):

    python -m pytest datos/argentinadatos/tests/ -v
    python datos\\argentinadatos\\tests\\test_padron_senado.py
"""
from __future__ import annotations

import csv
import importlib.util
import sys
import types
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]
SRC = RAIZ / "datos" / "argentinadatos" / "src" / "to_canonical.py"
PADRON_VIGENTE = RAIZ / "datos" / "padron" / "data" / "padron_senado.csv"

# Fecha de referencia: posterior al recambio del 10-dic-2025. Es el tramo que
# se rompió; si el test se escribiera contra una fecha vieja, no vería nada.
FECHA_2026 = "2026-05-01"


def _cargar_modulo():
    """Importa to_canonical sin exigir requests/pandas (el test no toca la red)."""
    for nombre in ("requests", "pandas"):
        try:
            __import__(nombre)
        except ImportError:
            stub = types.ModuleType(nombre)
            if nombre == "requests":
                stub.exceptions = types.SimpleNamespace(
                    ConnectionError=Exception, HTTPError=Exception, Timeout=Exception
                )
                sys.modules["requests.exceptions"] = stub.exceptions
            sys.modules[nombre] = stub
    spec = importlib.util.spec_from_file_location("to_canonical_test", SRC)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def tc():
    return _cargar_modulo()


@pytest.fixture(scope="module")
def idx(tc):
    return tc._padron_senado()


def _senadores_vigentes():
    with open(PADRON_VIGENTE, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


# --- 1. El padrón vigente está enchufado -------------------------------------

def test_el_padron_vigente_existe():
    """Si este archivo desaparece, el Senado 2026 entra ciego y nadie se entera."""
    assert PADRON_VIGENTE.exists(), (
        f"falta {PADRON_VIGENTE} — es el único padrón que cubre el mandato "
        f"que arrancó el 2025-12-10"
    )


def test_el_indice_incluye_al_padron_vigente(idx):
    """El índice tiene que traer claves con mandato abierto más allá de 2025-12-09."""
    hay_mandatos_nuevos = any(
        hasta > "2025-12-09"
        for filas in idx.values()
        for _desde, hasta, _bloque in filas
    )
    assert hay_mandatos_nuevos, (
        "el índice se corta el 2025-12-09: `_padron_senado()` no está leyendo "
        "datos/padron/data/padron_senado.csv"
    )


# --- 2. Casos testigo --------------------------------------------------------

def test_atauche_bloquea_en_lla_no_en_su_alianza_de_ingreso(tc, idx):
    """Caso que el equipo usó para descartar las fuentes automáticas.

    Atauche ENTRA por el Partido Renovador Federal pero BLOQUEA en LLA.
    argentinadatos y el listado oficial dan la alianza de ingreso; el padrón
    curado da el bloque parlamentario, que es el que importa para el recuento.
    """
    assert tc._bloque_sen(idx, "ATAUCHE, EZEQUIEL", FECHA_2026) == "LA LIBERTAD AVANZA"


def test_el_historico_sigue_mandando_en_el_tramo_solapado(tc, idx):
    """El padrón nuevo se agregó ÚLTIMO: no debe pisar lo ya curado.

    Los senadores con mandato 2021-2027 figuran en los dos archivos. En fechas
    anteriores al recambio tiene que seguir ganando el padrón histórico.
    """
    assert tc._bloque_sen(idx, "BULLRICH, ESTEBAN JOSE", "2018-05-01") == "FRENTE PRO"


def test_fecha_fuera_de_todo_mandato_da_sin_bloque(tc, idx):
    """El fallback tiene que ser explícito, no un bloque inventado."""
    assert tc._bloque_sen(idx, "ATAUCHE, EZEQUIEL", "2005-05-01") == "SIN BLOQUE"


def test_nombre_desconocido_da_sin_bloque(tc, idx):
    assert tc._bloque_sen(idx, "PERSONA QUE NO EXISTE", FECHA_2026) == "SIN BLOQUE"


# --- 3. Cobertura: el test que avisa cuando la falla vuelve -------------------

def test_los_72_senadores_vigentes_resuelven_bloque(tc, idx):
    """EL TEST QUE IMPORTA.

    Si esto baja, el nowcast del Senado se degrada sin romper nada. Es
    exactamente lo que pasó entre el 31-07 y el 06-08.
    """
    vigentes = _senadores_vigentes()
    sin_bloque = [
        r["legislador"]
        for r in vigentes
        if tc._bloque_sen(idx, r["legislador"], FECHA_2026) == "SIN BLOQUE"
    ]
    assert not sin_bloque, (
        f"{len(sin_bloque)}/{len(vigentes)} senadores vigentes sin bloque a "
        f"{FECHA_2026}: {sin_bloque[:10]}"
    )


def test_la_camara_esta_completa():
    """72 bancas. Si el padrón se desincroniza, el recuento arranca mal."""
    assert len(_senadores_vigentes()) == 72


# --- Modo script (convención del repo: `python <archivo>`) --------------------

if __name__ == "__main__":
    _tc = _cargar_modulo()
    _idx = _tc._padron_senado()

    # Las fixtures de pytest no existen acá: se resuelven a mano por nombre.
    _valores = {"tc": _tc, "idx": _idx}
    _casos = [
        (nombre, obj)
        for nombre, obj in sorted(globals().items())
        if nombre.startswith("test_") and callable(obj)
    ]

    fallas = 0
    for nombre, fn in _casos:
        args = [_valores[p] for p in fn.__code__.co_varnames[: fn.__code__.co_argcount]]
        try:
            fn(*args)
            print(f"  OK   {nombre}")
        except AssertionError as e:
            fallas += 1
            print(f"  FALLA {nombre}: {e}")

    print(f"\n{len(_casos) - fallas} chequeos OK, {fallas} fallas")
    raise SystemExit(1 if fallas else 0)
