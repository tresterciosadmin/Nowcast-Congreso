# Módulo: datos/bot_recoleccion

**Propósito.** El PADRÓN VIVO (idea de Franco, 11-07-2026): un bot diario que
trae lo nuevo de ambas cámaras — proyectos ingresados con firmantes y giros —
y (fase posterior) las votaciones nuevas, con upsert idempotente.

**Estado:** EN CURSO (adaptador Senado listo con tests; Diputados en exploración)
**Owner actual:** Claude+Franco (2026-07-11)

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

## Pendientes
Tipo ACUERDOS del DAE; backfill TP períodos 137-143 (cofirmantes históricos); upsert hacia datos/proyectos
(contrato de Valle) y capa expedientes; programación diaria (cron/Tarea de
Windows) cuando haya entorno 24/7 (Etapa 4 del plan).

## Convenciones
Resiliencia obligatoria (errores específicos, backoff, parsing defensivo por
firma de encabezados, logging). Consumir contratos de otros módulos, no su código.
