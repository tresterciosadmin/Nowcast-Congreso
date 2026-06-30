# Reconstruir la base canónica de votaciones (de cero)

Un comando arma todo el lado de **votos** (no toca la base de proyectos del equipo):

```bash
python datos/canonica/src/run_pipeline.py
```

## Qué hace (en orden)
1. **Semilla Década Votada** — descomprime `Aportes.../DecadaVotadaCSV.zip` y corre `decada_votada/src/from_csv.py` (Diputados 2001–2010 + Senado 2004–2014).
2. **CKAN Diputados** (2011–2019) — descarga y normaliza.
3. **argentinadatos** (Dip 2020–2025, Sen 2024–2025) — descarga y normaliza.
4. **Excel 2026** — `manual_2026` (votos a mano + bloque del Senado).
5. **build** — une, deduplica (precedencia oficial > agregador > semilla; manual_2026 máxima) y valida contra `docs/schemas`.
6. **entity_resolution** — legislador_id + bloque_norm/linaje/coalicion (time-aware).
7. **baseline** — `evaluacion/baseline`.

## Requisitos
- Internet (CKAN y argentinadatos se bajan en vivo).
- Deps: `pip install -r datos/canonica/src/requirements.txt` (+ openpyxl para manual_2026).

## Salida
- `datos/canonica/data/clean/{votos_canonico,actas_canonico,votos_resuelto}.parquet` (no se versionan; regenerables).
- Resultado actual: **~4.584 actas / 780.839 votos, 2001–2025 ambas cámaras**.

## Hueco conocido
- Senado **2015–2023** (entre el fin de la Década Votada y el Excel 2026). Senado 2001–2003 no existe como nominal.
