# docs/schemas — Contrato de datos canónico

`schema_version` actual: **1**

Toda fuente de `datos/*` normaliza a estas dos tablas antes de entrar a `datos/canonica`. Quien cambie un esquema sube `schema_version` y abre un ADR (ver `coordinacion/DECISIONES/`).

## Tablas

### `acta` (una fila por votación) — `acta.schema.json`

| Campo | Tipo | Nota |
|---|---|---|
| schema_version | int | =1 |
| acta_id | string | clave canónica: `<fuente>:<id_original>` |
| camara | enum | `diputados` \| `senado` |
| fecha | date | ISO `YYYY-MM-DD` |
| periodo | int? | período legislativo si se conoce |
| titulo | string | texto del asunto |
| expediente | string? | nº de expediente parseado del título si existe |
| tipo_mayoria | string? | p. ej. "Más de la mitad", "Dos tercios" |
| resultado | string? | resultado oficial |
| n_afirmativos | int? | conteo |
| n_negativos | int? | conteo |
| n_abstenciones | int? | conteo |
| n_ausentes | int? | conteo |
| fuente | enum | `decada_votada` \| `ckan_diputados` \| `argentinadatos` \| `senado` |

### `voto` (una fila por legislador-acta) — `voto.schema.json`

| Campo | Tipo | Nota |
|---|---|---|
| schema_version | int | =1 |
| acta_id | string | FK a `acta.acta_id` |
| legislador_id | string? | id canónico (lo asigna `datos/canonica` tras entity resolution) |
| legislador_nombre | string | nombre tal como viene en la fuente |
| bloque | string | bloque/interbloque |
| distrito | string? | provincia/distrito |
| voto | enum | **`AFIRMATIVO` \| `NEGATIVO` \| `ABSTENCION` \| `AUSENTE`** |
| fuente | enum | igual que en `acta` |

## Enum canónico de `voto`
Normalizar SIEMPRE a estos cuatro valores (mayúsculas, sin tildes):

| Canónico | Variantes de origen a mapear |
|---|---|
| AFIRMATIVO | afirmativo, "sí", positivo |
| NEGATIVO | negativo, "no" |
| ABSTENCION | abstención, abstencion |
| AUSENTE | ausente, ausentes, no vota, presidente (si no emite voto) |

## Mapeo por fuente (resumen)
- **decada_votada (legislAr):** `voto`→voto, `nombre_bloque`→bloque, `nombre_legislador`→legislador_nombre, `provincia`→distrito.
- **ckan_diputados:** detalle `voto/bloque/diputado_nombre/distrito_nombre`; cabecera `fecha/titulo/resultado/tipo_mayoria/votos_*`.
- **argentinadatos:** acta `fecha/titulo/resultado/votosAfirmativos…` + `votos[]`.
- **senado:** análogo; resolver nombres de bloque del Senado.

## Validación
Antes de escribir parquet en `data/clean`, validá contra el json-schema. Filas que no validan se descartan a un log en `Archivos_Borrar/` (no se silencian).
