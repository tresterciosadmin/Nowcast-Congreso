# Prompts de arranque para conversaciones nuevas (pegar tal cual)

## Reanudación desde la fase B (generado el 2026-09-30, al cerrar la fase A)

> Esta sección reemplaza a la de abajo para seguir desde la fase B. Si algo difiere del informe (`AUDITORIA-INTEGRAL-2026-09.md`, §9), vale el informe. Cuando se cierre la fase B, se genera el de la fase C de la misma manera.

---

Estoy retomando el proyecto *Nowcast Congreso* (repo `Nowcast Congreso`, carpeta de trabajo `Nowcast Congreso Argy`). Seguimos en **MODO AUDITORÍA**: auditar el motor y corregir el modelo hasta que funcione según la definición numérica del §9.4 del informe. **La fase A está cerrada** (A1 a A10, con la evidencia de cada ítem y la «Salida de la fase A» en `ESTADO-EJECUCION.md`). Hoy arrancamos la **fase B: anclaje básico**.

**Leé, en este orden, antes de hacer nada:** (1) `CLAUDE.md`, empezando por el bloque MODO AUDITORÍA; (2) `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md` completo (el plan A1…E6, la evidencia de A1 a A10, los pre-registros y la bitácora de alcance); (3) `AUDITORIA-INTEGRAL-2026-09.md` desde el §9 (mis decisiones y las reglas del carril, §9.9); (4) `05-consolidacion-y-anclaje.md` §5.3 (el anclaje: qué es un *parámetro*, tipos E/M/P y la secuencia de implementación, pasos 1 y 2) y `REGLAS-borrador.md` (reglas 2, 5 y 8); (5) `coordinacion/QUE-SE-MIDE.md` y `PENDIENTES-POST-AUDITORIA.md`.

**Alcance cerrado (lo más importante, sin cambios):**
1. **No me dejes saltar a otros temas.** Sólo trabajamos en la auditoría íntegra y en la corrección del modelo. Si te pido algo fuera del plan, no lo hagas: decime en una frase que está fuera, anotalo en `PENDIENTES-POST-AUDITORIA.md` y volvé al ítem en curso. Sólo lo hacés si escribo textualmente `CAMBIO DE ALCANCE:` seguido de lo que quiero, y antes de ejecutarlo lo registrás en la bitácora de alcance de `ESTADO-EJECUCION.md`. Las preguntas para entender el modelo o el estado se responden sin abrir trabajo.
2. **No se abren tareas nuevas** (ni en `TABLERO.md`, ni ramas, ni documentos) que no sean de la auditoría o de la corrección del modelo. **Las mejoras están suspendidas** hasta que el modelo funcione según el §9.4. Nada nuevo entra al modelo: se corrigen y re-estiman los términos que ya existen (δ, θ, ψ, β, ε₀, τ, guard de era, ICG…).
3. Ante la duda de si algo está dentro del alcance, **no lo hagas y anotalo**. Los hallazgos que aparezcan en el camino (en la fase A salieron dos del bot del ICG y de los DAE) van al estacionamiento, se me avisan y no se arreglan.

**Cómo se trabaja (sin cambios):** una fase a la vez; no pasás a la siguiente sin mostrarme la evidencia del criterio de salida (comando y salida). Se trabaja en **`main`**, commits chicos, suite en verde antes de cada uno, **sin `git push`** (lo hago yo). Podés prender y apagar banderas sin pedirme permiso, pero cada cambio se apoya en una medición con el motor real, con el criterio fijado antes de mirar el resultado, y queda anotado con el valor anterior. Nada se borra sin mirar quién lo usa. Los bots (`bot-diario`, `padron-vivo`, `icg-mensual`) siguen funcionando: no se tocan workflows ni permisos.

