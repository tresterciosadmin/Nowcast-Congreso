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

## 1. `ingesta_padron.py` sin argumentos BORRA la historia del padrón (Claude)
**Detectado:** 2026-08-22 · Claude · **bloquea: cualquiera que regenere el padrón**

La entrada por defecto del script es `datos/padron/data/raw/nomina_diputados.csv`, que
tiene **257 filas** (la foto vigente). La nómina acumulada con toda la historia es
`datos/padron/data/nomina_diputados.csv`, con **1.454 filas**.

Correr `python datos/padron/src/ingesta_padron.py` sin argumentos deja
`padron_diputados.csv` con 257 filas y **se lleva puestos 18 años de mandatos**, sin
error ni aviso. Me pasó hoy: lo detecté porque comparé antes/después, no porque algo
fallara.

**Mientras tanto, el comando correcto es:**

    python datos/padron/src/ingesta_padron.py diputados datos/padron/data/nomina_diputados.csv

**Qué hay que hacer:** que el default apunte a la nómina acumulada, o que el script
**se niegue a escribir** si la salida tiene muchas menos filas que el archivo que va a
pisar. Lo segundo es mejor: es un control que puede decir que no.

> **Re-verificado y POSTERGADO otra vez el 2026-08-25, con el motivo por escrito (Claude).**
> Las dos cifras se re-midieron con `csv.reader` sobre el disco y dan **exacto**: 1.454
> filas la acumulada, **257** la de `raw/`. Sigue vigente tal cual.
> No lo resolví porque `datos/padron` no era módulo de esta sesión (fueron las
> definiciones compartidas) y el arreglo bueno —el control que se niega a escribir— es un
> cambio de comportamiento en módulo ajeno.
> **Dato nuevo que lo agranda:** este mismo patrón —dos archivos con el mismo nombre,
> contenido distinto, el pipeline toma uno y nadie se entera— apareció **una segunda vez**
> el 25-08, en el dump suelto de La Década Votada. O sea que no es un descuido puntual de
> `ingesta_padron.py`: es una forma de fallar que el repo repite. El control que se niega
> a escribir vale más que el default corregido, justamente por eso.

## 2. Falso positivo del patrón IZQUIERDA en `entity_resolution` (Franco)
**Detectado:** 2026-08-22 · Claude · **ensucia: `bloque_linaje` de `datos/canonica` y del padrón**

El arreglo del 07-08 que reconoce al Frente de Izquierda **por patrón** (para cubrir las
13 variantes de etiqueta que el FIT rota cada elección) funciona bien: al re-sincronizar
el padrón oficial cambió 24 filas y **23 son correctas**.

La 24ª no: **Héctor Daer**, bloque "Bloque de los Trabajadores" (2017-05 a 2017-12), cae
en IZQUIERDA por la palabra *trabajadores*. Daer es de la CGT, peronista.

**Qué hay que hacer:** una excepción por etiqueta exacta antes del patrón, o exigir que
además aparezca alguna de las palabras del FIT (frente de izquierda / partido obrero /
PTS / MST / izquierda socialista). Es un caso y una ventana de siete meses, pero el
patrón va a seguir agarrando etiquetas con "trabajadores" que no son de izquierda.

## 3. Validar 15 filas MEDIA del roster de jefes (equipo)
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

> **Postergado otra vez el 2026-08-22, con el motivo por escrito (Claude).** No es de
> `datos/expedientes` ni de `modelo/ensemble`, que son los módulos de esta sesión, y no
> bloquea ni ensucia lo que se hizo. Se mantiene la prioridad rebajada del 31-07 (aporta
> 1,25x, no 7x). **Dato nuevo que lo vuelve más interesante, no más urgente:** dos de los
> cuatro nombres de la tabla —FERRARO y DEL CAÑO— aparecieron hoy en la auditoría del
> cálculo por otro motivo (Ferraro quedó como incógnita real al 49%, Del Caño estaba
> clasificado con P=1,00 cuando su récord es 0,01). O sea que las mismas filas mal
> curadas tocan dos señales distintas.

**Cómo validar:** buscar fuente explícita ("presidente/jefe del bloque X"),
actualizar `confianza` a ALTA con la fuente, o eliminar la fila dejando el
motivo como comentario `#` en el propio CSV (como se hizo con Bianchi).

## 4. El panel de puertas muestra DOS umbrales distintos (Claude)
**Detectado:** 2026-08-25 · Claude · **ensucia: el número que se lee en `Nowcast-Puertas.html`**

`nowcast_puertas.py:302` devuelve **dos** umbrales en el mismo payload:

