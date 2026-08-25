# Prompt — eficientizar el repo: buscar lo repetido y lo que se puede simplificar

> Para pegar en un chat nuevo. Guardado en `coordinacion/` para no reescribirlo.
> Escrito el 2026-08-22 al cierre de la sesión de la formulación única.
> Lo marcado **[medido 22-08]** salió del disco en esa sesión: no hace falta
> re-descubrirlo, pero **sí re-verificarlo antes de actuar** (el repo cambia sin aviso).

---

## Por qué existe esta tarea

La sesión del 21 y 22-08 se fue entera en un problema que **nadie había buscado**: en el
repo convivían **dos formulaciones del número** —la v1 y la de puertas— y eso no se
descubrió leyendo el código sino tropezándolo. Costó una sesión completa: una baja
formal, dos ADR, siete errores de cálculo encontrados de paso y 287 tests.

Valle lo dijo así: *«me di cuenta de que convivían estas dos formulaciones, y eso
originó todo el trabajo»*. **Esta tarea es ir a buscar el resto de esa familia antes de
que vuelva a pasar**, con dos objetivos: que Claude trabaje más barato adentro del
repo, y que al mirar el workflow se entienda qué pasa.

---

## Empezá por acá: `mapa-de-proyectos`

**Invocá la skill `mapa-de-proyectos` antes de abrir un solo archivo.** Es exactamente
la herramienta de esta tarea: mantiene el índice vivo (`MAPA.md`, `.mapa/`) y está
hecha para responder *«dónde está X», «qué archivos tocan Y», «qué se rompe si cambio
esto», «hay código muerto»* **sin releer el repo entero**.

Usá `.mapa/buscar.py` para ubicar código. No escanees el repo a mano: el punto de la
tarea es reducir el costo de trabajar acá, y empezar quemando contexto sería contradecirla.

Después, la rutina de la casa (skill `metodologia-nowcast`): `URGENTE.md` primero,
después `ESTADO-DEL-PROYECTO.md`, `TABLERO.md`, `tablero_datos.js`, y el README del
módulo que toques. **El disco manda sobre las bitácoras.**

---

## El caso que define qué estamos buscando

**[medido 22-08]** `periodo_parlamentario(fecha, anio)` está **copiada, cuerpo idéntico,
en CUATRO módulos**:

    datos/export/src/export_base.py:59
    modelo/voto_individual/src/disciplina.py:131
    variables/asistencia_quorum/src/asistencia.py:36
    variables/legislador/src/ficha.py:37

Y cada copia lleva un docstring que dice **«mantener sincronizadas»**. O sea: el repo
**ya sabe** que están duplicadas, y la mitigación es un comentario pidiéndole a una
persona que se acuerde. Es el mismo mecanismo que dejó convivir dos formulaciones.

**Y hay un agravante que se detectó tarde:** en esa misma sesión se agregó
`datos/expedientes/src/od_url.py::periodo_de`, que calcula **otro** período —el de
sesiones ordinarias, 1-mar a 28-feb, `año − 1882`— con un nombre casi idéntico al del
recambio legislativo (10-dic de años impares). **Dos conceptos distintos con nombres
que se confunden.** Eso es peor que una duplicación: una duplicación se unifica, una
colisión de nombres induce el error.

**Lo que buscamos es esa familia:** una misma regla escrita más de una vez, o dos
reglas distintas con el mismo nombre.

---

## Puntos de partida medidos [medido 22-08]

**Funciones con el mismo nombre en módulos distintos: 32.** Las que más pintan:

| Función | Módulos | Sospecha |
|---|---|---|
| `periodo_parlamentario` | export, voto_individual, asistencia_quorum, legislador | **copia literal x4, confirmada** |
| `_fecha_iso` | bot_recoleccion, padron, seguimiento, senado | normalización de fechas repetida |
| `_norm` | bot_recoleccion, expedientes, proyectos, seguimiento, senado, proyecto | normalización de texto repetida |
| `cargar` | 9 módulos | probablemente legítimo (cada módulo carga lo suyo) — **verificar, no asumir** |
| `_get`, `_pedir` | varios | clientes HTTP repetidos |

**Archivos con el mismo nombre en carpetas distintas**, y uno ya causó daño:

- **`nomina_diputados.csv` existe dos veces con CONTENIDO DISTINTO**: la acumulada
  (`datos/padron/data/`, **1.454 filas**) y la foto vigente (`datos/padron/data/raw/`,
  **257 filas**). `ingesta_padron.py` toma por defecto la de 257 y **borra 18 años de
  historia sin dar error**. Está en `URGENTE.md` punto 1. Es el ejemplo de que esto no
  es prolijidad: es pérdida de datos.
