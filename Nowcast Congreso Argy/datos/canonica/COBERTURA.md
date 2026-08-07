# Cobertura de la base canónica

> ⚠️ **Este archivo es un HISTORIAL, no una foto.** Se lee **de abajo hacia
> arriba**: la última "Actualización" manda. Corregido el 2026-08-06 — hasta
> entonces arrancaba con una tabla y un "Hoy:" de junio (1.414 actas / 340.892
> votos) que quedaron congelados mientras el resto del archivo crecía. Cualquiera
> que leyera sólo el encabezado se llevaba una foto tres meses vieja y **cuatro
> huecos que ya estaban cerrados**.

**Estado al 2026-08-06 (medido en disco):**

| | |
|---|---|
| **Votos** | **1.016.632** |
| **Actas** | **6.231** |
| **Cobertura** | 2001–2026, ambas cámaras |
| **Hueco abierto** | Diputados 2020–2023 (pausado por decisión del 10-07) |

Objetivo original: **2001–2025, ambas cámaras** (últimos ~25 años) — cumplido y
excedido; hoy llega a 2026.

## Huecos para llegar a la meta (lista ORIGINAL de junio — ver más abajo cuáles se cerraron)
1. **Diputados 2001–2010** → correr la **semilla** (`datos/decada_votada`, R).
2. **Diputados 2020–2023** → argentinadatos está incompleto; completar desde la fuente oficial `votaciones.hcdn.gob.ar`.
3. **Senado 2004–2013** → semilla (Andy Tow).
4. **Senado 2014–2023 y 2001–2003** → no hay fuente fácil; trabajo de `datos/senado` (scraping oficial).
5. **Bloque del Senado** → argentinadatos no lo trae en el voto; resolver padrón→bloque por fecha (hoy queda "SIN BLOQUE").

## Actualización (2026-06-27): Excel 2026 integrado
- Sumada la fuente `manual_2026`: 17 actas (10 Diputados + 7 Senado), votos nominales 2026 de ambas cámaras.
- **Senado con bloque resuelto** (del padrón del Excel) → primera medición de baseline del Senado.
- Base canónica: **1.431 actas, 343.964 votos** (Diputados 1.304, Senado 127).
- Hueco que sigue: Senado nominal 2004–2023 (semilla) y 2001–2003 (no existe nominal). Bloque de argentinadatos Senado 2024–2025 aún "SIN BLOQUE" (retro-completar con el padrón).

## Actualización (2026-06-27): semilla Década Votada (CSV) integrada
- Sumada la fuente `decada_votada` desde el CSV local: Diputados 2001–2010 + **Senado 2004–2014**.
- Base canónica: **4.584 actas, 780.839 votos**, cobertura **2001–2025 en ambas cámaras**.
- Baseline Senado ahora robusto: **0,971** (n=26.359).
- Hueco que queda: **Senado 2015–2023** (entre el fin de la Década Votada y el Excel 2026). Senado 2001–2003 no existe como nominal.


## Actualización (2026-07-02): Senado oficial 2015-2023 integrado — hueco CERRADO
- Nueva fuente `senado` (scraper oficial, módulo `datos/senado`): 749 actas / 53.910 votos 2015-2023, con **bloque contemporáneo al voto** (padrón Wikipedia 2017-25 + curación manual 2015-17; 100% cobertura, 0 anacronismos). Validación externa: 43.684 votos cruzados vs nahuelhds, 0 discrepancias.
- Base canónica: **5.333 actas / 834.749 votos**, 2001-2026 ambas cámaras (senado 2.887 actas / diputados 2.446).
- Baseline re-medido (LOO bloque_norm): global 0,979 todas / 0,964 disputadas. **Senado por primera vez completo: 0,983 todas / 0,957 disputadas (n=40.646)** — algo más de indisciplina que Diputados (0,965) en votaciones peleadas. Drift 2024-25 se sostiene (0,946 / 0,923).
- Tabla de arriba queda superada en la fila Senado: 2015-2023 ✅ fuente `senado`.
- Huecos restantes: **Diputados 2020-2023** (argentinadatos incompleto → `datos/diputados_oficial`); bloque Senado 2024-25 en argentinadatos sigue "SIN BLOQUE" (retro-completable con el padrón de `datos/senado`).


## Actualización (2026-07-31): 229 actas ingestadas — la base salta 22%
- Se re-corrió la ingesta y el build. **5.333 → 6.231 actas (+898)** y **834.749 → 1.016.632 votos (+182k)**.
- Cubre hasta **25-06-2026** (Diputados) y **16-07-2026** (Senado).
- La Cámara que aparece es otra: **LLA 95 bancas y FdT-UxP 93** (antes 35 y 92) — LLA pasó de tercera a primera minoría.
- El bloque del Senado 2024-25 quedó **resuelto** vía padrón versionado.
- Decisión del mismo día: **la canónica SÍ se versiona** (~6 MB). Es regenerable, pero dos incidentes nacieron de trabajar sobre copias viejas.


## Actualización (2026-08-06): el bloque del Senado 2026, tapado en la ENTRADA
- **Problema:** los 6.192 votos del Senado de 2026 entraban `SIN BLOQUE`. La ingesta (`datos/argentinadatos/src/to_canonical.py`) cruzaba sólo contra el padrón histórico, que **termina el 2025-12-09** — o sea, todo lo posterior al recambio del 10-dic caía afuera.
- **Fix:** se sumó `datos/padron/data/padron_senado.csv` (72 senadores vigentes, mandate-aware) como tercera fuente del cruce, **última en precedencia** para no pisar lo curado en el tramo solapado. Los 72 resuelven bloque; cubierto por 8 tests en `datos/argentinadatos/tests/`.
- **Ojo con el diagnóstico:** este síntoma se atribuyó dos veces a que "ninguna fuente publica el bloque del Senado". Era falso — el padrón existía desde el 14-jul; primero se lo comió el `.gitignore` y después nadie apuntó la ingesta hacia él.
- ⏳ **La corrección NO está en los parquet todavía:** requiere re-correr `run_pipeline.py` (~20 min, con internet). Ver `coordinacion/URGENTE.md` ítem 2.
- **Regla que aplica:** los huecos se tapan en la entrada, no en cada consumidor. `variables/bloque` tenía un parche de consumo (`_enriquecer_linaje_senado`) que se puede simplificar una vez que la canónica venga sana.
