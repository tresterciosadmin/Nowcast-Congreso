# Módulo: variables/bloque

**Propósito.** Cohesión, tamaño, posición (postura) y fracturas de cada bloque a lo
largo del tiempo — y, sobre esa serie, un **proyector point-in-time** que arma el
**escenario por bloque** que consume el ensemble/agregador (hoy se pone a mano).

**Estado:** EN CURSO (v1) · **Owner:** Claude+Valle (2026-07-12)

## Qué produce
1. **Serie temporal por bloque** (`outputs/serie_bloque.parquet`): una fila por
   `(periodo, camara, bloque_linaje)` con
   - `bancas_medias` (tamaño),
   - `share_afirmativo` (postura: fracción de actas donde la dirección del bloque fue AFIRMATIVO),
   - `cohesion_media` (índice de **Rice** = |afirm−neg|/emitidos; 1 = unánime, 0 = 50/50),
   - `desvio_medio` (fracción minoritaria interna = ruptura),
   - `tasa_fractura` (proporción de actas con Rice < 0,5, el bloque partido),
   - `n_actas`.
   El período es **parlamentario** (recambio 10-dic: diciembre cuenta para el año siguiente).
2. **Proyector** (`proyectar_postura(votos, fecha, camara)`): usando **solo actas
   anteriores** a la fecha dentro de una ventana móvil (walk-forward, sin leakage),
   devuelve `[{bloque, bancas, linea, desvio}, ...]` — el formato exacto del
   escenario del ensemble. `linea ∈ {AFIRMATIVO, NEGATIVO, NO_ACOMPANA}` (dirección
   modal reciente), `desvio ∈ [0,1]` (cohesión inversa).

## Contrato
- **Entrada:** `datos/canonica/data/clean/{votos_resuelto,actas_canonico}.parquet`
  (columnas usadas: `acta_id, legislador_id, bloque_linaje, voto` + `fecha, camara`).
- **Salida estable:** `outputs/serie_bloque.parquet`.
- **Consumidor:** `modelo/ensemble` (reemplaza la postura puesta a mano) y análisis de bloque.
- **Semántica:** idéntica a `modelo/agregador_institucional` (mismas conductas), para
  que el escenario encaje sin traducir.

## Alcance v1 y qué falta (honesto)
- **Lo que ya sale bien y era el hueco del ensemble:** la **cohesión/desvío** y el
  **tamaño** por bloque, proyectados point-in-time. En datos reales discrimina
  (p. ej. OTRO/PROVINCIAL desvío ~0,28 y fractura ~0,64 vs LA LIBERTAD AVANZA ~0,015).
- **Límite conocido — la DIRECCIÓN es incondicional:** como casi todo lo que llega
  al recinto se aprueba, la dirección proyectada sin condicionar da AFIRMATIVO para
  casi todos los bloques. **La postura que de verdad discrimina es POR TEMA/ORIGEN**
  y es el **v2**: depende de que `variables/proyecto` publique el tema (batch del
  agente de taxonomías, necesita API key) y el origen del proyecto. El proyector deja
  el hook para condicionar por esos rasgos sin cambiar el contrato.

## Cómo correr (local, PC de Valle)
```
python variables\bloque\src\bloque.py serie          # escribe outputs\serie_bloque.parquet
python variables\bloque\src\bloque.py proyectar 2025-05-01 diputados   # imprime el escenario
```
Tests offline (sin datos reales, desde /tmp por el protocolo de sync):
`python variables\bloque\tests\test_bloque.py`  → 7 chequeos.

## Convenciones
Resiliencia: errores específicos, parsing defensivo, logging estructurado (no hay I/O
de red acá). No editar archivos de otros módulos; se consume su contrato (parquet).

## v2 — dirección condicionada por tema/origen (2026-07-22)
`proyectar_postura(...)` acepta ahora `tema` (área, ej. `ECON`), `origen` (ej. `OPOSICION`)
y `cond_por_acta` (el contrato `variables/proyecto/data/tema_por_acta.parquet`, acta_id→tema).
Con eso, la DIRECCIÓN de cada bloque se calcula sobre las actas de la ventana que comparten
tema/origen y se mezcla con la incondicional por **encogimiento** (`k_shrink=5`), para no dar
vuelta una postura con 2-3 actas. **Sin `tema`/`origen` el resultado es IDÉNTICO al v1**
(campo `_share_incond` lo evidencia) → no rompe el contrato ni el ensemble.
Resuelve el límite del caso testigo 1167 (dirección incondicional → 100% irreal).
- CLI: `python variables\bloque\src\bloque.py proyectar <YYYY-MM-DD> <camara> --tema ECON [--origen OPOSICION]`
- Insumo: correr antes `variables\proyecto\src\tema_por_acta.py` (necesita API key) para generar el contrato.
- Tests: `python variables\bloque\tests\test_bloque_v2.py` (5 chequeos, sin red).
