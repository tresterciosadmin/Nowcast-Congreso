# ⚠️ DOCUMENTO CORREGIDO — 2026-08-04

**La versión anterior de este archivo estaba equivocada y hay que ignorarla.**

Decía que la carpeta local no era un clon de git y daba un instructivo de
PowerShell para inicializarlo. **Es falso: el repo siempre estuvo conectado**, y
Valle trabaja con GitHub Desktop sobre `main`.

**De dónde salió el error:** el entorno donde corre Claude monta la carpeta sin
exponer el directorio `.git`. Claude no lo vio, dedujo "no hay repo" y escribió
un instructivo entero sobre esa deducción. La lección, anotada para todos:
**la ausencia de algo en el sandbox no prueba su ausencia en el disco.** El disco
es la fuente de verdad; el sandbox es una vista parcial.

Si en el futuro Claude no ve un archivo o carpeta que debería estar, la respuesta
correcta es **preguntar**, no concluir.

---

## Lo único que sí vale de la versión anterior: el chequeo del `.gitignore`

Esto sigue siendo obligatorio antes de cada commit, y es la parte que
efectivamente sirvió (destapó el padrón del Senado que llevaba semanas
invisible). Corré esto en PowerShell parado en la carpeta del repo:

```powershell
$criticos = @(
  "datos\padron\data\padron_senado.csv",
  "datos\padron\data\padron_diputados.csv",
  "datos\padron\data\senado_linaje_manual.csv",
  "datos\padron\data\raw\nomina_senado.csv",
  "variables\proyecto\data\icg_mensual.csv",
  "variables\proyecto\data\jefes_bloque.csv",
  "datos\padron\data\estado_vigilancia.json"
)
foreach ($f in $criticos) {
  if (-not (Test-Path $f)) { Write-Host "NO EXISTE  $f" -ForegroundColor DarkGray; continue }
  git check-ignore -q $f
  if ($LASTEXITCODE -eq 0) { Write-Host "IGNORADO   $f" -ForegroundColor Red }
  else                     { Write-Host "OK viaja   $f" -ForegroundColor Green }
}
```

Si alguno sale **IGNORADO**, agregá la excepción al `.gitignore` **en el mismo
commit**. Es la regla de la casa, escrita en el propio archivo, y ya se
incumplió cuatro veces: parquet de expedientes (11-07), roster de jefes (30-07),
salidas del embudo (31-07) y padrón del Senado (detectado 04-08, el único que
llegó a generar una urgencia falsa).
