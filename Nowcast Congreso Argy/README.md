# Nowcast Legislativo Argentino

<!-- huella: db4689d3aa3a -->

Sistema que estima la probabilidad de sanción de proyectos de ley en el Congreso argentino.

**Resumen:** La raiz del proyecto: `CLAUDE.md`, `rutas.py`, `definiciones.py`, los scripts de regeneracion (`REGENERAR.ps1`, `verificar_*.py`) y este README. Los paneles HTML (tablero ejecutivo, mapa del modelo, panel de puertas) y sus `*_datos.js` se eliminaron en la auditoria 2026-09 (ítem A6): el estado vive en `coordinacion/`.

## Buscar acá si

- por que ya no hay tableros ni paneles HTML, y donde se ve el numero del motor (`modelo/ensemble/outputs/panel_regresion.json`; `python modelo/ensemble/src/nowcast_puertas.py ...`)
- el estado del proyecto y de la auditoria (`coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`, `coordinacion/QUE-SE-MIDE.md`)
- por donde empezar a leer el repo
- que significa "periodo parlamentario", que mayoria exige un proyecto o cuantas bancas tiene una camara (`definiciones.py`)

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
python3 .mapa/buscar.py --dato taxonomi        # que DATOS hay, donde, si viajan
python3 .mapa/buscar.py --dato                 # el inventario de datos completo
python3 .mapa/indexar.py .                      # reindexar (lo hace solo el hook pre-commit)
```

El texto que alimenta el mapa vive en el `README.md` de cada módulo: la línea
`**Resumen:**` y la sección `## Buscar acá si`. **Si cambia lo que hace un módulo,
se actualizan ahí** — no en `MAPA.md`, que se sobreescribe.

## Empezar acá (lectura obligatoria)
0. 🔴 **`coordinacion/URGENTE.md`** — SIEMPRE primero: lo que bloquea a otros. Si hay algo, se resuelve antes de empezar.
0b. ~~`TABLERO-CONTROL.html`~~ — **eliminado el 2026-09-30 (auditoría, A6)**, junto con `tablero_datos.js`. El estado del proyecto vive en `coordinacion/` (arrancá por `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md` mientras dure la auditoría).
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
En `docs/contexto/`: `INSTRUCTIVO-MAESTRO.md`, `Nowcast-Congreso_viabilidad_y_plan.md`, `Nowcast-Congreso_informe_validacion.docx`, la transcripción del premortem validado (`premortem-transcript-20260625-validado.md`; su HTML se eliminó en la auditoría A6) y los documentos de diseño v2.1 (referencia histórica).


## Los paneles HTML (eliminados el 2026-09-30, auditoría A6)

Los tres paneles que se abrían con doble clic **ya no existen** (decisiones 1 y 6 de Franco: esta
es una etapa de puesta en marcha operativa y lo que hay que mostrar es cuánto se mide de verdad,
no un panel; ver `coordinacion/QUE-SE-MIDE.md`). Se recuperan con `git log -- <ruta>`.

| Eliminado | Qué era | Qué lo reemplaza |
|---|---|---|
| `TABLERO-CONTROL.html` + `tablero_datos.js` | mapa ejecutivo: plan y avance | `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md` (mientras dure la auditoría) y `coordinacion/ESTADO-DEL-PROYECTO.md` |
| `Nowcast-Puertas.html` + `casos/nowcast_puertas_html.py` | el nowcast de un proyecto | consola: `python modelo/ensemble/src/nowcast_puertas.py diputados --fecha 2026-06-01 --origen EJECUTIVO [--json ruta]`; guardado en `modelo/ensemble/outputs/panel_regresion.json` (lo compara con el motor `modelo/ensemble/tests/test_panel_regresion.py`) |
| `MAPA-MODELO.html` + `mapa_modelo_datos.js` + `producto/dashboard/src/generar_mapa_modelo.py` | la maquinaria del cálculo | `MAPA.md` (generado) y `coordinacion/FORMULA-COMPLETA.md` |

Los paneles de coyuntura (`PANEL-NOWCAST/MOVIL/COYUNTURA.html`) y el
`COMPARADOR-ICG.html` salieron de la sesión del 04-08-2026 y **se dieron de baja el
11-08-2026** al eliminar la capa 2 global del ICG (ver ADR-0008, enmienda 2026-08-11).
Sus generadores están neutralizados; los HTML viejos se movieron a `Archivos_Borrar/`
el 2026-09-14 (los de PANEL-NOWCAST ya se habían borrado el 09-10).

`Nowcast-Ganancias-bicameral.html` también sigue en la raíz con cifras viejas: lo
producía un generador de `casos/` neutralizado el 22-08 (mecanismo propio, desfasado
del modelo). **No lo uses**: el panel de puertas que lo reemplazó también se eliminó
(A6, 2026-09-30); el número vivo sale de `modelo/ensemble/src/nowcast_puertas.py`. Detalle en
`casos/README.md`.
