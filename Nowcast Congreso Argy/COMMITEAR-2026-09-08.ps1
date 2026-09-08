<#
 COMMITEAR-2026-09-08.ps1 - los commits de la sesion del 08-09, uno por tarea.

 POR QUE UN SCRIPT Y NO LOS HIZO CLAUDE: la sesion trabaja sobre tu carpeta a traves
 de un puente que NO tiene identidad de git configurada (`git commit` muere con
 "Author identity unknown") y que ADEMAS no puede borrar archivos, asi que cada `git
 add` deja atras el `.git\index.lock` y unos temporales en `.git\objects`. Los commits
 los tenes que hacer vos. El contenido ya esta escrito y verificado.

 ANTES DE CORRER: cerra GitHub Desktop.

   1. .\COMMITEAR-2026-09-08.ps1 -Simular     # muestra que haria, no commitea
   2. .\COMMITEAR-2026-09-08.ps1

 NO HACE PUSH. A proposito.

 OJO CON EL COMMIT 5 (la base, 85,7 MB). Es el que implementa el ADR-0020 y es el que
 no se puede deshacer una vez pusheado. Si te arrepentis ANTES del push:
     git reset --soft HEAD~1
 Despues del push, sacarlo exige reescribir historia, que en este repo esta prohibido.
 Si preferis pensarlo, corre con -SinBase y quedan los otros cuatro.
#>
[CmdletBinding()]
param([switch]$Simular, [switch]$SinBase)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$pre = "Nowcast Congreso Argy/"

# Basura que dejo el puente: locks renombrados y temporales de objetos. No rompen
# nada, pero ensucian `git status` y `git count-objects`. Aca si se pueden borrar.
Get-ChildItem -Path ".git" -Filter "*.huerfano*" -Recurse -ErrorAction SilentlyContinue |
  ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
Get-ChildItem -Path ".git\objects" -Filter "tmp_obj_*" -Recurse -ErrorAction SilentlyContinue |
  ForEach-Object { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }

if (Test-Path (Join-Path $repo ".git\index.lock")) {
  Write-Host "X Hay un .git\index.lock. Cerra GitHub Desktop y borralo antes de seguir." -ForegroundColor Red
  exit 1
}

