# ADR-0009 — `proyectos.db` es la fuente de verdad de los proyectos

**Fecha:** 2026-08-07 · **Estado:** ACEPTADO (vigente)
**Decisor:** Valle · **Registra:** Claude
**Origen:** `URGENTE.md` ítem 1 — el bot recolecta proyectos y ningún módulo los carga.
**Reemplaza:** el borrador de dos opciones del mismo día (`0009-BORRADOR-…`, ya neutralizado).

---

## Decisión

**Opción B, directa.** `datos/proyectos/data/proyectos.db` pasa a ser la fuente de verdad del
universo de proyectos: recibe el backfill de CKAN **y** lo que junta el bot, y
`variables/embudo` lee de ahí. **El Senado entra en esta misma tanda.**

Se descartó la ruta gradual (anexar al parquet ahora y migrar después) por una razón
explícita de Valle: con el modelo ya andando, el incentivo para migrar se evapora y
`proyectos.db` queda como una decisión de junio que nadie ejecuta. **Se paga el costo una vez.**

## Por qué el Senado entra ya

| | filas |
|---|---:|
| `expedientes.parquet`, Diputados | 110.794 |
| `expedientes.parquet`, **Senado** | **1.999** |
| Proyectos de ley del Senado que el bot ya tiene (DAE, sufijo `-PL`) | **520** |

El universo del Senado en la base del embudo es prácticamente inexistente. Los 520 del bot no
son un +0,5% del total: son **+26% del universo senatorial entero**, y en la cámara donde el
nowcast más viene sufriendo (bloque, linaje, atribución de votos recientes).

**Lo que hay que resolver para que entre:** los formatos de expediente no coinciden — el DAE
trae `S-2/26-PL` y `expedientes.parquet` trae `4014-S-2013`. La normalización se escribe y se
valida; no se asume que cruza.

## 🔴 El hallazgo que cambia el plan: los dos contratos NO "se pegan"

`URGENTE.md` decía que esto era *"pegar dos contratos que existen, no diseñar nada nuevo"*.
**Es falso, y conviene que quede escrito antes de que alguien lo intente por ese camino.**

`upsert_proyecto()` **reemplaza las tablas hijas completas** en cada llamada:

```python
con.execute("DELETE FROM proyecto_tramite WHERE denominador = ?", (denom,))
for i, m in enumerate(ficha.get("tramite") or []):   # si la ficha no trae trámite → borra todo
```

Es la semántica correcta para su caso de uso original (un scrape de ficha completa refresca el
estado oficial), pero **hace que cargar dos fuentes con dos upserts sucesivos pierda datos en
cualquier orden**:

| orden | qué se pierde |
|---|---|
| CKAN → bot | el bot no trae `tramite`, así que **borra los dictámenes y movimientos de CKAN** |
| bot → CKAN | CKAN trae un solo `autor`, así que **borra los cofirmantes del bot** — justo el dato por el que se construyó el scraper del TP |

**Consecuencia de diseño:** no hay dos upserts, hay **un merge**. Se arma **una ficha por
denominador** combinando ambas fuentes, con precedencia explícita por campo, y recién ahí se
llama a `upsert_proyecto` una sola vez.

### Precedencia por campo (el contrato nuevo)

| campo | gana | por qué |
|---|---|---|
| `firmantes` | **bot** | trae los cofirmantes completos (1.016 de 2.826 tienen más de uno); CKAN sólo publica el primer firmante |
| `giros` (tabla `proyecto_giros`) | **CKAN**, salvo que CKAN no conozca el proyecto | ver la corrección de abajo |
| `n_giros_inicial` (columna) | **bot** | es el giro **al ingresar**, medido y no reconstruido |
| `tramite`, dictámenes, resultados, leyes | **CKAN** | el bot es una foto del día de ingreso; no sigue el expediente |
| `sumario`, `fecha_ingreso`, `camara` | **CKAN**, con el bot como *fallback* | CKAN es el registro oficial consolidado; el bot cubre lo que CKAN todavía no publicó |
| `taxonomias` | **nadie** (las escribe el agente) | ya está así en `schema.sql` y no se toca |

