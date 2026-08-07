# ADR-0009 (BORRADOR) — Dónde aterrizan los proyectos que junta el bot

**Fecha:** 2026-08-07 · **Estado:** 🟡 BORRADOR — **esperando la decisión de Valle**
**Decisor:** Valle · **Registra:** Claude
**Origen:** `URGENTE.md` ítem 1 — el bot recolecta proyectos y ningún módulo los carga.

---

## El problema, en una frase

El bot recolecta bien y **no entrega**. Escribe sus parquet, los commitea, y ahí quedan:
ningún script fuera de su propio módulo los lee. La base que mira el embudo se quedó en
**el 2 de junio**.

## Los números, medidos en disco hoy (07-08-2026)

> ⚠️ No son los de ayer. El bot siguió corriendo, así que el hueco **creció**.

| Base | Filas | Cubre hasta |
|---|---:|---|
| `datos/expedientes/…/expedientes.parquet` — **lo que lee el embudo** | 112.793 | **2026-06-02** |
| `datos/bot_recoleccion/…/tp_entradas.parquet` (Diputados) | 2.826 | 2026-08-05 |
| `datos/bot_recoleccion/…/dae_entradas.parquet` (Senado) | 1.007 | 2026-07-20 |
| `datos/proyectos/data/proyectos.db` — **el destino previsto** | **no existe** | — |

**El hueco real, desagregado** (esto no estaba medido y cambia la prioridad):

| | cantidad |
|---|---:|
| Proyectos del TP que faltan en `expedientes` | **914** (ayer eran 861) |
| …de los cuales son **DE LEY** (lo único que mira el embudo) | **283** |
| …el resto: resoluciones (1.289 en total) y declaraciones (462) | el embudo los filtra igual |
| Proyectos del TP **con cofirmantes** (>1 firmante) | **1.016 de 2.826** |
| Proyectos de ley del Senado en el DAE (sufijo `-PL`) | **520** |

### 🔴 El hallazgo que más pesa, y es nuevo

`expedientes.parquet` tiene **110.794 filas de Diputados y sólo 1.999 del Senado.**
El universo de proyectos del Senado en la base del embudo es, prácticamente, **inexistente**.

El DAE del bot trae **520 proyectos de ley del Senado**. Enchufarlos no agrega un 0,5% al
universo: agrega **un 26% al universo del Senado entero**. Para la cámara donde el nowcast
más viene sufriendo (bloque, linaje, atribución), ésta es la corrección de cobertura más
grande disponible hoy.

---

## Por qué hay que decidir algo (y no simplemente "hacerlo")

Hay **dos contratos vivos que describen la misma cosa de dos maneras incompatibles**, y el
bot está en el medio sin saber a cuál servir.

| | `datos/expedientes` (parquet) | `datos/proyectos` (SQLite) |
|---|---|---|
| **Clave** | `proyecto_id` = `HCDN292367` (id interno de CKAN) | `denominador` = `2595-D-2026` (expediente oficial) |
| **Forma** | 6 parquet planos que se cruzan por `proyecto_id` | 5 tablas relacionales con FK |
| **Autoría** | **una** columna `autor` (texto: primer firmante) | tabla `proyecto_autores` con orden, bloque y distrito |
| **Giros** | `expedientes_giros`: proyecto → comisión | tabla con orden, competencia primaria, fecha entrada/salida |
| **Taxonomías** | no existen | tabla `proyecto_taxonomias`, con `fuente` y `confianza` |
| **Estado** | en producción, lo lee el embudo | **vacío: nunca se creó** |
| **Origen** | backfill de CKAN | diseñado el 29-jun para el scrape ficha por ficha |

El bot produce datos con **la forma de `proyectos.db`** (firmantes múltiples, giros
ordenados, trámite) y el modelo consume datos con **la forma de `expedientes`**. Elegir es
elegir dónde poner el traductor — y esa elección es difícil de revertir, porque el embudo
es el módulo del que cuelga todo el nowcast.

---

# Opción A — `datos/expedientes` absorbe lo del bot

Un paso nuevo convierte `tp_entradas` / `dae_entradas` al formato de los parquet que ya
existen y los **anexa**, generando un `proyecto_id` sintético para lo que CKAN todavía no
publicó (p. ej. `BOT-2595-D-2026`, reemplazable cuando CKAN lo publique).

**Qué cambia para el resto del proyecto:** nada. El embudo no se entera.

### A favor

- **El embudo no se toca.** El contrato que consume queda idéntico; el módulo sigue siendo
  de su dueño y no hay coordinación entre dos personas.
- **Es la ruta corta al resultado visible:** el modelo vuelve a ver los últimos dos meses, y
  entran los 520 proyectos de ley del Senado.
- **Reversible.** Si sale mal, se borran las filas con `proyecto_id` que empieza con `BOT-`
  y todo vuelve al estado anterior. Ninguna otra opción tiene esta propiedad.
- **Se apoya en algo ya probado:** Franco acaba de hacer exactamente este movimiento con
  `giros_iniciales.parquet` — parquet nuevo, hook opcional, contrato intacto, y funcionó.

### En contra

- **No resuelve las taxonomías.** `expedientes` no tiene dónde guardarlas. El blocker que
  arrastran varios documentos sigue en pie.