$grupos = @(
  @{ msg = @"
gitignore: las bases SQLite viajan por git (ADR-0020)

Decision de Franco, explicita: preferimos pushes y pulls mas pesados antes que
varias bases. Hasta hoy `.gitignore` decia `*.db` y `proyectos.db` (85,7 MB)
--que el ADR-0009 declara fuente de verdad de proyectos-- vivia SOLO en el disco
de quien lo hubiera regenerado. Cada uno terminaba con SU base, las bases
divergen sin dar error, y despues se discuten numeros que salieron de datos
distintos. Ya paso dos veces con la canonica.

Se implementa con git plano. Lo medido, que es lo que hace honesta a la decision:

  proyectos.db      85,7 MB en disco -> 20,7 MB comprimida (24%) POR VERSION
  techo de GitHub   100 MB por archivo, RECHAZO (no advertencia)
  o sea             estamos al 86% del techo, y la base crece con cada ingesta

Un binario no diffea: diez regeneraciones commiteadas son ~207 MB de .git para
siempre. De ahi las dos reglas que quedan escritas en el .gitignore: no commitear
la base en cada corrida (solo cuando el contenido cambio de verdad), y el que la
regenera la commitea.

tests/test_bases_viajan.py (4 chequeos) es el control, escrito como propiedades y
no como el numero del dia: ninguna base ignorada, los journals (-wal/-shm) SI
ignorados, ningun archivo versionado por encima de 95 MB, y que no vuelva al
.gitignore una regla pelada `*.db`. Ese ultimo es el que importa: el modo de falla
es que alguien la reponga "por prolijidad".

El ADR tiene fecha de vencimiento y lo dice: cuando el test avise que la base paso
los 90 MB, hay que decidir Git LFS ANTES de que el push falle.
"@; paths = @(".gitignore", "coordinacion/DECISIONES/0020-las-bases-sqlite-viajan-por-git.md",
              "tests/test_bases_viajan.py", "tests/README.md") },

  @{ msg = @"
mapa: inventario de datos indexado (140 archivos, 195 MB)

El mapa indexaba el CODIGO y no los DATOS, y en este repo el trabajo caro no es el
codigo. `indexar.py` ignora *.parquet, *.csv, *.db y *.xlsx dos veces (por
IGNORAR_ARCHIVOS y por las reglas del .gitignore), asi que 140 archivos de datos
--195 MB, incluida la base que el ADR-0009 declara fuente de verdad-- eran
invisibles para cualquiera que leyera MAPA.md.

Lo que responde ahora el inventario, que es lo que se preguntaba a mano:
  - que hay y donde (ruta, formato, filas x columnas, peso);
  - si VIAJA por git o vive en un solo disco;
  - quien lo escribe y quien lo lee.

Lo tercero fue lo que costo. En este repo la ruta casi nunca se lee ni se escribe
donde se nombra: `CAL_CSV = DATA / "calendario_electoral.csv"` viaja como default
de firma hasta `pd.read_csv(cal_csv)`, y `OUT_DEFAULT` viaja como argumento hasta
`s.to_parquet(out)`. La v1, que solo miraba la vecindad de la mencion, decia que
`serie_bloque.parquet` --contrato del ensemble segun el .gitignore-- no lo escribia
ni lo leia nadie. Un inventario que dice eso de un contrato invita a borrarlo. Se
resuelve siguiendo los nombres dos saltos (asignacion, default de firma, y los
parametros de la funcion a la que se lo pasa).

Y los grupos se definen por lo que se MIDIO, no por lo que se concluye: "ningun
archivo de codigo lo nombra" es una propiedad; "no sirve" es una conclusion, y la
saca una persona. Un output con nombre armado por f-string cae en el primer grupo y
esta perfectamente vivo.

Presupuesto del MAPA: 260 -> 460 lineas, por decision explicita de Franco. El
argumento no es que el presupuesto no importe, es que importa MENOS que repetir
tareas: dos sesiones seguidas reconstruyeron tablas que ya existian en disco
porque no estaban indexadas en ningun lado. MAPA.md queda en 414.

Ademas: `buscar.py --dato <termino>`; el chequeo del presupuesto en
verificar_regeneracion.py ahora LEE MAX_LINEAS_MAPA de indexar.py en vez de copiar
el numero (fijaba el valor del dia en que se escribio y fallaba al cambiarlo a
proposito); y todas las llamadas a git usan --no-optional-locks, porque un `git
status` que no puede borrar su lock deja huerfano el .git\index.lock y bloquea el
commit del otro (URGENTE B, dos veces).

Lo que el inventario encontro el mismo dia esta en URGENTE N.
"@; paths = @(".mapa/indexar.py", ".mapa/buscar.py", ".mapa/mapa.json", "MAPA.md",
              "verificar_regeneracion.py", "CLAUDE.md", "README.md") },

  @{ msg = @"
gitignore: SEPTIMA vez -- los 143 alias de legislador_id no viajaban

Lo encontro el inventario de datos el mismo dia que se escribio, que es para lo que
se escribio.

`datos/canonica/data/alias_legislador_id.csv` son los 143 pares de legislador_id
que Franco reviso UNO POR UNO el 04-09 y aprobo. No se regenera: es criterio
humano. `alias_legislador.py` lo LEE, o sea que es insumo del pipeline, no un
reporte. Estaba cayendo en el `*.csv` de la linea 5.

Lo grave es COMO se escondio: COMMITEAR.ps1 lo nombra explicitamente en las rutas
de su commit 2, asi que el `git add` lo salteo en silencio y el commit se hizo
igual. Quien pullee hoy y corra entity_resolution.py obtiene CERO merges y no se
entera: los 2.302 ids se quedan sin unificar y el modelo mide sobre carreras
partidas. Exactamente el modo de falla que el .gitignore documenta seis veces.

Viaja tambien el CSV de veredictos: sin el, la proxima persona no puede auditar por
que dos ids son la misma persona, y la unica forma de rehacerlo es volver a
molestar a Franco 153 veces.
"@; paths = @("datos/canonica/data/alias_legislador_id.csv",
              "datos/canonica/outputs/legislador_id_merge_aprobado_2026-09-04.csv") },

  @{ msg = @"
coordinacion: plan de limpieza por fases, prompt para la sesion nueva y URGENTE N

PLAN-LIMPIEZA-2026-09.md: el orden en que hay que hacer la limpieza y por que ese
orden. En fases y no modulo por modulo, por tres razones: sin el inventario de
datos no se puede contestar "sirve este parquet" (se contesta con "quien lo lee");
los modulos no son independientes y la canonica es insumo de casi todo; y aca los
errores de datos NO dan error, asi que borrar antes de medir es como se pierde
trabajo pago.

PROMPT-LIMPIEZA-SESION-NUEVA.md: autocontenido, se pega tal cual en una sesion
nueva. Trae el estado medido, las reglas de la casa, los modulos congelados, las
trampas del entorno (los tests son scripts y pytest sobre todo el repo puede mentir
en verde; no hay bash; pip no esta en el PATH), las seis fases y como trabajar con
Franco.

URGENTE N: las dos decisiones que el inventario dejo a la vista. La de los alias ya
esta arreglada y solo falta commitear. La otra es de Franco: los ocho
datos/export/data/votaciones_*.xlsx son 49,6 MB versionados que NINGUN archivo de
codigo nombra --mas de un tercio de los 195 MB de datos--. O son el entregable para
que el equipo vea las votaciones sin correr nada, o son un resto de la etapa de
exportacion que todos se bajan en cada clone para nada. La pregunta concreta:
alguien del equipo abre esos xlsx?

NO se sellaron los 27 README vencidos. Se corrio --sellar-todo por comodidad y hubo
que revertir los 27: estampar la huella sin leer la prosa afirma una frescura falsa,
que es peor que no tener sello. Lo dice el propio indexar.py. Revisarlos es la fase
4 de la limpieza.
"@; paths = @("coordinacion/PLAN-LIMPIEZA-2026-09.md",
              "coordinacion/PROMPT-LIMPIEZA-SESION-NUEVA.md",
              "coordinacion/URGENTE.md",
              "COMMITEAR-2026-09-08.ps1") },

  @{ msg = @"
datos: proyectos.db entra al repo (85,7 MB) -- ADR-0020

Es el commit que hace efectiva la decision. A partir de aca hay UNA base para todo
el equipo y no una por maquina.

Numeros, para que quien lea el log sepa lo que esta viendo: 85,7 MB en disco, 20,7
MB comprimida (o sea lo que suma al .git POR VERSION), techo de GitHub 100 MB por
archivo. Estamos al 86% del techo.

Las dos reglas de uso, que estan escritas en el .gitignore: no se commitea en cada
corrida, solo cuando el contenido cambio de verdad (`git diff --stat` antes de
agregar); y el que la regenera la commitea.
"@; paths = @("datos/proyectos/data/proyectos.db"); base = $true }
)

$i = 0
foreach ($g in $grupos) {
  $i++
  if ($SinBase -and $g.base) {
    Write-Host "`n--- commit $i/$($grupos.Count): SALTEADO (-SinBase) ---" -ForegroundColor Yellow
    continue
  }
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
