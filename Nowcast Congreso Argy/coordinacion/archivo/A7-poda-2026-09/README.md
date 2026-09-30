# Archivo de la poda A7 (auditoría 2026-09, 30-09-2026)

Lo que se sacó del camino activo en el ítem A7 del plan de la auditoría (P0 y P1 del §5 del informe,
decisión 10 de Franco). **Nada se borró y nada salió de git: se movió con `git mv`** (el historial de
cada archivo se conserva). Criterio y método: `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md`, ítem A7.

## Por qué los `.py` terminan en `.archivado`

Para que no cuenten como código vivo: `pytest`, el bucle de scripts del CI (`find -name "test_*.py"`), el
indexador (`.mapa/indexar.py`) y `tests/test_rutas*.py` sólo miran `*.py`. La estructura de carpetas repite la
del proyecto: `coordinacion/archivo/A7-poda-2026-09/<ruta original>.archivado`.

## Cómo restaurar uno

Desde la raíz git (`Nowcast Congreso/`), sacando el sufijo:

    git mv "Nowcast Congreso Argy/coordinacion/archivo/A7-poda-2026-09/<ruta>.py.archivado" "Nowcast Congreso Argy/<ruta>.py"

Después: correr su test y `python -m pytest tests/ datos/proyectos/tests -q`. Si el archivo cita rutas o módulos
que cambiaron desde el 30-09-2026, hay que actualizarlas (`tests/test_rutas_citadas_existen.py` avisa).

## Qué hay

| Grupo (ADR) | Archivos (ruta original) | Qué era |
|---|---|---|
| **P1 — capítulos, pivotes y Senado** (ADR-0029/0030) | `evaluacion/baseline/src/`: `prueba1_pivotes_por_capitulo`, `prueba2_reconstruccion_por_rango`, `prueba3_cobertura_universo_vivo`, `validar_leybases_por_capitulos`, `validar_piloto_capitulos`, `validar_piloto_titulos`, `diagnostico_senado` | la línea cerrada de medición de capítulos y pivotes, y el diagnóstico del Senado |
| **P0 — capítulos** | `modelo/ensemble/src/composicion_capitulos` (+ test); `datos/expedientes/src/capitulos_nombre` (+ test); `variables/proyecto/src/tema_por_capitulo` (+ test) | composición de P(proyecto) por capítulos, lectura de nombres de capítulo y su clasificación temática |
| **P1 — firma temática** (ADR-0032) | `evaluacion/baseline/src/`: `firma_tematica_desvio`, `firma_tematica_fase0_celdas`, `firma_tematica_fase1_2` (+ `tests/test_firma_tematica`) | formulación del desvío por tema, descartada |
| **P1 — estabilidad, fase 0 y récord por tema** (ADR-0026/0028/0031) | `evaluacion/baseline/src/`: `medir_estabilidad_record_por_tema`, `fase0_control_temas`, `medir_rec_por_tema` | las mediciones con la fuga (el resultado limpio es de `medir_record_por_tema_limpio.py`, que sigue vivo) |
| **P1 — récord por origen** (ADR-0033) | `evaluacion/baseline/src/`: `record_por_origen`, `record_por_origen_brazos` (+ `tests/test_record_por_origen`) | el récord por origen entre gobiernos: persiste pero no mejora el motor |
| **P0 — backtest de la cadena v1** (ADR-0012) | `modelo/ensemble/src/backtest_cadena` (+ test) | el backtest de la formulación v1, neutralizado desde el 22-08 |
| **P0 — documentos** | `coordinacion/CONECTAR-GIT.md`, `coordinacion/DECISIONES/0009-BORRADOR-…md`, `coordinacion/_wtest` | un instructivo retirado, un borrador ya decidido y un archivo vacío |

Los **JSON de resultados** de estos scripts **no se movieron**: siguen en `evaluacion/baseline/outputs/` y
`modelo/ensemble/outputs/` porque los ADR los citan como evidencia.

## Lo que NO se movió, y por qué (excepciones del pre-registro de A7)

1. **`evaluacion/baseline/src/fase1_rec_por_tema.py` (+ `tests/test_fase1_rec_por_tema.py`)**: figuraba en P1
   con «nadie los importa», pero `medir_record_por_tema_limpio.py` —la medición limpia de ADR-0034, cuyo resultado
   cita `coordinacion/QUE-SE-MIDE.md`— importa `K_SHRINK` y `_areas_de` de él.
2. **Los stubs «dados de baja» de `modelo/ensemble/src/ensemble.py`**: figuraban en P0, pero no son código
   muerto sino una trampa deliberada (el archivo dice «no se borraron a propósito»: quien llame a la API de la v1
   recibe un `SystemExit` con el motivo y a dónde ir) y `test_ensemble.py` la fija. Sacarlos ahorra ~40 líneas y
   exige tocar un archivo del motor. Queda para que lo decida Franco.

## Dónde quedó lo que el informe pedía «rescatar» (P1)

- **Bootstrap por ley:** vive, activo, en `evaluacion/baseline/src/censo_estadisticos.py`
  (`skill_ic_desde_sumas`, `dif_brier_ic_desde_sumas`), desde el ítem A2.
- **`split_half`** (confiabilidad por mitades dentro de una era): hay dos versiones, archivadas —
  `evaluacion/baseline/src/record_por_origen.py.archivado` (`def split_half`, línea 404; y el `bootstrap` sobre un
  `Panel`, línea 343) y `evaluacion/baseline/src/firma_tematica_fase1_2.py.archivado` (`def split_half`, línea 246)—.
  No se agregó código a módulos vivos (regla 3 de la auditoría); si la fase D lo necesita, se restaura de acá.
