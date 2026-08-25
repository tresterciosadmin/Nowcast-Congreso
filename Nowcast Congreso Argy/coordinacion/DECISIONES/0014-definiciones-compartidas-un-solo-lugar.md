# ADR-0014 — Las definiciones compartidas viven en un solo lugar (`definiciones.py`)

**Fecha:** 2026-08-25 · **Estado:** Aceptada · **Quién:** Valle (decisión), Claude (auditoría e implementación)

## Contexto

La regla del repo es **"no importes el código de otro módulo, consumí su salida"** (CLAUDE.md). Es buena y sostiene el trabajo en paralelo. Pero cobra un precio que hasta ahora nadie había puesto sobre la mesa: las **definiciones** —qué período parlamentario es una fecha, qué mayoría exige un proyecto, cuántas bancas tiene cada cámara— no son salida de ningún módulo. No hay un parquet de "qué significa período". Entonces terminan copiadas en cada módulo que las necesita, sincronizadas a mano.

Medido contra el disco el 25-08, antes de tocar nada:

| Definición | Copias | Estado |
|---|---|---|
| `periodo_parlamentario(fecha, anio)` | 4 | 3 idénticas carácter por carácter (`datos/export`, `modelo/voto_individual`, `variables/asistencia_quorum`); la de `variables/legislador` hace la misma cuenta escrita con variables intermedias |
| `normalizar_mayoria(tipo)` | 3 | 2 idénticas en versión Serie (`datos/export`, `modelo/voto_individual`), 1 escalar en `modelo/agregador_institucional` |
| `clas(s)` (anidada en la anterior) | 2 | idénticas |
| `MIEMBROS = {"diputados": 257, "senado": 72}` | 3 | idénticas (más dos variantes escalares en `datos/padron`) |

Y el detalle que decide el caso: **`datos/export/src/export_base.py` y `modelo/voto_individual/src/disciplina.py` compartían TRES funciones seguidas**, copiadas del mismo bloque. No es una duplicación puntual: es un pedazo de código compartido que nunca tuvo domicilio.

### Por qué el guardián por test no alcanzaba

El 20-08 se agregó `tests/test_definiciones_compartidas.py`, que corre las copias sobre casos borde y verifica que coincidan. Fue lo correcto y sigue vivo. Pero el 25-08 estaba **avisando de un bug que nadie podía arreglar**:

> las CUATRO copias revientan con una columna de backend pyarrow — `pd.to_numeric(anio)` conserva `int64[pyarrow]` y `a % 2` levanta `NotImplementedError: mod not implemented` (verificado en pandas 2.2.3 y 3.0.2). En producción no se veía porque `read_parquet` devuelve numpy.

El arreglo era **una línea por copia**. Estuvo trabado un mes con el motivo por escrito en el propio `xfail`: *"No se aplica desde acá porque toca 4 módulos con dueño"*.

Ese es el argumento del ADR en una frase: **con las copias, un arreglo de una línea cuesta cuatro claims de módulo.** El test detectaba la divergencia y la regla de dueños impedía repararla. Un control que no puede accionar no es un control: es un aviso.

Y hay precedente de que coincidir hoy no es garantía: las cuatro copias **coincidían** en resultados y aun así el repo tenía un bug que ninguna podía arreglar sola.

## Decisión

Se crea **`definiciones.py` en la raíz**, hermano de `rutas.py` y con el mismo patrón de import (buscar la raíz hacia arriba en vez de contar `parents[3]`).

- `rutas.py` responde **DÓNDE** está cada artefacto que cruza de un módulo a otro.
- `definiciones.py` responde **QUÉ ES** cada cosa que significa lo mismo en dos módulos.

Contenido inicial: `periodo_parlamentario`, `normalizar_mayoria` (Serie), `normalizar_mayoria_valor` (escalar), `MAYORIAS` y `BANCAS`.

Los cinco módulos afectados **re-exportan** el nombre (`from definiciones import periodo_parlamentario`), así que `export_base.periodo_parlamentario` sigue existiendo y **nada aguas abajo cambia**.

Criterio de qué entra, escrito en el propio archivo: *¿si estas dos copias divergen mañana, alguien se entera?* Si la respuesta es no, va ahí. Si el módulo puede cambiar la suya sin romperle nada a nadie, se queda en el módulo.

**Lo que explícitamente NO entra:** dos funciones que se llaman igual pero hacen cosas distintas. Los cuatro `_fecha_iso` del repo parsean formatos genuinamente distintos ("14 DE MARZO DE 2026" vs `dd/mm/YYYY`); unificarlos sería peor que dejarlos. Ver "Consecuencias".

## Consecuencias

- **Es cambio de contrato compartido** — por eso este ADR y el aviso en el TABLERO. Toca cinco módulos: `datos/export`, `modelo/voto_individual`, `modelo/agregador_institucional`, `variables/asistencia_quorum`, `variables/legislador`.
- **Cero cambio de comportamiento.** Verificado sobre 15 casos borde de fecha y 13 de mayoría, en los dos backends de dtype: la definición nueva devuelve **exactamente lo mismo** que las cuatro copias viejas con backend numpy. La única diferencia es que con backend pyarrow las viejas levantan `NotImplementedError` y la nueva responde.
- **El bug de pyarrow queda arreglado** y su `xfail` se saca del test: ahora pasa de verdad.
- **Test nuevo que falla con el código viejo:** `test_ninguna_copia_redefine_las_definiciones` compara **identidad de objeto**, no resultados. Los tests anteriores comparaban valores y por eso pasaban igual con una definición o con cinco. Verificado: al re-pegar a mano una copia *behaviorally idéntica* dentro de `export_base.py`, los siete tests de valor siguen pasando y sólo este falla.
- **`variables/bloque` NO se unifica y eso es a propósito.** Su `_periodo_parlamentario` devuelve un **año legislativo** (un entero), no el período de dos años. Es un concepto distinto con un nombre parecido, ya cubierto por `test_bloque_publica_otro_periodo_con_el_mismo_nombre`. Lo mismo vale para `datos/expedientes/src/od_url.py::periodo_de`, que es el período de sesiones ordinarias de HCDN (`año − 1882`). El docstring de `periodo_parlamentario` ahora nombra a los tres para que quien lea uno sepa que existen los otros dos.
- **Queda anotado y NO resuelto:** `datos/padron` mantiene sus propias `BANCAS = 257` y `BANCAS_SENADO = 72`. Son otro módulo con dueño, la forma es distinta (escalares, no dict) y ahí funcionan como constante de validación. Migrarlas es barato pero no urgente.
- **Riesgo aceptado:** el patrón `sys.path.insert` + `from definiciones import ...` es el mismo de `rutas.py` y hereda su límite — depende de que `rutas.py` siga en la raíz como ancla. Se eligió eso, y no un paquete instalable, para no cambiar la forma de correr nada.