- **Pierde los cofirmantes en el camino.** La columna `autor` es una sola; los 1.016
  proyectos con más de un firmante entran achatados al primer firmante. *(Mitigable con un
  parquet lateral `expedientes_autores.parquet`, pero eso ya es empezar a construir el
  esquema relacional del otro lado — o sea, la Opción B por goteo.)*
- **`proyectos.db` queda muerto.** `store.py`, `schema.sql` y sus tests siguen ahí sin uso:
  código sin dueño que el próximo que pase va a creer vivo.
- **Deuda de identidad.** Convivirían dos claves para el mismo proyecto (`HCDN292367` y
  `BOT-2595-D-2026`) hasta que CKAN publique, con riesgo de contar dos veces si la
  deduplicación falla. Es el riesgo técnico principal de esta opción.

---

# Opción B — `proyectos.db` es la fuente de verdad y el embudo pasa a leerla

Se crea la base con `store.py init`, se escribe el upsert desde el bot, se migran los
112.793 de CKAN, y `cargar()` del embudo pasa a leer de SQLite.

### A favor

- **Es el diseño que el proyecto ya eligió** cuando escribió `schema.sql` en junio. Modela
  bien lo que el bot trae: autores con orden y bloque, giros con competencia primaria,
  trámite completo.
- **Desbloquea las taxonomías de verdad.** La tabla `proyecto_taxonomias` existe, con
  `fuente` (agente/humano) y `confianza`. Es la única opción que cierra ese pendiente.
- **Los cofirmantes entran enteros**, que era la razón de construir el scraper del TP.
- **Una sola clave** (`denominador`, el expediente oficial), que es además la que usan las
  fuentes oficiales y los informes.
- **Deja de haber dos bases de proyectos.** Hoy el proyecto tiene dos y ninguna completa.

### En contra

- **Toca el módulo del embudo, que es el más caliente del repo.** Y lo toca de verdad:
  `cargar()` y `construir_cohorte()` están escritos alrededor de 6 DataFrames cruzados por
  `proyecto_id`. No es cambiar la ruta de lectura, es reescribir cómo se arma la cohorte.
- **Riesgo de romper el skill sin darse cuenta.** El número que ordena todo hoy es
  **0,3647**. Cualquier diferencia de conteo en la migración (un giro duplicado, un tipo mal
  mapeado) lo mueve, y no habría forma de saber si mejoró el modelo o se rompió la carga.
  **Mitigación obligatoria: correr las dos rutas en paralelo y exigir el mismo skill al
  cuarto decimal antes de apagar la vieja.**
- **Necesita coordinación entre dos módulos con dueños distintos** (`variables/embudo` es de
  Valle, `datos/expedientes` es de Claude+Franco). Es exactamente el caso que la regla "un
  módulo, un dueño" está pensada para evitar.
- **El Senado no cruza solo.** El DAE trae `S-2/26-PD` y `expedientes` trae `4014-S-2013`:
  formatos distintos. Hay que escribir y validar la normalización — trabajo real, no
  trivial, y con posibilidad de falsos positivos.
- **Es la ruta larga.** El modelo sigue ciego mientras dura.

---

# Opción C — las dos, en ese orden *(la que yo recomendaría)*

No son excluyentes en el tiempo, y el orden importa.

1. **Ahora: la Opción A**, acotada a lo que mueve el nowcast (los 283 proyectos de ley del
   TP + los 520 del Senado). El modelo deja de estar ciego esta semana, con un cambio
   reversible que no toca el embudo.
2. **Después: la Opción B**, con `proyectos.db` naciendo como la base **completa** —
   incluidos los cofirmantes y las taxonomías — y el embudo migrando recién cuando la
   corrida en paralelo dé el mismo skill.

**Por qué en este orden y no al revés:** hoy no hay ningún proyecto de ley reciente
cargado, así que *cualquier* mejora de esquema se estaría diseñando sin poder probarla
contra el caso que importa. La Opción A produce el dato con el que después se valida la
Opción B.

**El riesgo de esta ruta, dicho sin adornos:** que el paso 2 no llegue nunca. Con el modelo
ya funcionando, el incentivo para migrar se evapora y `proyectos.db` queda como una decisión
de junio que nadie ejecutó. **Si elegís C, conviene que el paso 2 entre al TABLERO con
fecha en el mismo PR que el paso 1** — si no, esto se convierte en la Opción A con una
promesa.

---

## Lo que hay que decidir

1. **¿A, B o C?**
2. Si es A o C: ¿los cofirmantes entran ya como parquet lateral, o se aceptan achatados al
   primer firmante hasta el paso 2?
3. ¿El Senado entra en esta tanda? *(Es el mayor rendimiento por unidad de trabajo — +26%
   del universo del Senado — pero es también la parte con más riesgo de matching.)*

## Independientemente de lo que se elija

Estos dos no dependen de la decisión y conviene hacerlos igual:

- **`git pull --rebase` en el push de los workflows** (ya anotado el 06-08).
- **Subir `checkout@v4` → `v5` y `setup-python@v5` → `v6`** (URGENTE ítem 3): cuando GitHub
  corte Node 20, **fallan los tres workflows a la vez** y el bot deja de recolectar. Sería
  irónico resolver la entrega justo cuando se rompe la recolección.
