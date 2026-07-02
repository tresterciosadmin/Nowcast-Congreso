# Módulo: variables/legislador

**Propósito.** La **base de datos individual de legisladores**: una ficha por cada diputado/senador que votó alguna vez en la base canónica, con su historial completo — identidad, cámara(s), distrito, períodos parlamentarios, trayectoria de bloques, presentismo, perfil de voto y tasa de desvío vs. su bloque. Es el "análisis individual de cada legislador" del que la detección de díscolos (`modelo/voto_individual`) es un caso de uso, no el objetivo.

**Unidad de análisis temporal: el período parlamentario.** El Congreso se renueva cada 10 de diciembre de años impares; cada recambio —incluso con reelección— es una nueva configuración de escaños que interviene en el comportamiento y la disciplina. Por eso el análisis fino se hace sobre la tabla legislador × período, no sobre el agregado de carrera.

**Estado:** EN CURSO — v1 con dimensión período (re-correr tras cada rebuild de la canónica)
**Owner actual:** Claude+Valle (desde 2026-07-01)

## Contrato
- **Entradas:** `datos/canonica/data/clean/{votos_resuelto,actas_canonico}.parquet`. Opcional: `modelo/voto_individual/outputs/{disciplina_individual,disciplina_por_anio,disciplina_por_periodo}.csv` (si existen, las tablas incorporan la tasa de desvío; si no, esa columna queda vacía — NUNCA en cero).
- **Salida (contrato estable):** en `data/` (regenerable, NO se versiona):
  - `legisladores.parquet|.csv` — una fila por legislador (ficha resumen, con `periodos` y `n_periodos`)
  - `legislador_periodo.parquet` — **LA tabla de análisis**: legislador × período parlamentario × cámara (bloque, votaciones, presentismo, tasa de desvío)
  - `legislador_bloques.parquet` — historial legislador × bloque × cámara (desde–hasta)
  - `legislador_anio.parquet` — evolución anual
  - `legisladores.xlsx` — export legible (hojas Fichas / PorPeriodo / Bloques / PorAnio)
- **Depende de:** datos/canonica (+ modelo/voto_individual como insumo opcional)
- **Gate de pase:** features point-in-time, sin leakage (v1 usa agregados por período; la versión point-in-time por fecha viene después)

**Nota sobre `anio_desde/anio_hasta`:** son actividad observada en la base (primer/último año en que la persona aparece votando), NO el mandato formal. No detectan interrupciones y heredan los huecos de cobertura (Senado 2015–2023). El mandato exacto vendrá del padrón oficial de parlamentarios (pendiente). Para etapas usá `periodos` (ficha) o la tabla `legislador_periodo`.

## Cómo correr
```bash
python modelo/voto_individual/src/disciplina.py      # primero (genera los insumos de desvío)
python variables/legislador/src/ficha.py             # después (arma fichas y tablas)
python variables/legislador/tests/test_ficha.py      # tests sin red (18 chequeos)
```

## Pendientes conocidos
- **Perfil temático (central):** hoja "PorTema" = legislador × período × taxonomía con pct_afirmativo/pct_negativo/tasa_desvio, para detectar tendencia a aprobar/rechazar por tema. Bloqueado por: corrida del agente de taxonomías (variables/proyecto) + cruce acta→expediente→proyecto. Detalle en PLAN-DE-TRABAJO 1B.3.
- Mandato formal (asunción/cese) desde el padrón oficial de parlamentarios.
- Sumar el "apodo web" (slug) de cada diputado, que necesita `datos/seguimiento`.
- Versión point-in-time (una fila por legislador-fecha) para el feature store del modelo.
- Unificar `periodo_parlamentario()` en una lib común cuando exista `datos/_common` (hoy duplicada y sincronizada con `modelo/voto_individual`).
