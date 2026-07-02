# Módulo: modelo/voto_individual

**Propósito.** Reformulado por **ADR-0003** (2026-07-01): NO predecir el voto medio (eso lo resuelve la regla de bloque ~0,99, benchmark que queda fijo), sino modelar el **desvío del legislador respecto de su bloque** y detectar **pivotes**. Cuatro piezas: (a) índice de disciplina individual, (b) modelo de defección, (c) recuento como distribución, (d) detección de pivotes.

> **Contexto (aclaración 2026-07-01):** este módulo es UNA pieza del análisis individual, no el todo. La **base de datos individual de legisladores** (la ficha completa por diputado/senador) vive en `variables/legislador` y consume la salida de acá como una columna más. Los díscolos fueron el ejemplo que motivó el análisis individual, no su único objetivo.

**Unidad de análisis temporal: el período parlamentario** (entre recambios del 10 de diciembre de años impares). Cada recambio —incluso con reelección— reconfigura los escaños y cambia la disciplina; el desvío se mide por período además de global.

**Definición vigente del desvío: v2 (ADR-0004).** Tres conductas (aprobar / rechazar / no acompañar = abstenerse o ausentarse); línea del bloque = mayoría simple sobre TODOS sus escaños (bottom-up); desvío = conducta ≠ línea, estricta; empates → desempate por linaje real, y desvío parcial en OTRO/PROVINCIAL; presidentes de Diputados excluidos. El índice mide **indisciplina total**, no solo voto cruzado.

**Estado:** EN CURSO — pieza (a) implementada; gate 1 APROBADO sobre base completa (ver `RESULTADOS.md`)
**Owner actual:** Claude+Valle (desde 2026-07-01)

## Contrato
- **Entradas:** `datos/canonica/data/clean/{votos_resuelto,actas_canonico}.parquet`
- **Salida (contrato estable):** en `outputs/`:
  - `disciplina_individual.csv` — índice por legislador (tasas global / disputadas / tramo reciente)
  - `disciplina_por_periodo.csv` — legislador × período parlamentario × cámara (la unidad de análisis)
  - `disciplina_por_anio.csv` — legislador × año
  - `desvios_por_voto.parquet` — una fila por VOTO (conducta, línea, método, desvío): contrato para la columna `desvio` de datos/export
  - `set_pivote.json` — dimensionamiento del set pivote (gate 1)
- **Depende de:** datos/canonica (+ variables/legislador y variables/bloque cuando existan)
- **Gate de pase:** (1) set pivote dimensionado ✅ APROBADO (2) recuento-como-distribución calibra mejor que el punto en disputadas (pendiente)

## Cómo correr
```bash
python modelo/voto_individual/src/disciplina.py          # usa datos/canonica/data/clean
CANON=/otra/ruta MIN_VOTOS=50 python modelo/voto_individual/src/disciplina.py
python modelo/voto_individual/tests/test_disciplina.py   # tests sin red (12 chequeos)
```

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/voto-individual-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista. La definición de `periodo_parlamentario()` está duplicada y sincronizada con `variables/legislador/src/ficha.py` (unificar cuando exista `datos/_common`).
