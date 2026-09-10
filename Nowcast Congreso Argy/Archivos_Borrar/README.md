# Archivos_Borrar — el descarte, que se conserva un tiempo

**Resumen:** Acá va todo lo que el proyecto dejó de usar. **Nada de esto es fuente de
verdad** y nada de acá viaja por git (`.gitignore`, salvo este README). El entorno de
Claude no puede borrar archivos, así que el borrado final lo hace Franco a mano —
**y el 2026-09-10 lo hizo**: lo que había hasta esa fecha ya no está.

> ⚠️ **Al vaciar la carpeta, borrá el CONTENIDO y dejá este archivo.** `README.md` es lo
> único de acá que viaja por git (hay una excepción para él en el `.gitignore`), así que
> borrar la carpeta entera lo saca del repositorio. Ya pasó el 2026-09-10.

## Buscar acá si

- desapareció un archivo que existía y querés ver si se descartó o se movió
- querés saber por qué algo se sacó del repo, y cuándo

## Lo importante: borrar acá NO pierde nada

Todo lo que se archiva estaba **versionado en git**, así que se recupera siempre:

```
git log --all --oneline -- "Nowcast Congreso Argy/<ruta vieja>"     # dónde vivió
git show <commit>:"Nowcast Congreso Argy/<ruta vieja>" > recuperado.py
```

La única excepción son los cachés, que no viajan por git y **se regeneran corriendo el
paso que los produce** (ver `datos/Archivos_Borrar/`, abajo).

## Qué hay hoy

| carpeta | qué es | por qué se descartó |
|---|---|---|
| `sin-consumidor-2026-09-10/` | `postura_gobierno.py` + su test, los dos generadores neutralizados de `casos/`, y `AGENTE-CONSOLE-config.yaml` | Decisión de Franco en la limpieza. Ninguno tenía consumidor: el primero producía un contrato que nadie lee, los dos de `casos/` estaban neutralizados desde agosto, y el yaml era una segunda copia del prompt del clasificador que ya había divergido |

Lo anterior —los nueve parches de julio, `legislAr-main`, `towlandia-master` sin su ZIP y
los 167 locks de git— se borró el 2026-09-10.

## ⚠️ La OTRA carpeta de descarte, que es la grande

**`datos/Archivos_Borrar/` tiene 184 MB**: `senado_html` (115 MB) y `expedientes_ckan`
(69 MB). Son cachés de scraping, no descartes de código, y **las dos carpetas están en uso
a propósito** por scripts distintos (ver el CLAUDE.md, "Régimen de archivos descartables").
Borrarla no pierde nada: cuesta un re-scrape del Senado (~20 min) y ~75 MB de descarga de
CKAN la próxima vez que se reconstruya la base de cero.

## ⚠️ Lo que NUNCA se borra de la otra carpeta de Aportes

`Aportes sobre dataset congreso/towlandia-master/public/DecadaVotadaCSV.zip` (1,7 MB) es
**dependencia viva**: lo leen `datos/canonica/src/run_pipeline.py:29` y `rutas.py:161` para
la semilla histórica. Si falta, `run_pipeline.py` **no falla**: avisa por consola y sigue,
dejando una canónica sin historia.
