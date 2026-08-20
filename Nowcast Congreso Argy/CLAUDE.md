# CLAUDE.md — Bootstrap para trabajo en paralelo

> Cualquier Claude (o persona) que abra este repo lee este archivo **primero y completo** antes de tocar nada. Está pensado para que varios trabajemos en simultáneo sin pisarnos.

**Repositorio (fuente de verdad):** https://github.com/tresterciosadmin/Nowcast-Congreso

## Qué es este proyecto
Nowcast Legislativo Argentino: estima la probabilidad de sanción de proyectos de ley en el Congreso. Contexto de negocio, metodología y reglas de dominio están en `docs/contexto/INSTRUCTIVO-MAESTRO.md` y `docs/contexto/Nowcast-Congreso_viabilidad_y_plan.md`. **No los repitas; citalos.**

## Orden de lectura obligatorio
0. **`coordinacion/URGENTE.md`** — 🔴 **SIEMPRE PRIMERO.** Si tiene algo, se resuelve (o se decide postergar explícitamente) ANTES de reclamar tarea nueva. Ver la regla más abajo.
1. Este `CLAUDE.md`.
2. `coordinacion/ESTADO-DEL-PROYECTO.md` — qué se hizo hasta ahora (documento vivo).
3. `coordinacion/TABLERO.md` — qué tareas están libres / tomadas.
4. `coordinacion/PROTOCOLO-GIT.md` — cómo ramificar y mergear sin conflictos.
5. **`MAPA.md`** (raíz) — el índice del repo, generado. Dice qué hay en cada módulo, qué archivos son centrales y quién consume a quién. **Leerlo antes de abrir cualquier archivo de código**, y usar `python3 .mapa/buscar.py "<termino>"` para ubicar algo sin escanear el repo.
6. El `README.md` del módulo que vayas a tocar (contrato de entradas/salidas).
7. `TABLERO-CONTROL.html` (raíz) — el mapa ejecutivo; se actualiza vía `tablero_datos.js` (regla más abajo).

## Regla de oro anti-colisión: **un módulo, un dueño, una rama**
- El repo está partido en módulos (`datos/`, `variables/<variable>/`, `modelo/`, etc.). Cada módulo es una unidad de trabajo independiente con un contrato de salida estable.
- **Antes de escribir una línea**, reclamá el módulo en `TABLERO.md` (tu nombre/ID + fecha). Si ya está tomado, elegí otro o coordiná.
- Trabajás **solo dentro de tu módulo**. No edites archivos de otro módulo. Si necesitás algo de otro módulo, consumí su salida (parquet/contrato), no su código interno.
- Lo único compartido y "frágil" es `docs/schemas/` (los contratos de datos). **Cambiarlo requiere un ADR** en `coordinacion/DECISIONES/` y aviso en el TABLERO, porque afecta a todos.

## Regla del MAPA: **el índice se regenera, la prosa se escribe a mano**
`MAPA.md` (raíz) y `.mapa/` son **generados** por `.mapa/indexar.py`: no se editan a mano, los cambios se pierden. Lo que sí se escribe a mano es, en el `README.md` de cada módulo, la línea `**Resumen:**` y la sección `## Buscar acá si` — de ahí salen la columna "Qué es" y el router "Dónde buscar qué" del mapa. **Si cambia lo que hace tu módulo, actualizá esas dos cosas en su README**, en el mismo PR.

El hook `pre-commit` reindexa solo y avisa —sin bloquear— si algún README quedó vencido respecto del código de su módulo. Vive en la **raíz git** (`.git/hooks/pre-commit`), un nivel arriba de esta carpeta. Si no está instalado, desde el repo: `powershell -ExecutionPolicy Bypass -File "Nowcast Congreso Argy\.mapa\instalar-hook.ps1"` (en PowerShell **no hay `bash` en el PATH**; el hook en sí es bash y no importa, git en Windows lo corre con su propio `sh`). En Linux/Mac o Git Bash: `bash "Nowcast Congreso Argy/.mapa/instalar-hook.sh"` desde la raíz git.

**Por qué se eligió el README y no un `BITACORA.md` aparte** (lo que pide la skill `mapa-de-proyectos`): este repo ya tiene cinco documentos vivos que se contradicen entre sí; sumar un sexto archivo por carpeta empeoraba exactamente el problema que el mapa viene a resolver. `.mapa/indexar.py` está forkeado para leer el README, y el fork está documentado en su cabecera.

## Regla de oro de trazabilidad: **cada cambio se registra**
Todo avance relevante (terminar algo, cambiar un contrato, tomar una decisión) **agrega una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** en el mismo PR. Un PR que cambia código y no actualiza ESTADO no se mergea. Formato en ese archivo.

