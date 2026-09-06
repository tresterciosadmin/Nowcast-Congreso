# Regenerar los datos después de la sesión del 2026-09-04

> **Por qué hace falta.** El 04-09 cambiaron el **parser de dictámenes** (ADR-0017) y el
> **cableado del enlace acta↔expediente**, pero los parquets siguen siendo los del 03-09:
> el entorno de Claude tiene ~3 minutos por comando y estas corridas son de decenas de
> minutos. **Hasta que se corra esto, cualquier medición sobre `dictamen_clase` está
> leyendo el dato viejo con el código nuevo.**

Todo desde **PowerShell**, parado en `...\TresTercios\Nowcast Congreso\Nowcast Congreso Argy`.

```powershell
cd "C:\Users\Franco\OneDrive\Desktop\TresTercios\Nowcast Congreso\Nowcast Congreso Argy"
```


---

## ⚡ ATAJO: un solo comando y se deja corriendo

Desde el 2026-09-04 los ocho pasos de abajo están en **`REGENERAR.ps1`**, en la raíz del
repo. Corre todo en orden, deja un log por paso en `..\logs-regenerar\`, **corta si algo
falla** (los pasos de abajo leen lo que produce el de arriba) y al final mide sola los
criterios de aceptación.

```powershell
cd "C:\Users\Franco\OneDrive\Desktop\TresTercios\Nowcast Congreso\Nowcast Congreso Argy"
.\REGENERAR.ps1
```

- `.\REGENERAR.ps1 -Desde 4` retoma desde un paso (si se cortó la descarga, por ejemplo).
- `.\REGENERAR.ps1 -SoloVerificar` no corre nada: sólo mide y reporta.
- `.\REGENERAR.ps1 -Python py` si `python` no está en el PATH.
- **No hace nada de git.** El `index.lock` huérfano no molesta para esto.

**La guarda que tiene incorporada:** el paso 2 es la sonda del formulario del Senado, y si
devuelve **exactamente 20** Órdenes del Día **corta la corrida**. 20 es el tamaño de una
página: significa que la paginación perdió el filtro (el bug del 21-08), y seguir serían
1.700 descargas para nada.

Al terminar, pegame `..\logs-regenerar\VERIFICACION.txt` y lo leemos juntos. También se
puede correr suelto en cualquier momento:

```powershell
python verificar_regeneracion.py
```

Lo que sigue es el detalle paso por paso, por si hay que correr alguno a mano.

---

## PASO 0 — desbloquear git (30 segundos; NO hace falta para regenerar)

```powershell
# cerrá GitHub Desktop ANTES
Get-Process git* -ErrorAction SilentlyContinue      # tiene que estar vacío
Remove-Item "..\.git\index.lock"
git status
```

Hay un `index.lock` vacío del **03-09 19:49** que bloquea `git add`, `commit` y `mv`. Todo
el trabajo del 04-09 está sin commitear por eso. Ojo: el `.git` está **un nivel arriba**
de esta carpeta.

---

## PASO 1 — Diputados: reconstruir las firmas *(~45-60 min, sin red)*

Los 2.504 PDF ya están en `Archivos_Borrar\od_pdf` y el `od_trabajo.csv` también, así que
**esto no descarga nada**: sólo re-parsea.

```powershell
python datos\expedientes\src\construir_firmas.py --desde-cero | Tee-Object -FilePath ..\log_dip.txt
```

**Antes de correrlo entero, la prueba de 2 minutos:**

```powershell
python datos\expedientes\src\construir_firmas.py --limite 50
```

**Qué escribe:** `datos\expedientes\data\clean\dictamenes_firmas.parquet` y
`dictamenes_comisiones.parquet`.

**Criterio de aceptación** (medido sobre 220 ODs reales el 04-09):

- el total de firmas **no se mueve** (6.968 antes y después en la muestra);
- aparece ~3% de `dictamen_clase = "desconocido"` donde antes decía `"unico"`;
- ~0,5% pasa de `"unico"` a `"mayoria"`;
- `mayoria` y `minoria` quedan casi iguales (35.191 y 12.984 hoy).

Si el reparto se mueve mucho más que eso, **sospechá del cruce antes que del ADR**.

---

## PASO 2 — Senado: bajar las Órdenes del Día *(~40-60 min, CON red)*

⚠️ **Este paso es obligatorio y es el más largo.** El caché del Senado tiene sólo **229**
PDF (los que bajó Claude para leer el rotulado) y **falta `od_senado_listado.csv`**, así
que `construir_firmas.py --senado` no arranca sin esto.

**Primero el listado de un año solo, para verificar que el sitio no cambió el formulario:**

```powershell
python datos\expedientes\src\ingesta_od_senado.py --anios 2026 --solo-lista
```

Tiene que devolver decenas de filas, **no exactamente 20** (20 = el tamaño de una página,
o sea que la paginación perdió el filtro). Si eso pasa, frená: es el bug del 21-08.

**Y recién ahí, todo:**

```powershell
python datos\expedientes\src\ingesta_od_senado.py --anios 2008-2026 | Tee-Object -FilePath ..\log_od_senado.txt
```

Es **reanudable**: si se corta, volvé a correrlo y saltea lo que ya está en caché.

---

## PASO 3 — Senado: reconstruir las firmas *(~30-40 min, sin red)*

```powershell
python datos\expedientes\src\construir_firmas.py --senado --desde-cero | Tee-Object -FilePath ..\log_sen.txt
```

**Qué escribe:** `dictamenes_firmas_senado.parquet`.

**Criterio de aceptación** — esto es lo que hay que mirar de verdad:

| | hoy (03-09) | esperado |
|---|---:|---|
| `unico` | 17.669 (99,9%) | baja ~3% (pasan a `desconocido`) |
| `mayoria` | **0** | **~1,6% de las ODs** (3 de 193 en la muestra aleatoria) |
| `minoria` | 19 | **0** — eran una reimpresión de `senado-2018-16.pdf` |
| `dictamenes_repetidos` | (no existía) | ≥1, y `senado-2018-16.pdf` tiene que ser uno |

**Si `mayoria` sigue en 0 exacto, algo del parser no se aplicó.** Si `minoria` sigue en 19,
la deduplicación no corrió. Y si `mayoria` se va muy por encima del 2%, el regex está
agarrando de más: mirá los PDF antes de festejar.

**Control rápido después de correrlo:**

```powershell
python -c "import pandas as pd; d=pd.read_parquet(r'datos\expedientes\data\clean\dictamenes_firmas_senado.parquet'); print(d.dictamen_clase.value_counts(dropna=False)); print('repetidos:', d.dictamenes_repetidos.sum())"
```

---

## PASO 4 — regenerar el enlace acta↔expediente *(~2-5 min)*

Se **renombró** a `acta_expediente_todas.parquet` (tenía las dos cámaras y el nombre decía
"senado"). El script ya escribe el nombre nuevo.

```powershell
python datos\expedientes\src\enlace_senado.py --reporte     # diagnóstico, no escribe
python datos\expedientes\src\enlace_senado.py               # escribe
```

**Qué escribe:** `acta_expediente_todas.parquet` (~5.030 filas) y `cadena_camaras.parquet`.

> Si después de esto quedara un `acta_expediente_senado.parquet` viejo dando vueltas,
> borralo: **un archivo generado, un nombre**. Ese es justamente el modo de fallar que el
> repo repite.

---

## PASO 5 — re-estimar los coeficientes *(~10-20 min cada uno)*

```powershell
python modelo\ensemble\src\estimar_beta_dictamen.py                 | Tee-Object -FilePath ..\log_beta.txt
python modelo\ensemble\src\estimar_beta_dictamen.py --camara senado --salida modelo\ensemble\outputs\beta_dictamen_senado.json
```

⚠️ **`outputs\beta_dictamen.json` está pisado con una corrida `--muestra 400`** (fue un
error mío: el archivo no estaba commiteado y tenía la corrida completa del 03-09). La
primera línea de arriba lo regenera. El A/B controlado del 04-09 quedó aparte, en
`beta_dictamen_ab_2026-09-04.json`, y ese **no** hay que pisarlo.

**Qué mirar:**

- `jefes de bloque resueltos a legislador_id: 76/80 (76 por id explicito del roster, 0 por cruce de nombre)`;
- que `--camara senado` **no** diga "panel vacio: ninguna acta con dictamen identificado";
- en el Senado, `reparto_caracter` va a seguir siendo casi todo `UNICO`: **eso es correcto y
  está documentado**. δ no es estimable ahí.

---

## PASO 6 — el baseline y el panel *(~10-20 min)*

```powershell
python evaluacion\baseline\src\baseline_voto_individual.py
python casos\nowcast_puertas_html.py diputados --fecha 2026-06-01 --origen EJECUTIVO
```

El baseline ahora cruza **1.574 actas con carácter (1.100 Diputados + 474 Senado)** contra
las 710 de antes, todas de Diputados.

El panel hay que regenerarlo **sí o sí**: `Nowcast-Puertas.html` en la raíz todavía tiene
adentro los datos viejos con la clave `umbral_mayoria_simple`. Hoy es coherente consigo
mismo, pero quedó desalineado del generador. Después de regenerar, el margen en votos y la
barra tienen que salir del **mismo** umbral.

---

## PASO 7 — cerrar

```powershell
python .mapa\indexar.py .
git add -A
git commit -m "sesion 04-09: parser de dictamenes del Senado, cableado del enlace, roster de jefes y cuatro arreglos de seguridad"
```

**No hagas `git push`** hasta revisar el diff: hay cambios sin commitear que ya venían del
03-09 mezclados con los de esta sesión.

---

## Lo que NO hace falta correr

- **`ingesta_od.py`** (Diputados): los 2.504 PDF ya están en caché y el parquet salió
  idéntico al re-bajarlos el 03-09. La regla de la casa: **mirá el parquet, no la carpeta.**
- **`ingesta_padron.py`**: no cambió el dato, cambió el control. Si igual lo corrés, acordate
  del comando bueno, que ahora el script te lo dice si te equivocás:
  `python datos\padron\src\ingesta_padron.py diputados datos\padron\data\nomina_diputados.csv`
- **`vigilar_padron.py`**: lo corre el workflow los lunes. Si lo corrés local ahora escribe a
  `Archivos_Borrar\vigilancia_padron\` y **no** toca la ruta versionada.
- **`origen_por_acta.py`** (`variables/proyecto`): sigue leyendo `acta_expediente.parquet`.
  Alimentarlo con la tabla nueva es una mejora conocida (ya estaba anotada como próximo
  paso el 22-07), pero **toca el motor** y no se hizo sin vos.

## Tiempo total

Unas **2 a 3 horas**, casi todo en los pasos 1, 2 y 3. Los tres se pueden dejar corriendo y
son reanudables. El único que necesita red es el 2.
