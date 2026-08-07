# 🔴 URGENTE — lo primero que se lee y se resuelve en CADA sesión

> **Regla de la casa (CLAUDE.md):** cualquiera del equipo — persona o Claude —
> abre este archivo **al empezar**, antes de reclamar tarea. Si hay algo acá, se
> resuelve o se decide explícitamente postergarlo (dejando dicho por qué).
> Nada se toca "después": lo que está acá bloquea o ensucia trabajo de otros.
>
> **Cómo usarlo:** al detectar algo urgente, se agrega un bloque con fecha, quién
> lo detectó, qué hay que hacer y por qué es urgente. Al resolverlo se BORRA de
> acá (queda el registro en `ESTADO-DEL-PROYECTO.md`, que es la bitácora
> permanente). Este archivo debería estar vacío la mayor parte del tiempo.
>
> ⚠️ **Nada de secciones de "resueltos".** El 04-08 se dejó una, y adentro quedó
> enterrado un pendiente **vivo** (la ingesta del Senado leyendo el padrón viejo)
> que nadie vio durante dos días. Un archivo que existe para que no se pueda no
> ver algo no puede tener una zona donde las cosas se esconden. Lo resuelto se
> borra: para eso está la bitácora.

---

## 0. Revisar las VARIABLES del embudo — hay señales que no cierran
**Detectado:** 2026-07-31 · **Franco** · **bloquea: confiar en el número que sale**

Franco marcó que **varias variables del modelo no le cierran**. Revisar el set
completo antes de seguir construyendo encima. Lo que ya sabemos que está raro:

| variable | coef. | por qué no cierra |
|---|---:|---|
| `n_giros` / `multi_comision` | **1,35 / 1,45** | son **los dos rasgos más fuertes del modelo**, por encima de quién lo firma. ¿Es causal o proxy? Un proyecto girado a más comisiones puede ser "más importante" (y por eso avanza) o **más difícil** (más vetos). El signo positivo dice lo primero; la intuición legislativa diría lo segundo. **Sospecha fuerte de leakage sutil:** los giros pueden ampliarse *después* de presentado, y entonces el rasgo estaría mirando el futuro. |
| `autor_tasa_hist` | 0,61 | correlaciona **0,874** con `origen_ejecutivo` (el autor del PE *es* el presidente). Se lleva todo el crédito y deja a `origen` y `lider` en ~0. |
| `lider` | **‑0,03** | **negativo**, cuando la tasa cruda de líderes es 6x la de no-líderes. Artefacto de la colinealidad de arriba. |
| `origen_ejecutivo` | 0,04 | ~nulo, con tasas crudas de **78,8% vs 1,4%**. Idem. |
| `mes` | ‑0,04 | tratado como **número continuo** (enero=1 … diciembre=12): implica que diciembre es "12 veces enero". Debería ser categórico o, mejor, "días hasta el fin del período de sesiones". |
| `anio_electoral` | ‑0,06 | definido como `anio % 2 == 1`. Correcto para Argentina, pero no distingue **antes/después de la elección** dentro del mismo año, que es cuando cambia el comportamiento. |

**Qué hacer:** auditar una por una (definición, signo esperado vs. obtenido,
correlaciones cruzadas), **priorizando el chequeo de leakage en `n_giros`** — si
los giros se amplían después de presentado, el rasgo más importante del modelo
está contaminado y todo el skill 0,36 queda en duda. Verificable con
`expedientes_movimientos` (fecha de cada giro vs. fecha de presentación).

---

## 1. `p_embudo.parquet` está generado con el modelo que tenía el bug
**Detectado:** 2026-08-06 · Claude (auditoría) · **bloquea: cualquier número del ensemble**

Es el pendiente nº 1 del cierre del 04-08 y sigue sin hacerse. Verificado en disco:

| archivo | fecha |
|---|---|
| `variables/embudo/src/embudo.py` | **2026-08-04** (con el bug del one-hot corregido) |
| `variables/embudo/outputs/p_embudo.parquet` | **2026-07-12** (generado con el bug) |

El bug hacía que `construir_features` rechazara **en silencio** las 25 columnas
de comisiones leídas de parquet: quedaban en cero sin avisar. `p_embudo.parquet`
es el contrato que `modelo/ensemble` consume para el factor `P(llega al recinto)`
— o sea que **hoy todo nowcast se apoya en la mitad mutilada del embudo**, y el
código que lo produciría bien ya está arreglado hace dos días.

**Qué hacer** (en la PC, el sandbox no lo termina):

