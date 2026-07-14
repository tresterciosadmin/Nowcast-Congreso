# Mejoras y pendientes — agente de taxonomías

> Backlog del módulo. Cada mejora: **problema → propuesta → decisiones abiertas → dependencias**.
> Al implementar una, registrar en `coordinacion/ESTADO-DEL-PROYECTO.md` y (si toca contrato
> compartido como `docs/schemas`) abrir un ADR.

---

## M1 — Cola de revisión + tablero de curación semanal de taxonomías

**Estado:** PROPUESTA (a diseñar/priorizar con el equipo)
**Origen:** decisión 2026-07-14 (Franco). Se aceptó dejar entrar las etiquetas marginales del
agente (no filtrarlas en el momento) y resolverlas después, en equipo.

### Problema
El agente asigna bien lo sustantivo, pero deja **casos que no cierran solos**: etiquetas
secundarias de baja confianza (p. ej. `CULT.DEPORTE` 0.35 por una mención al "turismo social"
en unos fundamentos laborales), proyectos multi-tema ambiguos, `AUX.SINCLASIF`, y **candidatos
de temas nuevos** que el agente propone pero no puede agregar solo. Hoy esa información queda
**dispersa**: las confianzas viven en `proyecto_taxonomias`, los `candidatos_nuevos` solo salen
en el output del agente y no se guardan en ningún lado. Nadie tiene una vista única de "qué
falta decidir", y la decisión humana (que es la que manda) no tiene dónde apoyarse.

### Propuesta
Una **cola de revisión** que junte automáticamente los casos dudosos, y un **tablero
interactivo** que el equipo mira en una **reunión semanal de curación** para cerrar el
etiquetado. Lo que el equipo decide se guarda como `fuente='humano'` (el agente nunca lo pisa)
y el caso sale de la cola. Se registra quién decidió y cuándo, para medir el acuerdo
agente-vs-humano y la calidad del agente en el tiempo.

### Régimen de trabajo (diario → semanal)
El circuito completo, de la carga automática a la decisión humana:

1. **Diario (automático).** El bot de recolección trae los proyectos nuevos a la base
   (`datos/proyectos`) y el agente los cataloga en el momento (batch sobre los faltantes). Cada
   proyecto queda con sus taxonomías del agente y su registro de auditoría (ver abajo).
2. **Clasificación automática.** Si el agente resuelve con confianza (todo por encima de 0.70 y
   sin candidatos ni sin-clasificar), el proyecto queda catalogado y NO va a la cola: entra
   solo. Si tiene dudas (algún criterio de la cola), se marca **pendiente de revisión**.
3. **Semanal (humano).** Una vez por semana el tablero se actualiza con lo acumulado y el equipo
   entra a **terminar de afinar**: revisa los pendientes, decide, y de paso audita lo que el
   agente catalogó solo. Las decisiones quedan como `fuente='humano'`.

Idea de automatización: una tarea programada arma/actualiza el tablero cada lunes antes de la
reunión (los pendientes de la semana + el resumen de actividad del agente).

### Qué entra a la cola (criterios de "necesita ojo humano")
Un proyecto entra si cumple alguno:

1. **Etiqueta marginal:** alguna asignación con confianza en zona gris (**0.30–0.70**).
   Puede sobrar o faltar; la decide una persona. (Por encima de 0.70 se toma como buena y
   entra sola; por debajo de 0.30 se descarta.)
2. **Candidato de tema nuevo:** `candidatos_nuevos` no vacío (el agente vio algo que el
   vocabulario no cubre).
3. **Sin clasificar:** se asignó `AUX.SINCLASIF`.
4. **Multi-etiqueta débil:** ninguna asignación fuerte (máxima confianza por debajo del umbral).
5. **Desacuerdo agente-vs-humano:** cuando ya existe una etiqueta humana previa distinta a la
   del agente (para auditar).
6. **(opcional, arranque) Leído por visión:** proyectos escaneados clasificados por la ruta
   `pdf_documento`, para auditar el "OCR del modelo" hasta que haya confianza en ella.

Umbrales configurables (no hardcodear); arrancar con **0.30 / 0.70** y ajustar con datos.

### Qué muestra el tablero (por caso)
Denominador, cámara, sumario, **link al PDF**, etiquetas del agente **con su confianza**
(resaltando las marginales), candidatos propuestos, el comentario del agente y —si existe— la
etiqueta humana previa. Ordenable por motivo de entrada y por fecha de ingreso del proyecto.

