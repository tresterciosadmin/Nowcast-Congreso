# Módulo: datos/canonica

**Propósito.** Nuestra **base de datos propia y única** de votaciones. Unifica todas las fuentes (semilla histórica Andy Tow + CKAN + argentinadatos + Senado + lo que traiga el bot) en una sola tabla normalizada, deduplicada y con resolución de entidades (legislador, bloque, provincia, acta). Es la fuente de verdad de la que leen todos los módulos de `variables/` y `modelo/`.

**Estado:** PENDIENTE
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

## Contrato
- **Entradas:** los parquet de `datos/decada_votada`, `datos/ckan_diputados`, `datos/argentinadatos`, `datos/senado`, `datos/expedientes`.
- **Salida (contrato estable):** `data/clean/votos_canonico.parquet` y `actas_canonico.parquet` con `schema_version`. Clave estable por acta y por legislador.
- **Depende de:** `docs/schemas`, las fuentes de `datos/*`.
- **Gate de pase:** sin duplicados entre fuentes solapadas (p. ej. Diputados 2011–2019 está en semilla y en CKAN); resolución de entidades validada en muestra; serie temporal continua y auditada.

## Responsabilidades clave
1. **Deduplicación entre fuentes solapadas.** Definir precedencia (p. ej. fuente oficial > agregador) y clave de match por acta/fecha/cámara.
2. **Entity resolution.** Unificar nombres de legislador y bloque que varían entre fuentes y en el tiempo (mismo legislador, distinto string).
3. **Versionado.** `schema_version` y un changelog de la base; cada recarga es idempotente y trazable.

## Cómo trabajar acá
1. Reclamá el módulo en `coordinacion/TABLERO.md`.
2. Construí el merge incremental: la semilla y los históricos se cargan una vez; el bot agrega lo nuevo (upsert idempotente por clave de acta).
3. Resiliencia: parsing defensivo, validación contra schema, logging estructurado.
4. Registrá el avance en `coordinacion/ESTADO-DEL-PROYECTO.md`.
