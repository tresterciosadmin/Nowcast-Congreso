# Módulo: datos/expedientes

<!-- huella: e3b0c44298fc -->

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

**Resumen:** Registro de todo lo PRESENTADO (no solo lo votado): titulo, autor, tipo, fecha y cadena de vida del expediente. Denominador del embudo y enlace acta -> expediente.

## Buscar acá si

- que se presento en el Congreso y en que quedo
- el enlace entre un acta de votacion y su expediente
- giros iniciales a comision, dictamenes, o si un expediente llego a ley
- el backfill de CKAN, o por que HCDN publica con ~5 semanas de atraso
- la ingesta trae menos/mas de lo esperado (`REFRESH=1`: por defecto usa CACHE)
- QUIEN firmo un dictamen, si hubo disidencias y de que bloque es cada firma
- como se arma la URL del PDF de una Orden del Dia de HCDN
- los dictamenes del Senado (otra fuente, otro scraper: `ingesta_od_senado.py`)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

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

### Rescate del expediente desde el TÍTULO (2026-08-08, segunda corrida)

El cuello de botella de arriba (8,1%) **no era de ingesta**: el expediente está
escrito dentro del título del acta en 2.229 casos —
`"...Reforma Laboral. PE-608/03. Votacion en general"`. `expediente_en_titulo()`
lo rescata **sólo como respaldo**, cuando la columna `expediente` viene vacía.

| | antes | ahora |
|---|---:|---:|
| actas del Senado con expediente | 250 (8,1%) | **2.230 (72,4%)** |
| actas enlazadas | 1.337 | **2.104** |
| **proyectos con votación en las DOS cámaras** | **39** | **223** |

**El campo propio SIEMPRE manda.** Donde existen los dos coinciden en el
**98,8%** (246/249), y las 3 discrepancias son casos en que el título nombra un
expediente *referenciado* (un proyecto que se reproduce, el proyecto de fondo de
un dictamen de bicameral) y no el votado. Columna de contrato nueva:
`origen_clave` ∈ {`campo`, `titulo`}.

⚠️ **Cómo (no) leer la tasa global.** Baja de 59,7% a 49,8% **porque creció el
denominador**, no porque empeore: de las 1.980 rescatadas, las 963 posteriores a
2008 enlazan al **79,6%** y las 1.017 anteriores al **0%** (el maestro de CKAN
arranca el 2008-03-03). Cualquier cita del porcentaje tiene que decir la ventana.

**Lo que sigue siendo de ingesta, y es lo único:**
`datos/argentinadatos/src/to_canonical.py` tiene `expediente=None` **fijo** para
las dos cámaras (líneas 132 y 147). Hay que ver **con red** si la API lo expone;
si lo expone, se arregla el flujo vivo (2024-2026) en dos líneas. Hoy esas 311
actas se salvan por el título (65,9%).

### Tercer nivel: puente por ORDEN DEL DÍA (2026-08-08, sólo DIPUTADOS)

Desde 2020 las actas de **Diputados** entran sin expediente (**0 de 369** entre
2024 y 2026) y el título tampoco lo nombra — pero sí trae la **O.D.**:
`"O. D. 759 - DNU 179/2025, QUE APRUEBA..."`. Como `expedientes_resultados.parquet`
tiene `od_numero` + `od_publicacion`, el par **(año, nº de O.D.) lleva al proyecto**.

- Clave **con año** (las O.D. se renumeran cada año) y reintento en `año-1`:
  una O.D. de fin de año se vota al siguiente.
- **292 claves ambiguas descartadas** (una O.D. puede tener varios dictámenes).
- ✅ Control: donde el acta ya tenía expediente, la O.D. da el mismo proyecto en
  el **98,9%** (88/89).

⛔ **NO se aplica al Senado, a propósito.** El Senado numera **sus propias**
Órdenes del Día: buscar la "O.D. 206/2023" de un acta del Senado en la tabla de
HCDN devolvería un proyecto ajeno sin ningún aviso. Hay un test que lo impide.

**Orden de precedencia del módulo:** `campo expediente` → `expediente en el
título` → `O.D. en el título (sólo Diputados)`. La columna `origen_clave`
(`campo` | `titulo` | `od`) dice de dónde salió cada uno.

