# Módulo: datos/expedientes

**Propósito.** El registro de todo lo que se PRESENTÓ en el Congreso (no solo
lo que se votó): cada proyecto con su título, autor, tipo, fecha y su cadena de
vida (giros → dictámenes → movimientos → resultados → ley). Es el
**denominador del embudo**, el **enlace acta→expediente** y la semilla de la
red de autorías (Módulos B/C del plan).

**Estado:** EN CURSO (backfill CKAN corrido y verificado 11-07-2026)
**Owner actual:** Claude+Franco (2026-07-11)

## Resultados del backfill (corrida 2026-07-11)
- **112.793 proyectos, 2008-2026** (40.623 de LEY, 50.666 resoluciones, 20.016 declaraciones).
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