## Regla de URGENCIAS: **lo urgente salta al principio de cada sesión**
`coordinacion/URGENTE.md` es la bandeja de lo que **bloquea o ensucia trabajo de otros**: datos que hay que regenerar tras un pull, filas dudosas que pueden contaminar un modelo, contratos rotos. **Cualquiera del equipo —persona o Claude— lo abre al EMPEZAR, antes de elegir en qué trabajar.** Si hay algo, se resuelve; si se posterga, se deja escrito por qué. Al resolver, se BORRA de URGENTE (el registro permanente queda en `ESTADO-DEL-PROYECTO.md`): el archivo debe estar vacío la mayor parte del tiempo. Quien detecta algo urgente lo agrega ahí en el mismo PR, con fecha, qué hacer y por qué es urgente.

**Por qué existe:** dos incidentes reales. (1) El equipo diagnosticó el linaje del Senado sobre un parquet anterior a un fix ya pusheado y construyó un corrector que no cambia ninguna fila. (2) Una fila mal curada metió 610 proyectos falsos en una señal del modelo. En ambos casos el aviso existía en la bitácora, pero enterrado entre entradas: **lo urgente necesita un lugar donde no se pueda no verlo.**

## Regla del TABLERO DE CONTROL: **el mapa se actualiza en cada cambio**
En la raíz vive `TABLERO-CONTROL.html` (se abre con doble click), el tablero ejecutivo que consolida el plan de la plataforma con el estado real. Su única fuente de datos es **`tablero_datos.js`** — ese archivo es OBLIGATORIO actualizarlo en el mismo PR que ESTADO y EN-HUMANO cuando cambia algo relevante: (1) fecha y autor, (2) el `estado` de lo que tocaste (modulos_plataforma / etapas / modulos_repo), (3) un hito nuevo arriba de todo en `hitos` (1-3 frases, en humano), (4) kpis/metricas si cambiaron los números. **NO edites `TABLERO-CONTROL.html`** (es el diseño, fijo). Estados válidos: HECHO | EN CURSO | PARCIAL | PENDIENTE | FUTURO | REPLANTEADO. Un PR que cambia el estado del proyecto y no actualiza el tablero no se mergea.

## Régimen de archivos descartables: **todo lo borrable va a `Archivos_Borrar/`**
El entorno de Claude **no puede borrar archivos** (en la máquina de Franco, además, la carpeta está en OneDrive). Por eso, todo lo temporal o regenerable (cachés, descargas crudas, logs de validación, salidas intermedias, pruebas) se escribe en `Archivos_Borrar/` para que el dueño humano lo borre a mano. Nada ahí es fuente de verdad.

**Cuando Claude necesita que un archivo DESAPAREZCA** (no que se descarte: que deje de existir, p. ej. un duplicado que si corre hace daño): (1) copia a `Archivos_Borrar/` como `BORRAR_<ruta-con-guiones>`; (2) **neutraliza el original** — a un workflow se le sacan los disparadores automáticos, a un script el `__main__`, a un dato una cabecera que lo invalide; (3) lo anota en `Archivos_Borrar/PENDIENTES-DE-BORRAR.md`. **El paso 2 no es opcional:** un archivo que "hay que borrar" y mientras tanto sigue funcionando no es un pendiente, es un problema activo.

## ⛔ Límites del entorno de Claude: **lo que no ve NO prueba que no exista**
> Agregado 2026-08-04 después de tres errores en una misma sesión. Vale para cualquier Claude que abra este repo.

El sandbox donde corre Claude monta la carpeta con límites que **no se anuncian solos**. Cada uno ya produjo trabajo tirado:

1. **La raíz del repo está UN NIVEL ARRIBA de lo que Claude ve.** Se monta `Nowcast-Congreso\Nowcast-Congreso\Nowcast Congreso Argy`, pero la raíz git es `Nowcast-Congreso\Nowcast-Congreso`. Consecuencias: **`.github/workflows/` vive en la raíz** (lo que se escriba en la subcarpeta GitHub no lo lee nunca) y las rutas dentro de un workflow llevan el prefijo `"Nowcast Congreso Argy/"` **entrecomillado** (tiene espacios). Además `git <cmd> tablero_datos.js` desde la subcarpeta falla: git lo ve root-relative.
2. **Los archivos que empiezan con punto: depende de la sesión, NO asumir.** El 04-08 `ls -a` no mostraba `.git` ni `.github`, y de ahí salieron un instructivo entero para "conectar git" (ya estaba conectado) y un workflow que duplicaba al bot diario que corría desde julio. **El 06-08 sí se veían** `.github`, `.gitignore`, `.env` y `.gitattributes` — el comportamiento del mount cambió entre sesiones sin avisar. `.git` sigue sin verse, pero por el punto 1: no está en esta carpeta, está un nivel arriba. **Moraleja, que es más fuerte que el síntoma:** no vale ni "no lo veo, no existe" ni "la sesión pasada no se veía, tampoco ahora". Se mira, y si no aparece algo que debería estar, se pregunta.
3. **El mount trunca archivos grandes al leerlos**, y el read-modify-write propaga el corte. Verificar `wc -c` + `tail` antes de reescribir; en JS/JSON chequear balance de llaves después. **Ya dañó dos archivos en disco:** `CLAUDE.md` (detectado y reparado el 04-08) y `coordinacion/PLAN-DE-TRABAJO.md`, que quedó cortado a mitad de una palabra en "Mapa de paralelización" y recién se detectó el **06-08**. Si un archivo termina raro, sospechar de esto antes que de cualquier otra cosa.
4. **~45 s por comando y los procesos en background no sobreviven** entre llamadas. Las corridas pesadas (pipelines, exports, backtests) se le pasan al humano listas para PowerShell, con lo que tiene que dar cada paso.