- `umbral_mayoria_simple` = `n // 2 + 1` → **129** en Diputados. Eso es mayoría
  ABSOLUTA, no simple.
- `umbral_simulado` = el que efectivamente usó la simulación (mitad de los que votan)
  → **122,1** en el caso medido.

Y el HTML usa **los dos, en el mismo panel**: la barra se dibuja contra el simulado
(`casos/nowcast_puertas_html.py:236`), pero **el margen se calcula contra el otro**
(línea 283, `rs[i].m - c.umbral_mayoria_simple`).

Es el error "el umbral del navegador (129) no era el del modelo (125,5)" del 22-08,
**sobreviviendo en la mitad del código**. Se arregló donde se dibuja la barra y quedó
donde se calcula el margen.

**Qué hay que hacer:** decidir si `umbral_mayoria_simple` tiene que seguir en el
payload. Si no lo usa nadie más, sacarlo y que el margen salga de `umbral_simulado`;
si se queda, renombrarlo a `umbral_mayoria_absoluta`, que es lo que es. Con un test que
falle con el código de hoy. **No lo toqué**: `modelo/ensemble` y `casos/` no eran los
módulos de esta sesión y el cambio mueve un número publicado.

## 5. Tres de los cuatro `_fecha_iso` arman la fecha sin validarla (Claude)
**Detectado:** 2026-08-25 · Claude · **ensucia: fechas de padrón, Senado y bot**

Los cuatro `_fecha_iso` del repo parsean formatos genuinamente distintos y **está bien
que sean cuatro** (uno lee "14 DE MARZO DE 2026", otro `dd/mm/YYYY`, otro `dd-mm-YYYY`).
Eso no se unifica. Lo que sí divergió es la **validación**:

| Archivo | Valida? |
|---|---|
| `datos/seguimiento/src/giros.py:131` | sí — pasa por `datetime(y, m, d)` y devuelve `None` si no existe |
| `datos/bot_recoleccion/src/tp_diputados.py:95` | **no** |
| `datos/padron/src/ingesta_padron.py:65` | **no** |
| `datos/senado/src/padron_bloques.py:61` | **no** |

En los tres que no validan, un `31/02/2026` sale como `"2026-02-31"` sin chistar. Después
`pd.to_datetime(..., errors="coerce")` lo convierte en `NaT` **en silencio**, que en este
repo es el modo de fallar que más caro sale: no da error, da una columna vacía.

**Qué hay que hacer:** las tres que faltan pasan por `datetime(y, m, d)` con `try/except
ValueError -> None`, como la de `giros.py`. Son tres módulos con dueño distinto, por eso
queda acá y no lo hice.

## 6. Los outputs de `vigilar_padron.py` tienen DOS escritores y chocan todos los lunes (Claude)
**Detectado:** 2026-08-25 · Claude (lo trajo Valle con el error de GitHub Desktop) · **bloquea: cualquiera que haga pull un lunes**

`datos/padron/data/estado_vigilancia.json` y `datos/padron/outputs/vigilancia_padron.md`
los escribe **el bot** (`bot-nowcast`, commits *"padrón vivo: …"* los lunes: 10-08, 17-08,
24-08) **y también cualquier corrida local** de `vigilar_padron.py`. Están versionados —y
tienen que estarlo, porque el workflow necesita el estado para comparar entre corridas—,
así que cada lunes el pull encuentra los dos lados modificados y se planta con
*"Unable to pull when changes are present on your branch"*.

**Ya causó daño, no es hipotético.** El 25-08 el "Stash changes and continue" dejó los
**marcadores de conflicto escritos adentro** de los dos archivos y así se commitearon y
pushearon (`5aff5b0`). `estado_vigilancia.json` dejó de ser JSON válido. Y no da error:
`vigilar_padron.py:349` atrapa el `JSONDecodeError` y **lo trata como primera corrida**,
con lo que se pierde `hash_visto_desde` — el campo que mide hace cuántos días el raw no
cambia y dispara el aviso de dato rancio. El del Senado venía del **07-08** (18 días).
Restaurado desde el commit del bot; el registro queda en ESTADO.

**Qué hay que hacer:** que una corrida local **no pueda** escribir la ruta versionada.
`vigilar_padron.py` escribiría a una ruta de scratch (o `--dry-run` por defecto fuera de
CI), y el ÚNICO que escribe `data/estado_vigilancia.json` y `outputs/vigilancia_padron.md`
es el workflow. Un archivo generado, un escritor. Mientras tanto, si el pull choca ahí:
**quedate con la versión del bot**, que es la autoritativa —
`git checkout origin/main -- "<los dos archivos>"` — y NO stashees.
