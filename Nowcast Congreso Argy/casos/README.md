# casos/ — informes de un proyecto concreto

<!-- huella: bfe7ad62580e -->

**Resumen:** Casos reales del nowcast (una ley concreta), escritos a mano: hoy, el caso testigo de la ley de lobby con su scoring. Consume los contratos de `modelo/` y `variables/`; no define modelo propio. **Ya no hay generadores:** el último, `nowcast_puertas_html.py` (el panel de puertas en HTML), se eliminó en la auditoría 2026-09 (A6); los otros dos —bicameral y proyección hipotética— estaban neutralizados desde agosto y se archivaron el 2026-09-10.

**Estado:** sin generadores (2026-09-30). El número de un proyecto sale de `modelo/ensemble/src/nowcast_puertas.py` (consola o `--json`); su versión guardada es `modelo/ensemble/outputs/panel_regresion.json`.
**Owner actual:** — (sin reclamar)

## Buscar acá si

- el informe de una ley concreta (Ganancias, lobby, ...)
- proyectar un proyecto por las DOS camaras (origen + revisora): eso lo hace `modelo/ensemble/src/puerta_d.py`, no esta carpeta
- por que un caso da un numero distinto al del ensemble

## Que hay acá

| Archivo | Que es |
|---|---|
| `2026-07-31_ley-de-lobby.md` / `_scoring.json` | el caso testigo de la ley de lobby, con su scoring |

## Trampas

- Estos informes usaban `proyectar_postura` **condicionado por el origen del proyecto**. Si un caso viejo da otro numero, mira si no estaba usando `proyectar_lineas_alineacion` (promediaba todo).
- Los generadores que hubo acá calculaban el acompañamiento con mecanismo propio y quedaron desfasados del modelo sin que nada fallara (los dos neutralizados el 22-08 y el 25-08). Por eso no se rehacen: el número se consume de `nowcast_puertas.nowcast()`.
- El panel HTML eliminado se recupera con `git log -- casos/nowcast_puertas_html.py` (y `Nowcast-Puertas.html`).
