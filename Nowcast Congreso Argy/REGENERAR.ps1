<#
 REGENERAR.ps1 — la corrida completa despues de la sesion del 2026-09-04 (ADR-0017).

 QUE HACE: reconstruye los parquets que el codigo nuevo todavia no toco, en orden, y
 al final imprime los CRITERIOS DE ACEPTACION medidos para que se puedan revisar de
 un vistazo.

 COMO SE USA (PowerShell, parado donde este este archivo):
     .\REGENERAR.ps1                 # todo
     .\REGENERAR.ps1 -Desde 4        # retomar desde el paso 4
     .\REGENERAR.ps1 -SoloVerificar  # no corre nada: solo mide y reporta

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
  & $Python @argumentos 2>&1 | Tee-Object -FilePath $log
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
  Titulo 5 "Enlace acta - expediente (acta_expediente_todas.parquet)" "2-5"
  Correr 5 "enlace" @("datos\expedientes\src\enlace_senado.py")
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
& $Python "verificar_regeneracion.py" 2>&1 | Tee-Object -FilePath $log

$total = [math]::Round(((Get-Date) - $inicio).TotalMinutes, 1)
Write-Host ""
Write-Host "LISTO en $total min. Pegame el contenido de:" -ForegroundColor Green
Write-Host "  $log" -ForegroundColor Green
