# Prompt de arranque para la conversación nueva (pegar tal cual)

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
