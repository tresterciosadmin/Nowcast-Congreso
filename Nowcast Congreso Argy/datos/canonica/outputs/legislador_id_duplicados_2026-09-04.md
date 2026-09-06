# Censo de `legislador_id` duplicados — 2026-09-04

**Qué es.** La misma persona con **dos `legislador_id`** distintos en la canónica. La tabla
completa está en `legislador_id_duplicados_2026-09-04.csv` (153 pares). **No se mergeó
nada:** esto es el diagnóstico para que Franco decida par por par.

## Cómo se detectó, y cuál es el test que no falla

`_leg_id()` hashea `_name_key()`, que es **el conjunto ordenado de tokens del nombre**. Dos
fuentes que escriben "ROSSI Agustín" y "Rossi, Agustin Oscar" producen conjuntos distintos
—`{AGUSTIN, ROSSI}` vs `{AGUSTIN, OSCAR, ROSSI}`— y por lo tanto **dos ids**. El
duplicado nace de un segundo nombre presente en una fuente y ausente en la otra.

Por eso el candidato es: **un conjunto de tokens estrictamente contenido en el otro**, con
al menos 2 tokens en común. Eso da 155 pares sobre 30.319 candidatos.

**Y después el test decisivo, que es el único que no admite discusión:**

> **Si los dos ids votaron en la misma acta, son personas distintas.** Nadie vota dos veces.

De los 155, **2 quedan descartados por ahí** y son buenos controles de que el test funciona:

| par | actas juntas | qué son |
|---|---:|---|
| `Balestrini, Miguel Alberto` vs `Balestrini, Alberto` | 14 | dos personas |
| `Herrera, Alberto` vs `Herrera, José Alberto` | 275 | dos personas |

Quedan **153 pares** que nunca coincidieron en una votación.

## Cómo leer los tres veredictos

| veredicto | pares | qué significa |
|---|---:|---|
| **MISMA PERSONA** | **99** | mismo distrito normalizado. Es lo más cerca de "seguro" que se puede estar sin abrir la ficha. |
| REVISAR (sin distrito) | 45 | una de las dos filas no trae distrito, o lo trae como código numérico (`71`, `49`). No se puede decidir con lo que hay. |
| REVISAR (cambio de distrito?) | 9 | distritos distintos. **Ojo: acá el distrito NO decide.** Santilli (CABA → Buenos Aires), Massot (Córdoba → Buenos Aires) y Scioli son cambios reales de distrito de la misma persona; Marino (Juan, dip. Buenos Aires vs Juan Carlos, sen. La Pampa) sí son dos. Hay que mirar uno por uno. |

**El distrito es una pista, no una prueba.** Un legislador cambia de distrito y de cámara, y
algunas filas traen el distrito como número. El único criterio duro sigue siendo el de las
actas compartidas, y ese ya se aplicó a los 155.

## El tamaño del problema

- **196 ids** involucrados en los 99 pares de alta confianza: el **8,5%** de los 2.302 ids con votos.
- **74.626 votos** bajo esos ids: el **7,3%** de la canónica.
- El id **menor** de cada par tiene una mediana de **169 votos** — o sea que en el caso típico
  no es una esquirla: es media carrera partida al medio.
- En **57 de los 99** pares el id menor tiene ≥100 votos. Sólo en 2 tiene menos de 8.

## Por qué esto no es cosmético — y por qué toca el motor

El récord individual sale de `expanding()` sobre el historial de **un `legislador_id`**, y de
ahí sale el **98% de las predicciones** (censo del 03-09). Partir a una persona en dos ids
hace tres cosas, todas malas:

1. **Le corta el historial en dos**, así que cada mitad acumula menos y llega más tarde a
   `MIN_HIST_INDIVIDUAL = 8`.
2. **Manda a la rama de bloque** a quien debería tener récord propio — y esa rama tiene
   skill **−0,059** (URGENTE 9).
3. **Rompe cualquier cruce por id**, que es exactamente lo que pasó con el roster de jefes:
   ROSSI y STOLBIZER quedaron sin `legislador_id` explícito el 04-09 **por este motivo**.

Los tres que trancan el roster están en el censo:

| roster | par | veredicto |
|---|---|---|
| ROSSI, AGUSTIN | `leg:3a122de91183` + `leg:3cc84340cad1` | MISMA PERSONA |
| STOLBIZER, MARGARITA | `leg:9c9abb302e88` + `leg:b067aa2a9852` | MISMA PERSONA |
| ROYÓN, FLAVIA | `leg:97bbbf7cc358` + `leg:c4eabf6d9ca4` | REVISAR (sin distrito) |

## Lo que NO se hizo, y por qué

**No se mergeó ningún id.** Un merge reescribe `legislador_id` en la canónica, y eso mueve
el récord individual del 7,3% de los votos — o sea que **mueve el número publicado**. Va con
decisión de Franco y con su medición antes/después (el mismo baseline, mirando `por_era` y
el reparto entre rama individual y rama de bloque).

**Cómo se aplicaría, cuando se decida:** una tabla de alias `id_viejo → id_canonico` en
`datos/canonica`, aplicada en `entity_resolution`, con el id de MÁS votos como canónico. No
tocar `_name_key`: cambiarlo re-hashea **todos** los ids del repo.
