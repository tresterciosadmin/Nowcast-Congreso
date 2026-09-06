# Prompt para la sesión autónoma del 2026-09-04

> **Cómo se usa:** abrí un chat nuevo con la carpeta del proyecto conectada y pegá **todo
> lo que está debajo de la línea**. Está escrito para trabajar solo, sin preguntarte nada.

---

Sos parte del equipo del **Nowcast Legislativo Argentino**, una plataforma que estima la
probabilidad de que un proyecto se convierta en ley en el Congreso argentino. Trabajás con
Franco (producto y metodología) y Valle (datos), coordinando por git.

**Repo:** `C:\Users\Franco\OneDrive\Desktop\TresTercios\Nowcast Congreso\Nowcast Congreso Argy`

Franco no está disponible esta mañana. **No hagas preguntas: resolvé y dejá anotado.** Si
algo no se puede resolver sin él, no lo hagas y dejalo listado al final con qué necesitás.

---

## 0. Antes de tocar nada (en este orden, no lo saltees)

1. `coordinacion/URGENTE.md` — es la cola de trabajo. La regla de la casa es leerlo primero.
2. `MAPA.md` en la raíz, y `.mapa/buscar.py` para ubicar código **sin releer el repo entero**
   (`python .mapa/buscar.py "<tema>"`, `python .mapa/buscar.py --archivo <ruta>` para ver
   quién consume un archivo). Hay una skill `mapa-de-proyectos` que lo explica.
3. `CLAUDE.md` — reglas de la casa, incluidas las trampas de datos.
4. `coordinacion/FORMULA-COMPLETA.md` — qué mide el motor, en tres partes: **lo que corre /
   lo que no funciona / lo pendiente**. Es el contrato del ADR-0015.
5. `coordinacion/DECISIONES/0016-doctrina-de-la-parte-al-todo.md` — la doctrina que gobierna
   dónde va cada término.

---

## 1. La regla que no se rompe

> **La probabilidad de aprobación se construye DE LA PARTE AL TODO.** Todo factor —el clima,
> el dictamen, las elecciones, lo que hizo la otra cámara— es **información que un legislador
> lee y procesa** según su historial, su lealtad y el tema. La probabilidad de la cámara es
> la **consecuencia** de sumar esas decisiones, nunca un lugar donde se aplican correcciones.

Dos excepciones legítimas: **reglas del cuerpo** (umbrales, quórum, bancas) y **shocks
correlacionados**, pero implementados como shock común *dentro* de la simulación.

Al proponer cualquier término, la pregunta es: *¿esto lo lee una persona y decide, o es una
regla del reglamento?* Si es lo primero, va en $P_i$.

---

## 2. 🔴 Lo que NO podés hacer sin Franco

**No cambies el número publicado.** Concretamente, no toques el comportamiento efectivo de:

- `modelo/ensemble/`, `modelo/agregador_institucional/`, `modelo/voto_individual/`
- `variables/bloque/`, `variables/proyecto/` (modulador y origen), `variables/embudo/`

**Sí podés** implementar mejoras en esos módulos **detrás de una bandera apagada por
defecto**, con su test y su medición, para que Franco la prenda. Lo que no podés es que la
corrida por defecto dé un número distinto al de hoy.

Tampoco: `git push`, borrar datos, ni reescribir historia de git. Commitear local está bien
(mensajes claros, en español, uno por tarea).

---

## 3. Las trampas de estos datos — ya nos costaron caro tres veces

| trampa | síntoma que la delató | regla |
|---|---|---|
| **Nombres de comisión con comas** | una comisión faltaba el **100%** de las veces (242/242) | matchear contra el **catálogo** (151 nombres, del más largo al más corto). **Nunca partir por separadores.** Ver `datos/expedientes/src/giros_iniciales.py` → `contar_en_texto()` |
| **`expedientes_giros` mezcla las dos cámaras** | cobertura 2,1% en vez de 63,6% | filtrar por cámara **antes** de cualquier cálculo sobre giros |
| **`od_numero` se repite entre períodos** | 1.722 números para 2.517 pares | la clave es `(periodo, od_numero)` o `archivo` (`126-76.pdf`) |
| **Nombres de personas en formatos distintos** | un coeficiente esperado daba **p=0,88** | clave `APELLIDO\|PRIMER-NOMBRE`; ver `_clave_persona()` en `modelo/ensemble/src/estimar_beta_dictamen.py` |
| **Cachés vacíos ≠ datos faltantes** | 90 min de descarga para reproducir un archivo idéntico | mirar el **parquet**, no la carpeta de trabajo. `Archivos_Borrar/` y `data/raw/` son descartables por diseño |

> **La regla madre, y es la que más vale:** **un porcentaje imposible es un bug, no un
> fenómeno.** 100% de una comisión faltante, 0% de dictámenes de mayoría, 82% de ampliación
> donde había 8%. **Cuando un número esperado da nulo o absurdo, sospechá del cruce antes que
> de la hipótesis.** Las tres veces que pasó, era el cruce.

---

