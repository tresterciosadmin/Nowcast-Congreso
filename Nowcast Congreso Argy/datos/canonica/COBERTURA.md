# Cobertura de la base canónica (estado actual)

Objetivo: **2001–2025, ambas cámaras** (últimos ~25 años).

| Año | Diputados | Senado |
|---|---|---|
| 2001–2010 | ⛔ falta (semilla Andy Tow) | ⛔ falta (semilla: 2004–2013) |
| 2011–2018 | ✅ CKAN | ⛔ falta |
| 2019 | ✅ CKAN (período 137) | ⛔ falta |
| 2020–2023 | 🟡 incompleto (argentinadatos parcial) | ⛔ falta |
| 2024–2025 | ✅ argentinadatos | ✅ argentinadatos (sin bloque) |

Hoy: **1.414 actas / 340.892 votos**, Diputados 2011–2025 y Senado 2024–2025.

## Huecos para llegar a la meta
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