**`store.py` no se modifica.** La semántica de reemplazo se respeta; lo que se agrega es una
capa de merge encima. Cambiar `store.py` para que haga *upsert parcial* haría que un scrape
legítimo no pudiera **quitar** un giro revocado, que es justamente lo que hoy hace bien.

## Cómo se valida que no se rompió nada

La migración cambia de dónde sale el rasgo más pesado del modelo. **El riesgo no es que falle:
es que cuente distinto y nadie lo note.** Por eso:

> **Condición de aceptación, no negociable:** el embudo corre por las **dos rutas** (parquet y
> SQLite) y tienen que dar lo mismo. Hasta que eso pase, la ruta parquet **no se apaga**.

⚠️ **El 0,3647 quedó obsoleto como vara** — es anterior al refresco de CKAN del 07-08. El
baseline se volvió a medir sobre los datos nuevos. **CUMPLIDA el 07-08:**

| target | ruta parquet | ruta SQLite |
|---|---:|---:|
| `sancionado` (escalón 2) | 0,3643 | **0,3643** |
| `llega_recinto` | 0,4195 | **0,4195** |

Y antes del backtest, una prueba más fuerte: la **cohorte** salió idéntica **celda por celda**
(41.470 filas, 13 columnas, cero diferencias). Si la entrada es igual, la salida lo es por
construcción.

Si el número se mueve, no se acepta "mejoró": una diferencia de conteo (un giro duplicado, un
`tipo` mal mapeado, un `LEY` que dejó de matchear) se ve igual que una mejora. El único
resultado válido es que dé lo mismo.

## Consecuencias

**A favor, y por eso se eligió:**

- Los cofirmantes entran enteros: `proyecto_autores` tiene orden, bloque y distrito.
- **Desbloquea las taxonomías de verdad** — `proyecto_taxonomias` existe con `fuente`
  (agente/humano) y `confianza`. Era el blocker real que varios documentos arrastraban
  atribuido a la API key, resuelta desde el 14-jul.
- Una sola clave, `denominador` (`2595-D-2026`), que es la que usan las fuentes oficiales y los
  informes — en vez del id interno de CKAN (`HCDN292367`).
- Deja de haber dos bases de proyectos, ninguna completa.

**En contra, asumido:**

- Toca `variables/embudo`, el módulo del que cuelga todo el nowcast. Mitigado con la corrida en
  paralelo y con dejar la ruta parquet viva como *fallback*.
- El modelo sigue ciego a lo presentado después del 02-06 mientras dure la migración.
- Cruza dos módulos con dueños distintos, que es lo que la regla "un módulo, un dueño" evita.
  Mitigado reclamando los tres en `TABLERO.md` en la misma sesión.

## Alcance del hueco que esto cierra

Medido en disco el 07-08 (**no** son las cifras del 06-08: el bot siguió corriendo):

| | cantidad |
|---|---:|
| Proyectos del TP ausentes de `expedientes` | **914** |
| …de los cuales son **DE LEY** (lo único que mira el embudo) | **283** |
| Proyectos de ley del Senado en el DAE | **520** |
| Proyectos del TP con cofirmantes | **1.016 de 2.826** |

> El titular de "861 proyectos invisibles" que circulaba **estaba inflado para lo que importa**:
> el grueso son resoluciones y declaraciones que el embudo filtra igual. El agujero real del
> embudo son **283 de Diputados + 520 del Senado**. Sigue siendo grave — hoy no se puede
> nowcastear nada presentado en los últimos dos meses — pero el número que hay que citar es ése.

## Pendiente que este ADR NO resuelve

`expedientes.parquet` **no se apaga**: `datos/expedientes` sigue siendo el módulo que baja CKAN
y sigue produciendo su contrato. Lo que cambia es quién lo consume. Si más adelante se decide
que la ingesta escriba directo a SQLite, es otro ADR.


---

## ⚠️ Corrección al propio ADR (misma fecha, después de implementarlo)

**La tabla de precedencia decía "`giros` → gana el bot". Estaba mal**, y se detectó al mirar por
qué el log del embudo reportaba *menos* proyectos con el giro corregido (633 → 559) después de
cargar el bot, cuando debía reportar más.

**El error es conceptual: son dos cosas distintas con el mismo nombre.**

