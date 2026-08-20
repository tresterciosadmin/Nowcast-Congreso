# Módulo: producto/dashboard

<!-- huella: 8d96242db60d -->

**Propósito.** Tablero interno: radar de tracción + mapa de pivotes + escenarios. Encuadre augmentation.

**Estado:** EN CURSO — v1 entregada como **paneles HTML en la raíz del repo**, no como
app. Corregido el 2026-08-06: figuraba "PENDIENTE / vacante" cuando ya había cinco
paneles construidos. **2026-08-20: el módulo tiene por primera vez código propio**
(`src/generar_mapa_modelo.py` + la capa curada en `data/`), no sólo entregables sueltos
en la raíz.
**Owner actual:** Claude+Valle (desde 2026-07-10)

**Resumen:** Tablero interno: radar de traccion, mapa de pivotes y escenarios, y el MAPA DEL MODELO: el grafo de como se calcula P(sancion), generado desde el indice del repo. Los entregables se abren con doble clic desde la RAIZ; el codigo del generador vive aca.

## Buscar acá si

- los paneles que se abren con doble clic (estan en la raiz, no aca)
- el tablero ejecutivo `TABLERO-CONTROL.html` (se edita solo `tablero_datos.js`)
- de donde sale el numero: el mapa de la maquinaria del calculo (`MAPA-MODELO.html`)
- que script transforma que dato, o que archivo implementa una etapa del calculo
- las DOS formulaciones que conviven (v1 en produccion y las puertas A-B-C-D)
- que piezas del modelo estan parqueadas, pendientes o son huecos conocidos
- regenerar los datos de un panel sin tocar su HTML
- los informes bicamerales por caso (los generadores estan en `casos/`)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Lo que ya existe (todo en la raíz, doble clic, sin internet)

| Archivo | Qué muestra | Desde |
|---|---|---|
| `TABLERO-CONTROL.html` | mapa ejecutivo: plan y avance (se alimenta de `tablero_datos.js`; **no se edita el HTML**) | 2026-07-02 |
| `MAPA-MODELO.html` | **la maquinaria**: cómo se calcula P(sanción), de la fuente oficial al número (se alimenta de `mapa_modelo_datos.js`; **no se edita el HTML**) | 2026-08-20 |

> Los dos son complementarios y no se pisan: **TABLERO-CONTROL muestra el PLAN y el
> AVANCE; MAPA-MODELO muestra la MÁQUINA.** Si la pregunta es "¿cómo venimos?", es el
> primero. Si es "¿de dónde sale este número?", es el segundo.

> Los paneles `PANEL-NOWCAST/MOVIL/COYUNTURA.html` y el `COMPARADOR-ICG.html`
> (2026-08-04) se **dieron de baja el 2026-08-11** al eliminar la capa 2 global del
> ICG (ver ADR-0008, enmienda). Los paneles de coyuntura servían para que el analista
> asignara la intensidad global, que ya no existe.

**Decisión de forma (no escrita hasta hoy):** se eligió HTML autocontenido en vez de
Streamlit porque el equipo lo abre con doble clic, sin instalar nada y sin internet.
El costo es que la lógica del motor está duplicada en JS. Si el dashboard pasa a ser
producto, esa duplicación es lo primero a resolver.

**Requisito operativo (ADR-0008):** ningún nowcast se publica sin evaluación de
coyuntura registrada. Se genera en `PANEL-COYUNTURA.html` / `PANEL-MOVIL.html`.

## El Mapa del Modelo — cómo está armado

Dos capas, igual que el resto del repo separa diseño de datos. **Ningún dato vive
dentro del HTML**: ese es el modo de falla documentado de este proyecto (la copia que
envejece y a los tres meses miente).

