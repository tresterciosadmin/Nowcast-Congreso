# casos/ — informes de un proyecto concreto

<!-- huella: bfe7ad62580e -->

**Resumen:** Aplicaciones del nowcast a un caso real (una ley concreta): el panel de puertas en HTML. Consume los contratos de `modelo/` y `variables/`; no define modelo propio. Quedo UN generador: los otros dos -bicameral y proyeccion hipotetica- estaban neutralizados desde agosto y se archivaron el 2026-09-10.

## Buscar acá si

- el informe o el HTML de una ley concreta (Ganancias, lobby, ...), y el generador de los paneles que estan en la RAIZ
- proyectar un proyecto por las DOS camaras (origen + revisora): eso lo hace `modelo/ensemble/src/puerta_d.py`, no esta carpeta
- por que un caso da un numero distinto al del ensemble

## Que hay acá

| Archivo | Que es |
|---|---|
| `nowcast_bicameral_html.py` | genera el informe HTML bicameral de un proyecto |
| `proyeccion_hipotetica_bicameral.py` | ⛔ **NEUTRALIZADO 2026-08-25.** Era la TERCERA formulacion del numero: umbral de mayoria ABSOLUTA en vez de simple, y el share del bloque sin componer con el desvio. Su `main` levanta `SystemExit`; el cuerpo viejo quedo como `_main_original` por si se rehace sobre `nowcast_puertas`. |
| `2026-07-31_ley-de-lobby.md` / `.json` | el caso testigo de la ley de lobby, con su scoring |

## Trampas

- Los HTML que estos scripts producen **quedan en la raiz del repo**, no acá ni en `producto/dashboard/`. Es deuda conocida, no un descuido: `TABLERO-CONTROL.html` se abre con doble clic desde la raiz y esta citado en CLAUDE.md y en varias entradas de ESTADO.
- Estos informes usan `proyectar_postura` **condicionado por el origen del proyecto**. Si un caso viejo da otro numero, mira si no estaba usando `proyectar_lineas_alineacion` (promediaba todo).
- **Dos de los tres generadores de esta carpeta estan neutralizados** (`nowcast_bicameral_html.py` el 22-08, `proyeccion_hipotetica_bicameral.py` el 25-08). No es limpieza: cada uno calculaba el acompañamiento con mecanismo propio y quedo desfasado del modelo sin que nada fallara. **El unico vivo es `nowcast_puertas_html.py`**, que consume `modelo/ensemble/src/nowcast_puertas.py` en vez de calcular. Si vas a agregar un caso nuevo, copia ESE — no los otros dos.
- Los HTML que produjeron los neutralizados **siguen en la raiz con las cifras viejas adentro** (`Nowcast-Ganancias-bicameral.html`). El que vale es `Nowcast-Puertas.html`.
