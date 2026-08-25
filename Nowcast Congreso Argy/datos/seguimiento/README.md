# Módulo: datos/seguimiento

<!-- huella: e3b0c44298fc -->

**Propósito.** Dado un expediente **ya conocido**, bajar su ficha oficial y extraer el **estado de avance**: giros a comisiones, movimientos de trámite, fechas y link al PDF. Es el insumo del **embudo** (`variables/embudo`): "qué entró y en qué quedó". No descubre proyectos nuevos (eso es `datos/expedientes` / el monitor); acá se hace el **seguimiento** de los que ya están en la base.

**Estado:** EN CURSO (primer extractor de giros, ambas cámaras, validado contra fixtures).

**Resumen:** Dado un expediente ya conocido, baja su ficha oficial y extrae el estado de avance: giros, movimientos, fechas y PDF. Insumo del embudo. NO descubre proyectos nuevos.

## Buscar acá si

- en que etapa esta un expediente concreto
- giros a comision o movimientos de tramite de un proyecto
- el PDF del texto de un proyecto

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entrada:**
  - Diputados: `expediente` (`NNNN-D-AAAA`) + `slug` del diputado autor (ej. `sajmechet`). El slug se guarda en el dataset de parlamentarios.
  - Senado: `nro` + `anio` (ej. 1091, 2026). No necesita slug.
- **Salida:** objeto `FichaExpediente` (dataclass, serializable a JSON) con:
  `expediente` (denominador canónico NNNN-X-AAAA), `camara`, `url`, `sumario`,
  `fecha_ingreso`, `firmantes[]`, `giros[]` (comisión, orden, competencia primaria,
  fecha ingreso/egreso), `tramite[]`, `pdf_url`, `estado` (derivado), `fuente_ok`,
  `capturado_en`.
- **Correr (test en vivo, en PC con internet):**
  - `python src/giros.py diputados 2832-D-2026 sajmechet`
  - `python src/giros.py senado 1091 2026`
- **Test sin red:** `python tests/test_giros.py`

## Fuentes (verificadas jun-2026)
- **Diputados** — página del autor: `hcdn.gov.ar/diputados/<slug>/proyecto.html?exp=<exp>`.
  Trae firmantes (con distrito y bloque), giro a comisiones (marca "Primera Competencia")
  y tabla de trámite. **Requiere el slug del autor**; si el autor deja la banca la URL
  puede caerse → plan B pendiente (ficha genérica del expediente).
- **Senado** — ficha del expediente: `senado.gob.ar/parlamentario/comisiones/verExp/<NRO>.<AA>/S/PL`.
  Más completa y sin slug: autor, fechas de mesa de entradas, giros con **fecha de
  ingreso/egreso y orden de giro**, y link al PDF (`/downloadPdf`).

## Diseño
- Parsing **defensivo por firma de encabezados**: las tablas se clasifican por sus
  columnas (no por posición), así sobrevive a cambios de layout. Campos ausentes → `None`.
- Resiliencia: reintentos con backoff (tenacity), errores HTTP específicos, logging.
- El **denominador** es la clave primaria del proyecto: se normaliza siempre a `NNNN-X-AAAA`
  (Senado: `1091/26` → `1091-S-2026`).
- `estado` es derivado best-effort (ingresado / en_comision / con_dictamen / media_sancion /
  sancionado / rechazado); se afinará al definir el embudo.

## Pendiente
- Validar selectores **en vivo** en PC con internet (el sandbox no llega a las webs del Congreso).
- Diputados: plan B cuando el slug del autor no resuelve.
- Persistencia: hoy devuelve objetos; la carga a la **base de Proyectos** es el próximo paso (otro módulo).
- Trámite del Senado más allá de giros (media sanción / sanción) cuando aparezca en fichas avanzadas.
