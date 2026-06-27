# Módulo: datos/bot_recoleccion

**Propósito.** Bot programado que **detecta y recolecta las votaciones nuevas** de las fuentes oficiales y las agrega a `datos/canonica`. Es lo que nos independiza de Andy Tow: una vez sembrada la historia, la base la mantenemos nosotros, sola, hacia adelante.

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Qué hace
- Corre periódicamente (cron local primero; Cloud Scheduler en la fase nube).
- Consulta las fuentes vivas: CKAN HCDN, API argentinadatos, y los portales `votaciones.hcdn.gob.ar` / Senado para lo que no esté en datos abiertos.
- Detecta actas nuevas (no presentes en la canónica), las normaliza al esquema y hace **upsert idempotente** en `datos/canonica`.
- Deja un registro de corrida (qué trajo, desde cuándo, errores).

## Contrato
- **Entradas:** fuentes oficiales vivas + estado actual de `datos/canonica` (para saber el último acta conocida).
- **Salida (contrato estable):** nuevas filas en `votos_canonico` / `actas_canonico`, vía la interfaz de `datos/canonica`. Log de corrida en `outputs/`.
- **Depende de:** `datos/canonica` (esquema y clave), `docs/schemas`.
- **Gate de pase:** corrida idempotente (re-ejecutar no duplica), detección correcta de actas nuevas en una ventana de prueba, alertas ante caída de fuente.

## Diseño (resiliencia obligatoria)
- Reintentos con backoff y manejo específico de errores por fuente (una fuente caída no frena al resto).
- Parsing defensivo + validación contra schema antes de escribir.
- Logging estructurado; marca de "última acta vista" por cámara para arranques incrementales.
- Idempotencia por clave de acta: si una corrida se repite, no inserta duplicados.

## Cómo trabajar acá
1. Reclamá el módulo en `coordinacion/TABLERO.md`.
2. Empezá leyendo desde la canónica el último acta conocido por cámara; pedí a cada fuente solo lo posterior.
3. No abrir hasta tener `datos/canonica` con al menos una fuente cargada (necesitás el esquema y la clave).
4. Registrá el avance en `coordinacion/ESTADO-DEL-PROYECTO.md`.
