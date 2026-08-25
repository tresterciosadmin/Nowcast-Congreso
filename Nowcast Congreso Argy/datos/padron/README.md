# Módulo: datos/padron

<!-- huella: e3b0c44298fc -->

**Propósito.** Padrón **oficial** de bancas a nivel **LEGISLADOR** (no bloque): quién
ocupa cada banca y en qué ventana de mandato. Es la **composición de la cámara a la
fecha** — la pieza que faltaba para que el proyector/agregador usen el roster real
(257 Diputados / 72 Senado) en lugar de contar votantes por ventana móvil (que
inflaba el cuerpo con el recambio del 10-dic).

**Estado:** EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)

**Resumen:** Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72).

## La foto de la cámara a una fecha (`src/padron_vigente.py`, 2026-08-22)

`padron_vigente(camara, fecha)` devuelve **una fila por banca**: el padrón OFICIAL
primero y el HISTÓRICO rellenando lo que aquél no cubre. Es lo que consume
`modelo/ensemble.roster_nominal`, que hasta hoy leía **un solo archivo** — y el
oficial cubre 81 de 257 bancas en 2008 y 203 en 2019, así que todo cálculo sobre
fechas viejas corría sobre una cámara agujereada. Medido: la Puerta D al 2024-06-01
pasó de 0,6525 a 0,9900 al dejar de simular sobre 188 bancas y pasar a 258.

**Pegarlos sin más no sirve, y está medido:** al 2026-06-01 el concat crudo da **513
diputados en vez de 257**. Y deduplicar por `legislador_id` tampoco alcanza, porque
la misma persona tiene otro id en cada archivo cuando su nombre está escrito distinto:

| oficial | histórico |
|---|---|
| `ANALIA QUIROGA RACH` | `ALEXANDRA ANALIA QUIROGA RACH` |
| `BAHILLO JOSE JUAN` | `BAHILLO JUANJO` |
| `MARCELA PAULA URROZ` | `PAULA URROZ` |

La solución no es nueva: **match por SUBCONJUNTO de tokens**, la misma regla que
`datos/expedientes/src/resolver_firmantes.py` usa para emparejar firmantes de
dictamen. Se reusa su tokenizador. Y **un empate nunca se rompe por la fuerza**: si
una fila del histórico matchea con dos oficiales, no se colapsa contra ninguna y se
cuenta como ambigua.

**El control, contra las 257 bancas reales** (`python datos/padron/src/padron_vigente.py`):

| fecha | oficial | histórico | bancas | desvío | ambiguas |
|---|---|---|---|---|---|
| 2008-06-01 | 81 | 257 | 256 | −1 | 0 |
| 2013-06-01 | 221 | 264 | 257 | 0 | 0 |
| 2019-06-01 | 203 | 256 | 259 | +2 | 0 |
| 2024-06-01 | 188 | 257 | 258 | +1 | 0 |
| 2026-06-01 | 257 | 256 | 257 | 0 | 0 |

El desvío de −1/+2 es **rotación real** (renuncias y asunciones a mitad de período),
el mismo patrón que ya se midió al construir el histórico. Un desvío grande sí sería
un problema de emparejamiento, y el control lo diría.

⚠️ **El Senado antes de 2017-12-10 da 0 bancas** y el control lo marca con −72: el
padrón histórico del Senado todavía no existe. Es la decisión pendiente anotada en
el TABLERO, y acá se ve sin tener que buscarla.

## Buscar acá si

- cuantas bancas tiene un bloque a una fecha, o quien estaba en el recinto
- el cuerpo aparece inflado o desinflado (contar votantes vs. roster real)
- recambio del 10-dic, reemplazos, renuncias, bancas vacantes
- el padron cambio y hay que revisarlo (`vigilar_padron.py`, corre los lunes)
- el padron historico del Senado (reconstruido de nomina oficial + Wikipedia)
- el padron historico de DIPUTADOS (reconstruido de la canonica; la nomina
  oficial solo cubre la foto vigente: 81 de 257 bancas en 2008)
- un anio da mas de 257 bancas (son duplicados de entity resolution)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Por qué a nivel legislador (no bloque)
El valor del nowcast está en los **legisladores pivote de las votaciones disputadas**,
no en el promedio del bloque (que ya se predice ~99%). El padrón individual permite
enganchar a cada banca su **desvío individual** (`modelo/voto_individual`) y, más
adelante, su voto proyectado por proyecto — que es lo que define las votaciones al filo.

## Contrato de salida (`data/padron_<camara>.csv`)
Una fila por legislador-mandato:

- `legislador` — nombre (Apellido, Nombre).
- `clave` — clave canónica invariante al formato (join con la canónica y con
  `variables/legislador` / `modelo/voto_individual`). Se genera con `_name_key` de
  `datos/canonica/entity_resolution` (misma lógica, sin drift).
