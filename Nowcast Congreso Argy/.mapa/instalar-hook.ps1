# Instala el hook de reindexado del mapa. Correr UNA vez, desde cualquier
# carpeta del repo:
#
#     powershell -ExecutionPolicy Bypass -File "Nowcast Congreso Argy\.mapa\instalar-hook.ps1"
#
# Existe porque en PowerShell no siempre hay `bash` en el PATH (viene con Git
# para Windows pero no queda expuesto). El HOOK en si es bash y no importa: git
# en Windows corre los hooks con el `sh` que trae adentro, no con el del PATH.
#
# Los hooks NO viajan en git: cada persona que clone el repo tiene que correrlo.

$ErrorActionPreference = "Stop"

$raiz = (git rev-parse --show-toplevel) 2>$null
if (-not $raiz) { throw "No estoy dentro de un repo git. Pare en la carpeta del repo y volve a correrlo." }
$raiz = $raiz -replace '/', '\'

$src = Join-Path $raiz "Nowcast Congreso Argy\.mapa\hook-pre-commit"
$dst = Join-Path $raiz ".git\hooks\pre-commit"

if (-not (Test-Path $src)) { throw "No encuentro $src" }
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null

if ((Test-Path $dst) -and -not (Select-String -Path $dst -Pattern "mapa: el indexado fallo" -Quiet)) {
    Copy-Item $dst "$dst.antes-del-mapa" -Force
    Write-Host "ya habia un pre-commit: lo guarde como pre-commit.antes-del-mapa"
}

# Sin BOM y con finales de linea LF: git lo ejecuta con sh y un \r al final de
# la primera linea lo rompe con "bad interpreter".
$texto = (Get-Content $src -Raw) -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($dst, $texto, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "hook instalado en $dst"
Write-Host "Probalo sin commitear nada:  git commit --dry-run  (o simplemente hace tu proximo commit)"
