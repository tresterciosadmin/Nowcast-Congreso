<#
 COMMITEAR.ps1 — los commits de la sesion del 2026-09-06, uno por tarea.

 POR QUE UN SCRIPT Y NO A MANO: son 117 archivos tocados en siete tareas distintas.
 Un commit unico no se puede revertir por partes, y el ADR-0015 exige que un cambio al
 motor viaje en el MISMO commit que su presentacion en FORMULA-COMPLETA.md. Esto arma
 esos grupos.

 ANTES DE CORRER: tiene que no haber ningun `.git\index.lock`.
   1. Cerra GitHub Desktop (es lo que lo deja huerfano; aparecio uno nuevo el 06-09 01:21,
      durante la corrida de REGENERAR).
   2. del "..\.git\index.lock"
   3. .\COMMITEAR.ps1 -Simular     # muestra que haria, no commitea
   4. .\COMMITEAR.ps1

 NO HACE PUSH. A proposito.
#>
[CmdletBinding()]
param([switch]$Simular)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$pre = "Nowcast Congreso Argy/"

if (Test-Path (Join-Path $repo ".git\index.lock")) {
  Write-Host "X Hay un .git\index.lock. Cerra GitHub Desktop y borralo antes de seguir." -ForegroundColor Red
  exit 1
}