## 4. Las tareas, en orden. Hacé las que entren.

### TAREA A — 🔴 URGENTE 11: arreglar el dictamen del Senado *(la principal)*

**El problema, medido el 03-09:**

| `dictamen_clase` | Diputados | Senado |
|---|---:|---:|
| único | 60% | **99,9%** |
| **mayoría** | **28%** | **0** |
| minoría | 10% | 0,1% |

Y proyectos con más de un despacho: **920 de 3.248 en Diputados** contra **1 de 952 en el
Senado**. Cero mayorías donde la otra cámara tiene 28% no es política: es un default.

**La causa:** `datos/expedientes/src/parser_od.py` → `_clase_del_dictamen()` arranca en
`clase = "unico"` y sólo la cambia si `RE_CABECERA_DICTAMEN` matchea algo que empiece con
`MAYOR`/`MINOR`. **El Senado usa el mismo parser** (`construir_firmas.py` lo importa para
las dos cámaras) y sus Órdenes del Día rotulan distinto, así que todo cae al default.

**Qué hacer:**

1. **Mirá los PDFs reales antes de tocar el regex.** Están en
   `Archivos_Borrar/od_pdf/` (Diputados) y el caché del Senado que arma
   `ingesta_od_senado.py` → `cache_dir`. Abrí **al menos 8 ODs del Senado de años distintos**
   —usá `parser_od.texto_de_pdf()`— y **transcribí en el ADR cómo rotulan los dictámenes**.
   Esta es la parte que decide todo lo demás: **no inventes el patrón, leelo.**
2. Ampliá `RE_CABECERA_DICTAMEN` (o hacé una rama por cámara si la forma es muy distinta).
3. **Cambiá el default:** si no se encuentra cabecera, la clase correcta es
   **`"desconocido"`, no `"unico"`.** Un default silencioso convirtió 17.669 dictámenes en
   una categoría que quizás no les toca. Ojo: esto cambia un contrato — revisá con
   `.mapa/buscar.py --archivo` quién consume `dictamen_clase` y actualizá los consumidores
   para que traten `"desconocido"` como "sin dato" y **no** como "único".
4. Reconstruí: `python datos\expedientes\src\construir_firmas.py`
5. **Criterio de aceptación:** el reparto de `dictamen_clase` del Senado deja de tener
   0 mayorías. No hay un número objetivo — **si después de leer los PDFs resulta que el
   Senado genuinamente casi no tiene dictámenes de minoría, eso también es un resultado
   válido**, pero tiene que quedar documentado con las citas de los PDFs que lo respaldan.
6. Corré los tests: `python datos/expedientes/tests/test_parser_od.py`. Si el cambio rompe
   alguno, arreglá el test sólo si el test estaba mal; si no, arreglá el código.

**Segunda parte, de cableado:** `acta_expediente_senado.parquet` **está mal nombrado: tiene
las dos cámaras** (5.030 filas; la primera es `ckan_diputados:3775`). Y es **mejor tabla**
que `acta_expediente.parquet`: trae `proyecto_id` ya resuelto más `fecha`, `resultado`,
`tipo_mayoria` y `titulo`, y cruza **2.730** actas de la canónica contra **1.849**.

- Decidí si conviene **renombrarla** (`acta_expediente_todas.parquet`) o **unificar** las dos.
- Repuntá los consumidores. Los que sé que la necesitan:
  `modelo/ensemble/src/estimar_beta_dictamen.py` → `firmas_por_acta()` y
  `evaluacion/baseline/src/baseline_voto_individual.py` → `mapa_acta_caracter()`.
  Buscá el resto con `.mapa/buscar.py --archivo`.
- **Verificación:** `python modelo\ensemble\src\estimar_beta_dictamen.py --camara senado`
  hoy devuelve **"0 actas con dictamen identificado"**. Tiene que devolver un panel con
  datos. Si después del arreglo la variable sigue sin varianza, **decilo** en vez de forzar
  un resultado.

---

### TAREA B — URGENTE 10: completar el roster de jefes de bloque

**Estado:** 50 de 80 se resuelven a `legislador_id`. Con 21/80, β₂ daba **+0,039 (p=0,88)**;
con 50/80 da **+0,645 (p=0,0002)**. El coeficiente no cambió porque cambió la realidad:
**bajó el ruido**. Los 30 que faltan lo siguen atenuando.

**Qué hacer:**

1. Corré el diagnóstico que ya existe dentro de `estimar_beta_dictamen.py` (`jefes()` +
   `_clave_persona`) para listar los 30 sin resolver.
2. Los del Senado deberían mejorar solos con la Tarea A. Los que queden, resolvelos
   **agregando una columna `legislador_id` explícita** en
   `variables/proyecto/data/jefes_bloque.csv` en vez de depender del cruce por nombre.
   Sacá el id de `dictamenes_firmas*.parquet` o del padrón.
3. **Si un nombre es ambiguo (dos ids posibles), NO adivines**: dejalo vacío y anotalo. Es
   preferible perder cobertura a asignarle la firma a otra persona.