### Acciones del equipo (escriben decisión)
- **Confirmar** una etiqueta del agente (pasa a `humano`).
- **Quitar** una etiqueta que no corresponde.
- **Agregar** una etiqueta del vocabulario controlado.
- **Aceptar un candidato** como tema nuevo → dispara el flujo de edición de `taxonomias.json`
  (contrato compartido: versionado + aviso en TABLERO, ver `docs/taxonomias/TAXONOMIAS.md`;
  probablemente ADR).
- **Marcar resuelto** → sale de la cola; queda registro de quién/cuándo.

### Panel de auditoría / control (qué hizo el agente y con qué criterio)
El tablero no es solo la cola de dudas: tiene que dar **control total sobre la actividad del
agente**, para poder auditar qué catalogó, qué rechazó y por qué. Dos vistas:

- **Vista A — Cola de revisión:** los pendientes que necesitan decisión humana (lo de arriba).
- **Vista B — Registro de actividad (auditoría):** TODO lo que hizo el agente, filtrable por
  día/cámara/tema. Por proyecto debe poder verse:
  - **Catalogado automático:** entró solo (todo > 0.70), con sus etiquetas y confianzas.
  - **En cola:** con el **motivo** por el que entró (marginal / candidato / sin-clasificar /
    multi-débil / desacuerdo).
  - **Sin clasificar:** quedó en `AUX.SINCLASIF`.
  - **Ids inventados descartados:** qué ids propuso el modelo que NO existen en el vocabulario y
    el validador tiró (hoy en `res.descartadas`, no se persiste — hay que guardarlo).
  - **Candidatos de tema propuestos:** los `candidatos_nuevos` (hoy no se persisten).
  - **Leído por visión:** si fue PDF escaneado (`via='pdf_documento'`) y con qué modelo.
  - **No clasificado / error:** escaneados sin datos, PDFs rotos, fallos de descarga.
- **Resumen agregado:** cuántos por día, distribución de confianza, % que entra solo vs. a
  cola, top temas asignados, tasa de sin-clasificar, cantidad de candidatos propuestos. Es el
  pulso para saber si el agente está afinando bien o se está desviando.

### Cadencia
Reunión **semanal** de curación; el tablero es el insumo (Vista A para decidir, Vista B para
auditar). Ideal: una tarea programada que cada lunes actualice ambas vistas antes de la reunión.

### Decisiones técnicas abiertas (a resolver antes de construir)
1. **Persistencia del estado de revisión.** Hoy `proyecto_taxonomias` no tiene "estado" ni
   guarda `candidatos_nuevos`. Dos opciones:
   - (a) **Tocar el schema** (→ ADR): tabla `proyecto_revision` (denominador, motivo, estado,
     resuelto_por, resuelto_en) y un lugar para los candidatos (tabla `taxonomia_candidatos`
     o campo). Más limpio y consultable.
   - (b) **Sin tocar el schema:** derivar la cola al vuelo desde `proyecto_taxonomias`
     (confianza + `AUX.SINCLASIF`) y guardar los candidatos en un archivo aparte. Más rápido
     de arrancar, menos robusto.
2. **Prerequisito: persistir el registro de cada corrida (para la Vista B de auditoría).** Hoy
   solo se guardan las asignaciones en `proyecto_taxonomias`; se PIERDEN los datos que la
   auditoría necesita: `candidatos_nuevos`, `descartadas` (ids inventados), `via` (texto vs.
   visión), `modelo`, `comentario`, motivo de entrada a la cola y timestamp. Hay que guardar un
   **log por proyecto/corrida** (tabla `taxonomia_log` o similar). Es lo primero a implementar,
   es pequeño, y sin esto no hay control de "qué hizo y con qué criterio".
3. **Dónde vive el tablero.** Candidatos: **Streamlit** en `producto/dashboard` (hay skill
   `ui-ux-web-moderno` para el diseño) o un **artifact HTML** interactivo. Empezar read-only
   (solo mostrar la cola) y después habilitar la escritura de decisiones a la base.
4. **Umbrales** de confianza configurables (env o config), no fijos en código.

### Dependencias y encaje
- **Alimenta** el "Perfil temático por legislador" (hoja PorTema) y todo lo que use taxonomías:
  mejor curaduría → mejores features (ver `PLAN-DE-TRABAJO.md` 1B.3).
- **Se apoya** en el set de referencia `outputs/muestra_manual_taxonomias.csv` para medir
  acuerdo agente-vs-humano.
- **Encaja** en `producto/dashboard` (Fase 3) pero como **herramienta interna de datos**, no el
  tablero comercial: conviene un sub-tablero o vista aparte. Reclamar el módulo en `TABLERO.md`
  antes de construir.
