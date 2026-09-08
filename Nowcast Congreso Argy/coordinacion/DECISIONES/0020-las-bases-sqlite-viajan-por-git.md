# ADR-0020 — Las bases SQLite viajan por git

**Fecha:** 2026-09-08 · **Estado:** APLICADO · **Decide:** Franco · **Toca:** `.gitignore`, `tests/test_bases_viajan.py` · **Se relaciona con:** ADR-0009 (proyectos.db es fuente de verdad de proyectos), ADR-0011 (chequeo del gitignore)

## Contexto

`.gitignore` decía `*.db`. La consecuencia: `datos/proyectos/data/proyectos.db`
—que el ADR-0009 declara **fuente de verdad de proyectos**— nunca estuvo en el
repositorio. Vivía en el disco de quien lo hubiera regenerado por última vez.

Eso no es una hipótesis de riesgo, es el modo de falla más repetido de este
proyecto. El propio `.gitignore` documenta **seis** episodios del mismo bug, cada
uno con su fecha y su costo:

| fecha | qué escondió | qué costó |
|---|---|---|
| 11-07 | parquet de `datos/expedientes` | el equipo no veía los datos del embudo |
| 30-07 | roster de jefes de bloque (curado a mano) | — |
| 31-07 | salidas de `variables/embudo` | — |
| 04-08 | `padron_senado.csv` | **una urgencia entera**: URGENTE 3 decía "ninguna fuente publica el bloque del Senado" y el archivo con los 72 senadores existía |
| 06-08 | `p_embudo.parquet` y 3 contratos más | quien clonaba **no podía correr el ensemble** |
| 06-09 | registro único de taxonomías | clasificación que cuesta llamadas de API |

Las seis veces el archivo existía, no daba error, y cualquiera que mirara el repo
concluía —con razón— que el dato no existía.

Sobre la base el efecto es peor que la ausencia: como cada uno la regenera cuando
la necesita, **cada uno termina con SU base**. Las bases divergen sin dar error, y
después se discuten números que salieron de datos distintos. Ya pasó dos veces con
la canónica (el corrector de linaje del Senado del 23-07, construido sobre un
parquet previo a un fix, terminó siendo un no-op sobre 831.677 filas; y el efecto
líder medido sobre datos que ya no existían). La decisión del 31-07 de versionar
la canónica fue exactamente esta discusión, resuelta a favor de versionar.

## Decisión

**Las bases SQLite viajan.** Se saca `*.db` / `*.sqlite` / `*.sqlite3` del
`.gitignore`. Franco acepta explícitamente el costo: *"Sé que hará más pesadas las
cargas y descargas, pero creo que es la mejor forma de mantener una unidad y que
no pase esto de que terminamos teniendo varias bases."*

Se implementa con **git plano**, no con Git LFS. Es la opción elegida sabiendo lo
que sigue.

## Lo medido, que es lo que hace honesta a la decisión

| | valor (08-09-2026) |
|---|---|
| `proyectos.db` en disco | **85,7 MB** |
| comprimida (lo que ocupa **cada versión** en `.git`) | **20,7 MB** (24%) |
| `cuarentena.db` | 4 KB (ya viajaba por excepción desde el 04-08) |
| `.git` antes del cambio | ~139 MB |
| techo duro de GitHub | **100 MB por archivo** — rechazo, no advertencia |
| aviso de GitHub | 50 MB |

Tres cosas se desprenden de esa tabla y ninguna es opcional:

1. **Estamos al 86% del techo.** No hay margen para muchas ingestas más. Cuando
   `proyectos.db` pase los 100 MB, el push falla entero, y el arreglo del lado del
   servidor es reescribir historia — prohibido en este repo.
2. **Un binario no diffea.** Cada commit que toque la base guarda una copia
   completa: diez regeneraciones commiteadas son ~207 MB de `.git` para siempre.
3. **Sacar la base del `.gitignore` sin vigilar el tamaño** es cambiar un problema
   silencioso (bases que divergen) por otro (un push que no entra y nadie sabe por
   qué). Por eso la decisión incluye el control.

## Las dos reglas de uso

1. **No commitear la base en cada corrida.** Se commitea cuando el contenido
   cambió de verdad (ingesta nueva, taxonomías nuevas), no porque SQLite le movió
   un byte al abrirla.
2. **El que la regenera, la commitea.** Mismo régimen que la canónica. Una base
   regenerada que se queda en un disco reabre el problema que este ADR cierra.

Los journals (`-wal`, `-shm`, `-journal`) **siguen ignorados**: son estado de una
corrida. Versionar un `-wal` le entrega a otra persona una transacción a medio
escribir sobre una base que ella no abrió.

## Verificación

`tests/test_bases_viajan.py` (4 chequeos), y están escritos como propiedades, no
como el número del día:

- ninguna base `.db` fuera de `Archivos_Borrar/` está ignorada;
- los journals siguen ignorados;
- **ningún archivo versionado supera los 95 MB** (margen sobre el techo de 100);
  entre 50 y 95 MB avisa sin fallar;
- no volvió al `.gitignore` una regla pelada `*.db` (el modo de falla es que
  alguien la reponga "por prolijidad" y el punto 1 se rompa en silencio).

## Consecuencias, incluida la que no nos gusta

- Un `git clone` pasa de ~139 MB a ~160 MB, y crece ~21 MB por cada versión de la
  base que se commitee. Es el costo aceptado.
- **Este ADR tiene fecha de vencimiento.** Cuando el test avise que la base pasó
  los 90 MB, hay que decidir Git LFS **antes** de que el push empiece a fallar.
  LFS cumple el mismo objetivo de unidad (una sola base, versionada, para todo el
  equipo) sin techo ni inflado, a costa de que cada uno lo instale una vez. No se
  eligió hoy porque el costo de instalación se paga en todas las máquinas del
  equipo y hoy no hace falta; el día que haga falta, hará falta de golpe.
- Queda pendiente de decidir si el mismo criterio aplica a los `.xlsx` de
  `datos/export/data` (50,7 MB entre 10 archivos). Hoy ya viajan por el régimen
  transitorio de Valle 02-07, así que no cambia nada; se anota porque suman al
  mismo `.git`.
