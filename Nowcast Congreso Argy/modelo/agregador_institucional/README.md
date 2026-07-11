# modelo/agregador_institucional

Motor de **agregación institucional**: convierte la postura esperada de cada bloque en una
**probabilidad de aprobación** de la votación, entregada como **distribución** (rango con
incertidumbre), no como número puntual. Es la pieza (c) "recuento como distribución" del
plan de voto_individual, aplicando las reglas de quórum y mayorías.

**Estado:** EN CURSO — Owner: Valle (reclamado 2026-07-10). Gate de pase: reglas validadas
contra resultados históricos reales (backtest, en curso).

## Qué hace
Dado, para una votación (acta/proyecto):
- el **roster**: una línea esperada por legislador en `{AFIRMATIVO, NEGATIVO, NO_ACOMPANA}`
  (la baja de línea de su bloque), y su **tasa de desvío** individual (de `modelo/voto_individual`);
- la **cámara** y el **tipo de mayoría**;

simula la votación muchas veces (cada legislador sigue su línea con probabilidad `1-d` y se
desvía con `d`, repartido entre las otras dos conductas) y devuelve `P(aprobación)`, la media
y la banda 5–95% de afirmativos, el umbral y los emitidos esperados.

## Contrato
Entrada (para el backtest): `datos/canonica/data/clean/{votos_resuelto,actas_canonico}.parquet`
y `modelo/voto_individual/outputs/disciplina_individual.csv` (columna `tasa_desvio`).

Salida: `outputs/backtest_agregador.json` (Brier, accuracy@0.5, skill score, calibración por
deciles) y `outputs/backtest_detalle.csv` (p_pred vs y_real por acta).

Función reutilizable: `simular_votacion(lineas, desvios, tipo_mayoria, camara, n_sims)` → dict.

## Uso
```
# validar que el motor reproduce la historia
python modelo/agregador_institucional/src/agregador.py backtest
CANON=/ruta/clean DISC=/ruta/outputs N_SIMS=400 MAX_ACTAS=500 python .../agregador.py backtest

# nowcast de una votación desde un escenario JSON {lineas:[...], desvios:[...], tipo_mayoria, camara}
python modelo/agregador_institucional/src/agregador.py nowcast escenario.json

# tests (sin datos)
python modelo/agregador_institucional/tests/test_agregador.py
```

El **Panel Nowcast** (`PANEL-NOWCAST.html`, raíz del repo) trae una réplica en JavaScript de
este motor para simular votaciones de forma interactiva (se abre con doble clic).

## Reglas y sincronización
Umbrales y miembros de cada cámara están **replicados** de `datos/export` y `modelo/voto_individual`
(no se importa código entre módulos; mantener las tres copias sincronizadas):
`SIMPLE = emitidos/2 · ABSOLUTA = 129/37 · DOS_TERCIOS = ⌈2/3 emitidos⌉ · TRES_CUARTOS = ⌈3/4 emitidos⌉`.

## Simplificaciones v1 (documentadas)
- **Quórum laxo**: la sesión se asume válida si los presentes ≥ mitad+1 de los miembros. El
  modelado fino de asistencia es `variables/asistencia_quorum` (pendiente).
- **Postura de bloque como dato de entrada**: en el sistema final la proyecta un módulo de
  posición de bloque por tema; acá se pasa (observada en el backtest, elegida a mano en el panel).
- **Desvío como ruido individual** con reparto 50/50 entre las otras dos conductas (parámetro
  `reparto_desvio`).