| Archivo | Qué es | Se edita a mano |
|---|---|---|
| `MAPA-MODELO.html` (raíz) | el diseño: grafo SVG, filtros, ficha lateral, tabla gemela, leyenda | **NO** |
| `mapa_modelo_datos.js` (raíz) | los datos del grafo | **NO** — se genera |
| `src/generar_mapa_modelo.py` | la capa **mecánica**: lee el repo | sí (es código) |
| `data/mapa_modelo_semantica.json` | la capa **curada**: el significado | **SÍ — es el único archivo que se toca para corregir un nodo** |

**Qué hace cada capa.**

- **Mecánica** (`generar_mapa_modelo.py`): lee `.mapa/mapa.json` (LOC, símbolos con
  línea, entrypoints), importa `rutas.py` y usa su `inventario()`, y saca el
  `**Estado:**` / `**Owner actual:**` del `README.md` de cada módulo. Un parquet hereda
  el estado y el dueño del módulo que lo produce: el módulo se deduce del path (el
  ancestro más cercano con README), no se copia a mano.
- **Curada** (`mapa_modelo_semantica.json`): qué calcula cada script en castellano, qué
  significa cada parquet, la fórmula de cada etapa, qué puertas están parqueadas y por
  qué, los cinco "caminos" guiados y las trampas conocidas.

**El control que importa.** Si un nodo declara un `archivo` que no existe en disco, o
una `ruta_declarada` que no está en `rutas.py`, **el generador falla y no escribe
nada**. Un mapa que apunta a un archivo que se movió es peor que no tener mapa.

**Cómo regenerarlo** (desde la raíz del proyecto):

    python producto/dashboard/src/generar_mapa_modelo.py

Tiene que imprimir `OK  96 nodos - 130 aristas - N problemas`. Los "problemas" son
avisos, no errores: outputs que todavía no se corrieron, o READMEs sin la línea
`**Estado:**`. Se listan arriba de la tabla gemela, dentro del propio mapa.

Para ver qué cambiaría sin escribir nada: `--verificar`.

**Qué tocar según lo que cambió:**

| Cambió… | Se toca |
|---|---|
| el estado o el dueño de un módulo | el `README.md` de ese módulo (y nada más) |
| lo que hace un script, o el significado de un parquet | `data/mapa_modelo_semantica.json` |
| se agregó un artefacto que cruza módulos | `rutas.py` primero, después la capa curada |
| se despachó la Puerta C, o se estimó `delta` en la D | sólo la capa curada |
| el aspecto del mapa | `MAPA-MODELO.html` (es diseño, y es lo único que se edita ahí) |

## Contrato
- **Entradas:** modelo/ensemble, variables/embudo, variables/proyecto (ICG); y para el
  Mapa del Modelo: `.mapa/mapa.json`, `rutas.py` y los `README.md` de cada módulo
- **Salida (contrato estable):** paneles HTML autocontenidos en la raíz + su `*_datos.js`
- **Depende de:** modelo/ensemble
- **Gate de pase:** Una consultora valida utilidad en entrevista — **sin cumplir**

## Cómo trabajar acá
1. Reclamá este módulo en `coordinacion/TABLERO.md` (poné tu nombre/ID y fecha).
2. Trabajá en una rama `feat/dashboard-<desc-corta>`.
3. No toques archivos de otros módulos. Si necesitás cambiar un contrato compartido (p. ej. `docs/schemas`), abrí un ADR en `coordinacion/DECISIONES/` primero.
4. Al terminar (o al hacer un avance relevante), **agregá una entrada a `coordinacion/ESTADO-DEL-PROYECTO.md`** y abrí un PR.
5. Si tocaste un panel, **corré su generador y commiteá el `*_datos.js`** en el mismo PR.
   Y corré `git check-ignore -q <archivo>` sobre las salidas nuevas antes de commitear:
   las reglas `*.csv` / `*.parquet` del `.gitignore` ya escondieron trabajo cuatro veces.

## Convenciones de código
Resiliencia obligatoria: errores específicos, reintentos con backoff en I/O de red, parsing defensivo, logging estructurado. Reusá `datos/_common/` cuando exista.
