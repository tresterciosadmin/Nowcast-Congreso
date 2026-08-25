# -*- coding: utf-8 -*-
"""Un solo lugar donde dice QUE ES cada cosa que significa lo mismo en dos modulos.

## Por que existe

`rutas.py` resolvio DONDE esta cada artefacto compartido. Este archivo resuelve
lo otro: QUE ES un periodo parlamentario, que mayoria exige un proyecto, cuantas
bancas tiene cada camara.

La regla del repo -- "no importes el codigo de otro modulo, consumi su salida"
(CLAUDE.md) -- es buena, pero cobra un precio: las DEFINICIONES terminan copiadas
en cada modulo que las necesita, sincronizadas a mano. Hasta el 2026-08-25 el
control era un docstring que decia "mantener sincronizadas", o sea: que alguien
se acuerde.

Y este proyecto ya sabe como termina eso. Dos hechos medidos, no hipoteticos:

1. `periodo_parlamentario` estaba en CUATRO modulos. Tres eran identicas caracter
   por caracter; la de `variables/legislador` hacia la misma cuenta escrita con
   variables intermedias. Un parche aplicado sobre "las tres iguales" habria
   dejado la cuarta atras sin que nada fallara.
2. `tests/test_definiciones_compartidas.py` (20-08) detecto que las CUATRO copias
   revientan con una columna de backend pyarrow. El arreglo era UNA linea por
   copia -- y quedo trabado un mes, con el motivo por escrito: "toca 4 modulos con
   dueno". El guardian veia el problema y la regla de dueños impedia arreglarlo.

Ese segundo hecho es el argumento: con las copias, un arreglo de una linea cuesta
cuatro claims de modulo. Aca cuesta uno.

## Que va aca y que NO

- **SI:** una regla que dos o mas modulos tienen que responder IGUAL para que el
  numero cierre. Es el contrato entre modulos hecho funcion.
- **NO:** logica propia de un modulo, aunque se parezca a la de otro. Dos parsers
  de fecha que leen formatos distintos NO son la misma regla: son dos reglas que
  se llaman parecido. Unificarlas es peor que dejarlas.

Ante la duda, el criterio: **si estas dos copias divergen manana, alguien se
entera?** Si la respuesta es no, va aca. Si el modulo puede cambiar la suya sin
romperle nada a nadie, se queda en el modulo.

## Como se usa

Las mismas cinco lineas de `rutas.py` -- buscan la raiz hacia arriba en vez de
contar `parents[3]`, asi que sobreviven a que el modulo cambie de profundidad:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(next(d for d in Path(__file__).resolve().parents
                                if (d / "rutas.py").is_file())))
    from definiciones import periodo_parlamentario  # noqa: E402

Los modulos que ya exponian estos nombres los RE-EXPORTAN, asi que
`export_base.periodo_parlamentario` sigue existiendo y nada aguas abajo se entera.

## Reglas

1. **Cambiar algo de aca exige ADR** (`coordinacion/DECISIONES/`) y aviso en el
   TABLERO. Es contrato compartido: por definicion, afecta a todos.
2. **Nada se agrega aca sin al menos DOS modulos que lo consuman.** Una definicion
   compartida que usa un solo modulo es logica de ese modulo con domicilio falso.
3. **Nada de pandas en las firmas escalares.** `normalizar_mayoria_valor` toma y
   devuelve `str` para que la pueda usar codigo que no trabaja con Series.
4. **Los dos backends de dtype.** Una guarda que anda con numpy y revienta con
   pyarrow no es una guarda: es el bug de arriba otra vez. Ver
   `tests/test_definiciones_compartidas.py`.

Ver ADR-0014.
"""
from __future__ import annotations

import pandas as pd

__all__ = [
    "BANCAS",
    "periodo_parlamentario",
    "normalizar_mayoria",
    "normalizar_mayoria_valor",
    "MAYORIAS",
]

