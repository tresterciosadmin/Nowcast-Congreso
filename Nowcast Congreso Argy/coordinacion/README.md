# coordinacion/ — el estado vivo del proyecto

<!-- huella: 44513fe83307 -->

**Resumen:** Las bitacoras y el protocolo: que bloquea a otros, que se hizo, quien tomo que modulo y por que se decidio cada cosa. Aca NO hay codigo del producto.

## Buscar acá si

- que hay que resolver antes de empezar a trabajar (`URGENTE.md`, siempre primero)
- que se hizo y cuando (`ESTADO-DEL-PROYECTO.md`, entrada mas reciente arriba)
- lo mismo contado sin tecnicismos (`EN-HUMANO.md`)
- que modulo esta tomado y por quien (`TABLERO.md`)
- por que se decidio algo (`DECISIONES/`, los ADR)
- como ramificar y mergear sin conflictos (`PROTOCOLO-GIT.md`)
- que hacer y en que orden, por modulo y fase (`PLAN-DE-TRABAJO.md`)

## Que hay acá

| Archivo | Que es | Cuando se toca |
|---|---|---|
| `URGENTE.md` | bandeja de lo que bloquea o ensucia trabajo de otros | se lee al EMPEZAR; lo resuelto se BORRA (queda el registro en ESTADO) |
| `ESTADO-DEL-PROYECTO.md` | bitacora tecnica permanente | en el mismo cambio que el codigo, entrada nueva arriba |
| `EN-HUMANO.md` | la misma bitacora sin tecnicismos | junto con ESTADO |
| `TABLERO.md` | claim de modulos (anti-colision) | al reclamar y al liberar un modulo |
| `PLAN-DE-TRABAJO.md` | el plan por modulo y fase | cuando cambia el rumbo |
| `PROTOCOLO-GIT.md` | ramas, PRs, conflictos | rara vez |
| `DECISIONES/` | ADR numerados. Las revisiones van como `## Enmienda <fecha>` arriba, el cuerpo queda como registro historico | al elegir entre alternativas con costo real |
| `CIERRE-SESION-*.md`, `CORRIDA-*.md`, `PUESTA-EN-MARCHA-*.md` | notas de una sesion concreta | son historicos: no se actualizan |
| `_aplicar_*.py`, `_reparar_tablero.py` | parches de un solo uso **ya ejecutados y NEUTRALIZADOS** | no correrlos: volver a hacerlo duplica entradas de bitacora |

## Trampas

- **Las cuatro bitacoras se mueven JUNTAS** (ESTADO + EN-HUMANO + TABLERO + `tablero_datos.js` en la raiz). Un cambio que toca el estado y mueve solo una deja el repo inconsistente.
- **El disco manda sobre las cuatro.** Antes de repetir una cifra que leiste aca, abri el archivo o el parquet. La auditoria del 06-08-2026 encontro la canonica con tres cifras distintas en circulacion.
- **`URGENTE.md` no lleva seccion de "resueltos".** El 04-08 se dejo una y adentro quedo enterrado un pendiente vivo durante dos dias.
- `ESTADO-DEL-PROYECTO.md` pesa ~360 KB: **no reescribirlo entero**, el mount lo trunca y el read-modify-write propaga el corte.