```powershell
cd "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy"
python variables\embudo\src\embudo.py modelo
```

Después chequear que la fecha del parquet cambió y **commitearlo** (está en el
régimen transitorio del `.gitignore`, así que viaja por git).

---

## 2. Re-correr la ingesta para que el Senado 2026 entre CON bloque
**Detectado:** 2026-08-06 · Claude · **bloquea: el nowcast del Senado**

**El código ya está arreglado; falta la corrida.** `to_canonical.py` leía sólo el
padrón histórico del Senado, que termina el **2025-12-09**: todo voto posterior
al recambio del 10-dic entraba a la canónica con `bloque='SIN BLOQUE'` (6.192
votos de 2026). El 06-08 se le sumó `datos/padron/data/padron_senado.csv`
(mandate-aware, va último para no pisar lo curado) y **los 72 senadores vigentes
resuelven bloque** — incluido el caso Atauche, que ingresa por el Partido
Renovador Federal pero bloquea en LLA. Hay 8 tests nuevos que lo cubren.

Pero la canónica **en disco** sigue siendo la del 04-08, construida con el
código viejo. Hasta que se re-corra, el Senado sigue ciego:

```powershell
cd "C:\Users\tthia\Desktop\Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy"
python datos\canonica\src\run_pipeline.py
```

Son ~20 minutos y necesita internet. Después: verificar que el Senado 2026 dejó
de estar 100% sin bloque, y **commitear los tres parquet** (la canónica se
versiona desde el 31-07). El bot, además, tiene 76 actas nuevas de Diputados y
174 del Senado detectadas al 06-08 que entran en la misma corrida.

---

## 3. Los workflows nuevos no están donde GitHub los lee
**Detectado:** 2026-08-06 · Claude (auditoría) · **bloquea: que el padrón y el ICG se actualicen solos**

**Los tres YAML ya están en la raíz** (movidos el 06-08) y el permiso de
escritura quedó en *Read and write*. Estado de cada uno:

| Workflow | Estado |
|---|---|
| `padron-vivo.yml` (lunes) | ✅ **corrió y funciona** — `padron-vivo #1`, verde, commiteó el reporte |
| `bot-diario.yml` | 🟡 mergeado el 06-08 con los avisos que le faltaban; **falta verlo correr una vez** |
| `icg-mensual.yml` (día 5) | 🔴 **sin estrenar** |

**Qué falta:** disparar a mano cada uno desde Actions → *Run workflow* y ver que
llegue al paso de commit. `icg-mensual.yml` recién se dispararía solo el 5 del
mes que viene, así que sin prueba manual no hay forma de saber si anda.

**Anotado del run #1:** GitHub avisa que `actions/checkout@v4` y
`actions/setup-python@v5` corren sobre Node.js 20, ya deprecado, y los fuerza a
Node 24. Hoy es sólo un warning; cuando GitHub lo corte, los tres workflows
fallan a la vez. Subir a `checkout@v5` / `setup-python@v6` es de un minuto y
conviene hacerlo antes de que sea urgente.

---

## 4. El bot recolecta proyectos y NADIE los carga: el universo del modelo está congelado
**Detectado:** 2026-08-06 · Valle (la pregunta) + Claude (verificación) · **bloquea: nowcastear cualquier proyecto reciente**

Valle preguntó si el bot diario carga en la base los proyectos que detecta.
**No los carga.** Verificado con `grep` sobre todo el repo: fuera de su propio
módulo, **ningún script lee** `tp_entradas.parquet`, `dae_entradas.parquet` ni
`votaciones_nuevas.parquet`. El bot los escribe, los commitea, y ahí quedan.

**Con las VOTACIONES no hay problema** — y es por diseño. `run_pipeline.py` no
lee el parquet del bot, pero re-baja las actas de la API de argentinadatos, así
que entran igual. El bot funciona como **alarma**: detecta actas nuevas y abre un
issue con los comandos. Decisión explícita del 04-08: no reconstruir la fuente de
verdad sin revisión humana. Funciona.

**El agujero está en los PROYECTOS.** Los números, medidos el 06-08:

| Base | Qué tiene | Hasta cuándo |
|---|---|---|
| `datos/expedientes/.../expedientes.parquet` (**lo que mira el embudo**) | 112.793 proyectos | **2026-06-02** |
| `datos/bot_recoleccion/.../tp_entradas.parquet` (Diputados, TP) | 2.799 proyectos | 2026-08-04 |
| `datos/bot_recoleccion/.../dae_entradas.parquet` (Senado, DAE) | 1.007 expedientes | 2026-07-20 |
| `datos/proyectos/data/proyectos.db` (**el destino previsto**) | **no existe — la carpeta está vacía** | — |