4. Re-corré `estimar_beta_dictamen.py` y **anotá cómo se movió β₂** en
   `coordinacion/FORMULA-COMPLETA.md` (§III.A.2). Se espera que suba.

---

### TAREA C — arreglos de seguridad que ya están diagnosticados

Están descritos con detalle en `URGENTE.md`. Son chicos, autocontenidos y de bajo riesgo:

- **URGENTE 3:** `ingesta_padron.py` sin argumentos **borra la historia del padrón**. Poné
  un guard que exija un flag explícito para el modo destructivo.
- **URGENTE 7:** tres de los cuatro `_fecha_iso` arman la fecha sin validarla.
- **URGENTE 8bis:** los outputs de `vigilar_padron.py` tienen dos escritores que chocan.
- **URGENTE 6:** el panel de puertas muestra dos umbrales distintos.

Cada uno con su test. **Borrá el ítem de `URGENTE.md` al resolverlo** (la regla de la casa:
lo resuelto se borra, el registro queda en la bitácora; **nada de secciones de "resueltos"**).

---

### TAREA D — si sobra tiempo: URGENTE 8, tabla de récord por TEMA

`rec_i^tema` = afirmativos/emitidos de cada legislador **condicionado a la taxonomía**, con
corte walk-forward. Hoy sólo existe el récord general.

**Medí primero cuántos legisladores llegan a $n_i^{tema} \ge 8$.** Si son pocos, el término
entra como ruido y hay que encogerlo contra el récord general (Empirical-Bayes, $k=5$, igual
que el share). **Reportá esa medición aunque el resultado sea "no alcanza".**

Insumos: taxonomías en `datos/proyectos/data/proyectos.db` (`proyecto_taxonomias`), enlace
acta↔expediente en `datos/expedientes/data/clean/`, votos en
`datos/canonica/data/clean/votos_canonico.parquet`.

**No implementes el término $\rho$ en el motor** — es de los que espera decisión de Franco.

---

### NO HACER sin Franco

- **URGENTE 9 (guard de era):** cambia $P_i$ para el 98% de las predicciones. Si querés,
  dejalo implementado **detrás de una bandera apagada** con su medición, pero no lo prendas.
- **Prender δ, β, ε₀, τ, θ o ψ** en el motor. Están todos estimados y ninguno implementado;
  la tabla está al final de `FORMULA-COMPLETA.md`.
- **URGENTE 5** (validar 15 filas MEDIA del roster): pide criterio humano sobre fuentes.
- **URGENTE 4** (falso positivo IZQUIERDA): toca clasificación política. Diagnosticá y
  proponé, pero no reclasifiques.

---

## 5. Cómo trabajar

**El entorno tiene un límite de ~3 minutos por comando.** Las corridas largas se cortan y
los procesos en background **no sobreviven entre llamadas**. Usá `--muestra` para iterar y
dejale a Franco el comando de la corrida completa para PowerShell.

**Medí antes de creer, y elegí bien la unidad.** El 26-08 dos mediciones correctas del mismo
fenómeno dieron resultados **opuestos**: comparando actas, el desvío subía con $p=2\cdot10^{-4}$;
comparando **legisladores consigo mismos**, el efecto desaparecía. Un $p$ chico sobre
unidades mal elegidas es efecto de composición con cara de hallazgo. **Antes de creerle a un
número, preguntate qué se mantiene fijo.**

**Si el resultado contradice lo que esperábamos, decilo.** Este proyecto viene descartando
hipótesis propias con datos y así es como mejora. Un resultado negativo bien medido vale más
que uno positivo forzado.

**No reimplementes contratos de otros módulos.** `proyectar_postura` (variables/bloque),
`contar_en_texto` (expedientes), `perfil_legislador` (ensemble) ya existen: importalos.

---

## 6. Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — una entrada de bitácora arriba de todo, con
   qué se hizo, **qué se midió** y qué se decidió. Es la memoria del proyecto: escribí para
   alguien que no estuvo. Los hallazgos negativos y los errores propios también van.
2. **`coordinacion/URGENTE.md`** — borrá lo resuelto, agregá lo nuevo que aparezca.
3. **`coordinacion/FORMULA-COMPLETA.md`** — si tocás algo que la afecta, actualizala en el
   mismo commit (ADR-0015). Si no la afecta, decilo con una línea: *"la fórmula no cambia"*.
4. **Un ADR** en `coordinacion/DECISIONES/` si tomás una decisión de diseño (el próximo
   número es **0017**). El del rotulado de dictámenes del Senado probablemente amerite uno.
5. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga, para el registro que
   Franco lee sin contexto técnico.
6. Reindexá el mapa: `python .mapa/indexar.py .`
7. **Un resumen final en el chat** con: qué quedó resuelto, qué se midió, **qué esperabas y
   salió distinto**, y **la lista de lo que necesita a Franco**, con la pregunta concreta
   para cada cosa.

**No hagas `git push`.** Dejá los commits locales para que Franco revise.

Arrancá por `URGENTE.md` y la Tarea A.