**Fase B: los tres ítems y su criterio de salida** (tabla de `ESTADO-EJECUCION.md`):
- **B1. Registro de parámetros generado desde el código + `test_defaults_fijados`.** Salida: *cambiar un default rompe un test* (el ejemplo del plan: poner `TAU` en 1,2 en el código hace fallar el test). «Parámetro» = toda variable de entorno, constante numérica o archivo derivado que lee el camino de `nowcast()` (§5.3). El documento da dos versiones: **sólo AST** (~4 h) y **AST más perturbación del panel** para marcar cuáles *afectan* el número (~10 min de cómputo). Antes de escribir código, pre-registrá cuál hacés y por qué. El registro **lee y fija lo que existe** (ε₀, τ, `RECORD_POR_TEMA`, `SHRINK_RECORD`, `MIN_HIST`, las banderas…): no agrega términos ni banderas al motor.
- **B2. `invariancia_al_futuro.py` como test de la suite.** Hoy vive en `coordinacion/AUDITORIA-2026-09/` con su resultado en `resultados/` y tarda ~12 s por acta. Salida: pasa en `HEAD` y **una fuga sintética** (usar datos de la fecha o de la misma ley) la pone en rojo. El plan lo ubica en `evaluacion/baseline/tests/`.
- **B3. `control_independiente.py` como test de regresión.** Salida: reproduce **0,1335** y detecta el desvío. Regla 5: cada invariante lleva su control positivo (un caso que **debe** fallar).

**Lo que aprendí en la fase A y te ahorra tiempo:**
- **El CI** (`.github/workflows/tests.yml`, en la **raíz git**, no en el proyecto): Python 3.11, instala sólo `requirements.txt` (versiones fijadas), corre `pytest tests/ datos/proyectos/tests` y después **cada** `test_*.py` restante como script. `*.parquet`, `*.csv` y `**/data/clean/` están en `.gitignore`: lo que un test necesite en el CI tiene que viajar por git, como JSON (así se resolvió A2: `evaluacion/baseline/src/censo_estadisticos.py` y `evaluacion/baseline/outputs/censo_estadisticos_2026-09-28.json`; el detalle del censo de 37 MB no viaja). Un test nuevo de B2 o B3 **no puede depender de un archivo ignorado**; si es lento, decidí el diseño (muestra, tiempo) en el pre-registro. Antes de dar un ítem por hecho, verificalo en un **checkout limpio** (`git archive HEAD` a una carpeta temporal, venv de Python 3.11 con los pines) y yo lo confirmo en *Actions*.
- **Método de cada ítem:** pre-registro (qué se mide, con qué panel y qué umbral decide) escrito en `ESTADO-EJECUCION.md` y commiteado **antes** de medir; después la medición con el motor real; después la evidencia en el mismo archivo. Ejemplos en las secciones «A3/A5/A7/A9 — pre-registro».
- **Esta PC (Windows, OneDrive):** `CLAUDE.md` y `ESTADO-EJECUCION.md` tienen finales de línea CRLF (editá conservándolos; `write_text` de Python los convierte). No corras dos suites a la vez: `verificar._abrir()` copia la base a un temporal de nombre fijo y se pisan. El cargador del censo usa rutas relativas: corré desde la raíz del proyecto. Al agregar un `.py` corré a mano `python .mapa/indexar.py .` y commiteá `MAPA.md` y `.mapa/mapa.json` (el hook no está instalado). Un docstring de `.py` que cite un archivo archivado (`x.py.archivado`) rompe `test_rutas_citadas_existen`: citalo sin la ruta. Las rutas del repo son largas: `git worktree add` falla en el scratchpad.
- **Los scripts auxiliares de la fase A** (huellas, simulación del CI, comparaciones antes/después) vivían en una carpeta temporal y **no están en el repo**: si los necesitás, rehacelos chicos. Lo que sí está en el repo y reproduce números: `coordinacion/AUDITORIA-2026-09/*.py` (control independiente, invariancia, contraste de aprobación, cobertura de la canónica, `verificar_bots.py`).
- **Los bots empujan a `main`:** antes de mi próximo `git push` voy a hacer `git pull --rebase`. No te sorprendas por commits de `bot-nowcast` o `bot-recoleccion`.
- **Estado al cerrar la fase A:** `HEAD` `a75c3bb` (o posterior con commits de los bots), `git status` limpio, `python -m pytest tests/ datos/proyectos/tests -q` → 54 pasan, los 58 scripts `test_*.py` salen en 0, el motor da P(APROBACIÓN) 61,3 % en el caso de `test_panel_regresion`.

**Modelos:** Sonnet 5.5 como principal; Opus 5.5 como revisor en los puntos del §9.10 (ninguno cae en la fase B: el primero es el diseño de la re-estimación, antes de D1). Lanzá los subagentes escalonados (el límite de tasa ya cortó trabajo dos veces).

**Al terminar cada ítem y cada sesión:** actualizá `ESTADO-EJECUCION.md` (estado y evidencia) y decime cuál es el próximo ítem. **Al terminar la fase B**, mostrame la evidencia de salida de los tres ítems (comando y salida) antes de pasar a la C, y generá el prompt de la fase C en este mismo archivo. Si la conversación se alarga, pedime abrir una nueva antes de que se pierda contexto: el estado vive en el repo, no en el chat. Sólo yo declaro cerrada la auditoría (§9.8).

