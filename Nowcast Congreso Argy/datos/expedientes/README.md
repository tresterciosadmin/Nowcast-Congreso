# Módulo: datos/expedientes

**Propósito.** El registro de todo lo que se PRESENTÓ en el Congreso (no solo
lo que se votó): cada proyecto con su título, autor, tipo, fecha y su cadena de
vida (giros → dictámenes → movimientos → resultados → ley). Es el
**denominador del embudo**, el **enlace acta→expediente** y la semilla de la
red de autorías (Módulos B/C del plan).

**Estado:** EN CURSO — backfill CKAN **refrescado el 07-08-2026**.

> ⚠️ **La ingesta usa CACHÉ salvo que exista la variable `REFRESH`.** El 07-08 se
> corrió y no bajó nada: el log decía `caché: proyectos.csv` en las 8 líneas. Para
> traer datos nuevos hace falta `REFRESH=1`.
>
> **Al refrescar (llevaba un mes sin correr):** 112.793 → **113.177** proyectos, y la
> cobertura pasa del **02-jun** al **30-jun-2026**. Dato operativo que queda:
> **HCDN publica con ~5 semanas de atraso**, así que el bot sigue haciendo falta pero
> para una ventana más chica de lo que se creía.
>
> **Quién consume esto ahora:** `datos/proyectos` lo migra a `proyectos.db`
> (ADR-0009), que es de donde lee el embudo. Este módulo sigue siendo el que baja
> CKAN y produce su contrato; lo que cambió es quién lo lee.
**Owner actual:** Claude+Franco (2026-07-11)

## Resultados del backfill (corrida 2026-07-11)
- **113.177 proyectos, 2008 → 30-jun-2026** (40.752 de LEY, 50.851 resoluciones, 20.084 declaraciones). *(medido el 07-08; antes decía 112.793 / 02-jun)*
- Cadena de vida: 422.143 giros · 23.801 dictámenes · 140.903 movimientos · 117.026 resultados · 1.335 leyes.
- **EMBUDO BRUTO: 3,22%** — de 41.339 proyectos de ley presentados, 1.332 sancionados.
  Y solo 4 RECHAZADOS explícitos en 18 años: **el Congreso no rechaza, deja morir** (por eso el embudo es EL diferencial).
- **Enlace acta→expediente: 89,1%** de las actas CKAN de la canónica matcheadas (períodos 129-137).

## Contrato (salida estable, `data/clean/`)
| Archivo | Contenido | Clave |
|---|---|---|
| `expedientes.parquet` | maestro: proyecto_id, titulo, fecha_publicacion, camara_origen, exp_diputados, exp_senado, tipo, autor | proyecto_id |
| `expedientes_giros.parquet` | giro a comisiones (comision, orden) | proyecto_id |
| `expedientes_dictamenes.parquet` | dictámenes | proyecto_id |
| `expedientes_movimientos.parquet` | movimientos con fecha | proyecto_id |
| `expedientes_resultados.parquet` | resultados (APROBADO/MEDIA SANCION/SANCIONADO/…; nulo = sigue vivo o murió en silencio) | proyecto_id |
| `expedientes_leyes.parquet` | leyes sancionadas (nro de ley) | proyecto_id |
| `acta_expediente.parquet` | enlace acta_id (formato canónico `ckan_diputados:<id>`) ↔ expediente, períodos 129-137 | acta_id |
| `comisiones_integrantes.parquet` | integrantes de comisiones permanentes (Committee Overlap) | — |

- **Entradas:** CKAN datos.hcdn.gob.ar (7 datasets vivos + 1 congelado; inventario en `Archivos_Borrar/expedientes_ckan/inventario.json`).
- **Depende de:** — (fuente primaria). Lo consumen: variables/embudo, variables/proyecto (perfil temático histórico), Módulos B/C.
- **Gate de pase:** % de proyectos con votación nominal / embudo bruto medido — CUMPLIDO (3,22%).

## Cómo correr (PC con internet; ~75 MB la 1ª vez, caché en Archivos_Borrar)
```bash
python datos/expedientes/src/explorar_ckan.py   # paso 0: inventario + muestras (ya corrido)
python datos/expedientes/src/ingesta_ckan.py    # backfill completo -> data/clean/
```
`REFRESH=1` fuerza re-descarga (los datasets vivos rotan ~mensual).

