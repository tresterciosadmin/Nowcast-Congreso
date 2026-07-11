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

## Validación manual del vocabulario (2026-07-11)
Muestra estratificada de 88 actas de la canónica clasificada a mano contra los 74 ids:
82% clasificable por título, 89% con confianza alta/media, 22% multi-etiqueta.
Resultados y huecos/fronteras propuestos en `RESULTADOS-muestra-manual.md`;
datos en `outputs/muestra_manual_taxonomias.csv` (queda como set de referencia para
medir el acuerdo agente-vs-humano cuando corra el batch).

## Ingesta ICG Di Tella — `src/ingesta_icg.py` (familia E del feature store)
Serie mensual del Índice de Confianza en el Gobierno (UTDT, escala 0-5, nov-2001→hoy).
No hay API: el script scrapea la página oficial de descarga (el `fname` del Excel rota
cada mes) y normaliza a `data/icg_mensual.csv` (contrato: fecha/anio/mes/icg). Fallback:
microdatos `.dta` espejados en GitHub (PoliticaArgentina/data_warehouse, vía `opinAr`).
- **Correr (local):** `python src/ingesta_icg.py` — imprime los últimos 12 meses para
  validar a ojo contra los informes de UTDT.
- **Actualización mensual liviana:** `python src/ingesta_icg.py ultimo` — scrapea la
  página de INFORMES (que publica el mes nuevo ANTES de que rote el Excel: "El ICG de
  junio fue de 2,07 puntos") y AGREGA al CSV solo los meses que falten. No pisa valores
  existentes (el Excel es más preciso; el informe redondea a 2 decimales). Idempotente:
  correrlo dos veces no duplica. Es la pieza que el bot de recolección puede invocar
  cada mes (UTDT publica según su cronograma, ~mitad de mes).
- **Test sin red:** `python tests/test_ingesta_icg.py` (21 chequeos: layouts del Excel
  incl. el transpuesto real de UTDT + scraper de informes con ambas redacciones +
  merge idempotente).
- **Cita:** Índice de Confianza en el Gobierno. Escuela de Gobierno. UTDT. https://www.utdt.edu/icg

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
