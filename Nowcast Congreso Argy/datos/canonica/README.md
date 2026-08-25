# Módulo: datos/canonica

<!-- huella: e3b0c44298fc -->

**Propósito.** Nuestra **base de datos propia y única** de votaciones. Unifica todas las fuentes (semilla histórica Andy Tow + CKAN + argentinadatos + Senado + lo que traiga el bot) en una sola tabla normalizada, deduplicada y con resolución de entidades (legislador, bloque, provincia, acta). Es la fuente de verdad de la que leen todos los módulos de `variables/` y `modelo/`.

**Estado:** EN CURSO — v1 en producción. **1.016.632 votos / 6.231 actas**, 2001-2026,
ambas cámaras (medido en disco el 2026-08-06). Falta Diputados 2020-23 (pausado por
decisión del 10-07).
**Owner actual:** Claude+Franco (desde 2026-06-25)

> **Este módulo NO está libre.** Hasta el 06-08 figuraba "PENDIENTE / vacante" acá y
> como disponible en `TABLERO.md`, por arrastre del README original — cuando es la
> fuente de verdad de la que leen todos los demás. Un README que invita a reclamar un
> módulo ocupado es el mecanismo anti-colisión fallando al revés.

**Resumen:** La base propia y unica de votaciones nominales: todas las fuentes unificadas, deduplicadas y con entidades resueltas. Fuente de verdad de la que leen `variables/` y `modelo/`.

## Buscar acá si

- de donde sale un voto, un acta o un legislador (la tabla madre)
- cuantos votos/actas hay en total, o desde/hasta que fecha llega la base
- reconstruir la base de cero (`run_pipeline.py`, ~20 min con internet)
- un legislador que aparece dos veces con nombres distintos (resolucion de entidades)
- el hueco de Diputados 2020-23, o que fuente cubre que periodo

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

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