$grupos = @(
  @{ msg = @"
datos: el distrito del Senado sale del padron, no del Excel

La columna PROVINCIA de la hoja Senado del Excel 2025-2027 estaba PERMUTADA:
66 de 72 senadores tenian el distrito de otro. No era un corrimiento -ningun
offset lo explicaba- sino una permutacion: las 72 provincias correctas estaban
todas, repartidas entre las personas equivocadas. Firma de "ordenar sin extender
la seleccion". Entro a la canonica y se quedo ahi sin dar error.

Arreglado en los dos lados. El Excel se corrigio (66 PROVINCIA + 8 Bloque) y
to_canonical.py resuelve ahora el distrito contra padron_senado.csv, que es
fuente oficial independiente. Tres decisiones:

- el padron manda sobre el DISTRITO, y cada correccion se reporta;
- el BLOQUE se reporta pero NO se pisa: depende del tiempo, y pisarlo le pondria
  a un voto de marzo el bloque de agosto, que es leakage y no da error;
- se compara NORMALIZADO. Sin eso, una comparacion sensible a mayusculas
  "corrige" las 256 filas de Diputados que estaban perfectas. Paso al escribirlo.

Verificado: 72/72 en distrito contra el padron y 24 provincias con exactamente
3 senadores. La canonica se parcheo en las 3.072 filas de manual_2026 (462
distritos, 56 bloques, CERO votos cambiados) y no por el pipeline, porque
build.py desde _sources/ da 834.749 votos en vez de 1.016.058 (URGENTE H).

Test nuevo: datos/manual_2026/tests/test_to_canonical.py (28 checks).
"@; paths = @("datos/manual_2026/", "datos/canonica/data/clean/votos_canonico.parquet",
              "datos/canonica/data/clean/_sources/manual_2026_actas.parquet",
              "datos/canonica/data/clean/_sources/manual_2026_votos.parquet") },

  @{ msg = @"
canonica: aplicar la tabla de alias de legislador_id (143 pares)

_leg_id hashea el CONJUNTO de palabras del nombre, asi que "ROSSI Agustin" y
"Rossi, Agustin Oscar" son dos personas para el sistema. Franco reviso los 153
pares del censo del 04-09 uno por uno y aprobo 145.

Se aplica al final de entity_resolution (MERGE_IDS=0 lo apaga), no cambiando
_name_key: eso re-hashearia todos los ids del repo, incluidos los sanos.
Resultado: 25.030 filas de voto reasignadas, 2.302 ids -> 2.159.

Control duro: CERO pares (acta, id canonico) con mas de un voto sobre 1.016.058
filas. Si alguno de esos pares fuera dos personas, en un millon de filas se
habrian cruzado.

Va DESPUES del guard de era y no antes, y esta medido: el merge solo empeora
(0,1317 -> 0,1301) porque la fragmentacion de ids funcionaba como guard de era
accidental. Con el guard puesto cuesta -0,0007, casi todo en 2019-2023 (-0,0140),
la era con menos votos. Se aplico igual porque SON LA MISMA PERSONA: una metrica
que mejora manteniendo partida una carrera mide un beneficio accidental.

El test que decide: si dos ids votaron en la MISMA ACTA son dos personas. El que
NO sirve, y casi hace excluir mal a Snopek: comparar los RANGOS de fechas -- una
carrera con hueco inventa un tramo continuo que se traga el del otro id.
"@; paths = @("datos/canonica/src/", "datos/canonica/data/alias_legislador_id.csv",
              "datos/canonica/tests/", "datos/canonica/outputs/") },

  @{ msg = @"
definiciones: el calendario de gobiernos en un solo lugar (ADR-0019)

Estaba escrito TRES veces -bloque._GOBIERNOS, origen_lider.GOBIERNOS,
origen_por_acta.GOBIERNO_NOMBRES- las tres con un comentario pidiendo "mantener
sincronizadas", que es el control que el ADR-0014 dice que no alcanza.

Lo que obligo fue el cuarto consumidor: el guard de era del record individual.
Si el record se corta por una lista y proyectar_postura por otra, el numero no
cierra y nada falla.

La frontera va a definiciones.py; la carga util (quien era oficialista) se queda
en origen_lider. Los modulos re-exportan sus nombres con la misma forma, asi que
aguas abajo no cambia nada.

Y icg_contexto.GOBIERNOS NO se unifico, a proposito: son nueve ventanas, arranca
en De la Rua, parte CFK en I y II, tiene un tramo "Crisis" de once dias y cierra
cada ventana con el dia ANTERIOR al recambio. Es otra regla que se llama parecido.
Hay un test cuyo unico trabajo es que la proxima persona no las "arregle".

El test compara contra las literales VIEJAS transcritas del codigo del 04-09, en
14 fechas y con los dos bordes de cada ventana: el refactor no movio ninguna.
"@; paths = @("definiciones.py", "variables/bloque/src/bloque.py",
              "variables/proyecto/src/origen_lider.py",
              "variables/proyecto/src/origen_por_acta.py",
              "tests/test_definiciones_compartidas.py",
              "coordinacion/DECISIONES/0019-el-calendario-de-gobiernos-vive-en-definiciones.md") },

  @{ msg = @"
motor: guard de era, encogimiento del record y umbral en 1 (ADR-0018)

URGENTE 9 decia que el record individual no tenia guard de era. Lo tenia, con la
fecha clavada en 2023-12-10. Para el gobierno vigente esa ES la era correcta;
para cualquier fecha anterior el filtro se cruza con el de walk-forward, deja el
conjunto vacio y los 478 legisladores caen enteros a la rama de bloque. O sea que
el motor no se podia backtestear fuera de la era vigente.

Y el harness que lo media no era el espejo que dice ser: usaba expanding() sobre
toda la historia sin condicionar por origen. Mediana de la diferencia 0,004, pero
12,2% por encima de 0,10 y peor caso 0,73 -- la cola son los que cambiaron de
lado en el recambio. El "+0,024 desde 2023" media un modelo que no corria.

Tres cosas, las tres prendidas por decision de Franco:

1. la era se deduce de la fecha del nowcast (GUARD_ERA=0 para volver atras);
2. el record se encoge hacia el share de su linaje, Empirical-Bayes k=5, contra
   el MISMO objeto que usa la rama de bloque (SHRINK_RECORD=0);
3. MIN_HIST_INDIVIDUAL baja de 8 a 1: el encogimiento lo dejo sin trabajo y
   encima costaba, de forma monotona.

EL NUMERO PUBLICADO NO SE MOVIO: P = 0,9801 en las cuatro configuraciones.

Confirmado con el censo (6.091 actas, 730.574 votos, 579,9 min): skill
0,1304 -> 0,1611, 2015-2019 de -0,0105 a 0,0954, desde 2023 de 0,0235 a 0,0474,
Senado 0,072 -> 0,120. El proxy habia dicho 0,1665: misma direccion, ganancia
real 15% menor.

El censo agrego la razon para sacar el umbral: la rama de bloque tiene skill
NEGATIVO (-0,10 sobre 19.923 votos). No era un refugio conservador, era un pozo.

Lo unico que empeora: sesgo medio del margen -0,0151 -> -0,0201 y p90 del error
0,2500 -> 0,2541. El MAE baja. Chico y en direccion conservadora.
"@; paths = @("modelo/ensemble/src/nowcast_puertas.py",
              "modelo/ensemble/tests/test_nowcast_puertas.py",
              "evaluacion/baseline/src/baseline_voto_individual.py",
              "evaluacion/baseline/src/medir_guard_era.py",
              "evaluacion/baseline/tests/",
              "coordinacion/DECISIONES/0018-guard-de-era-en-el-record-individual.md",
              "coordinacion/FORMULA-COMPLETA.md") },

  @{ msg = @"
beta: no reportar un coeficiente que se apoya en un solo acta

La corrida del Senado del 06-09 devolvio dict_solo_minoria = +2,5026 con p = 0,0
y un error estandar de 0,157, del mismo orden que el de la constante. Ese
coeficiente sale de UN acta (53 votos de senado-2010-54.pdf).

El error estandar es cluster-robusto POR ACTA: con un cluster no es un error
estandar, es un numero que el estimador devuelve porque tiene que devolver algo.
Con p = 0,0 al lado se lee como el hallazgo mas fuerte de la tabla.

MIN_CLUSTERS_CONFIABLE = 20. El reparto de caracter se publica ahora en ACTAS
ademas de en votos, y por debajo del piso sale un logger.error que dice
explicitamente "NO leas dict_X como un hallazgo".

Corrige de paso el diagnostico de URGENTE D: delta ya NO es 100% UNICO en el
Senado (UNICO 438 actas, mayoria 20, solo-minoria 1), pero sigue sin ser
estimable -- ahora por falta de clusters, no de varianza.
"@; paths = @("modelo/ensemble/src/estimar_beta_dictamen.py",
              "modelo/ensemble/src/estimar_psi_arrastre.py",
              "modelo/ensemble/src/estimar_theta_sobre_tablas.py") },

  @{ msg = @"
infra: declarar las dependencias y fallar en el segundo 1, no en el minuto 9

El paso 6 de REGENERAR murio con ModuleNotFoundError: statsmodels DESPUES de
procesar 1.556 actas (9,2 min), porque el import esta adentro de estimar(), la
ultima cosa util que hace el programa. La causa de fondo: el repo nunca tuvo
requirements.txt.

Tres capas:
- los tres scripts que usan statsmodels chequean al arrancar (verificado
  simulando el modulo ausente: falla en 1,5 s con el pip install en el mensaje);
- REGENERAR.ps1 tiene un PASO 0 que chequea las dependencias de todos los pasos
  del rango antes de empezar;
- requirements.txt y verificar_dependencias.py (--paso N para uno solo).

Y dos arreglos del .ps1 que costaron una corrida cada uno:
- $ErrorActionPreference="Stop" + `2>&1 |` hace que PowerShell 5.1 convierta cada
  linea de stderr de un comando nativo en un error TERMINANTE. Un INFO de
  enlace_senado.py (el unico script del pipeline que logueaba a stderr) abortaba
  el paso 5 sin que nada fallara. Ahora quien decide es el codigo de salida.
- los mensajes decian "pip install" y en la maquina de Franco pip no esta en el
  PATH. Dicen "python -m pip". Una instruccion de arreglo que no corre en la
  maquina donde hay que correrla no es una instruccion de arreglo.

Sin versiones fijadas a proposito: no hay entorno reproducible declarado, y
fijarlas sin uno seria dar una garantia que no existe.
"@; paths = @("requirements.txt", "verificar_dependencias.py", "REGENERAR.ps1",
              "verificar_regeneracion.py", "COMMITEAR.ps1",
              "datos/expedientes/src/enlace_senado.py") },

  @{ msg = @"
expedientes: rotulado del dictamen y tabla de enlace bicameral (ADR-0017)

El Senado rotula la clase del dictamen en el SUMARIO y abre el cuerpo con la
formula generica "DICTAMEN DE COMISION"; el parser se quedaba con la ultima
etiqueta que veia, asi que la generica borraba el anuncio todas las veces.

Pero las mayorias que faltaban son REALES: sobre 193 Ordenes del Dia leidas a
mano, solo 3 dicen "de mayoria" y ninguna "de minoria". El Senado no acostumbra
sacar dos despachos: el que no acuerda firma igual y deja constancia de su
disidencia. El cero no era un bug nuestro.

Lo que si trababa al Senado era el CABLEADO: habia dos tablas de enlace acta
<-> expediente y se usaba la peor. Renombrada a acta_expediente_todas.parquet,
el Senado paso de 0 votaciones utilizables a 459 actas y 26.513 votos, y por
primera vez se estiman ahi los dos coeficientes del dictamen.

Ademas: dedupe de reimpresiones (el mismo dictamen impreso dos veces inventaba
19 "minorias"), clase 'desconocido' para cuando no hay rotulo (antes se
disfrazaba de 'unico'), y ANEXO como corte (leia un anexo catastral como 18
firmas inventadas).

Regeneracion completa medida: Diputados 125.561 firmas (96,1% resueltas), Senado
18.163 filas, enlace 5.036. La muestra de 193 sobreestimaba las mayorias del
Senado por 3x (decia 1,6%, el censo da 0,5%): no cambia la conclusion del ADR,
la hace mas fuerte.
"@; paths = @("datos/expedientes/", "rutas.py",
              "coordinacion/DECISIONES/0017-rotulado-del-dictamen-y-tabla-de-enlace.md") },

  @{ msg = @"
datos y outputs regenerados por la corrida del 05/06-09 (579,9 min)
"@; paths = @("modelo/ensemble/outputs/", "evaluacion/baseline/outputs/",
              "datos/canonica/data/clean/votos_resuelto.parquet",
              "variables/", "casos/", "datos/padron/", "modelo/") },

  @{ msg = @"
docs: bitacora, URGENTE, mapa y tablero de la sesion del 06-09

URGENTE: se cierran A (regeneracion), B (index.lock) y 9 (guard de era), se
reescribe D (delta en el Senado ya no es 100% UNICO pero sigue sin ser estimable,
ahora por falta de clusters) y se abren H (_sources viejo borra 181.309 votos si
alguien corre build.py suelto), I (las 17 actas de manual_2026 sin fecha) y J
(MAPA.md dio 301 lineas en una maquina y 259 en otra, con los mismos 158
archivos: no se pudo reproducir).

indexar.py imprime ahora el desglose de lineas por seccion cuando excede el
presupuesto, y siempre con --verbose: "excede el presupuesto" sin decir DONDE no
es un aviso accionable.
"@; paths = @("coordinacion/", "MAPA.md", ".mapa/", "tablero_datos.js", "Archivos_Borrar/") }
)

$i = 0
foreach ($g in $grupos) {
  $i++
  $rutas = $g.paths | ForEach-Object { $pre + $_ }
  Write-Host ""
  Write-Host "--- commit $i/$($grupos.Count) ---" -ForegroundColor Cyan
  Write-Host ($g.msg -split "`n")[0] -ForegroundColor White
  if ($Simular) {
    git add -n -- $rutas 2>&1 | Select-Object -First 8
    continue
  }
  git add -- $rutas
  $hay = git diff --cached --name-only
  if (-not $hay) { Write-Host "  (nada que commitear)" -ForegroundColor DarkGray; continue }
  Write-Host "  $(($hay | Measure-Object).Count) archivos" -ForegroundColor DarkGray
  $cuerpo = $g.msg + "`n`nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
  $tmp = [System.IO.Path]::GetTempFileName()
  [System.IO.File]::WriteAllText($tmp, $cuerpo, (New-Object System.Text.UTF8Encoding $false))
  git commit -F $tmp | Out-Null
  Remove-Item $tmp
}

Write-Host ""
Write-Host "Listo. SIN PUSH, a proposito. Lo que quedo afuera:" -ForegroundColor Green
git status --porcelain
