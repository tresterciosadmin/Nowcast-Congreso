# -*- coding: utf-8 -*-
"""Las definiciones que viven duplicadas en varios modulos tienen que COINCIDIR.

POR QUE EXISTE ESTE TEST
------------------------
La regla del repo es "no importes el codigo de otro modulo, consumi su salida"
(CLAUDE.md). Es una buena regla, pero tiene un costo: las DEFINICIONES
compartidas (que periodo parlamentario es una fecha, que mayoria exige un
proyecto, cuantas bancas tiene cada camara) terminan copiadas en varios modulos,
sincronizadas a mano. Hoy los docstrings dicen "mantener sincronizadas" — o sea,
el unico control es que alguien se acuerde.

Y este proyecto ya sabe como termina eso: sus errores de datos NO dan error.
Si `periodo_parlamentario` se corrige en un modulo y no en los otros, nada se
rompe: el skill se mueve un poco y nadie sabe por que.

Este test NO mueve una sola linea de codigo de produccion. Solo afirma que las
copias siguen de acuerdo, sobre los casos borde donde una divergencia se veria
primero. Si alguna vez falla, la respuesta correcta NO es tocar el test: es
decidir cual de las copias tiene razon y arreglar las otras.

Como correr:
    python -m pytest tests/test_definiciones_compartidas.py -q     # desde la raiz del proyecto
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parents[1]

# Las copias, con la ruta de su modulo. Si aparece una quinta copia, se agrega aca.
COPIAS_PERIODO = {
    "export": "datos/export/src/export_base.py",
    "voto_individual": "modelo/voto_individual/src/disciplina.py",
    "legislador": "variables/legislador/src/ficha.py",
    "asistencia_quorum": "variables/asistencia_quorum/src/asistencia.py",
}
COPIAS_MAYORIA_SERIE = {
    "export": "datos/export/src/export_base.py",
    "voto_individual": "modelo/voto_individual/src/disciplina.py",
}
COPIAS_MAYORIA_ESCALAR = {
    "agregador": "modelo/agregador_institucional/src/agregador.py",
}


def cargar(alias: str, rel: str):
    """Importa un archivo por RUTA, con un nombre unico.

    A proposito NO se usa `sys.path.insert` + `import <modulo>`, que es como se
    cruzan los modulos en el resto del repo: ese patron toma el PRIMER archivo
    que encuentra con ese nombre. En este repo hay tres `to_canonical.py`, asi
    que el patron es una trampa esperando. Aca cada copia entra con su propio
    nombre y no puede taparse con otra.
    """
    ruta = RAIZ / rel
    if not ruta.exists():                                  # el modulo se movio
        pytest.skip(f"no esta {rel} (se movio o se renombro): revisar este test")
    nombre = f"_defcomp_{alias}"
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod                              # para dataclasses/pickle
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------- casos borde
# El recambio legislativo es el 10 de diciembre de los anios IMPARES. Los casos
# que importan son los tres dias alrededor de esa bisagra, y las fechas que
# faltan (que en este repo llegan como None, NaN o pd.NA segun el backend).
CASOS_PERIODO = [
    # (fecha, anio, periodo esperado)
    ("2019-12-09", 2019, "2017-2019"),   # vispera del recambio: todavia el anterior
    ("2019-12-10", 2019, "2019-2021"),   # el dia exacto: ya el nuevo
    ("2019-12-11", 2019, "2019-2021"),
    ("2020-06-01", 2020, "2019-2021"),   # anio par: siempre el periodo abierto en el impar previo
    ("2018-12-10", 2018, "2017-2019"),   # 10-dic de anio PAR: no hay recambio, no aplica la bisagra
    ("2021-01-05", 2021, "2019-2021"),   # enero de impar: antes del recambio de ese anio
    ("2021-12-10", 2021, "2021-2023"),
    ("2023-12-09", 2023, "2021-2023"),
    ("2024-03-01", 2024, "2023-2025"),
    (None, 2020, "2019-2021"),           # sin fecha: cae al anio
    (None, 2021, "2021-2023"),
    (None, None, None),                  # sin nada: NA, nunca un periodo inventado
]

CASOS_MAYORIA = [
    (None, "SIMPLE"),                    # sin dato -> SIMPLE (el caso comun)
    ("", "SIMPLE"),
    ("SIMPLE", "SIMPLE"),
    ("Simple", "SIMPLE"),
    ("ABSOLUTA", "ABSOLUTA"),
    ("MAYORIA ABSOLUTA DE LOS PRESENTES", "SIMPLE"),
    ("MAYORIA ABSOLUTA SOBRE EL TOTAL DEL CUERPO", "ABSOLUTA"),
    ("LA MITAD MAS UNO", "ABSOLUTA"),
    ("MITAD MÁS UNO", "ABSOLUTA"),
    ("DOS TERCIOS DE LOS PRESENTES", "DOS_TERCIOS"),
    ("DOS TERCIOS SOBRE EL TOTAL DEL CUERPO", "DOS_TERCIOS_CUERPO"),
    ("TRES CUARTOS", "TRES_CUARTOS"),
]


def marco(backend: str) -> pd.DataFrame:
    """El mismo caso de prueba en los DOS backends de dtype.

    No es paranoia de estilo: el 08-08-2026 un test dio 83/83 en el sandbox y
    reventó en la PC de Valle porque un faltante llegaba como float('nan') en un
    lado y como pd.NA en el otro. Si una copia se escribe asumiendo un backend,
    acá se ve.
    """
    df = pd.DataFrame({
        "fecha": [c[0] for c in CASOS_PERIODO],
        "anio": [c[1] for c in CASOS_PERIODO],
    })
    if backend == "pyarrow":
        pytest.importorskip("pyarrow")
        df = df.convert_dtypes(dtype_backend="pyarrow")
    return df


# ------------------------------------------------------- periodo_parlamentario

def _correr_periodo(backend):
    """Corre las cuatro copias sobre los casos borde y devuelve {alias: resultado}."""
    df = marco(backend)
    esperado = [c[2] for c in CASOS_PERIODO]

    resultados = {}
    for alias, rel in COPIAS_PERIODO.items():
        mod = cargar(f"periodo_{alias}_{backend}", rel)
        fn = getattr(mod, "periodo_parlamentario", None)
        assert fn is not None, (
            f"{rel} ya no define periodo_parlamentario. Si se movio a un lugar "
            f"comun, sacá su fila de COPIAS_PERIODO; si desaparecio, revisá quien la usaba.")
        obtenido = [None if pd.isna(v) else str(v) for v in fn(df["fecha"], df["anio"])]
        resultados[alias] = obtenido

    return resultados


def test_periodo_parlamentario_todas_las_copias_coinciden():
    """Backend numpy/object: el que usan hoy todas las corridas reales."""
    backend = "object"
    esperado = [c[2] for c in CASOS_PERIODO]
    resultados = _correr_periodo(backend)

    # 1) cada copia contra la definicion escrita (no solo entre ellas: si las
    #    cuatro se equivocan igual, coincidir no prueba nada)
    for alias, obtenido in resultados.items():
        for (fecha, anio, esp), got in zip(CASOS_PERIODO, obtenido):
            assert got == esp, (
                f"[{alias}] periodo_parlamentario({fecha!r}, {anio!r}) = {got!r}, "
                f"esperaba {esp!r} (backend {backend})")

    # 2) y todas entre si, que es lo que se rompe primero
    base = resultados[next(iter(resultados))]
    for alias, obtenido in resultados.items():
        assert obtenido == base, (
            f"[{alias}] se desincronizo del resto ({backend}).\n"
            f"  {alias}: {obtenido}\n  resto : {base}\n"
            f"Decidí cual tiene razon y arreglá las otras — no toques este test.")
    assert esperado == base


@pytest.mark.xfail(
    raises=NotImplementedError, strict=False,
    reason="las CUATRO copias revientan con backend pyarrow: `pd.to_numeric(anio)` "
           "conserva el dtype int64[pyarrow] y `a % 2` levanta "
           "NotImplementedError: mod not implemented (verificado en pandas 2.2.3 y 3.0.2). "
           "Arreglo: una linea por copia -> "
           "a = pd.to_numeric(anio, errors='coerce').astype('float64'). "
           "No se aplica desde aca porque toca 4 modulos con dueno; ver ESTADO 2026-08-20. "
           "Cuando se arregle, este test pasa a XPASS y hay que sacarle el xfail.")
def test_periodo_parlamentario_backend_pyarrow():
    """Hoy NINGUNA copia sobrevive a una columna con backend Arrow.

    En produccion no se nota porque `pd.read_parquet` devuelve numpy. Pero la
    metodologia del repo pide ejercitar los dos backends justamente porque el
    08-08-2026 un test dio 83/83 en el sandbox y reventó en la PC de Valle.
    Este test deja el agujero anotado en vez de escondido.
    """
    resultados = _correr_periodo("pyarrow")
    base = resultados[next(iter(resultados))]
    for alias, obtenido in resultados.items():
        assert obtenido == base, f"[{alias}] se desincronizo del resto (pyarrow)"


# --------------------------------------------------------- normalizar_mayoria

@pytest.mark.parametrize("backend", ["object", "pyarrow"])
def test_normalizar_mayoria_todas_las_copias_coinciden(backend):
    s = pd.Series([c[0] for c in CASOS_MAYORIA], dtype="object")
    if backend == "pyarrow":
        pytest.importorskip("pyarrow")
        s = s.convert_dtypes(dtype_backend="pyarrow")
    esperado = [c[1] for c in CASOS_MAYORIA]

    resultados = {}
    for alias, rel in COPIAS_MAYORIA_SERIE.items():
        mod = cargar(f"mayoria_{alias}_{backend}", rel)
        fn = mod.normalizar_mayoria
        resultados[alias] = [None if pd.isna(v) else str(v) for v in fn(s)]

    # la del agregador toma un escalar, no una Serie: mismo contrato, otra firma
    for alias, rel in COPIAS_MAYORIA_ESCALAR.items():
        mod = cargar(f"mayoria_{alias}_{backend}", rel)
        fn = mod.normalizar_mayoria
        resultados[alias] = [str(fn(None if pd.isna(v) else v)) for v in s]

    for alias, obtenido in resultados.items():
        for (entrada, esp), got in zip(CASOS_MAYORIA, obtenido):
            assert got == esp, (
                f"[{alias}] normalizar_mayoria({entrada!r}) = {got!r}, esperaba {esp!r} "
                f"(backend {backend})")


# ------------------------------------------------------- constantes compartidas

def test_constantes_compartidas():
    """Numeros del dominio copiados en varios modulos. Un 257 que se corrige en
    un lado y no en el otro mueve el umbral de quorum sin avisar."""
    esperado = {
        "MIEMBROS": {"diputados": 257, "senado": 72},
        "MARGEN_DISPUTADA": 0.05,
    }
    donde = {
        "MIEMBROS": {
            "export": "datos/export/src/export_base.py",
            "voto_individual": "modelo/voto_individual/src/disciplina.py",
            "agregador": "modelo/agregador_institucional/src/agregador.py",
        },
        "MARGEN_DISPUTADA": {
            "export": "datos/export/src/export_base.py",
            "voto_individual": "modelo/voto_individual/src/disciplina.py",
        },
    }
    for const, copias in donde.items():
        for alias, rel in copias.items():
            mod = cargar(f"const_{const}_{alias}", rel)
            assert hasattr(mod, const), f"{rel} ya no define {const}: actualizá este test"
            assert getattr(mod, const) == esperado[const], (
                f"[{alias}] {const} = {getattr(mod, const)!r}, "
                f"el resto del repo usa {esperado[const]!r}")


def test_conductas_y_presentes_coinciden():
    """Las etiquetas de conducta y el conjunto de 'estuvo presente' tambien viven
    duplicados. Si divergen, presentismo y disciplina cuentan cosas distintas."""
    disc = cargar("conductas_voto_individual", "modelo/voto_individual/src/disciplina.py")
    agg = cargar("conductas_agregador", "modelo/agregador_institucional/src/agregador.py")
    asi = cargar("presentes_asistencia", "variables/asistencia_quorum/src/asistencia.py")

    assert list(disc.CONDUCTAS) == list(agg.CONDUCTAS), (
        f"CONDUCTAS divergio: voto_individual={list(disc.CONDUCTAS)} vs "
        f"agregador={list(agg.CONDUCTAS)}")
    assert set(disc.PRESENTE_VOTOS) == set(asi.PRESENTES), (
        f"quien cuenta como PRESENTE divergio: voto_individual={sorted(disc.PRESENTE_VOTOS)} "
        f"vs asistencia_quorum={sorted(asi.PRESENTES)}")


# ------------------------------------- la QUINTA copia, que NO es la misma cosa

def test_bloque_publica_otro_periodo_con_el_mismo_nombre():
    """`variables/bloque` publica una columna `periodo` que NO significa lo mismo.

    Esto no es un bug: es una trampa documentada. `bloque._periodo_parlamentario`
    devuelve un AÑO legislativo (entero) con la regla "diciembre cuenta para el
    año siguiente", aplicada a TODOS los años y sin el corte del día 10. Las
    otras cuatro devuelven el PERÍODO de dos años entre recambios ("2019-2021").

    O sea: `serie_bloque.parquet` y `ficha_legislador.parquet` tienen los dos una
    columna llamada `periodo`, y cruzarlas por ese nombre da cualquier cosa —
    sin levantar un error, que es como fallan las cosas en este repo.

    Si alguna vez se unifican de verdad, este test hay que BORRARLO a mano,
    dejando dicho en ESTADO que se unificaron. Que falle es la señal de que
    alguien cambió una de las dos sin mirar la otra.
    """
    blo = cargar("periodo_bloque", "variables/bloque/src/bloque.py")
    fic = cargar("periodo_ficha_vs_bloque", "variables/legislador/src/ficha.py")

    fechas = pd.Series(["2018-12-15", "2019-12-15", "2020-06-01"])
    anios = pd.Series([2018, 2019, 2020])

    como_bloque = [str(v) for v in blo._periodo_parlamentario(fechas)]
    como_resto = [str(v) for v in fic.periodo_parlamentario(fechas, anios)]

    assert como_bloque == ["2019", "2020", "2020"], (
        f"cambió la definición de bloque: {como_bloque}")
    assert como_resto == ["2017-2019", "2019-2021", "2019-2021"], (
        f"cambió la definición del resto: {como_resto}")
    assert como_bloque != como_resto, (
        "las dos definiciones de `periodo` coinciden: o se unificaron (borrá este "
        "test y anotalo en ESTADO) o una se rompió")