**Empezá por el ítem B1.** Primero verificá que `git status` esté limpio y que la suite dé 54 pasan, y avisame si algo del estado del repo no coincide con lo que dice `ESTADO-EJECUCION.md`.

---

## Arranque original (fase A; ya cumplido, se conserva porque es el del §10 del informe)


> Es la misma versión que el §10 del informe. Si difieren, vale el informe.

---

Estoy retomando el proyecto *Nowcast Congreso* (repo `Nowcast Congreso`, carpeta de trabajo `Nowcast Congreso Argy`). Estamos en **MODO AUDITORÍA**: ejecutar la auditoría integral del motor y corregir el modelo hasta que vuelva a funcionar, según lo que decidí el 29-09-2026.

**Leé, en este orden, antes de hacer nada:** (1) `CLAUDE.md`, empezando por el bloque MODO AUDITORÍA; (2) `coordinacion/AUDITORIA-2026-09/AUDITORIA-INTEGRAL-2026-09.md`, **desde el §9** (mis decisiones y las reglas del carril, §9.9); (3) `coordinacion/AUDITORIA-2026-09/ESTADO-EJECUCION.md` (el plan por ítems A1…E6 y su estado); (4) `00-linea-base.md` de esa carpeta.

**Alcance cerrado (lo más importante):**
1. **No me dejes saltar a otros temas.** Sólo trabajamos en la auditoría íntegra y en la corrección del modelo. Si te pido algo fuera del plan, no lo hagas: decime en una frase que está fuera, anotalo en `PENDIENTES-POST-AUDITORIA.md` y volvé al ítem en curso. Sólo lo hacés si escribo textualmente `CAMBIO DE ALCANCE:` seguido de lo que quiero, y antes de ejecutarlo lo registrás en la bitácora de alcance de `ESTADO-EJECUCION.md`. Las preguntas para entender el modelo o el estado se responden sin abrir trabajo.
2. **No se abren tareas nuevas** (ni en `TABLERO.md`, ni ramas, ni documentos) que no sean de la auditoría o de la corrección del modelo. **Las mejoras están suspendidas** hasta que el modelo esté funcionando según la definición numérica del §9.4. Nada nuevo entra al modelo: se corrigen y re-estiman los términos que ya existen (δ, θ, ψ, β, ε₀, τ, guard de era, ICG…).
3. Ante la duda de si algo está dentro del alcance, **no lo hagas y anotalo**.

**Cómo se trabaja:** una fase a la vez, empezando por la **A**; no pasás a la siguiente sin mostrarme la evidencia del criterio de salida (comando y salida). Se trabaja en **`main`**, con commits chicos y la suite en verde antes de cada uno; **sin `git push`** (lo hago yo). Podés prender y apagar banderas sin pedirme permiso hasta que yo declare cerrada la auditoría, pero **cada cambio se apoya en una medición hecha con el motor real, con el criterio fijado antes de mirar el resultado, y queda anotado con el valor anterior**. Nada se borra sin mirar quién lo usa: se copia a `Archivos_Borrar/`; lo que el informe manda eliminar (HTML de producto y panel) es lo único que sale de git. Los bots (`bot-diario`, `padron-vivo`, `icg-mensual`) tienen que seguir funcionando; el `icg-mensual` **no se pausa**.

**Modelos:** trabajá con Sonnet 5.5 como principal y llamá a Opus 5.5 como revisor en los puntos del §9.10 (diseño de la re-estimación, cada veredicto de la fase D, la integración del ICG y el veredicto de cierre). Lanzá los subagentes escalonados (el límite de tasa ya cortó trabajo dos veces).

**Al terminar cada ítem y cada sesión:** actualizá `ESTADO-EJECUCION.md` (estado + evidencia) y decime cuál es el próximo ítem. Si la conversación se alarga, pedime abrir una nueva antes de que se pierda contexto: el estado vive en el repo, no en el chat.

**Cierre:** sólo yo declaro cerrada la auditoría (criterios en el §9.8). Ahí generás `PROMPT-POST-AUDITORIA.md` a partir de `PENDIENTES-POST-AUDITORIA.md` para empezar con las mejoras.

**Empezá por el ítem A1** y avisame si algo del estado del repo no coincide con lo que dice el informe.
