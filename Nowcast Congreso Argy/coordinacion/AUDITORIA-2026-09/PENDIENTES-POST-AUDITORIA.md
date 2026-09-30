# Pendientes para después de la auditoría (estacionamiento)

> Acá se **anotan, en una línea, sin analizar y sin hacer**, las ideas, mejoras y tareas que aparecen mientras dura la auditoría y no son de la auditoría ni de la corrección del modelo (regla 1 del §9.9 del informe). Al cerrarse la auditoría, esta lista es la base del `PROMPT-POST-AUDITORIA.md` (ítem E6).
> No es una lista de tareas activas: **nada de lo que figura acá se toca hasta que Franco declare cerrada la auditoría.**

| fecha | qué | origen | nota |
|---|---|---|---|
| 2026-09-29 | **Validar las etiquetas de `origen`** con una muestra estratificada de 200 actas etiquetadas a mano por una persona (d1) | decisión 8 de Franco: "más adelante, con una persona" | se declara como límite en `QUE-SE-MIDE.md`; casi todo el skill viene del origen (sin origen 0,048) y 43% es `DESCONOCIDO` |
| 2026-09-29 | **Presencia**: agregar ausentes al harness y medir la calibración de `p_presente` y su efecto en la banda (d2) | recomendación (d) | la banda de afirmativos es condicional a los presentes |
| 2026-09-29 | **Auditoría de segunda ronda de `datos/` y de los tres workflows**, con matriz insumo → motor y test de validez por insumo (d3) | recomendación (d) | — |
| 2026-09-29 | **Investigar y rellenar el hueco de Diputados 2020-23** (25 actas, 6.421 votos) y otros de la canónica (d4-b) | recomendación (d) | la *medición y declaración* de la cobertura por año (d4-a) sí está en A4 |
| 2026-09-29 | **Protección de `main` con "requerir PR + CI"**, permitiendo que los bots la salten (deploy key, token de un administrador o GitHub App) (d10) | pregunta de Franco ("¿cómo hacemos eso?") | mientras tanto los bots empujan directo; ver §9.6 d10 |
| 2026-09-29 | Poda P3-P7 del §5 (ramas dormidas, banderas de 14 a ≤ 4, desacople de estimadores) — **P4 y P5 hay que reformularlas** con la decisión 2 (no reemplazar ni archivar δ, β) | informe §5 | esperan a la métrica de verdad (C1) |
| 2026-09-29 | **`.mapa/indexar.py` marca `viaja: True` para TODO en Windows**: le pasa las rutas a `git check-ignore --stdin` con `
` (Python `text=True`) y git no las reconoce; en Linux anda. Efecto: la columna "viaja por git" de `MAPA.md` y de `mapa.json` es siempre verdadera en esta PC. No afecta a `test_insumos_del_motor_viajan` (consulta git en vivo) | hallazgo en A2 | arreglo de una línea (`newline="
"` o `input=` en bytes); fuera del plan |
