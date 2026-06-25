# CLAUDE.md — Bootstrap para trabajo en paralelo

> Cualquier Claude (o persona) que abra este repo lee este archivo **primero y completo** antes de tocar nada. Está pensado para que varios trabajemos en simultáneo sin pisarnos.

## Qué es este proyecto
Nowcast Legislativo Argentino: estima la probabilidad de sanción de proyectos de ley en el Congreso. Contexto de negocio, metodología y reglas de dominio están en `docs/contexto/INSTRUCTIVO-MAESTRO.md` y `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`. **No los repitas; citalos.**

## Orden de lectura obligatorio
1. Este `CLAUDE.md`.
2. `coordinacion/ESTADO-DEL-PROYECTO.md` — qué se hizo hasta ahora (documento vivo).
3. `coordinacion/TABLERO.md` — qué tareas están libres / tomadas.
4. `coordinacion/PROTOCOLO-GIT.md` — cómo ramificar y mergear sin conflictos.
5. El `README.md` del módulo que vayas a tocar (contrato de entradas/salidas).

## Regla de oro anti-colisión: **un módulo, un dueño, una rama**
- El repo está partido en módulos (`datos/`, `variables/<variable>/`, `modelo/`, etc.). Cada módulo es una unidad de trabajo independiente con un contrato de salida estable.
- **Antes de escribir una línea**, reclamá el módulo en `TABLERO.md` (tu nombre/ID + fecha). Si ya está tomado, elegí otro o coordiná.
- Trabajás **solo dentro de tu módulo**. No edites archivos de otro módulo. Si necesitás algo de otro módulo, consumí su salida (parquet/contrato), no su código interno.
- Lo único compartido y "frágil" es `docs/schemas/` (los contratos de datos). **Cambiarlo requiere un ADR** en `coordinacion/DECISIONES/` y aviso en el TABLERO, porque afecta a todos.

## Regla de oro de trazabilidad: **cada cambio se registra**
Todo avance relevante (terminar algo, cambiar un contrato, tomar una decisión) **agrega una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** en el mismo PR. Un PR que cambia código y no actualiza ESTADO no se mergea. Formato en ese archivo.

## Flujo mínimo por sesión
1. `git pull` → leé ESTADO + TABLERO.
2. Reclamá un módulo/tarea en TABLERO.
3. Rama `feat/<modulo>-<desc>`.
4. Trabajá dentro del módulo; código con las 4 directivas de resiliencia (errores específicos, backoff en red, parsing defensivo, logging estructurado).
5. Actualizá ESTADO-DEL-PROYECTO.md.
6. PR chico, descripción clara, mergeá apenas pase. Liberá el módulo en TABLERO.

## Estado actual (resumen — el detalle está en ESTADO)
- **Fase 0 cerrada:** baseline de bloque medido. Predecir la *dirección* del voto individual por bloque ≈ 0,99 (callejón sin salida para ML). La incertidumbre vive en **asistencia/quórum**, **embudo** y **posición de bloque**.
- **Corrección de datos:** el CKAN de votaciones se congeló en 2020; lo reciente (→2025) sale de `argentinadatos.com`. Hay que combinar ambas fuentes.
- **Prioridades abiertas:** `variables/embudo`, `variables/asistencia_quorum`, `datos/argentinadatos`, `datos/expedientes`.
