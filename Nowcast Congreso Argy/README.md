# Nowcast Legislativo Argentino

<!-- huella: 0eeed6f47804 -->

Sistema que estima la probabilidad de sanción de proyectos de ley en el Congreso argentino.

**Resumen:** La raiz del proyecto: los paneles que se abren con doble clic, el tablero ejecutivo y su unica fuente de datos (`tablero_datos.js`).

## Buscar acá si

- el tablero ejecutivo del proyecto (`TABLERO-CONTROL.html`; se edita SOLO `tablero_datos.js`)
- los KPIs, hitos o el estado de una pieza de la plataforma
- los paneles HTML de coyuntura o el informe bicameral (los generadores estan en `casos/`)
- por donde empezar a leer el repo

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md. -->

## Dónde está cada cosa: `MAPA.md`

**`MAPA.md` (raíz) es el índice del repo** y se genera solo. Leerlo antes de abrir
cualquier archivo: dice qué hay en cada módulo, qué archivos son centrales, quién
consume a quién y de qué fuentes externas se baja cada dato.

Para ubicar algo concreto sin abrir nada:

```bash
python3 .mapa/buscar.py "gamma"                 # simbolo + archivo:linea
python3 .mapa/buscar.py --carpeta variables/embudo
python3 .mapa/buscar.py --archivo modelo/ensemble/src/ensemble.py   # quien lo usa
python3 .mapa/indexar.py .                      # reindexar (lo hace solo el hook pre-commit)
```

El texto que alimenta el mapa vive en el `README.md` de cada módulo: la línea
`**Resumen:**` y la sección `## Buscar acá si`. **Si cambia lo que hace un módulo,
se actualizan ahí** — no en `MAPA.md`, que se sobreescribe.

## Empezar acá (lectura obligatoria)
0. 🔴 **`coordinacion/URGENTE.md`** — SIEMPRE primero: lo que bloquea a otros. Si hay algo, se resuelve antes de empezar.
0b. **`TABLERO-CONTROL.html`** — el tablero ejecutivo del proyecto (doble click, se abre en el navegador): plan completo de la plataforma + estado real de cada pieza. Se actualiza editando SOLO `tablero_datos.js` (regla en CLAUDE.md).
1. **`CLAUDE.md`** — bootstrap para trabajar en paralelo sin pisarse.
2. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — qué se hizo hasta ahora (documento vivo).
3. **`coordinacion/PLAN-DE-TRABAJO.md`** — qué hacer y cómo, por módulo y fase.
4. **`coordinacion/TABLERO.md`** — reclamá tu tarea antes de empezar.
5. **`coordinacion/PROTOCOLO-GIT.md`** — ramas, PRs, cómo evitar conflictos.

## Estructura
```
datos/          ingesta por fuente (ckan_diputados, argentinadatos, senado, expedientes)
variables/      una carpeta por variable: legislador, proyecto, bloque,
                asistencia_quorum, embudo, contexto
modelo/         voto_individual (baseline), agregador_institucional, ensemble
evaluacion/     baseline, backtesting, metricas
producto/       dashboard, api
docs/schemas/   contratos de datos (schema_version)
docs/contexto/  documentos de negocio, metodología y diseño (referencia)
coordinacion/   plan, estado vivo, tablero, protocolo git, decisiones (ADR)
fase0/          baseline ya ejecutado (Fase 0 cerrada)
```
Cada carpeta de módulo tiene su `README.md` con el contrato (entradas, salida, dependencias, gate).

## Estado
Fase 0 cerrada: el baseline de bloque predice la dirección del voto individual ≈ 0,99; el valor del producto está en **asistencia/quórum**, **embudo** y **posición de bloque**. Detalle en `coordinacion/ESTADO-DEL-PROYECTO.md`.

## Contexto de negocio y metodología
En `docs/contexto/`: `INSTRUCTIVO-MAESTRO.md`, `Nowcast-Congreso_viabilidad_y_plan.md`, `Nowcast-Congreso_informe_validacion.docx`, el premortem validado y los documentos de diseño v2.1 (referencia histórica).


## Los paneles (doble clic)

| Archivo | Para qué |
|---|---|
| `TABLERO-CONTROL.html` | mapa ejecutivo del proyecto — se alimenta de `tablero_datos.js` |

Los paneles de coyuntura (`PANEL-NOWCAST/MOVIL/COYUNTURA.html`) y el
`COMPARADOR-ICG.html` salieron de la sesión del 04-08-2026 y **se dieron de baja el
11-08-2026** al eliminar la capa 2 global del ICG (ver ADR-0008, enmienda 2026-08-11).
