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

## 1. El bot recolecta proyectos y NADIE los carga: el universo del modelo está congelado
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

## 2. Validar 15 filas MEDIA del roster de jefes (equipo)
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

---

## 3. Documentar / prolijidad (no bloquea, pero conviene)
**Detectado:** 2026-08-07

- **Padrón de Diputados: 256/257.** Falta Pitrola (la API le carga `2026-04-27 →
  2026-04-27`) y Matzkin no figura. Se probó reparar y da 278 o 263: la fuente no
  distingue quién asumió de quién cesó. Arreglo de fondo: **nómina oficial de
  HCDN**. Ver `datos/padron/src/bajar_nomina.py`.
- **`p_embudo.parquet` conviene regenerarlo** con el giro inicial enchufado
  (`python variables/embudo/src/embudo.py modelo`, corrida larga que el sandbox no
  termina). El modelo está sano; sólo falta que la salida lo refleje.
- **Actions — subido a Node 24 el 07-08, FALTA VERLO CORRER.** Los tres workflows
  pasaron a `checkout@v5` · `setup-python@v6` · `github-script@v8`. El riesgo de
  Node 20 está cerrado en código, pero **una corrida verde de cada uno es lo que
  lo confirma**: si algo se rompió, el modo de falla es que el bot deje de
  recolectar sin avisar. Disparar a mano los tres desde Actions y confirmar. Al
  verlos verdes, **borrar este bullet**.
