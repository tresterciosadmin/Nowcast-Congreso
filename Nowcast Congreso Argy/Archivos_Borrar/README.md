# Archivos_Borrar — el descarte, que se conserva un tiempo

**Resumen:** Acá va todo lo que el proyecto dejó de usar. **Nada de esto es fuente de
verdad** y nada de acá viaja por git (`.gitignore`, salvo este README). El entorno de
Claude no puede borrar archivos, así que el borrado final lo hace Franco a mano.

## Buscar acá si

- desapareció un archivo que existía y querés ver si se descartó o se movió
- querés saber por qué algo se sacó del repo, y cuándo

## Qué hay hoy (2026-09-08, limpieza fase 2)

| carpeta | qué es | por qué se descartó |
|---|---|---|
| `parches-de-un-solo-uso/` | 9 scripts `_aplicar_*.py`, `_reparar_tablero.py`, `_patch_tablero_v2.py`, `_aplicar_bitacoras.py`, más `_prueba.txt` | Parches ya ejecutados en julio, con la fecha en el nombre. **Medido con `git grep`: ningún código los importa ni los corre**; las únicas menciones eran documentación. `_patch_tablero_v2.py` decía de sí mismo "OBSOLETO" |
| `Aportes-sobre-dataset-congreso/` | `legislAr-main/` (75 archivos) y `towlandia-master/` sin su ZIP (93 archivos) | Material de terceros de un solo uso (ADR-0002). La semilla ya está normalizada en `datos/decada_votada/`, y `export_seed.R` instala `legislAr` **desde GitHub**, no desde esta copia |

## ⚠️ Lo que NO se movió, y por qué

`Aportes sobre dataset congreso/towlandia-master/public/DecadaVotadaCSV.zip` (1,7 MB)
**se quedó donde estaba**: es **dependencia viva**. Lo leen `datos/canonica/src/run_pipeline.py:29`
y `rutas.py:161` por su ruta literal, en el paso 1 del pipeline, para la semilla histórica.
Si falta, `run_pipeline.py` **no falla**: imprime `[warn] no está DecadaVotadaCSV.zip;
salteo la semilla histórica` y sigue, dejando una canónica sin historia. Es el modo de
falla de la casa —el dato no está y nada da error—, así que el ZIP no se toca.

`Aportes sobre dataset congreso/Decada Votada/` quedó como un árbol de carpetas vacías:
su contenido (19 MB) ya lo había descartado Valle el 06-09. Las carpetas vacías siguen ahí
porque Claude no puede borrarlas.
