# CLAUDE.md — Bootstrap para trabajo en paralelo

> Cualquier Claude (o persona) que abra este repo lee este archivo **primero y completo** antes de tocar nada. Está pensado para que varios trabajemos en simultáneo sin pisarnos.

**Repositorio (fuente de verdad):** https://github.com/tresterciosadmin/Nowcast-Congreso

## Qué es este proyecto
Nowcast Legislativo Argentino: estima la probabilidad de sanción de proyectos de ley en el Congreso. Contexto de negocio, metodología y reglas de dominio están en `docs/contexto/INSTRUCTIVO-MAESTRO.md` y `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`. **No los repitas; citalos.**

## Orden de lectura obligatorio
1. Este `CLAUDE.md`.
2. `coordinacion/ESTADO-DEL-PROYECTO.md` — qué se hizo hasta ahora (documento vivo).
3. `coordinacion/TABLERO.md` — qué tareas están libres / tomadas.
4. `coordinacion/PROTOCOLO-GIT.md` — cómo ramificar y mergear sin conflictos.
5. El `README.md` del módulo que vayas a tocar (contrato de entradas/salidas).
6. `TABLERO-CONTROL.html` (raíz) — el mapa ejecutivo; se actualiza vía `tablero_datos.js` (regla más abajo).

## Regla de oro anti-colisión: **un módulo, un dueño, una rama**
- El repo está partido en módulos (`datos/`, `variables/<variable>/`, `modelo/`, etc.). Cada módulo es una unidad de trabajo independiente con un contrato de salida estable.
- **Antes de escribir una línea**, reclamá el módulo en `TABLERO.md` (tu nombre/ID + fecha). Si ya está tomado, elegí otro o coordiná.
- Trabajás **solo dentro de tu módulo**. No edites archivos de otro módulo. Si necesitás algo de otro módulo, consumí su salida (parquet/contrato), no su código interno.
- Lo único compartido y "frágil" es `docs/schemas/` (los contratos de datos). **Cambiarlo requiere un ADR** en `coordinacion/DECISIONES/` y aviso en el TABLERO, porque afecta a todos.

## Regla de oro de trazabilidad: **cada cambio se registra**
Todo avance relevante (terminar algo, cambiar un contrato, tomar una decisión) **agrega una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** en el mismo PR. Un PR que cambia código y no actualiza ESTADO no se mergea. Formato en ese archivo.

## Regla del TABLERO DE CONTROL: **el mapa se actualiza en cada cambio**
En la raíz vive `TABLERO-CONTROL.html` (se abre con doble click), el tablero ejecutivo que consolida el plan de la plataforma con el estado real. Su única fuente de datos es **`tablero_datos.js`** — ese archivo es OBLIGATORIO actualizarlo en el mismo PR que ESTADO y EN-HUMANO cuando cambia algo relevante: (1) fecha y autor, (2) el `estado` de lo que tocaste (modulos_plataforma / etapas / modulos_repo), (3) un hito nuevo arriba de todo en `hitos` (1-3 frases, en humano), (4) kpis/metricas si cambiaron los números. **NO edites `TABLERO-CONTROL.html`** (es el diseño, fijo). Estados válidos: HECHO | EN CURSO | PARCIAL | PENDIENTE | FUTURO | REPLANTEADO. Un PR que cambia el estado del proyecto y no actualiza el tablero no se mergea.

## Régimen de archivos descartables: **todo lo borrable va a `Archivos_Borrar/`**
La carpeta está en OneDrive y el entorno no puede borrar archivos. Por eso, todo lo temporal o regenerable (cachés, descargas crudas, logs de validación, salidas intermedias, pruebas) se escribe en `Archivos_Borrar/` para que el dueño humano lo borre a mano. Nada ahí es fuente de verdad.

## Flujo mínimo por sesión
1. `git pull` → leé ESTADO + TABLERO.
2. Reclamá un módulo/tarea en TABLERO.
3. Rama `feat/<modulo>-<desc>`.
4. Trabajá dentro del módulo; código con las 4 directivas de resiliencia (errores específicos, backoff en red, parsing defensivo, logging estructurado).
5. Actualizá ESTADO-DEL-PROYECTO.md.
6. PR chico, descripción clara, mergeá apenas pase. Liberá el módulo en TABLERO.

## Estrategia de datos (ver ADR-0002)
**Semilla → canónica propia → bot.** Andy Tow ("La Década Votada" / legislAr) se usa como **semilla histórica de un solo uso**; no se copia ni se depende en vivo de su dataset. Sobre esa semilla + CKAN + argentinadatos construimos una **base canónica propia** (`datos/canonica`, la fuente de verdad) y un **bot** (`datos/bot_recoleccion`) que recolecta las votaciones nuevas de las fuentes oficiales. legislAr corre en R solo para el export; el resto en Python.

## Estado actual (resumen — el detalle está en ESTADO)
- **Fase 0 cerrada:** baseline de bloque medido. Predecir la *dirección* del voto individual por bloque ≈ 0,99 (callejón sin salida para ML). La incertidumbre vive en **asistencia/quórum**, **embudo** y **posición de bloque**.
- **Datos:** CKAN de votaciones congelado en 2020; lo reciente (→2025) sale de `argentinadatos.com`; la historia profunda (1998–, Senado 2004–2013) de la semilla Andy Tow. Hueco conocido: **Senado 2014–2023**.
- **Esquema canónico** definido en `docs/schemas` (schema_version=1).
- **Prioridades abiertas:** `datos/decada_votada` (export listo, falta correr), `datos/canonica`, `variables/embudo`, `variables/asistencia_quorum`.
- **Avances jul-2026:** base canónica completa y reproducible (781k votos, `run_pipeline.py`); `modelo/voto_individual` reformulado (ADR-0003) con gate 1 APROBADO (desvío concentrado; drift 2024-26 confirmado); `variables/legislador` con ficha individual + análisis por **período parlamentario** (recambios del 10-dic impares = unidad de análisis). Pieza central en co