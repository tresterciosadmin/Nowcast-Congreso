# Módulo: evaluacion/baseline

<!-- huella: c73b1745da0f -->

**Propósito.** Baseline de bloque (HECHO). Documenta el piso a superar por cualquier modelo.

**Estado:** HECHO
**Owner actual:** _(vacante — reclamalo en coordinacion/TABLERO.md antes de empezar)_

**Resumen:** El censo del motor sobre el voto individual. Desde el 28-09 (ADR-0034) el harness NO reimplementa nada del legislador: importa `record_legisladores`, `proyectar_postura` y `perfil_legislador` del motor y solo decide que votos existian (historia estricta: fecha anterior y OTRA ley). Un test lo compara contra `nowcast()` legislador por legislador. El baseline de BLOQUE -el ~0,99- se midio en `fase0/` y ahi quedo.

## Buscar acá si

- el numero publicado del motor (skill del voto individual) y como se reproduce: `censo_detalle_paralelo.py` + `resumen_censo_limpio.py`
- la **metrica de verdad** (skill por era y camara con IC por ley de 2.000 replicas, DBrier pareado, procedencia y certificado de que el motor de hoy da esas P_i), con UN comando que no pisa ningun numero versionado: `src/metrica_de_verdad.py` -> `outputs/metrica_de_verdad.json` (`tests/test_metrica_de_verdad.py`; auditoria C1)
- la **calibracion declarada** de P(aprobacion) y de la banda, en mayoria simple y por camara (Brier contra una constante con IC pareado, AUC, recalibrado, cobertura de la banda al 90%), desde un JSON por acta que viaja por git, con UN comando que no pisa ningun numero versionado: `src/calibracion_declarada.py` -> `outputs/calibracion_declarada.json` (`--simular` regenera el JSON por acta con el motor de hoy, 6 min; `tests/test_calibracion_declarada.py`; auditoria C2)
- el **guard de era** sin cortar (brazo `era_desde` del harness, el motor no cambia) y su veredicto medido (primario: actas desde 2015-12-10; NO SE DISTINGUE): `src/medir_sin_corte_por_era.py` -> `outputs/guard_era_sin_corte.json` y `outputs/censo_estadisticos_sin_corte_era_2026-10-01.json` (el de C3, sobre el censo del 28-09) y `outputs/censo_estadisticos_sin_corte_era_2026-10-02.json` (re-corrido sobre el motor de D1.0: el insumo de D1) (`--censo` corre el censo del brazo, 14 min; `tests/test_guard_era_sin_corte.py`; auditoria C3)
- los **brazos del harness** (argumento `brazo` de `Contexto`/`correr`: k y ventana de la postura, origen por lado, `era_desde`; un valor o uno por año; default = el motor de hoy, que no se toca) y el **walk-forward de D1** (los siete hiperparámetros de P_i contra V0: selección anual, compuesto, IC por ley y por mes, Holm y el árbol del protocolo, desde una tabla por acta que viaja por git): `src/medir_d1_parametros_pi.py` (`--censo`, `--controles`, `--panel`, `--medir`; `tests/test_d1_parametros_pi.py`; auditoria D1)
- los estadisticos del censo que SI viajan por git (skill + IC por ley, tau, eps0) y como se regeneran: `censo_estadisticos.py` -> `outputs/censo_estadisticos_*.json` (el detalle voto a voto es un parquet ignorado; `tests/test_censo_estadisticos.py`)
- la regla del EXPEDIENTE: que cuenta como historia de un voto, y como se agrupan actas en leyes (`ley_por_acta`, `historia=estricta`)
- IC que re-muestrean leyes, no actas (`skill_ic_por_ley`, `dif_brier_ic_por_ley`)
- la fuga del harness viejo (shift(1) por fila) y cuanto pesaba: `medir_fuga_historia.py` (0,161 -> 0,092 -> 0,074)
- de donde salia el 11,06% de RECORD_POR_TEMA: `medir_record_por_tema_limpio.py`
- que el harness mide al motor y no una copia: `tests/test_harness_es_el_motor.py` (desde el 2026-10-02 también en la rama de bloque, con la ficha de desvío AL DÍA del motor: auditoría D1.0; el detalle del censo guarda sus componentes en las columnas `ficha_*`)
- el record por ORIGEN entre gobiernos (ADR-0033): **archivado en A7** (`coordinacion/archivo/A7-poda-2026-09/evaluacion/baseline/src/`); sus resultados siguen en `outputs/record_por_origen_*.json`
- las reglas de combinacion de temas de la POSTURA (ADR-0024/0028): `--combinar-temas`, experimento cerrado

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## El harness (ADR-0034, 28-09-2026)

Hasta el 28-09 este harness tenia su propia copia del record y de `perfil` ("espejo exacto de
`perfil_legislador`"). Divergio dos veces: no condicionaba el record por origen (el motor si)
y contaba como historia los votos del mismo dia (`shift(1)` por fila). Ahora:

| pieza | de donde sale |
|---|---|
| record | `nowcast_puertas.record_legisladores` |
| postura del linaje | `bloque.proyectar_postura`, a la fecha exacta del acta |
| P_i | `nowcast_puertas.perfil_legislador` |
| que votos existian | el harness: `--historia estricta` (default), `fecha`, `dia_incluido` (el `<=` viejo del motor) |

`perfil()` queda como delegacion al motor para los `estimar_*.py` viejos. Esos scripts y
`medir_guard_era.py` y `fase1_rec_por_tema.py` (`medir_rec_por_tema.py` y `diagnostico_senado.py` se archivaron en A7)
todavia arman su propio record con `shift(1)`: estan marcados en el codigo como espejos viejos.

## Contrato
- **Entradas:** datos/* (detalle)
- **Salida (contrato estable):** outputs/baseline_resultados.{json,md}
- **Depende de:** datos/ckan_diputados
- **Gate de pase:** Benchmark publicado: dirección ~0.99 / 4-clases ~0.81

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/baseline-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
