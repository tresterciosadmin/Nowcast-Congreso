# Módulo: producto/dashboard

**Propósito.** Tablero interno: radar de tracción + mapa de pivotes + escenarios. Encuadre augmentation.

**Estado:** EN CURSO — v1 entregada como **paneles HTML en la raíz del repo**, no como
app. Corregido el 2026-08-06: figuraba "PENDIENTE / vacante" cuando ya había cinco
paneles construidos.
**Owner actual:** Claude+Valle (desde 2026-07-10)

## Lo que ya existe (todo en la raíz, doble clic, sin internet)

| Archivo | Qué muestra | Desde |
|---|---|---|
| `PANEL-NOWCAST.html` | simulador de una votación (motor JS) | 2026-07-11 |
| `PANEL-MOVIL.html` | coyuntura en el teléfono: 12 proyectos recalculados en vivo sobre los 257 diputados reales | 2026-08-04 |
| `PANEL-COYUNTURA.html` | lo mismo para escritorio, con más detalle | 2026-08-04 |
| `COMPARADOR-ICG.html` | las dos vías del ICG + las 4 preguntas abiertas, para decidir en equipo | 2026-08-04 |
| `TABLERO-CONTROL.html` | mapa ejecutivo (se alimenta de `tablero_datos.js`; **no se edita el HTML**) | 2026-07-02 |

**Decisión de forma (no escrita hasta hoy):** se eligió HTML autocontenido en vez de
Streamlit porque el equipo lo abre con doble clic, sin instalar nada y sin internet.
El costo es que la lógica del motor está duplicada en JS. Si el dashboard pasa a ser
producto, esa duplicación es lo primero a resolver.

**Requisito operativo (ADR-0008):** ningún nowcast se publica sin evaluación de
coyuntura registrada. Se genera en `PANEL-COYUNTURA.html` / `PANEL-MOVIL.html`.

## Contrato
- **Entradas:** modelo/ensemble, variables/embudo, variables/proyecto (ICG)
- **Salida (contrato estable):** paneles HTML autocontenidos en la raíz
- **Depende de:** modelo/ensemble
- **Gate de pase:** Una consultora valida utilidad en entrevista — **sin cumplir**

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/dashboard-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
