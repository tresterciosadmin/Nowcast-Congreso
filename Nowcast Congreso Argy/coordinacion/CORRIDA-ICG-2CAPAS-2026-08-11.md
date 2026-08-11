# CORRIDA — γ del ICG en 2 capas (oficial, con intervalos de confianza)

**Para:** Valle · **Desde:** la raíz del repo (`Nowcast-Congreso\Nowcast-Congreso`), en PowerShell.
**Por qué acá:** el bootstrap sobre ~444k votos es pesado y el sandbox se corta a los ~45 s.
Los números que dejó Claude son PROVISIONALES (bootstrap chico). Esta corrida los fija.

> Recordatorio: **"pasa en el sandbox" no es "pasa".** Tu pandas difiere del del
> sandbox. Si algún test sale rojo acá, ese es el que vale.

## Paso 1 — regenerar el contexto del ICG (agrega z_fondo / z_corto al parquet)

```powershell
python "Nowcast Congreso Argy\variables\proyecto\src\icg_contexto.py"
```

Tiene que decir algo como `... (297 meses, N imputados, ~217 aptos para ajuste)`.

## Paso 2 — estimación oficial de las 2 capas (con IC por bootstrap)

```powershell
python "Nowcast Congreso Argy\variables\proyecto\src\estimar_gamma_individual.py" --modelo dos_capas --boot 500
```

Escribe `Nowcast Congreso Argy\variables\proyecto\outputs\gamma_icg_dos_capas.json`.
El modulador lee ese archivo solo: al reescribirse, los γ del nowcast quedan
actualizados sin tocar más nada. (Puede tardar bastante; si querés una pasada
rápida primero, `--boot 150`.)

**Qué mirar en la salida (esto es lo que decide si el modelo queda):**
- **`gamma_fondo`** debería seguir sólido y significativo en los tramos (≈0,44–0,51
  entre desvío 0,10 y 0,30). Si se sostiene, la hipótesis de atenuación queda confirmada.
- **`gamma_corto`**: el punto da positivo y creciente (0,27 → 0,32 → 0,58), pero con
  bootstrap chico el IC cruzaba cero. **La pregunta es si con --boot 500 el IC del
  corto se despega de cero** en los tramos de bisagra (≥0,20 / ≥0,30). Si sí, el
  sacudón reciente es señal; si no, el fondo manda y el corto queda como matiz.
- Ojo al tramo **≥0,40** (n chico, 104 legisladores): ahí el fondo baja y el corto
  sube. Si el IC es ancho, no leerlo como patrón; si se sostiene, es que los muy
  díscolos montan el sacudón más que el humor de fondo.

## Paso 3 — tests (con corte si alguno sale rojo)

PowerShell no frena solo entre líneas; este patrón corta:

```powershell
python "Nowcast Congreso Argy\variables\proyecto\tests\test_icg_contexto.py"
if ($LASTEXITCODE -ne 0) { Write-Host "test_icg_contexto ROJO" -ForegroundColor Red; return }
python "Nowcast Congreso Argy\variables\proyecto\tests\test_modulador_shrink.py"
if ($LASTEXITCODE -ne 0) { Write-Host "test_modulador_shrink ROJO" -ForegroundColor Red; return }
Write-Host "TESTS VERDES" -ForegroundColor Green
```

## Paso 4 (opcional) — ver el nowcast con el clima nuevo, de punta a punta

```powershell
python "Nowcast Congreso Argy\casos\proyeccion_hipotetica_bicameral.py"
```

## Después

Si los tests están verdes y los γ te cierran, commiteás. Si el corto NO confirma
significancia y preferís apagarlo, es una línea (poner su tramo en 0 en el JSON o
avisame y lo dejo condicionado a significancia). Nada más depende de esto.
