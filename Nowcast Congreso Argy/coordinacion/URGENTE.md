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

> ℹ️ **Sacado de urgencias por decisión de Valle (07-08).** El sesgo de supervivencia del
> Senado (el modelo da 48% a proyectos del Senado contra 1,7% de Diputados, porque la base sólo
> tiene los que ya cruzaron a Diputados) **no se parchea de a un síntoma**: queda como insumo de
> la **Revisión de las Comisiones**, la línea que revisa el circuito completo comisión → cámara.
> Está desarrollado en `PLAN-DE-TRABAJO.md`. **Precaución vigente mientras tanto: no publicar
> P(sanción) de proyectos con origen Senado.**

## 1. Validar 15 filas MEDIA del roster de jefes (equipo)
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

## 2. Re-correr el resto de la cadena tras el cambio de linajes
**Detectado:** 2026-08-07

✅ **Hechos (Franco, 07-08):** `entity_resolution.py` (IZQUIERDA: ~2.700 → **8.816
votos / 19 bloques**), `bloque.py serie` y `disciplina.py`. La medición mejoró:
**mediana de desvío 0,1654 → 0,1477** y legisladores medibles 1.591 → **1.751**.
Validación del cambio: `IZQUIERDA` da **cohesión 1,0000 y desvío 0,0000** en 2025 y
2026 — vota siempre igual, sin una fractura; disuelta en OTRO/PROVINCIAL eso era
invisible. Share afirmativo 2026: **0,2414 contra 0,8211 de LLA**.

⏳ **Falta:** `variables/embudo` no depende de esto, pero **`modelo/ensemble` y el
γ del ICG sí** (leen el desvío, que cambió). Y **commitear los parquet**.

⚠️ **Predicción que NO se verificó:** se anticipó que el desvío de
`OTRO / PROVINCIAL` bajaría al sacarle la izquierda. Quedó en **0,2820 con cohesión
0,4359** y no hay valor previo del mismo indicador para comparar. Queda dicho para
no dar por buena una predicción que no se comprobó.