- `to_canonical.py`, `asuntos-diputados.csv`, `bloques-diputados.csv`,
  `votaciones-diputados.csv` aparecen repetidos — revisar si son copias o etapas.

**Duplicaciones encontradas y YA resueltas el 22-08** (sirven de patrón, no hay que
volver a hacerlas): las guardas de sobreconfianza estaban definidas en 3 lugares y
faltaban en un 4º; `alineacion_individual` vivía en `casos/` y se levantó al modelo; el
tablero por legislador y la probabilidad salían de dos cálculos distintos; el umbral de
mayoría del navegador no era el del Python.

**Sin revisar, anotado al pasar:** `casos/proyeccion_hipotetica_bicameral.py` mantiene
su propio diccionario `PADRON` y su propia lógica de postura, en paralelo a
`nowcast_puertas`. Es candidato fuerte.

---

## Cómo se decide qué hacer con cada hallazgo

Para cada duplicación, **una de tres salidas, y ninguna es "lo dejo así"**:

1. **Unificar.** Vive en un solo lugar y los demás lo consumen. Requiere un **test que
   falle con el código viejo** — si no, no se sabe si el cambio hizo algo.
2. **Declararla intencional.** A veces dos módulos deben ser independientes a propósito.
   Entonces se escribe **por qué** en los dos lados, y el comentario dice qué pasa si
   divergen. Un «mantener sincronizadas» sin motivo NO cuenta: eso es lo que falló.
3. **Dejarla y decir por qué no se toca ahora.** Con el motivo escrito y, si bloquea a
   alguien, en `URGENTE.md`.

**El criterio para elegir:** ¿si estas dos copias divergen mañana, alguien se entera?
Si la respuesta es no, es deuda activa.

---

## Límites duros

- **No refactorizar por gusto.** Un cambio que no arregla una divergencia posible ni
  reduce el costo de leer el repo, no va. El objetivo no es código bonito.
- **Un módulo, un dueño, una rama.** Reclamalo en `TABLERO.md` antes de escribir. No se
  edita el código de otro módulo: se consume su contrato.
- **Tocar algo compartido exige ADR** en `coordinacion/DECISIONES/` (el próximo es el
  **0014**) y aviso en el TABLERO. Unificar `periodo_parlamentario` es, precisamente,
  cambio de contrato compartido.
- **Régimen de `Archivos_Borrar/`:** lo que hay que dar de baja se copia, **se
  neutraliza el original** y se anota en `PENDIENTES-DE-BORRAR.md`. Un archivo que hay
  que borrar y sigue funcionando no es un pendiente, es un problema activo.
- **«Pasa en el sandbox» no es «pasa».** Guardas con `pd.isna()`, tests sobre los dos
  backends de dtype. La corrida de Valle es la que vale.
- **Prefijá `GIT_OPTIONAL_LOCKS=0`** a todo comando git, o le trabás el git a Valle.

---

## Lo que NO es esta tarea

- **No es emprolijar el `MAPA-MODELO.html`.** El dibujo arranca encajado abajo con media
  pantalla vacía y *Ajustar* no lo recentra — medido: 3799×754 con 96 nodos, 4312×754
  con 101, o sea que **viene de antes**. Es su propia tarea y va DESPUÉS de ésta, porque
  el mapa dibuja el repo: si primero se emprolija el dibujo y después se limpia el
  código, hay que rehacerlo. Es plausible que parte del problema visual se arregle solo
  al sacar nodos duplicados.
- **No es armar el backtest.** Está neutralizado a propósito y antes hay que decidir
  contra qué se mide (ver ADR-0012). Esa decisión no depende de esta tarea.
- **No es la Tarea 2** (nombres de las puertas), que sigue pendiente en `PROMPT-3`.

---

## Qué entregar

1. **Un inventario de lo repetido**, con archivo y línea, y para cada ítem cuál de las
   tres salidas se eligió y por qué.
2. **Las unificaciones hechas**, cada una con su test que falla con el código viejo.
3. **El ADR** de lo que haya sido contrato compartido.
4. **Las 4 bitácoras movidas juntas** y `URGENTE.md` al día.
5. **Reindexar** (`python .mapa/indexar.py .`). Ojo: `MAPA.md` da **264 líneas contra un
   presupuesto de 260** — si la limpieza no lo baja sola, decidir qué se poda.

---

**Antes de escribir código: invocá `mapa-de-proyectos`, verificá contra el disco los
puntos de partida de arriba, y contame qué encontraste y qué pensás unificar. Esperá
que Valle confirme.**
