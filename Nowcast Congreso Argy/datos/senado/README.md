# Módulo: datos/senado

**Propósito.** Ingesta de votaciones nominales del Senado desde la fuente
oficial (senado.gob.ar/votaciones) + reconstrucción del **bloque histórico**
contemporáneo a cada voto. Tapa el hueco **2015–2023** de la canónica.

**Estado:** HECHO (2015–2023 completo; quedan filas `REVISAR` en el padrón manual)
**Owner actual:** Claude+Franco (2026-07-01/02)

## Resultados (corrida 2026-07-02)
- **749 actas / 53.910 votos**, 2015–2023, cámara completa en cada acta
  (71–72 filas, ausentes nominales → insumo directo de asistencia/quórum).
- Validación externa: **43.684 votos cruzados contra nahuelhds, 0 discrepancias**.
- Bloque histórico aplicado: **100% de cobertura, 0 anacronismos**.

## Contrato
- **Entradas:** senado.gob.ar/votaciones/actas (listado por año, form POST),
  senado.gob.ar/votaciones/detalleActa/`<id>` (nominal con bloque/provincia),
  anexos Wikipedia "Senadores nacionales de Argentina (período)" 2017–2025.
- **Salida (contrato estable):** `data/clean/senado_actas.parquet` y
  `data/clean/senado_votos.parquet`, esquema canónico v1,
  `acta_id = "senado:<detalle_id>"`, `fuente = "senado"`.
- **Fuente de verdad versionada:** `data/padron_manual_2015_2017.csv`
  (padrón de bloques curado a mano; excepción explícita en `.gitignore`).
- **Depende de:** docs/schemas.
- **Gate de pase:** mapeo de bloques del Senado resuelto — CUMPLIDO.

## Pipeline (PC con internet; el sandbox no llega a los sitios)
```bash
pip install -r datos/senado/src/requirements.txt
python datos/senado/src/scrape_votaciones.py      # 1. votos 2015-2023 (~20 min 1ª vez; con caché, ~40 s)
python datos/senado/src/bajar_anexos_wiki.py      # 2. anexos Wikipedia (una vez)
python datos/senado/src/padron_bloques.py         # 3. padrón de bloques (no pisa el manual)
python datos/senado/src/aplicar_bloques.py        # 4. bloque contemporáneo -> parquet
```
**El orden importa:** re-correr el paso 1 regenera el parquet con los bloques
anacrónicos del sitio → siempre re-correr el paso 4 después.
Caché HTML en `datos/Archivos_Borrar/` (descartable). Tests offline:
`python datos/senado/tests/test_scrape.py` (29 chequeos).

## Por qué hace falta el padrón (LIMITACIÓN de la fuente oficial)
El detalle del sitio pinta el **último bloque conocido** del senador, no el de
la época (verificado: "FRENTE DE TODOS" en actas de 2018). El PDF oficial del
acta tampoco trae bloque (verificado 2015 y 2023). Por eso el bloque se
reconstruye aparte (decisión 2026-07-01, Franco — merece ADR):
- **2017–2025:** anexos de Wikipedia por período (`padron_bloques_senado.csv`,
  regenerable, NO editar).
- **2015–2017 + correcciones:** `padron_manual_2015_2017.csv` (curado a mano,
  **gana** sobre el automático). Fuentes de la curación: bloque real 2014 de la
  semilla Década Votada (66 filas), período siguiente para bloques estables
  (21), inferencias documentadas (11, casi todas FpV-PJ pre-ruptura dic-2017) y
  correcciones manuales (8: huecos del anexo wiki 2021-23 —Cornejo, Torres,
  Weretilneck, Olalla, Rodríguez—, variante de nombre de Ledesma Abdala,
  Unidad Federal nacido 22/02/2023, sesión preparatoria 09/12/2021).

### PARA EL EQUIPO: revisiones pendientes en el padrón manual
Filas con `REVISAR` en la nota: (a) 11 bloques 2015-2017 inferidos;
(b) sub-bloques FdT 2021-22 de los futuros Unidad Federal (validado por Franco
02-07-2026: Caserio/Perotti FpV-PJ y Catalfamo/Espínola FNyP correctos);
(c) sub-bloque de Rodríguez (TdF) por analogía con Duré.
Editar el CSV directamente; lo curado ahí pisa todo.

### Casos con historia (para no re-tropezar)
- **"FRENTE DE TODOS (CORRIENTES)"** (Roldán, 2015-17): partido correntino
  pre-2019, HOMÓNIMO del FdT nacional. Renombrado para que la resolución de
  entidades de canonica no los funda. El control de anacronismos compara por
  igualdad exacta por esto.
- El anexo Wikipedia 2021-2023 **omite senadores en ejercicio** (verificado
  contra actas oficiales en PDF). No asumir que un anexo es la composición
  completa.

## Notas
- `verActaVotacion/<id>` devuelve el PDF oficial del acta (sin bloque).
- Acta `senado:1119`: los totales publicados por el sitio no cuadran con su
  propia tabla nominal (43≠36); el nominal es lo confiable.
- 2001–2003 no existe como voto nominal (ver `NOTA-2001-2003.md`).
- Plan B del scraper si el form cambiara: `--ids <desde> <hasta>`.
- Pendientes fuera de alcance: sumar la fuente a `run_pipeline.py` (módulo
  canonica), ADR precedencia senado vs. argentinadatos 2024-25, ADR fuente
  Wikipedia.

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/senado-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