- `legislador_id` — `leg:<hash>` derivado de la clave (mismo id que la canónica).
- `camara` — diputados | senado.
- `distrito` — provincia/distrito.
- `bloque` — bloque crudo de la nómina oficial.
- `bloque_norm`, `bloque_linaje` — normalización y linaje **reusando
  `entity_resolution`** (consistente con `variables/bloque` y el agregador). El linaje
  se resuelve con la fecha de inicio de mandato (para las reglas por ventana).
- `desde`, `hasta` — mandato formal (ISO). **Composición a la fecha F** = filas con
  `desde <= F <= hasta`.
- `fuente`, `nota`.

## Fuente
Nómina oficial de la cámara (columnas `Apellido, Nombre, Distrito, IniciaMandato,
FinalizaMandato, Bloque`). El entorno no alcanza los dominios oficiales; la nómina se
baja aparte y se deja en `data/raw/nomina_<camara>.csv`. El módulo solo **normaliza**.

## Cómo correr
```
python datos/padron/src/ingesta_padron.py diputados            # usa data/raw/nomina_diputados.csv
python datos/padron/src/ingesta_padron.py diputados <in.csv> <out.csv>
```
Imprime bancas por linaje + total (debe dar 257 Dip / 72 Sen) + los bloques crudos
que cayeron a `OTRO / PROVINCIAL` (para revisar el mapeo).

## v1 y qué falta
- **Hecho:** Diputados 257 (post recambio dic-2025) y Senado 72 vigentes, con mandato
  individual y linaje. Nómina Senado = export oficial `.xls` (columnas DESIGNACIÓN/CESE
  LEGAL como desde/hasta); se convierte a CSV con LibreOffice.
- **Flag conocido (mapeo):** 4 bancas de la izquierda (variantes 2025 del FIT:
  "PARTIDO OBRERO EN EL FRENTE..." y "PTS-FRENTE...") caen hoy en `OTRO / PROVINCIAL`
  porque sus strings 2025 no están en los alias de `entity_resolution`. Agregarlos es
  cambio de contrato compartido (ADR) → queda anotado, no se toca acá.
- **Falta:** histórico profundo de mandatos (fase 2) para nowcast de fechas pasadas;
  hoy el padrón es la foto vigente. Revisar si algunos federales/provinciales del
  Senado (Convicción Federal, Justicia Social Federal, etc.) deben ir a PERONISMO FEDERAL.

## Convenciones
Consume el contrato de `datos/canonica` (no edita su código). Resiliencia: errores
específicos, parsing defensivo (fechas dd/mm/YYYY, comillas internas), logging.

## Padrón vivo — `src/vigilar_padron.py` (2026-08-04, URGENTE 2)

Corre **semanal** (workflow `.github/workflows/padron-vivo.yml`, lunes 08:00 ARG)
y compara la nómina contra el padrón versionado. Avisa:

- **altas** (asumió alguien) · **bajas** (renuncias, cesantías, fallecimientos)
- **pases de bloque** — medidos por **linaje**, no por el string crudo. Un cambio
  de texto (`...TRABAJADORES-U` → `...-UNIDAD`) no es una ruptura política y se
  informa aparte. Este chequeo existe porque la primera corrida reportó
  exactamente ese falso positivo.
- **total ≠ 257 / 72** — la alarma más barata del proyecto.

Idempotente: la huella del diff va a `data/estado_vigilancia.json`; si no cambió,
no re-avisa. La antigüedad del crudo del Senado se mide por **hash de contenido**,
no por `mtime` (en CI el checkout reescribe todo y el mtime siempre diría 0 días).

```bash
python datos/padron/src/vigilar_padron.py                       # ambas cámaras
python datos/padron/src/vigilar_padron.py --camara senado --dry-run
python datos/padron/tests/test_vigilar_padron.py                # 15 chequeos offline
```

Códigos de salida: `0` sin novedades · `10` novedades · `20` alarma dura.

## Padrón HISTÓRICO del Senado (nuevo, 2026-08-08 — línea Revisión de Comisiones)

`src/padron_senado_historico.py` cierra el pendiente "falta histórico de
mandatos" **del lado del Senado**. Antes había sólo la foto de los 72 vigentes,
así que no se podía revivir la composición de una votación pasada — y sin eso no
se puede backtestear la cadena entre cámaras.

**No hubo que bajar nada nuevo.** Se unifican dos fuentes que ya estaban:
`datos/senado/data/padron_bloques_senado.csv` (291 tramos de Wikipedia,
2017-2025) y `data/padron_senado.csv` (72 vigentes, oficial). Ante solape manda
la oficial; Wikipedia aporta la historia que la oficial no tiene.

**Salida:** `data/padron_senado_historico.csv` — **mismo esquema que
`padron_diputados.csv`**, para que los consumidores traten a las dos cámaras
igual. **243 tramos, 176 senadores, 2017-12-10 → 2031-12-09.**

**Decisiones:**
- Tramos consecutivos con el mismo bloque **se fusionan**: los anexos de
  Wikipedia son por período, así que un mandato de 6 años venía partido en 3.