5. **El sandbox tiene OTRA VERSIÓN DE PANDAS que la PC de Valle, y eso ya escondió un bug.**
   El 08-08 `test_enlace_senado.py` daba **83/83 OK** acá y reventaba en la
   máquina de Valle con `'float' object has no attribute 'split'`. Según la
   versión y el backend de la columna (object vs. Arrow), un faltante llega como
   `None`, como `float('nan')` o como `pd.NA` — y **`not float('nan')` es
   `False`** (el NaN pasa la guarda), mientras **`not pd.NA` levanta
   `TypeError: boolean value of NA is ambiguous`**. Un `if not valor` cubre sólo
   el primer caso, que es el único que uno se acuerda de probar.
   **Qué hacer:** guardas de faltantes con `pd.isna()`, `str()` explícito antes
   de `.split()`/`.strip()`, y **tests que ejerciten los dos backends**
   (`convert_dtypes(dtype_backend="pyarrow")`). **"Pasa en el sandbox" no es
   "pasa": la corrida de Valle es la que vale.**

**La regla:** ante un archivo, carpeta o dato que *debería* estar y no aparece, **preguntar, no concluir**. Y antes de tocar infraestructura del repo (workflows, hooks, CI), **pedir un listado de la raíz**. El detalle está en `coordinacion/PLAN-DE-TRABAJO.md`.

**El corolario que costó más caro, y que no es sobre el sandbox:** los tres
errores del 04-08 y los cinco del 06-08 tienen la misma forma — *alguien
concluyó algo sobre el estado del proyecto sin mirar el disco*. El padrón del
Senado "que no existía" existía; los workflows "corriendo en Actions" nunca se
dispararon; la canónica "de 835k votos" tenía 1.016.632. **Antes de repetir un
número o un estado que leíste en una bitácora, verificalo contra el archivo.**

## Flujo mínimo por sesión
1. `git pull` → leé ESTADO + TABLERO.
2. Reclamá un módulo/tarea en TABLERO.
3. Rama `feat/<modulo>-<desc>`.
4. Trabajá dentro del módulo; código con las 4 directivas de resiliencia (errores específicos, backoff en red, parsing defensivo, logging estructurado).
5. Actualizá ESTADO-DEL-PROYECTO.md.
6. PR chico, descripción clara, mergeá apenas pase. Liberá el módulo en TABLERO.

## Estrategia de datos (ver ADR-0002)
**Semilla → canónica propia → bot.** Andy Tow ("La Década Votada" / legislAr) se usa como **semilla histórica de un solo uso**; no se copia ni se depende en vivo de su dataset. Sobre esa semilla + CKAN + argentinadatos construimos una **base canónica propia** (`datos/canonica`, la fuente de verdad) y un **bot** (`datos/bot_recoleccion`) que recolecta las votaciones nuevas de las fuentes oficiales. legislAr corre en R solo para el export; el resto en Python.

## Estado actual: **NO se escribe acá, se lee de la bitácora viva**
> Reescrito 2026-08-04. Esta sección era un resumen del estado y tenía dos problemas: (1) estaba **desactualizado** (hablaba de 781k votos cuando la canónica ya va por 1.017M, y daba el hueco Senado 2014-2023 como abierto cuando ya se cerró); (2) estaba **truncado a mitad de una palabra** — el mount corta archivos grandes y alguna sesión anterior reescribió sobre una lectura cortada. Duplicar el estado en un archivo que nadie actualiza es el modo de falla recurrente del proyecto: tres incidentes nacieron de trabajar sobre copias viejas.

El estado vivo está, y sólo está, acá:

| Dónde | Qué |
|---|---|
| `coordinacion/URGENTE.md` | lo que bloquea a otros — **se lee primero, siempre** |
| `coordinacion/ESTADO-DEL-PROYECTO.md` | bitácora técnica, entrada más reciente arriba |
| `coordinacion/TABLERO.md` | qué módulo está tomado y por quién |
| `coordinacion/EN-HUMANO.md` | lo mismo sin tecnicismos |
| `TABLERO-CONTROL.html` + `tablero_datos.js` | mapa ejecutivo, KPIs e hitos |

Lo único que no cambia y conviene tener presente al abrir el repo: **la Fase 0 está cerrada** y su resultado ordena todo lo demás — predecir la *dirección* del voto individual mirando al bloque acierta ≈0,99, así que ahí no hay negocio. La incertidumbre vive en **asistencia/quórum**, **embudo**, **posición de bloque** y las **10-20 bisagras** de las votaciones peleadas. El esquema canónico está en `docs/schemas` (schema_version=1) y la estrategia de datos en ADR-0002.
