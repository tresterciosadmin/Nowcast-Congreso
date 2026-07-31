# ADR-0007 — Régimen de salida: qué debe responder el modelo ante CADA proyecto nuevo

**Fecha:** 2026-07-31 · **Estado:** ACEPTADO (vigente)
**Decisor:** Franco · **Registra:** Claude
**Ejemplo canónico:** `casos/2026-07-31_ley-de-lobby.md`

---

## Decisión

Ante cada proyecto de ley nuevo, el sistema entrega **dos respuestas, siempre las mismas
dos**:

### 1. ¿Qué probabilidad tiene de sancionarse?
Un número con su contexto: contra la tasa base, contra proyectos comparables, y **por qué**
ese número y no otro (qué rasgos lo suben y cuáles lo bajan).

### 2. ¿A quién hay que afectar?
Los **nombres concretos** de los legisladores que definen su suerte, con la aritmética que
los vuelve pivotes. No "el bloque X": personas, y en qué instancia deciden.

> **Ni una sola sin la otra.** Una probabilidad sin destinatarios es una curiosidad
> estadística; una lista de nombres sin probabilidad es una agenda sin prioridad. El
> producto es la conjunción.

## Estructura del informe

El caso de la Ley de Lobby fija la plantilla. Secciones, en orden:

| # | Sección | Qué responde |
|---|---|---|
| 1 | **Identificación** | expediente, autor, fecha, giro, estado y **días parado** |
| 2 | **Taxonomía** | ids del vocabulario controlado, con el porqué de cada uno. Si es ómnibus, desglose por título (ADR-0006) |
| 3 | **Probabilidad** | P(recinto) y P(sanción) contra tasa base; las causas del desvío; **antecedentes del tema** (¿cuántos proyectos parecidos hubo y cómo terminaron?) |
| 4 | **Escenarios de autoría** | el mismo texto firmado por PE / jefe de bloque / diputado común. Aísla cuánto vale el impulsor |
| 5 | **Pivotes** | composición de las comisiones del giro, cuántas firmas faltan para el dictamen y **quiénes son** |
| 6 | **Lo que el modelo NO puede responder hoy** | obligatorio. Datos faltantes, supuestos, limitaciones conocidas |
| 7 | **Resumen ejecutivo** | un párrafo que se pueda leer solo |

## Reglas de la casa para estos informes

1. **La sección 6 no es opcional.** Un nowcast que no declara sus agujeros es peor que no
   tenerlo, porque se le cree. En el caso de la Ley de Lobby la sección 6 fue lo que
   destapó las 229 actas faltantes.
2. **Nombres, no bloques.** "Falta una firma en Asuntos Constitucionales y Diógenes
   González (UCR) integra y vicepreside las dos comisiones" es accionable. "Hay que
   negociar con el radicalismo" no.
3. **La comisión antes que el recinto.** Los proyectos mueren en comisión, no en votación:
   4 rechazos explícitos en 18 años contra decenas de miles de expedientes en el cajón. El
   análisis de pivotes empieza por el dictamen.
4. **Todo número con su población.** Cohorte madura o completa, n explícito. Mezclarlas
   produce errores silenciosos (pasó en el borrador del primer caso).
5. **Cada corrida se archiva en `casos/`.** Sirve de producto y de test de regresión: si
   mañana el modelo dice otra cosa sobre el mismo proyecto, hay contra qué comparar.

## Consecuencia de diseño ya detectada

El caso de la Ley de Lobby mostró que **la sección 5 (pivotes) es la que más valor tiene y
la que menos depende del modelo estadístico**: sale de la composición de comisiones, que es
un dato público y actual. La sección 3 depende de un modelo con skill 0,36. Conviene que la
arquitectura no ate una a la otra: **el análisis de pivotes debe poder entregarse aunque el
modelo probabilístico esté degradado**, que es exactamente la situación de hoy con las
votaciones desactualizadas.
