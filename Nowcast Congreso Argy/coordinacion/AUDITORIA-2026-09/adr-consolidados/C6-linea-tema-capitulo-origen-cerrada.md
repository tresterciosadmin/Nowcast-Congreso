# C6 — Línea de tema, capítulo y origen heredado: cerrada

**BORRADOR** · **Absorbe:** 0006, 0023, 0024, 0026, 0027, 0028, 0029, 0030, 0031, 0033 · **Referencias:** 0032 (C5), 0034 (C5), 0018 (C2)

## 1. La regla

> **Ningún mecanismo de tema, de capítulo ni de récord por origen heredado entra al número.** Todo queda apagado por defecto, con el valor fijado por un test. **Se reabre sólo** con una medición hecha según C5 que mejore el Brier pareado por ley, con IC que excluya 0, en el total **y** en la era vigente, y con al menos 50% de los votos con dato condicionado real.

## 2. Por qué (qué se probó y qué dio)

| línea | ADR | resultado | medición |
|---|---|---|---|
| multietiqueta a nivel **bloque** (`union`, `ponderada`, `peor_tema`) | 0024, 0028 | ninguna regla se distingue de no condicionar por tema (Δ +0,0018 [−0,003; +0,011]); **el "control" era idéntico al tratamiento** (rama `primaria` sin `tema`, diferencia 0,0 exacta en 232 actas) | harness con `shift(1)`, cluster por acta, 232 actas de bloque (0,33% de los votos) |
| **récord por tema** | 0026 | +11,06% con fuga → **−2,9%** con la misma metodología y historia estricta → **+2,1% de error** contra el motor [0,8; 3,5]; +6,4% donde actúa; Senado +20,5% | censo limpio (ADR-0034) |
| composición por **capítulos** y votación por artículo | 0023, 0027, 0029, 0030 | sin resultado por capítulo (0 de 20 con dato real); sin consumidor en el número; el 9,8% de las leyes aprobadas pierde algún tramo (dato descriptivo) | conteos; ninguna medición de skill |
| **firma temática** del desvío | 0032 | +0,015 [−0,03; 0,06] | IC por legislador (el ancho por ley sólo refuerza el nulo) |
| récord por **origen heredado** entre gobiernos | 0033 | −0,03% (ns); lo que persiste entre gobiernos es la memoria del linaje, no la del legislador | brazos con fecha estricta, sin "otra ley" |
| guard de era en el récord temático | 0031 | "el guard queda confirmado" vale sólo para tasa cruda | correlaciones entre ventanas |
| multitaxonomía por título | 0006 | diseño aceptado, implementación pendiente | — |

**Reglas que sobreviven:** *agregar sin reemplazar* (0023) · *lo manual gana; sin dato, no-op* (0024) · *un solo grado de libertad; encoger hacia el récord general; en logit* (0026) · *un control que da idéntico al tratamiento es una alarma* (0028, pasa a C5) · *todo fallback avisa con un contador agregado* (0031, pasa a C5).

## 3. Cómo se verifica que sigue cerrada

- **Propuesto:** un test que fije `RECORD_POR_TEMA=False`, `TEMA_AUTO=False`, `COMBINAR_TEMAS='primaria'` y `SOBRE_TABLAS=False` como los de `test_beta_dictamen.py:85-90` (hoy nadie fija los dos primeros).
- `python .mapa/buscar.py --archivo modelo/ensemble/src/composicion_capitulos.py` debe devolver sólo tests y `validar_*`.

## 4. Qué la invalida (y con qué medición mínima se reabre)

- **Tema:** `censo_detalle_paralelo.py` (ya calcula la variante `record_por_tema`) más una versión **relabelada por lado** (gobierno/oposición), con `GUARD_ERA` 0 y 1; criterio ΔBrier pareado < 0.
- **Capítulos:** sólo si una PRUEBA 2 ampliada da ≥ 20 leyes con resultado por capítulo; $P_k$ con `nowcast()` real, corte `<`, IC por ley.
- **Firma:** "con quién se desvía", par a par, partición por ley entera, ≥ 100 leyes efectivas.
- Que el panel pase a incluir `proyecto_id` o `tema` (hoy no puede: `REGENERAR.ps1:291`); ahí la medición deja de ser opcional.

## 5. Estado real hoy (verificado)

- **Nada de esta línea está en el camino del número con los defaults.** Código dormido dentro de archivos vivos: `alineacion_individual_por_area` (~111 líneas, `nowcast_puertas.py:385-495`), las ramas de combinación de `proyectar_postura` (~190, `bloque.py:570-743`). Módulos sin llamador productivo: `composicion_capitulos.py` (145), `tema_por_acta.py`, `tema_por_capitulo.py`. **≈ 4.850 líneas entre código y tests** (lote E) y `*.parquet` de salida ignorados por git.
- `RECORD_POR_TEMA` OFF (`nowcast_puertas.py:219`); `TEMA_AUTO` OFF (`:155`).
- **Encabezados desactualizados:** 0026 dice PRENDIDO; 0024 y 0028 tienen un banner que contradice su cuerpo; 0027 dice "decisión pendiente" y la decisión se tomó en 0030; 0029 dice "sin crédito de API" y el crédito se recargó el mismo día. Comentarios vivos que dicen "prendido": `nowcast_puertas.py:198-208,226-230`, `tablero_datos.js:332-333`.
- **Datos parciales** de 0029: ninguno se usa en producción.

**Historia:** 0006 (07-31) multitaxonomía por título · 0023 (09-15, Claude, mandato de Franco) votación por artículo · 0024 (09-15) multietiqueta y `TEMA_AUTO` · **0026 (09-16, Claude "con autonomía delegada") `RECORD_POR_TEMA`, prendido y apagado 12 días después** · 0027 (09-16) composición por capítulos · 0028 (09-16) cierre del multitema · 0029 (09-16) tema por capítulo, "parcial" · 0030 (09-17) cierre de capítulos y pivotes · 0031 (09-17) el guard y el fallback observable · 0033 (09-27/28) récord por origen relabelado.

**Se pierde:** los niveles de skill de 0033 (superados por 0034); la cobertura ampliada como "insumo vivo"; el diagnóstico del Senado de 0030 (`diagnostico_senado.py` tiene la fuga: sus cifras 0,072 → 0,120 y 68,8% ya no valen); la afirmación "el guard queda confirmado también para el tema" (0031).
