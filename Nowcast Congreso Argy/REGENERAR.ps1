<#
 REGENERAR.ps1 — la corrida completa despues de la sesion del 2026-09-04 (ADR-0017).

 QUE HACE: reconstruye los parquets que el codigo nuevo todavia no toco, en orden, y
 al final imprime los CRITERIOS DE ACEPTACION medidos para que se puedan revisar de
 un vistazo.

 COMO SE USA (PowerShell, parado donde este este archivo):
     .\REGENERAR.ps1                 # todo
     .\REGENERAR.ps1 -Desde 4        # retomar desde el paso 4
     .\REGENERAR.ps1 -SoloVerificar  # no corre nada: solo mide y reporta
     .\REGENERAR.ps1 -ConCanonica    # ademas rehace la canonica antes de todo
     .\REGENERAR.ps1 -ConExpedientes # ademas rebaja los expedientes de CKAN

 Tarda 2-3 horas. Se puede dejar sola. Cada paso deja su log en ..\logs-regenerar\.
 Si un paso falla, CORTA: los pasos de mas abajo leen lo que produce el de arriba y
 seguir con un insumo a medias es la forma de fallar mas cara de este repo.

 NO hace nada de git. El `.git\index.lock` huerfano no molesta para esto.
#>
[CmdletBinding()]
param(
  [int]$Desde = 1,
  [int]$Hasta = 8,
  [switch]$SoloVerificar,
  # Reconstruye la CANONICA antes de todo (run_pipeline.py, ~20 min y necesita red).
  # APAGADO por defecto a proposito: la canonica es la fuente de verdad y rehacerla
  # no es parte de una regeneracion normal. Se prende cuando hay que aplicar un
  # cambio en la INGESTA -- por ejemplo el arreglo de `tipo_mayoria` de Diputados
  # del 2026-09-10, que solo entra re-ingestando argentinadatos (URGENTE O).
  # De paso deja `_sources/` al dia, que es el item H de URGENTE.
  [switch]$ConCanonica,
  # Rebaja los EXPEDIENTES de CKAN (ingesta_ckan.py + giros_iniciales.py). Tambien
  # APAGADO por defecto: son ~75 MB, el cache se borro el 10-09 y HCDN publica con
  # ~5 semanas de atraso, asi que rebajar todos los dias no aporta. Se prende cuando
  # expedientes.parquet quedo viejo -- lo leen estimar_beta_dictamen, origen_lider,
  # origen_por_acta y embudo, o sea el motor.
  [switch]$ConExpedientes,
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
Set-Location $repo
$logs = Join-Path (Split-Path $repo -Parent) "logs-regenerar"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$inicio = Get-Date

function Titulo($n, $txt, $mins) {
  Write-Host ""
  Write-Host ("=" * 78) -ForegroundColor Cyan
  Write-Host ("  PASO $n — $txt   (~$mins min)") -ForegroundColor Cyan
  Write-Host ("=" * 78) -ForegroundColor Cyan
}

function Correr($n, $nombre, $argumentos) {
  $log = Join-Path $logs "$n-$nombre.log"
  Write-Host "  log: $log" -ForegroundColor DarkGray
  $t0 = Get-Date
  # OJO: $ErrorActionPreference="Stop" + `2>&1 |` hace que PowerShell 5.1 convierta CADA
  # linea de stderr de un comando nativo en un error TERMINANTE. Un INFO de logging que
  # va a stderr aborta el paso sin que nada haya fallado: paso el 05-09 en el paso 5 de 8
  # (enlace_senado.py era el unico del pipeline que logueaba a stderr; tambien se
  # arreglo). Quien decide si un paso fallo es su CODIGO DE SALIDA, no que haya escrito
  # en stderr.
  $previo = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  # Ver el comentario de arriba: ademas de no abortar, se convierte a texto para que el
  # log no se llene de NativeCommandError por cada linea de stderr (paso el 11-09 con
  # run_pipeline.py, que loguea INFO por stderr).
  & $Python @argumentos 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log
  $code = $LASTEXITCODE
  $ErrorActionPreference = $previo
  $mins = [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
  if ($code -ne 0) {
    Write-Host ""
    Write-Host "  X PASO $n FALLO (codigo $code, $mins min). Corto aca." -ForegroundColor Red
    Write-Host "    Mira el final de $log y contame que dice." -ForegroundColor Red
    Write-Host "    Para retomar desde este paso:  .\REGENERAR.ps1 -Desde $n" -ForegroundColor Yellow
    exit $code
  }
  Write-Host "  OK paso $n ($mins min)" -ForegroundColor Green
}

function EnRango($n) { return (-not $SoloVerificar) -and ($n -ge $Desde) -and ($n -le $Hasta) }

# ─────────────────────────────────────────────────────────────────────────────
# PASO 0 — CHEQUEO PREVIO. Lo que puede fallar en el segundo 1 no puede fallar
# en el minuto 9.
#
# El 06-09-2026 el PASO 6 murio con `ModuleNotFoundError: statsmodels` DESPUES de
# procesar 1.556 actas: 9,2 minutos de CPU para descubrir un `pip install` que
# faltaba, porque el import esta adentro de la ultima funcion del programa. Los
# scripts ahora tambien chequean su propia dependencia al arrancar; esto chequea
# TODOS los pasos que se van a correr, de una, antes de empezar.
# ─────────────────────────────────────────────────────────────────────────────
if (-not $SoloVerificar) {
  Write-Host ""
  Write-Host ("=" * 78) -ForegroundColor Cyan
  Write-Host "  PASO 0 - dependencias de los pasos $Desde a $Hasta" -ForegroundColor Cyan
  Write-Host ("=" * 78) -ForegroundColor Cyan
  $faltan = $false
  foreach ($n in $Desde..$Hasta) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Python "verificar_dependencias.py" "--paso" $n 2>&1 | Where-Object { $_ -match "FALTA|pip install" }
    if ($LASTEXITCODE -ne 0) { $faltan = $true }
    $ErrorActionPreference = $prev
  }
  if ($faltan) {
    Write-Host ""
    Write-Host "  X FALTAN DEPENDENCIAS. Instalalas y volve a largar." -ForegroundColor Red
    Write-Host "    Detalle:  python verificar_dependencias.py" -ForegroundColor Yellow
    Write-Host "    O todo:   python -m pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "    (python -m pip, no pip: pip puede no estar en el PATH)" -ForegroundColor DarkGray
    exit 1
  }
  Write-Host "  OK: esta todo lo que estos pasos necesitan" -ForegroundColor Green

  # INSUMO, no dependencia: los pasos 1 y 4 reconstruyen las firmas desde los PDFs
  # de las Ordenes del Dia, que viven en un CACHE. El 2026-09-10 ese cache se borro
  # junto con Archivos_Borrar/ y el paso 1 murio en el minuto 2 con un
  # FileNotFoundError -- justo lo que este paso 0 existe para evitar.
  # Las salidas de los pasos 1-4 SI viajan por git y suelen estar al dia: si el
  # cache no esta, casi siempre lo correcto es saltearlos con -Desde 5.
  if ((EnRango 1) -or (EnRango 4)) {
    $odTrabajo = Join-Path $PSScriptRoot "Archivos_Borrar\od_pdf\od_trabajo.csv"
    if (-not (Test-Path $odTrabajo)) {
      Write-Host ""
      Write-Host "  X FALTA EL CACHE DE ORDENES DEL DIA (lo piden los pasos 1 y 4)" -ForegroundColor Red
      Write-Host "    No esta: $odTrabajo" -ForegroundColor Yellow
      Write-Host "    Opcion A (lo habitual): saltear las firmas, que ya estan versionadas" -ForegroundColor Yellow
      Write-Host "        .\REGENERAR.ps1 -Desde 5" -ForegroundColor Green
      Write-Host "    Opcion B: rebajar los PDFs primero (es LARGO, ~1.700 ODs)" -ForegroundColor Yellow
      Write-Host "        python datos\expedientes\src\ingesta_od.py" -ForegroundColor Green
      exit 1
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
if ($ConCanonica -and -not $SoloVerificar) {
  Titulo "C" "CANONICA desde cero (run_pipeline.py) - necesita RED" "20-30"
  $logC = Join-Path $logs "C-canonica.log"
  Write-Host "  log: $logC" -ForegroundColor DarkGray
  $previoC = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  # ForEach-Object { "$_" }: convierte a texto los registros de error que PowerShell 5.1
  # fabrica con CADA linea de stderr de un comando nativo. Sin esto el log se llena de
  # NativeCommandError por cada INFO de logging, que asusta y no significa nada. El exito
  # lo sigue decidiendo $LASTEXITCODE, que lo fija el comando nativo igual.
  & $Python "datos\canonica\src\run_pipeline.py" 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $logC
  $codeC = $LASTEXITCODE
  $ErrorActionPreference = $previoC
  if ($codeC -ne 0) {
    Write-Host ""
    Write-Host "  X LA CANONICA FALLO (codigo $codeC). Corto aca." -ForegroundColor Red
    Write-Host "    Mira el final de $logC." -ForegroundColor Red
    Write-Host "    Para seguir SIN rehacer la canonica:  .\REGENERAR.ps1" -ForegroundColor Yellow
    exit $codeC
  }
}

# ─────────────────────────────────────────────────────────────────────────────
if ($ConExpedientes -and -not $SoloVerificar) {
  Titulo "E" "EXPEDIENTES de CKAN (ingesta_ckan + giros) - necesita RED, ~75 MB" "15-30"
  $logE = Join-Path $logs "E-expedientes.log"
  Write-Host "  log: $logE" -ForegroundColor DarkGray
  $previoE = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $Python "datos\expedientes\src\ingesta_ckan.py" 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $logE
  $codeE = $LASTEXITCODE
  if ($codeE -eq 0) {
    & $Python "datos\expedientes\src\giros_iniciales.py" 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $logE -Append
    $codeE = $LASTEXITCODE
  }
  $ErrorActionPreference = $previoE
  if ($codeE -ne 0) {
    Write-Host ""
    Write-Host "  X LOS EXPEDIENTES FALLARON (codigo $codeE). Corto aca." -ForegroundColor Red
    Write-Host "    Mira el final de $logE." -ForegroundColor Red
    Write-Host "    Para seguir SIN rebajarlos:  .\REGENERAR.ps1 -Desde 5" -ForegroundColor Yellow
    exit $codeE
  }
}

# ─────────────────────────────────────────────────────────────────────────────
if (EnRango 1) {
  Titulo 1 "Diputados: reconstruir las firmas (SIN red, 2.504 PDF en cache)" "45-60"
  Correr 1 "firmas-diputados" @("datos\expedientes\src\construir_firmas.py", "--desde-cero")
}

if (EnRango 2) {
  Titulo 2 "Senado: SONDA del formulario (1 anio, sin bajar PDF)" "1"
  # Guarda real: si el sitio cambio el formulario, la paginacion pierde el filtro y
  # TODOS los anios devuelven exactamente 20 filas (el tamanio de una pagina).
  # Ningun dato real sale tan parejo. Es el bug del 21-08 y se detecta aca, no
  # despues de 1.700 descargas.
  $log2 = Join-Path $logs "2-sonda-senado.log"
  & $Python "datos\expedientes\src\ingesta_od_senado.py" --anios 2026 --solo-lista 2>&1 |
      Tee-Object -FilePath $log2
  if ($LASTEXITCODE -ne 0) { Write-Host "  X la sonda fallo" -ForegroundColor Red; exit 1 }
  $m = Select-String -Path $log2 -Pattern "(\d+) Ordenes del D|(\d+) Órdenes del D" |
       Select-Object -Last 1
  if ($m -and $m.Line -match "(\d+)\s+[OÓ]rdenes del D") {
    $n = [int]$Matches[1]
    Write-Host "  la sonda devolvio $n Ordenes del Dia para 2026" -ForegroundColor Gray
    if ($n -eq 20) {
      Write-Host "  X EXACTAMENTE 20: es el tamanio de una pagina, no un dato real." -ForegroundColor Red
      Write-Host "    La paginacion perdio el filtro (bug del 21-08). NO sigas: avisame." -ForegroundColor Red
      exit 2
    }
  } else {
    Write-Host "  ! no pude leer el conteo del log; revisalo a ojo antes de seguir" -ForegroundColor Yellow
  }
}

if (EnRango 3) {
  Titulo 3 "Senado: bajar las Ordenes del Dia (CON red, reanudable)" "40-60"
  Write-Host "  el cache ya tiene 229 de ~1.761; si se corta, volve a correr este paso" -ForegroundColor DarkGray
  Correr 3 "ingesta-od-senado" @("datos\expedientes\src\ingesta_od_senado.py", "--anios", "2008-2026")
}

if (EnRango 4) {
  Titulo 4 "Senado: reconstruir las firmas" "30-40"
  Correr 4 "firmas-senado" @("datos\expedientes\src\construir_firmas.py", "--senado", "--desde-cero")
}

if (EnRango 5) {
  Titulo 5 "Enlace acta-expediente + fichas de legislador + features de origen" "10-20"
  Correr 5 "enlace" @("datos\expedientes\src\enlace_senado.py")

  # Agregados el 2026-09-10 (limpieza). Los tres FALTABAN, y por eso sus salidas
  # quedaban viejas mientras la canonica avanzaba:
  #   - ficha.py escribe legislador_bloques.parquet, que leen origen_lider.py:184 y
  #     origen_por_acta.py:153, o sea la variable ORIGEN del motor. Sin el, `origen`
  #     cae a DESCONOCIDO en el 94,6% de las filas y NADIE recibe un error.
  #   - origen_lider / origen_por_acta escriben features_proyecto.parquet y
  #     origen_por_acta.parquet, que el 08-09 eran del 20-08: anteriores al dedup
  #     del 25-08 y al parser del 06-09.
  # El orden importa: origen_* leen lo que escribe ficha.
  Correr 5 "fichas-legislador" @("variables\legislador\src\ficha.py")
  Correr 5 "origen-lider"      @("variables\proyecto\src\origen_lider.py")
  Correr 5 "origen-por-acta"   @("variables\proyecto\src\origen_por_acta.py")

  # Agregados el 2026-09-10, DESPUES de la primera corrida: los dos leen la canonica
  # y tampoco estaban. Se vio en el cierre de la limpieza -- la canonica quedo del
  # 10-09 y estas dos salidas eran del 20-08 y del 08-08:
  #   - disciplina_individual.csv lo leen agregador.py, estimar_gamma_individual.py
  #     y comparar_vias_icg.py. Es un insumo del panel de puertas.
  #   - serie_bloque.parquet es la serie de cohesion y postura por bloque.
  # Van DESPUES de origen_por_acta porque bloque.py lo lee.
  Correr 5 "disciplina"        @("modelo\voto_individual\src\disciplina.py")
  # OJO: bloque.py EXIGE subcomando. Sin el imprime el uso y sale con codigo 2.
  # Paso el 11-09: se agrego sin argumento y corto la corrida entera en el ultimo
  # paso nuevo, despues de 40 min de canonica y expedientes.
  Correr 5 "serie-bloque"      @("variables\bloque\src\bloque.py", "serie")
}

if (EnRango 6) {
  Titulo 6 "Re-estimar beta (ambas camaras, y despues solo Senado)" "10-20"
  Correr 6 "beta-ambas" @("modelo\ensemble\src\estimar_beta_dictamen.py")
  Correr 6 "beta-senado" @("modelo\ensemble\src\estimar_beta_dictamen.py", "--camara", "senado",
                           "--salida", "modelo\ensemble\outputs\beta_dictamen_senado.json")
}

if (EnRango 7) {
  Titulo 7 "Baseline de voto individual" "10-20"
  Correr 7 "baseline" @("evaluacion\baseline\src\baseline_voto_individual.py")
}

if (EnRango 8) {
  Titulo 8 "Panel de puertas + reindexar el mapa" "5"
  Correr 8 "panel" @("casos\nowcast_puertas_html.py", "diputados", "--fecha", "2026-06-01",
                     "--origen", "EJECUTIVO")
  Correr 8 "mapa" @(".mapa\indexar.py", ".")
}

# ─────────────────────────────────────────────────────────────────────────────
Titulo "V" "VERIFICACION — esto es lo que hay que mirar" "1"
$log = Join-Path $logs "VERIFICACION.txt"
& $Python "verificar_regeneracion.py" 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log

# ─────────────────────────────────────────────────────────────────────────────
# La suite, al final y en la misma corrida (pedido de Franco, 2026-09-10). Son los
# dos unicos paths migrados a pytest: el resto de los test_*.py son SCRIPTS que
# corren al importarse, y pasarle el repo entero a pytest aborta la corrida.
Titulo "T" "TESTS — la suite migrada" "1-2"
$logT = Join-Path $logs "TESTS.txt"
& $Python "-m" "pytest" "tests/" "datos/proyectos/tests" "-q" 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $logT
if ($LASTEXITCODE -ne 0) {
  Write-Host "  La suite NO paso. Mirá $logT antes de creerle a la verificacion." -ForegroundColor Red
}

$total = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
Write-Host ""
Write-Host "LISTO en $total min. Pegame el contenido de:" -ForegroundColor Green
Write-Host "  $log" -ForegroundColor Green
