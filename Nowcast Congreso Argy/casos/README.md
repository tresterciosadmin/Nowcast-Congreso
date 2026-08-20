# casos/ — informes de un proyecto concreto

<!-- huella: f1462ad6a724 -->

**Resumen:** Aplicaciones del nowcast a un caso real (una ley concreta): el scoring, el informe en HTML y la proyeccion bicameral. Consumen los contratos de `modelo/` y `variables/`; no definen modelo propio.

## Buscar acá si

- el informe o el HTML de una ley concreta (Ganancias, lobby, ...)
- proyectar un proyecto por las DOS camaras (origen + revisora)
- por que un caso da un numero distinto al del ensemble
- el generador de los paneles HTML que estan en la raiz del repo

## Que hay acá

| Archivo | Que es |
|---|---|
| `nowcast_bicameral_html.py` | genera el informe HTML bicameral de un proyecto |
| `proyeccion_hipotetica_bicameral.py` | proyeccion de un escenario hipotetico por ambas camaras |
| `2026-07-31_ley-de-lobby.md` / `.json` | el caso testigo de la ley de lobby, con su scoring |

## Trampas

- Los HTML que estos scripts producen **quedan en la raiz del repo**, no acá ni en `producto/dashboard/`. Es deuda conocida, no un descuido: `TABLERO-CONTROL.html` se abre con doble clic desde la raiz y esta citado en CLAUDE.md y en varias entradas de ESTADO.
- Estos informes usan `proyectar_postura` **condicionado por el origen del proyecto**. Si un caso viejo da otro numero, mira si no estaba usando `proyectar_lineas_alineacion` (promediaba todo).
