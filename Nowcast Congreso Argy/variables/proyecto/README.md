# Módulo: variables/proyecto

**Propósito.** Features por proyecto: tema/materia, autor, cámara de origen, tipo de mayoría requerida, parsing de texto (NLP).

**Estado:** EN CURSO
**Owner actual:** Valle (con Claude)

## Agente de taxonomías (LLM) — `src/agente_taxonomias.py` + `src/pdf_text.py`
Clasifica un proyecto leyendo su PDF y asignándole taxonomías del vocabulario controlado
(`docs/taxonomias/`). Motor: **Claude API** (LLM).

- **Flujo:** `pdf_text` baja el PDF (de `pdf_url`) y extrae texto → `agente_taxonomias`
  arma el prompt con la lista controlada, llama al LLM, valida que los ids existan
  (descarta inventados), y escribe en `datos/proyectos` → `proyecto_taxonomias`.
- **El humano gana:** el agente nunca pisa una taxonomía cargada a mano (fuente `humano`).
- **Escaneados:** si el PDF no tiene texto (es imagen), se marca y se saltea (OCR pendiente).
- **Config:** `ANTHROPIC_API_KEY` (obligatoria en vivo) y `TAXO_MODEL` (default `claude-haiku-4-5-20251001`;
  la tarea es acotada y validamos los ids, así que Haiku alcanza y es barato. Subí a Sonnet si algún caso ambiguo lo amerita).
- **Correr:**
  ```bash
  pip install -r src/requirements.txt
  setx ANTHROPIC_API_KEY "sk-ant-..."   # (en PowerShell; reabrí la terminal)
  python src/agente_taxonomias.py probar https://www.hcdn.gob.ar/.../documento.pdf
  python src/agente_taxonomias.py clasificar ..\..\datos\proyectos\data\proyectos.db 1091-S-2026
  ```
- **Test sin red:** `python tests/test_agente.py` (LLM falso inyectado; valida prompt,
  parseo/validación, persistencia humano-gana y detección de escaneado).
- **Pendiente:** OCR para PDFs escaneados; clasificar la historia vía `datos/expedientes`;
  el viejo `classify_tema_v1.py` (keywords) queda como fallback/baseline.

## Contrato
- **Entradas:** datos/expedientes, cabecera
- **Salida (contrato estable):** feature store proyecto (parquet, una fila por proyecto)
- **Depende de:** datos/expedientes
- **Gate de pase:** Tema asignado y validado en muestra etiquetada

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/proyecto-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.

## Nota (2026-06-25): clasificación por TEMA — prioridad confirmada
El usuario confirmó que hay que **separar/clasificar por tema del proyecto** (materia del expediente: económico, penal, laboral, salud, etc.). Es una feature central de este módulo: a partir del `titulo`/texto del expediente, asignar una taxonomía de temas (reglas + NLP), validada en una muestra etiquetada. Habilita análisis y modelos por materia.
