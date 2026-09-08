# Módulo: datos/manual_2026

<!-- huella: e3b0c44298fc -->

**Propósito.** Integrar el Excel curado a mano por Franco (período 2025–2027) al esquema canónico. Aporta votos nominales 2026 de **ambas cámaras**, padrón con **bloque del Senado** (resuelve el hueco), provincia, comisión y mandato.

**Estado:** HECHO (primera carga). Fuente viva: Franco la sigue completando a mano.

**Resumen:** El Excel curado a mano por Franco (2025-2027). FUERA DEL PIPELINE desde el 06-09: sus 17 actas eran las mismas votaciones que ya trae argentinadatos, con fecha y expediente.

## Buscar acá si

- por que el Excel salio del pipeline (sus 17 actas eran gemelas de argentinadatos)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entrada:** `Congreso_25-27.xlsx` (hojas Diputados, Senado; una columna por ley con el voto de cada legislador).
- **Salida:** `data/clean/manual_2026_{actas,votos}.parquet` (esquema canónico, fuente=`manual_2026`).
- **Correr:** `XLSX=Congreso_25-27.xlsx python src/to_canonical.py`

## Mapeo
- Cada (ley × cámara) con votos → un acta (`manual_2026:<camara>:<slug_ley>`).
- Voto: AFIRMATIVO/NEGATIVO/ABSTENCIÓN/AUSENTE. "PRESIDENTE" → AUSENTE. "PENDIENTE DE INCORPORACIÓN" → se excluye (banca no asumida).
- `legislador_nombre` = "Apellido, Nombre".
- **`distrito`: manda el PADRÓN** (`datos/padron/data/padron_{camara}.csv`), no el Excel. Ver "El distrito no sale del Excel" abajo.
- **`bloque`: manda el EXCEL.** El padrón se compara y se **reporta**, pero no se pisa.
- `fecha` queda vacía (el Excel no trae fecha por ley); por eso estos votos no entran en el corte por año del baseline.

## El distrito no sale del Excel (06-09-2026)

La columna PROVINCIA de la hoja Senado estaba **desalineada**: 66 de 72 senadores tenían
el distrito de otro. No era un corrimiento —ningún offset lo explicaba— sino una
**permutación**: las 72 provincias correctas estaban todas, repartidas entre las personas
equivocadas. Es la firma de un "ordenar sin extender la selección". Y no dio error: el dato
entró a la canónica y ahí se quedó.

Desde entonces el Excel es la fuente de los **votos**, y la identidad se resuelve contra el
padrón oficial. Tres reglas, cada una con su motivo:

| | qué hace | por qué |
|---|---|---|
| `distrito` | **el padrón lo pisa**, y cada corrección se reporta | es estable mientras dure la banca |
| `bloque` | **se reporta y NO se pisa**; decide una persona | depende del tiempo: pisarlo le pone a un voto de marzo el bloque de agosto (leakage que no da error) |
| la comparación | **normalizada** (sin acentos, mayúsculas, alias de CABA y Tierra del Fuego) | el padrón guarda "Santa Fe" y el Excel "SANTA FE": comparar sensible a mayúsculas "corrige" 256 filas que estaban perfectas — pasó al escribir esto |

`_reportar()` escala el aviso: si más de la mitad de los distritos no coincide, dice que
**eso no es una fila mal cargada, es una columna desalineada**.

Tests: `tests/test_to_canonical.py` (28 checks), incluido el control estructural de que las
24 provincias tengan exactamente 3 senadores cada una.

## Valor
- Extiende la base a 2026.
- **Resuelve el bloque del Senado** → habilitó la primera medición de baseline del Senado (~0,94 en disputadas, muestra chica).
- `manual_2026` tiene **máxima precedencia** en la deduplicación (curado a mano).

## Pendiente
- **Las 17 actas entran con `fecha = None`** y hoy eso se compensa río abajo, dos veces y por separado (`modelo/voto_individual/src/disciplina.py:178` y `variables/legislador/src/ficha.py:61`, ambos ponen `anio = 2026`). Además, sin fecha `_linaje_vec` no encuentra ventana aplicable y **JUSTICIALISTA del Senado 2025-2027 no llega a ningún linaje**. Es URGENTE I: la fecha tiene que resolverse **acá, una vez**, y eso pide decidir qué fecha lleva un proyecto anunciado y sin votar.
- Cuando Franco agregue fechas por ley, enriquecer `fecha`.
- Usar el padrón del Senado para **retro-completar** el bloque de los votos de argentinadatos 2024–2025 (hoy "SIN BLOQUE").