| | inicio | + título | **+ O.D.** |
|---|---:|---:|---:|
| actas enlazadas | 1.337 | 2.104 | **2.355** |
| **cadena completa (2 cámaras)** | **39** | **223** | **243** |
| cadena en 2025 / 2026 | 0 / 0 | 0 / 0 | **7 / 5** |

**Pendientes conocidos:**
- 2020-2023 sigue casi vacío del lado de Diputados (1 a 9 actas por año): es el
  hueco **Dip 2020-23 pausado desde el 10-jul**, no un problema de este módulo.
- `datos/argentinadatos/src/explorar_campos.py` es una **sonda** para decidir
  con red si la API expone el expediente (hoy `to_canonical.py` lo pone en
  `None` fijo, líneas 132 y 147). Un comando y queda resuelto.
- ✏️ El módulo se llama `enlace_senado.py` y ya resuelve las **dos** cámaras.
  El nombre quedó chico; no se renombró porque el entorno no puede borrar y
  quedaría un archivo zombi.

---

## Firmantes del dictamen (2026-08-21) — contrato NUEVO

**El problema.** Sabíamos que un proyecto tenía dictamen, pero no **quién lo
firmó**. No era culpa del loader: el dataset `dictamenes` del CKAN de Diputados
no publica los firmantes. Su propia ingesta ya lo decía — *«`autor` es solo el
firmante PRIMARIO (el CKAN no publica cofirmantes)»*. El dato existe únicamente
en el PDF de la Orden del Día.

Es el prerrequisito de la **Puerta A como señal observada**: la puerta deja de
ser una probabilidad de que la comisión actúe y pasa a ser el **carácter** del
trabajo en comisión.

### La cadena, en cuatro archivos

| archivo | qué hace |
|---|---|
| `src/od_url.py` | de una Orden del Día a la URL de su PDF |
| `src/ingesta_od.py` | baja los PDF a `Archivos_Borrar/od_pdf/` (caché descartable) |
| `src/parser_od.py` | saca comisiones, dictámenes, firmantes y disidencias |
| `src/construir_firmas.py` | resuelve contra el padrón y escribe los dos parquet |

### La regla de la URL (verificada contra 7 PDF reales, 2008-2026)

    periodo = anio(od_publicacion) - 1882 - (1 si el mes es enero o febrero)
    https://www3.hcdn.gob.ar/dependencias/dcomisiones/periodo-<P>/<P>-<N>.pdf

El período parlamentario va del 1-mar al 28/29-feb, así que una OD impresa en
enero o febrero cae en el período del año anterior. **El número de OD NO reinicia
con el período** —reinicia con la renovación de la Cámara, el 10-dic de los años
impares— así que el período se deduce de la FECHA y nunca del número. `www3` y
`www4` son espejos del mismo archivo.

### Salida (`data/clean/`)

`dictamenes_firmas.parquet` — una fila por **(proyecto, cámara, dictamen, firmante)**:

    proyecto_id · camara · od_numero · od_publicacion · comisiones · expedientes_sumario
    dictamen_orden · dictamen_clase (mayoria|minoria|unico) · fecha_sala
    firmante_raw · orden_firma · primer_firmante · disidencia (none|parcial|total)
    dos_comisiones (el asterisco del PDF: integra las DOS comisiones que firman)
    origen_firmas (ancla|sin_ancla)
    legislador_id · legislador · bloque · bloque_norm · bloque_linaje · metodo_match
    enlace (expediente|orden_del_dia) · fuente_url · parseo_ok · motivo

`dictamenes_comisiones.parquet` — el índice **(proyecto, cámara, comisión, dictamen)**.

**Son dos tablas y no una, a propósito.** Un dictamen conjunto de dos comisiones
trae **una sola lista de firmas**: el PDF no dice cuál de las dos integra cada
diputado. Meter todo junto obligaría a repetir cada firmante una vez por comisión,
**inventando una atribución que el documento no da**.

### Lo que hay que saber antes de usarlo

- **El ancla del parser es `Sala de las comisiones, <fecha>.`** y es la misma en
  las dos cámaras. No se buscan "cosas que parezcan nombres": después del
  articulado viene la firma del **Poder Ejecutivo** sobre el mensaje, que no
  firmó ningún dictamen, y un parser ingenuo la mete adentro de la comisión.
- **El bloque NO sale del PDF.** Se resuelve contra `datos/padron` a la fecha del
  dictamen. En el dictamen de mayoría los firmantes vienen sin bloque, y sacarlo
  de ahí daría una segunda fuente contradictoria para un dato que ya tenemos.