## LIMITACIONES CONOCIDAS
1. **`autor` = solo el firmante primario.** El CKAN no publica cofirmantes; la
   red completa de co-firmas es la fase 2 (ver abajo).
2. Solo cámara Diputados como fuente (incluye revisiones del Senado vía
   exp_senado, pero los proyectos con origen Senado puro requieren el DAE).
3. `acta_expediente` congelado en 2019 (períodos 129-137); las actas
   posteriores ya traen expediente propio en la canónica.

## FASE 2 anotada: el bot diario (padrón vivo — idea de Franco 11-07-2026)
Para la actualización automática: un bot que cada día lea el **diario oficial
de ingresos de cada cámara** — el **Trámite Parlamentario** (Diputados) y el
**DAE** (Senado) — que publican TODO lo presentado ese día **con todos los
firmantes y giros en un solo documento** (mucho mejor que scrapear las páginas
personales de cada diputado: 1 request/día vs 257, y sin depender de slugs).
La ficha por expediente de `datos/seguimiento` (Valle) queda como fallback
puntual — consumir su CONTRATO, no reimplementarlo. Ese bot vive en
`datos/bot_recoleccion` (su dependencia — canónica cargada — ya está cumplida)
y de paso trae las votaciones nuevas. Da: proyectos nuevos + firmantes
completos + giros, diario. **Es el candidato natural a próximo claim.**

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md`.
2. Rama `feat/expedientes-<desc>`. No toques otros módulos; consumí contratos.
3. Todo avance → entrada en ESTADO + EN-HUMANO + `tablero_datos.js`.

## Convenciones de código
Resiliencia obligatoria: errores específicos, backoff en red, parsing
defensivo, logging estructurado.

## Enlace ENTRE CÁMARAS (nuevo, 2026-08-08 — línea Revisión de Comisiones)

`src/enlace_senado.py` responde **qué proyecto se votó en cada acta**, que es lo
que hace falta para modelar `cámara de origen -> cámara revisora`.

**El problema:** las actas del Senado traen la numeración INTERNA del Senado
(`CD-38/22-PL`), no el denominador de HCDN, así que el cruce directo daba ~0.

**La clave:** el puente ya estaba acá. `expedientes.parquet` tiene `exp_senado`
con exactamente esa numeración, ya normalizada (`0038-CD-2022`). **No hay que
scrapear senado.gob.ar.** Prefijos: `CD-` entró desde Diputados con media
sanción · `S-` origen Senado · `PE-` Ejecutivo · `OV-` oficiales varios.

| Archivo (`data/clean/`) | Contenido | Clave |
|---|---|---|
| `acta_expediente_senado.parquet` | acta_id, camara, expediente, clave, prefijo, proyecto_id, metodo, es_cruce | acta_id |
| `cadena_camaras.parquet` | un proyecto por fila con su votación en cada cámara: acta/fecha/resultado por cámara + `n_camaras` | proyecto_id |

**Cobertura medida (08-08):** 1.337 de 2.241 actas con expediente (59,7%) —
Senado 201/250 (80,4%), Diputados 1.136/1.991 (57,1%). **39 proyectos con
votación en las dos cámaras.**

⚠️ **El cuello de botella NO está acá:** sólo **250 de 3.078 actas del Senado
traen expediente (8,1%)**. Subir eso multiplica la cadena completa, y se arregla
en `datos/senado/src/scrape_votaciones.py` y en la ingesta de argentinadatos.

💡 **Activo subutilizado:** `expedientes_leyes.parquet` trae
`primera_media_sancion`, `segunda_media_sancion`, `camara_sancionadora` y
`sancion_definitiva` **para el 100% de las leyes**, mientras
`expedientes_resultados` registra la media sanción de sólo el 43,7%. Para
cualquier medición de la cadena, usar `expedientes_leyes`.

```bash
python datos/expedientes/src/enlace_senado.py            # construye y reporta
python datos/expedientes/src/enlace_senado.py --reporte  # sólo diagnóstico
python datos/expedientes/tests/test_enlace_senado.py     # 42 checks, sin red
```