**Tres consecuencias concretas:**

1. **861 proyectos** que el bot ya tiene no existen para el modelo. Un proyecto
   presentado en julio o agosto **no se puede nowcastear**: no está en la base
   que lee el embudo.
2. **Se pierde un dato que CKAN no publica.** El bot trae los **cofirmantes
   completos** (1.008 de los 2.799 tienen más de un firmante) — era justamente
   la razón de construir el TP scraper. Ese dato no llega a ningún rasgo.
3. **Es el blocker real de las taxonomías.** Varios documentos dicen "el blocker
   es `proyectos.db` + M1". Confirmado: `proyectos.db` nunca se creó, así que el
   agente de taxonomías no tiene dónde escribir. La API key está resuelta desde
   el 14-jul; **lo que falta es la base.**

**Por qué está acá y no en el backlog:** el `README.md` del bot ya lo lista como
pendiente ("upsert hacia datos/proyectos y capa expedientes"), pero **en ningún
lado estaba escrita la consecuencia**. Leído como pendiente técnico parece
prolijidad; leído como "el sistema no puede predecir nada presentado en los
últimos dos meses" es otra cosa. El bot hoy hace la mitad de su trabajo:
recolecta bien y no entrega.

**Qué hacer** (es trabajo de módulo, no una corrida):

1. Crear `proyectos.db` con el esquema que ya existe:
   `python datos\proyectos\src\store.py init`
2. Escribir el **upsert bot → `datos/proyectos`**: `tp_entradas` y `dae_entradas`
   ya traen expediente, firmantes, giros y sumario; `store.py` ya tiene
   `upsert_proyecto` idempotente por denominador. Es pegar dos contratos que
   existen, no diseñar nada nuevo.
3. Decidir **cómo se une con `datos/expedientes`** (el backfill de CKAN): ¿el
   embudo pasa a leer `proyectos.db`, o `datos/expedientes` absorbe lo del bot?
   Es una decisión de contrato → **conviene un ADR**.

**Módulos:** `datos/bot_recoleccion` + `datos/proyectos` (los dos LIBRES al 06-08).

---

## 5. Validar 15 filas MEDIA del roster de jefes (equipo)
**Detectado:** 2026-07-30 · Claude+Franco · **bloquea: confiar en `lider_jefe_bloque`**

> **Prioridad rebajada el 31-07.** Medido el efecto real, `lider_jefe_bloque` aporta
> **1,25x** (no el 7x que se creía): el jefe de bloque es *aceite del motor*, no
> propositor. Estas 15 filas siguen valiendo para interpretabilidad y para el Mapa
> de Influencia, pero **ya no contaminan una señal predictiva fuerte**.

En `variables/proyecto/data/jefes_bloque.csv` hay **15 filas con confianza
MEDIA** (marcadas "VALIDAR"/"REVISAR"): jefaturas inferidas de contexto, no
confirmadas por fuente explícita.

**Prioridad por volumen de proyectos que aportan:**

| Nombre | Bloque | Período | Aporta |
|---|---|---|---|
| FERRARO, MAXIMILIANO | Coalición Cívica | 2019– | 140 |
| CAMAÑO, GRACIELA | Frente Renovador / UNA | 2015-2019 | 124 |
| DEL CAÑO, NICOLÁS | Frente de Izquierda | 2014– | 101 |
| PINEDO, FEDERICO | PRO | 2013-2019 | 76 |
| + 11 filas menores | (Losada, Atauche, Massa, Ciciliani, Zamora, Thomas, Mayans/FNyP, Fernández Sagasti/UC, Pichetto/etiqueta "Justicialista") | | |

**Caso especial — Del Caño:** el FIT **rota** la jefatura entre PTS y PO;
probablemente requiera tramos más finos que una fila única.

**Por qué sigue acá — el caso Bianchi:** el 30-07 se detectó que
"BIANCHI, IVANA MARÍA" figuraba como jefa de Compromiso Federal aportando **610
proyectos (27% de la señal)**. No presidía el bloque: era la diputada con más
proyectos de toda la Cámara en 2017 — la señal se habría **duplicado a sí misma
disfrazada de otra**. Una sola fila mal puesta contaminó cientos de casos.

**Cómo validar:** buscar fuente explícita ("presidente/jefe del bloque X"),
actualizar `confianza` a ALTA con la fuente, o eliminar la fila dejando el
motivo como comentario `#` en el propio CSV (como se hizo con Bianchi).
