# Módulo: producto/dashboard

<!-- huella: e5d193d4e732 -->

**Propósito.** (Histórico) Tablero interno: radar de tracción + mapa de pivotes + escenarios + el mapa del modelo. Encuadre augmentation.

**Estado:** SIN CÓDIGO desde el 2026-09-30. La v1 —los paneles HTML de la raíz y el generador del Mapa del Modelo (`src/generar_mapa_modelo.py`)— se **eliminó en la auditoría 2026-09 (ítem A6, decisiones 1 y 6 de Franco)**. Queda sólo la capa curada `data/mapa_modelo_semantica.json`, sin consumidor (ver abajo).
**Owner actual:** — (sin reclamar)

**Resumen:** Módulo sin código: conserva `data/mapa_modelo_semantica.json`, la capa CURADA del mapa del modelo (qué calcula cada script en castellano, qué significa cada parquet, qué puertas están parqueadas y por qué). Su generador y los tres paneles HTML se eliminaron en la auditoría 2026-09.

## Buscar acá si

- el significado, escrito a mano, de cada script y de cada dato de la maquinaria del cálculo (`data/mapa_modelo_semantica.json`)
- por qué ya no hay paneles ni tablero HTML: `README.md` de la raíz («Los paneles HTML») y `coordinacion/QUE-SE-MIDE.md`
- cómo era el generador del mapa: `git log -- producto/dashboard/src/generar_mapa_modelo.py`

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Qué quedó y qué se eliminó

| | |
|---|---|
| **Eliminado (A6, 2026-09-30)** | `TABLERO-CONTROL.html` + `tablero_datos.js`; `MAPA-MODELO.html` + `mapa_modelo_datos.js` + `src/generar_mapa_modelo.py`; `Nowcast-Puertas.html` + `casos/nowcast_puertas_html.py`. Copias en `Archivos_Borrar/A6-eliminados/` y recuperables con `git log -- <ruta>` |
| **Se conserva** | `data/mapa_modelo_semantica.json` (73 KB): texto curado que costó trabajo escribir y que nadie decidió descartar. **No tiene consumidor** desde que se eliminó su generador; qué hacer con él está en `coordinacion/AUDITORIA-2026-09/PENDIENTES-POST-AUDITORIA.md` |

**Por qué se eliminaron.** «Esta es una etapa de puesta en marcha operativa»: lo que corresponde
es declarar cuánto se mide de verdad y dejar como tarea aumentarlo (`coordinacion/QUE-SE-MIDE.md`), no
mantener paneles con lógica del motor duplicada en JS —el modo de falla que este README ya había
documentado— que llegaron a mostrar cifras de meses atrás (el panel de puertas decía 0,9801 cuando
el motor daba 0,6132).

## Contrato
- **Entradas:** ninguna (sin código).
- **Salida:** ninguna.
- **Gate de pase:** Una consultora valida utilidad en entrevista — **sin cumplir**, y ya no hay entregable que validar.