# ─────────────────────────── bancas por camara ───────────────────────────
# Composicion constitucional del cuerpo, no cuantos votaron. Lo que se cuenta en
# el recinto sale del padron (`datos/padron`), que puede tener bancas vacantes.
BANCAS = {"diputados": 257, "senado": 72}


# ──────────────────────── periodo parlamentario ────────────────────────
def periodo_parlamentario(fecha: pd.Series, anio: pd.Series) -> pd.Series:
    """Periodo de DOS ANOS entre recambios legislativos: el 10-dic de anos impares.

    Devuelve "2023-2025" y similares. Sin fecha usable cae al `anio` (redondeado
    hacia abajo al impar), y sin ninguno de los dos devuelve nulo.

    OJO -- en este repo conviven TRES cosas que se llaman parecido y NO son esto:

      - `variables/bloque/src/bloque.py::_periodo_parlamentario` es el ANO
        legislativo (un int; diciembre cuenta para el ano siguiente).
      - `datos/expedientes/src/od_url.py::periodo_de` es el periodo de sesiones
        ORDINARIAS de HCDN (1-mar a 28-feb, `ano - 1882`), que es el `<NNN>` de la
        URL de una Orden del Dia.
      - lo de aca es el recambio de bancas del 10-dic de anos impares.

    Los tres son correctos en su contexto. Antes de usar uno, mira cual necesitas.
    """
    f = pd.to_datetime(fecha, errors="coerce")
    # float64 explicito ANTES de cualquier `%`: con backend pyarrow, `pd.to_numeric`
    # conserva `int64[pyarrow]` y `a % 2` levanta NotImplementedError('mod not
    # implemented'). En produccion no se veia porque `read_parquet` devuelve numpy.
    # Fue el bug que las cuatro copias compartian (verificado en pandas 2.2.3 y 3.0.2).
    y = f.dt.year.astype("float64")
    ini = y.where(y % 2 == 1, y - 1)
    antes = (y % 2 == 1) & ((f.dt.month < 12) | ((f.dt.month == 12) & (f.dt.day < 10)))
    ini = ini.where(~antes, ini - 2)
    a = pd.to_numeric(anio, errors="coerce").astype("float64")
    ini = ini.fillna(a.where(a % 2 == 1, a - 1))
    out = ini.astype("Int64").astype("string")
    return (out + "-" + (ini + 2).astype("Int64").astype("string")).where(ini.notna())


# ────────────────────────── tipo de mayoria ──────────────────────────
MAYORIAS = ("SIMPLE", "ABSOLUTA", "DOS_TERCIOS", "DOS_TERCIOS_CUERPO", "TRES_CUARTOS")


def normalizar_mayoria_valor(tipo) -> str:
    """Un valor suelto -> una de `MAYORIAS`. Sin dato -> SIMPLE.

    SIMPLE es el default a proposito: es el caso abrumadoramente mas comun, y la
    fuente deja el campo vacio justamente cuando no hay nada especial que declarar.
    """
    s = "" if (tipo is None or (isinstance(tipo, float) and tipo != tipo)) else str(tipo)
    if s in ("<NA>", "NaT", "nan", "None"):
        s = ""
    s = s.upper()
    if "TERCIO" in s:
        return "DOS_TERCIOS_CUERPO" if "CUERPO" in s else "DOS_TERCIOS"
    if "CUARTO" in s:
        return "TRES_CUARTOS"
    if s == "ABSOLUTA" or "CUERPO" in s or "MITAD MÁS UNO" in s or "MITAD MAS UNO" in s:
        return "ABSOLUTA"
    return "SIMPLE"


def normalizar_mayoria(tipo: pd.Series) -> pd.Series:
    """La version Serie. Es la MISMA regla: llama a `normalizar_mayoria_valor` fila
    por fila, para que no puedan divergir aunque quieran."""
    t = pd.Series(tipo).fillna("").astype(str)
    return t.map(normalizar_mayoria_valor).astype("string")