| fuente | qué son sus giros |
|---|---|
| CKAN | los **acumulados de hoy** — incluyen las ampliaciones posteriores a la presentación |
| bot | los **del día que entró** el proyecto — la foto del momento cero |

Dar precedencia al bot sobre `proyecto_giros` **borró el acumulado** de 2.267 proyectos: de 4.115
giros a 4.006. Al modelo no lo afectó (usa el inicial, y el skill dio idéntico), pero se perdía
justamente el dato con el que Franco midió las ampliaciones de giro el 07-08.

**Regla corregida, ya implementada:**

- `proyecto_giros` guarda **el acumulado**. Sólo lo escribe el bot cuando el proyecto **no existe
  en CKAN** — ahí es la única fuente que hay.
- El giro al ingresar vive **sólo** en la columna `n_giros_inicial`, que es su lugar.

**Resultado tras corregir:** los 4.115 giros acumulados vuelven a estar completos, `comisiones`
deja de tener 174 filas alteradas (pasa a **0**), y la cobertura del giro **medido** sube de 2.927
a **4.449 proyectos** — un 52% más que antes de cargar el bot.

**La lección, que es la de todo el día:** el número que delató el error no era un error. Era el
log diciendo *"559 proyectos con el giro corregido"* donde antes decía 633. Nada fallaba.


---

## Corrección 2 (misma fecha) — cuarentena, no freno

**Valle frenó el primer diseño del control**, y con razón:

> *"No creo que sea esta la manera. Trabajamos con muchos datos de manera constante… Si llegase a
> pasar que encontramos errores, a lo mejor que se carguen con una etiqueta que los marque como
> pendientes de revisión."*

El primer intento hacía `SystemExit` ante **cualquier** fila rara. **Está mal para este
proyecto:** el bot corre solo todos los días y un refresco de CKAN trae 300+ proyectos. Frenar la
tanda entera porque un expediente vino raro es **el mismo error que el workflow ya había
corregido con `continue-on-error`** — una fuente caída no puede matar la recolección.

### La distinción que faltaba

| clase | ejemplo | qué corresponde |
|---|---|---|
| **fila rara** | un expediente con formato desconocido, un `tipo` que no está en el mapa | **cuarentena**: se aparta, se guarda entera, la carga sigue |
| **invariante rota** | el trámite desapareció, la llave colapsó 1.531 filas en una, una variable de resultado cambió | **frenar**: la lógica de carga está rota y publicar así es peor que no publicar |

De los tres errores del 07-08, **dos eran invariante rota** (frenar estaba bien) y **el de los 34
del Ejecutivo era fila rara** — ahí el `SystemExit` sobraba. Valle apuntó exactamente a ése.

### Cómo quedó (decisión de Valle)

> *"Los pendientes de revisión van a una base de datos distinta y los que están bien pasan a la
> base de datos general."*

**Separación física, no una etiqueta.** `datos/proyectos/data/cuarentena.db` guarda la fila cruda
entera + el motivo. **`proyectos.db` queda limpia por definición:** si una fila está ahí, se leyó
bien. Nada dudoso toca el modelo y nada se pierde.

**La cuarentena SÍ viaja a git** (excepción explícita en el `.gitignore`): pesa kilobytes y la
tiene que mirar una persona. Si no viajara, los pendientes quedarían sólo en la máquina de quien
cargó — que es la quinta versión del mismo problema.

### Y una avalancha sí frena

Una fila rara es normal: la fuente cambia. **Muchas juntas significan otra cosa.** Si más del
**5%** de una tanda cae en cuarentena, la carga corta: eso no es una anomalía, es el formato que
cambió.

⚠️ **Con un PISO ABSOLUTO de 10 filas, y esto salió de probarlo, no de pensarlo.** Con sólo el
porcentaje, una tanda chica frena de más: el bot diario puede traer 20 expedientes y uno raro ya
es 5%. **Un cron que aborta por una fila rara vuelve al problema de origen.** Debajo de 10 filas
nunca frena.

**Probado con tres escenarios** (`test_verificar.py`): 1 de 20 → sigue · 3 de 100 → sigue ·
15 de 100 → frena.