- El **linaje se calcula con la fecha del tramo**, no sólo con el nombre del
  bloque (ADR-0005: el mismo bloque significa cosas distintas en épocas
  distintas). Se importa `_linaje_vec` de la canónica, no se copia.

🔴 **Reconciliación de identidades — el apellido manda.** Wikipedia usa el nombre
de uso ("Eduardo Vischi") y la nómina oficial el completo ("VISCHI, ALEJANDRO
EDUARDO"): la misma persona generaba dos claves y el padrón devolvía **90 bancas
sobre 72** al 12-jun-2024. Se fusiona sólo si el APELLIDO oficial (antes de la
coma) está contenido en el nombre de Wikipedia **y** comparten un nombre de pila.
Una regla laxa de "comparten 2 tokens" fusionaría *PAGOTTO, Carlos Juan* con
*Juan Carlos Romero* y *BENSUSAN, Daniel Pablo* con *Pablo Daniel Blanco*: son
cuatro senadores distintos y están fijados como test.

⚠️ **Pendiente de criterio del equipo:** al proyectar a marzo-2019 el linaje da
PERONISMO FEDERAL 22 contra FdT-UxP 9. Es la ventana del JUSTICIALISTA del
ADR-0005 aplicada al pie, pero se calibró mirando Diputados. No se parcheó.

⚠️ **Cobertura:** empieza en 2017-12-10. Las fechas anteriores devuelven vacío a
propósito — **no se extrapola**. Algunas fechas dan 69-71 bancas: son huecos
reales de Wikipedia (reemplazos de mandato), no un error de lógica.

```bash
python datos/padron/src/padron_senado_historico.py                 # construye
python datos/padron/src/padron_senado_historico.py --verificar     # sólo controla
python datos/padron/src/padron_senado_historico.py --fecha 2019-03-12
python datos/padron/tests/test_padron_senado_historico.py          # 19 checks
```
```python
from padron_senado_historico import composicion_a_fecha
comp = composicion_a_fecha(df, "2019-03-12")   # 72 filas
```

---

## Padrón HISTÓRICO de Diputados — `src/padron_diputados_historico.py` (2026-08-21)

Cierra para Diputados el pendiente que este README declaraba como fase 2
(*«Falta: histórico profundo de mandatos … hoy el padrón es la foto vigente»*).
Es el análogo de `padron_senado_historico.py`: **archivo aparte, mismo esquema**.

**Por qué hizo falta, con número.** Bancas que el padrón oficial cubre al 1 de
julio de cada año, sobre 257:

    2008:  81   2010: 209   2012: 221   2014: 220   2016: 204
    2018: 196   2020: 242   2022: 142   2024: 193   2026: 257

`nomina_diputados.csv` tiene las mismas 1.454 filas: el hueco viene de la fuente.
Al resolver los firmantes de los dictámenes (`datos/expedientes`), el padrón solo
resolvía el **55%** de las firmas; con el histórico pasa a **98,9%**.

**Fuente:** `datos/canonica` (se consume su contrato, no se toca su código). Que
alguien tenía banca una fecha se prueba porque **votó** ese día; el bloque sale
del voto, o sea point-in-time real; la identidad usa `_name_key`/`_leg_id` de
`entity_resolution`, los mismos que `ingesta_padron.py`. **No hay ids nuevos.**

**Salida:** `data/padron_diputados_historico.csv`, 7.323 filas / 2.060
legisladores, `fuente=derivado:canonica`.

### Qué NO sabe, y lo dice

Un voto prueba presencia **un día**, no los bordes del mandato. Por eso:

- el borde se estira al límite del período sólo si el voto está a menos de
  `MARGEN_DIAS`; si está lejos, arranca en el primer voto, porque probablemente
  sea un **reemplazo** y estirar hacia atrás le inventaría banca **y bloque**;
- el corte entre bloques va **por mes**, no por voto: el `bloque` de la canónica
  cambia de grafía entre votaciones, y cortar cada vez daba 50.036 filas para
  ~3.200 bancas. Un pase de bloque real dura meses; el ruido dura un voto;
- todo eso queda escrito fila por fila en la columna `nota`.

### Los dos límites, medidos

- **2021 y 2022 no se pueden reconstruir:** la canónica tiene 1 y 9 actas de
  Diputados esos años. Es el hueco **Dip 2020-23**, pausado el 10-jul.
- **Algunos años dan más de 257 bancas** (máximo 286 en 2006). `--verificar`
  descompone el exceso: los **74 pares** de `legislador_id` que son la misma
  persona con dos grafías explican casi todo, y el resto —de −4 a +2 desde
  2006— es recambio real. Los pares se listan en
  `Archivos_Borrar/duplicados_entity_resolution_diputados.csv`: **es de
  `datos/canonica`, no de acá.**

### Uso

    python datos/padron/src/padron_diputados_historico.py --verificar   # controla, no escribe
    python datos/padron/src/padron_diputados_historico.py               # escribe
    python datos/padron/tests/test_padron_diputados_historico.py        # 46 checks

Si un control falla, **no escribe el archivo**.