- **Lo que no se pudo leer entra igual**, con `parseo_ok=False` y su `motivo`. Si
  desapareciera, la cobertura se vería mejor de lo que es.
- **El enganche con el proyecto** es por expediente del sumario cuando matchea
  (`enlace=expediente`) y por Orden del Día cuando no (`enlace=orden_del_dia`),
  que es más flojo y por eso está dicho en una columna.
- **Sólo proyectos de LEY.** 2.517 Órdenes del Día, no las 18.087 totales: las
  otras ~15.500 son resoluciones y declaraciones, que no alimentan ninguna puerta.
- **`origen_firmas` no es decorativo.** En las Órdenes del Día de **2020 y 2021**
  —las de las sesiones remotas— la fórmula `Sala de las comisiones` **no existe**:
  la palabra "sala" aparece cero veces y los firmantes van pegados al final del
  dictamen. Esas se leen reconociendo el bloque **por su forma** (líneas seguidas
  separadas por `–`, entre la cabecera del dictamen y el primer encabezado en
  mayúsculas) y salen marcadas `sin_ancla`. Son **152 de 2.517** (corrida completa
  del 22-08-2026), con el grueso concentrado en esos dos períodos. **Control:** esas
  3.187 firmas resuelven contra el padrón al **96,2%**, la misma tasa que las 122.317
  leídas con la fórmula (96,0%) — si el reconocimiento por forma levantara texto
  cualquiera, la tasa se desplomaría. **Una firma leída sin ancla es más frágil que
  una leída con la fórmula: al medir, separalas.**
- **`139-1.pdf` cuelga a pdfminer para siempre** (2,2 MB, 72 páginas, 58 fuentes
  con 38 CMaps). Por eso `texto_de_pdf` lee con tope de 20 páginas y, si no
  aparece el ancla, se pasa a pypdf sobre el archivo completo —2 segundos— con
  el espaciado reparado. No hay timeouts ni procesos aparte.

### El Senado

**Volumen real (medido el 21-08-2026): el listado da 1.882 filas, pero son 1.761
Órdenes del Día reales** — 98 son el mismo documento repetido con otro id interno
(mismo número, año y expediente). 2008-2026.
Entre 100 y 120 por año hasta 2022, y después cae (79 en 2023, 69 en 2024, 54 en
2025, 43 en 2026), igual que la actividad de comisiones en Diputados.

**Y el dato que la Puerta C no tenía: 475 de esas 1.761 (27%) son de cámara
REVISORA** — dictámenes del Senado sobre proyectos que ya tenían media sanción de
Diputados. La proporción se sostiene entre el 13% y el 50% a lo largo de casi
veinte años, sin ninguna ventana en cero. Va en la columna `rol_camara`, que se
deriva del **origen del expediente** y no de un supuesto: `CD-` = revisora
(Puerta C), `PE-`/`S-` = origen (Puerta A).

⚠️ **El padrón del Senado sólo cubre desde el 10-dic-2017**, así que **1.102 de las
1.761 (63%) son anteriores** y su bloque no resuelve. En la corrida completa el Senado
dio **52,0%** contra el **96,0%** de Diputados, con el desglose apuntando a eso: `sin_candidatos`
significa "a esa fecha el padrón no tiene ninguna banca cargada", no que el nombre
no matchee. La canónica **sí** tiene el Senado cubierto (220.426 votos, 2004-2026,
con exactamente 72 senadores por año no electoral), así que la reconstrucción es
viable — pero **no se copia la de Diputados**: el Senado se renueva por tercios cada
dos años con mandatos de seis, y la regla de "el período va del 10-dic de año impar"
no aplica.

`src/ingesta_od_senado.py`. Las Órdenes del Día de arriba son de **Diputados**;
el CKAN publica los dictámenes de las comisiones **de Diputados**, sea origen o
revisora (1.515 filas de LEY son de proyectos con origen Senado). El hueco real
es el sistema de comisiones del Senado, que publica por su propia vía: POST a
`/parlamentario/parlamentaria/ordenDelDiaResultado` con
`busqueda_orden[ordenDelDiaPeriodo]` (1983-2026) y `tipoExpedientes` (`PL`,
`CD`), y descarga por id interno. **Sus PDF traen los firmantes con la misma
fórmula de cierre**, así que los lee el mismo `parser_od.py`.
