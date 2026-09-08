# Módulo: datos/taxonomias

**Propósito.** El **registro único** de taxonomías ASIGNADAS: qué tema le corresponde a
cada acta y a cada proyecto, con su procedencia. Una sola tabla, versionada, en texto.

**Estado:** HECHO (registro consolidado, 6.772 asignaciones sobre 3.119 objetos).

**Resumen:** El registro unico de taxonomias asignadas: una fila por (objeto, taxonomia), en CSV versionado, consolidado desde todas las fuentes que existian sueltas.

## Buscar acá si

- que tema tiene un acta o un proyecto, y de donde salio esa asignacion
- por que las taxonomias no aparecian: estaban repartidas en cuatro lugares

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Por qué existe

El 06-09-2026 Franco preguntó por las taxonomías históricas y dijo que el equipo las había
hecho. La respuesta fue que la tabla estaba vacía. **Las dos cosas eran ciertas**, y ése es
el problema: había cuatro lugares donde podían estar y ninguno era EL lugar.

| dónde | tenía | problema |
|---|---:|---|
| `variables/proyecto/data/tema_por_acta.parquet` | 3.083 | binario, `*.parquet` está en `.gitignore` |
| `datos/proyectos/data/taxonomias.csv` | **0** | respaldo de la db; nunca se llenó |
| `proyecto_taxonomias` (en `proyectos.db`) | **0** | la base son 90 MB y no viaja a git |
| `variables/proyecto/outputs/muestra_manual_taxonomias.csv` | 88 | validación a mano, formato propio |

Buscar en el lugar equivocado y concluir "no hay nada" es el modo de fallar de este repo.

## Contrato

- **Salida (contrato estable):** `data/asignaciones.csv` — una fila por
  `(nivel, objeto, taxonomia_id)`.

| columna | qué es |
|---|---|
| `nivel` | `acta` \| `proyecto` |
| `objeto` | `acta_id`, o el denominador del proyecto |
| `taxonomia_id` | id del vocabulario (`ECON.TRIB`, `AUX.TRAMITE`, …) |
| `area` | prefijo del id; derivable, se guarda por comodidad |
| `principal` | 1 si es la principal del objeto, 0 si es secundaria (multitaxonomía, ADR-0006) |
| `confianza` | 0..1 |
| `fuente` | `agente:texto` \| `manual` \| … |
| `asignada_en` | ISO-8601 UTC |

- **Correr:**

```bash
python datos/taxonomias/src/registro.py consolidar   # barre todas las fuentes y une
python datos/taxonomias/src/registro.py estado       # qué hay y de dónde salió
```

`consolidar` es **idempotente**: al mergear gana la de mayor confianza y, a igualdad, la
más reciente. `tema_por_acta.py` lo llama solo al terminar de clasificar.

## Lo que NO guarda

El **vocabulario**. Ése vive en `docs/taxonomias/taxonomias.json` (16 áreas + 3 auxiliares,
con reglas de frontera) y es otra cosa: la lista de qué existe, no de qué se asignó.
Separarlos es correcto; no hay que "unificarlos".

`tema_por_acta.parquet` pasa a ser una **caché derivada**: se puede borrar y se reconstruye.

## Pendiente de decisión

`OPACO` y `PROCEDIMENTAL` son dos etiquetas que la revisión manual usó y el vocabulario NO
tiene. Se mapean a `AUX.SINCLASIF` y `AUX.TRAMITE` (ver `ALIAS_FUERA_DEL_VOCABULARIO`),
pero **`OPACO` merece su propio id**: `AUX.SINCLASIF` dice "no encaja en ninguna, revisar"
y `OPACO` dice algo más preciso y más útil — *el clasificador por título no puede saberlo*
("Temas Varios", "Votación en General y Particular"). Es justamente el techo de la vía
`texto`. Decide Franco: agregarlo al vocabulario o dejarlo mapeado.
