# Módulo: datos/bot_recoleccion

<!-- huella: 510308d091f9 -->

**Propósito.** El PADRÓN VIVO (idea de Franco, 11-07-2026): un bot diario que
trae lo nuevo de ambas cámaras — proyectos ingresados con firmantes y giros —
y (fase posterior) las votaciones nuevas, con upsert idempotente.

**Estado:** EN CURSO — bicameral, automatizado en GitHub Actions **y entregando a `proyectos.db`** desde el 07-08-2026 (ADR-0009).
**Owner actual:** Claude+Franco (2026-07-11)

**Resumen:** El bot diario que trae lo nuevo de ambas camaras (proyectos con firmantes y giros, y votaciones) con upsert idempotente. Corre solo en GitHub Actions.

## Buscar acá si

- el modelo no ve los proyectos de las ultimas semanas
- el bot diario fallo, no commiteo, o abrio un issue
- scraping de Tramite Parlamentario (Diputados) o DAE (Senado)
- hasta que fecha llega lo que el bot entrego

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Arquitectura (diseño en README de datos/expedientes, fase 2)
- **Senado → `src/dae_senado.py`** (LISTO): lee el DAE Digital (diario oficial de
  ingresos, numeración secuencial por año). Estado local en `data/estado_bot.json`
  (último DAE visto) → trae solo lo nuevo → `data/clean/dae_entradas.parquet`
  (fecha_mesa, dae, expediente, GIROS, extracto, urls). Idempotente.
- **Diputados → `src/tp_diputados.py`** (LISTO): lee el Trámite Parlamentario
  (`tp.html?periodo=<P>&numero=<N>`, numeración secuencial por período
  parlamentario; histórico desde el período 137). Por proyecto: **firmantes
  COMPLETOS (autor + cofirmantes)** — el dato que el CKAN no publica —, tipo,
  sumario, expediente (link al PDF), sección de origen y giros. Estado
  incremental e idempotente igual que el DAE → `data/clean/tp_entradas.parquet`.
- **Votaciones nuevas** (fase 3): reutiliza scrape_votaciones (Senado, plan
  `--ids` incremental) + fuente Diputados.
- Los firmantes por expediente salen del propio diario (TP) o de la ficha
  verExp (contrato de datos/seguimiento) — NO de las páginas personales.

## Cómo correr
```bash
python datos/bot_recoleccion/src/dae_senado.py          # trae DAEs nuevos
python datos/bot_recoleccion/src/dae_senado.py 30 2026  # un DAE puntual (debug)
python datos/bot_recoleccion/tests/test_dae.py          # 13 chequeos offline
```

## Dónde corre: GitHub Actions (decisión 11-07-2026)
El bot vive en `.github/workflows/bot-diario.yml` (raíz del repo git): cron
diario 07:00 ARG (lun-sáb) + botón manual en la pestaña Actions. Corre
`dae_senado.py` y, si hay DAE nuevos, commitea `dae_entradas.parquet` +
`estado_bot.json` (excepciones en .gitignore). Sin novedades = sin commit.
Es el ejecutor 24/7 interino hasta la Etapa 4 (Oracle); la base se completa
sola en el propio repo. Al hacer `git pull` te traés lo que el bot juntó.

## ✅ LA ENTREGA — resuelta el 2026-08-07 (ADR-0009)

**Ningún script del repo lee las salidas de este módulo** fuera de sus propios
tests. Comprobado con `grep` sobre todo el árbol: `tp_entradas.parquet`,
`dae_entradas.parquet` y `votaciones_nuevas.parquet` se escriben, se commitean, y
ahí quedan.

**Con las votaciones no hay problema, y es por diseño.** `run_pipeline.py` no lee
`votaciones_nuevas.parquet`, pero re-baja las actas de la API, así que entran
igual. Acá el bot es la **alarma**: detecta y abre un issue con los comandos.
Decisión explícita del 04-08 — no reconstruir la fuente de verdad sin revisión
humana.

**✅ EL AGUJERO SE CERRÓ el 2026-08-07 (ADR-0009).** Este README decía hasta ese
día que el bot "recolecta pero no entrega". **Ya entrega.**

`datos/proyectos/src/upsert_bot.py` carga lo que junta este módulo en
`proyectos.db`, que es la fuente de verdad que consume el embudo:

| | resultado |
|---|---:|
| proyectos nuevos cargados | **+1.531** |
| …de ellos, **proyectos de ley del Senado** | **514** |
| proyectos existentes enriquecidos con datos de acá | 2.293 |
| proyectos con **cofirmantes completos** (el dato que CKAN no publica) | **1.222** (máx. 15 firmantes) |
| el universo del modelo pasa a llegar hasta | **05-ago-2026** (antes: 02-jun) |

**El giro AL INGRESAR que captura el TP** entra como `n_giros_inicial`, que es
medición directa y le gana a la reconstrucción de `giros_iniciales.py`. La cobertura
del giro medido subió de 2.927 a **4.449 proyectos**.

**Lo que NO se pudo leer va a `datos/proyectos/data/cuarentena.db`**, una base aparte
(decisión de Valle): la carga no se frena por una fila rara, pero nada dudoso entra a
la base general. Ver `python datos/proyectos/src/cuarentena.py`.

> ⚠️ **Cuidado al leer el TP:** el campo `giros` viene **sin separadores**
> (`"ASUNTOS CONSTITUCIONALES LEGISLACION PENAL PRESUPUESTO Y HACIENDA"` son tres).
> Hay que matchear contra el catálogo de 151 comisiones, del nombre más largo al más
> corto. Partirlo por espacios da un error de 10x — ya pasó el 07-08.
>
> ⚠️ **Y el DAE del Senado trae el código de origen en el prefijo** (`S-` senador,
> `PE-` Ejecutivo, `CD-` Diputados). Un parser que sólo matchee `^S-` descarta **los
> del Poder Ejecutivo**, que son los de mayor peso del modelo (convierte ~77% contra
> 1,4%). Pasó el 07-08 con 34 expedientes, y el único síntoma fue un
> `logger.warning`.

## Pendientes
**(1) El upsert hacia `datos/proyectos`** — ver la sección de arriba; es el que
convierte a este módulo en algo que sirve. Después: tipo ACUERDOS del DAE;
backfill TP períodos 137-143 (cofirmantes históricos); capa expedientes;
programación diaria (cron/Tarea de Windows) cuando haya entorno 24/7 (Etapa 4).

## Convenciones
Resiliencia obligatoria (errores específicos, backoff, parsing defensivo por
firma de encabezados, logging). Consumir contratos de otros módulos, no su código.
