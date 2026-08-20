# Módulo: datos/padron

<!-- huella: 3a1b4340baa7 -->

**Propósito.** Padrón **oficial** de bancas a nivel **LEGISLADOR** (no bloque): quién
ocupa cada banca y en qué ventana de mandato. Es la **composición de la cámara a la
fecha** — la pieza que faltaba para que el proyector/agregador usen el roster real
(257 Diputados / 72 Senado) en lugar de contar votantes por ventana móvil (que
inflaba el cuerpo con el recambio del 10-dic).

**Estado:** EN CURSO (v1: Diputados 257 + Senado 72 vigentes) · **Owner:** Valle (2026-07-14)

**Resumen:** Padron OFICIAL de bancas a nivel LEGISLADOR: quien ocupa cada banca y en que ventana de mandato. Es la composicion real de la camara a una fecha (257 / 72).

## Buscar acá si

- cuantas bancas tiene un bloque a una fecha, o quien estaba en el recinto
- el cuerpo aparece inflado o desinflado (contar votantes vs. roster real)
- recambio del 10-dic, reemplazos, renuncias, bancas vacantes
- el padron cambio y hay que revisarlo (`vigilar_padron.py`, corre los lunes)
- el padron historico del Senado (reconstruido de nomina oficial + Wikipedia)

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
