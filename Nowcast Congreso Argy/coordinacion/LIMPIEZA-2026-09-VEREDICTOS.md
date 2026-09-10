# LIMPIEZA 2026-09 — línea de base y veredictos

**Resumen:** El registro de la limpieza descrita en `PLAN-LIMPIEZA-2026-09.md`: la línea de
base medida antes de tocar nada, y el veredicto de cada archivo a medida que se revisa.
**Es un archivo temporal**: cuando la limpieza cierra, lo que quede vivo se pasa a
`ESTADO-DEL-PROYECTO.md` y este archivo se borra. No es un sexto documento vivo.

## Buscar acá si

- querés saber por qué un archivo se archivó, se fusionó o se dejó como estaba
- estás retomando la limpieza a mitad de camino y necesitás saber dónde quedó

---

## Línea de base — medida el 2026-09-08, ANTES de tocar nada

Contra esto se compara el cierre (fase 6). Si algo de acá cambia, la limpieza está mal.

| control | resultado |
|---|---|
| árbol de git | **limpio** (`git status --porcelain` vacío, incluidos untracked) |
| último commit | `b1ccd4d` "limpieza" (2026-09-07) |
| `pytest tests/ datos/proyectos/tests -q` | **30 passed** en 30 s → **33 desde la fase 2**, ver abajo |
| `verificar_regeneracion.py` | **16 OK · 0 a mirar · 0 sin poder leer** |
| **P(aprob) del panel de puertas** | **0,9801** (mayoría absoluta 129, simulado 122,5, afirmativos esperados 151,1, margen +28,6) |
| β ambas cámaras | n_actas 1.549 · n_votos 245.883 · β₁ 2,1045 · β₂ 2,138 (p=0,0) |
| β sólo Senado | n_actas 449 · n_votos 26.100 · β₁ 1,9931 · β₂ 1,681 (p=0,00176) |
| enlace acta→expediente | 5.004 filas (2.719 Senado + 2.285 Diputados) |
| `MAPA.md` | 414 líneas (presupuesto 460) |
| índice | 162 archivos · 38.865 LOC · 77 carpetas |
| inventario de datos | 140 archivos · 195,2 MB · 105 viajan por git, 35 no |

**Dónde se corrió:** Linux (Python 3.10.12, pandas 2.3.3, numpy 2.2.6, pyarrow 25.0.1,
statsmodels 0.15.0), no en la PC de Franco. Vale la advertencia del CLAUDE.md: *"pasa en el
sandbox" no es "pasa"*. La corrida que manda es la de Franco:

```powershell
python -m pytest tests/ datos/proyectos/tests -q
python verificar_regeneracion.py
```

## Lo que la fase 0 encontró de paso

1. **URGENTE ítem N.1 ya está resuelto y todavía figura como pendiente.**
   `datos/canonica/data/alias_legislador_id.csv` **sí está versionado**
   (`git ls-files` lo lista), igual que `legislador_id_merge_aprobado_2026-09-04.csv`
   y `datos/taxonomias/data/asignaciones.csv`. El commit que faltaba se hizo. Se borra
   de `URGENTE.md` en el cierre, junto con lo demás que se resuelva.

2. **`--estructura` sub-reporta las bitácoras vencidas: dice 7, son 27.**
   `diagnostico()` (línea 911 de `.mapa/indexar.py`) saltea toda carpeta con
   `archivos == 0`, y un módulo cuyo código vive en `src/` tiene 0 archivos propios.
   Por eso `--estructura` sólo ve `./`, `casos/`, `coordinacion/`, `datos/decada_votada/`,
   `docs/taxonomias/`, `modelo/ensemble/` y `variables/bloque/`, mientras la sección
   **Frescura** del MAPA (que no filtra) lista las 27 reales. El número bueno es 27.
   Candidato a arreglo en la fase 4: es el diagnóstico mintiendo sobre sí mismo.

3. **Los nueve restos de la fase 2 están confirmados: nadie los ejecuta ni los importa.**
   Medido con `git grep --cached` sobre todo el repo. Las únicas menciones son
   documentación (`coordinacion/README.md` los describe como "ya ejecutados y
   NEUTRALIZADOS", el plan de limpieza y este archivo). `_patch_tablero_v2.py` tiene una
   sola línea y dice de sí mismo **"OBSOLETO"**.
   Aparece además un resto que el plan no listaba y `ESTADO-DEL-PROYECTO.md` ya había
   anotado: **`_prueba.txt`** (3 bytes, raíz). El otro que esa entrada nombraba, `_wtest`,
   **ya no existe** — verificado en disco, no copiado de la bitácora.

4. **El hook `pre-commit` NO está instalado.** `.git/hooks/` sólo tiene los `.sample` de
   git. El CLAUDE.md lo da por puesto ("reindexa solo y avisa si algún README quedó
   vencido"), y es parte de por qué hay 27 bitácoras vencidas: nadie recibió el aviso.
   Se instala con
   `powershell -ExecutionPolicy Bypass -File "Nowcast Congreso Argy\.mapa\instalar-hook.ps1"`
   desde la raíz git. **Lo corre Franco**, y conviene hacerlo recién al cerrar la limpieza:
   con 27 bitácoras vencidas hoy, avisaría en cada commit.


## Fase 1 — Datos (140 archivos)

Fuente: el inventario del MAPA (`.mapa/mapa.json` → `inventario_datos`). No se rehizo.

### Lo que el inventario mide bien, y lo que no

Antes de usarlo para decidir, dos límites **medidos**, no supuestos. Los dos van en la
misma dirección peligrosa: el inventario se equivoca en el sentido de "este archivo no
sirve".

1. **Sub-atribuye cuando la ruta se arma con f-string.** Ya estaba documentado
   (`nowcast_{pid}.json`) y hay más casos: `embudo_por_origen.csv` y
   `embudo_por_lider.csv` figuran sin productor y los escribe `embudo.py:647`
   (`f"embudo_por_{dim}.csv"`); `beta_dictamen_senado.json` figura sin productor y lo
   escribe `estimar_beta_dictamen.py` vía `--salida`, que es el paso 6 de `REGENERAR.ps1`.
2. **Sobre-atribuye cuando el nombre de archivo es genérico.** `_decada_csv/diputados.csv`
   figura escrito por `padron_diputados_historico.py`, `test_ingesta_padron.py` y
   `test_ensemble.py` y leído por dos módulos más: **es falso**. El único código que nombra
   esa carpeta es `run_pipeline.py:30`; el resto son coincidencias del basename
   `diputados.csv`. Vale igual para `senadores.csv` y los `bloques-*.csv`.

### El hallazgo: la OCTAVA vez que el `.gitignore` esconde un insumo del motor

`variables/legislador/data/legislador_bloques.parquet` (52 KB) **no viajaba por git**, y lo
leen `variables/proyecto/src/origen_lider.py:184` y `origen_por_acta.py:153` — la variable
**origen** del motor.

Cómo falla, medido y no supuesto:

- `origen_por_acta.py:154` es `pd.read_parquet(p) if p.exists() else None`. Sin warning.
  (El helper `_pq` de al lado sí loguea; esta línea no.)
- Con el archivo ausente, `_mapa_autor_linaje` devuelve `{}` → `autor_linaje` None →
  `oficialista` None y `clase_ofi` None (**verificado llamando a las dos funciones**, no
  leyendo el código) → `_origen` cae al último `return`: `DESCONOCIDO`.
- Impacto sobre los datos de hoy: **39.249 de 41.470 filas** de `features_proyecto.parquet`
  (94,6%) pasarían a DESCONOCIDO, y `match_autor` de **96,07% a 0%**. En
  `origen_por_acta.parquet`, 1.658 de 6.231 actas (DESCONOCIDO de 45,5% a 72,1%).
- **Y la regeneración no lo salva:** `REGENERAR.ps1` tiene 8 pasos y ninguno corre
  `variables/legislador/src/ficha.py`, que es lo único que escribe ese parquet.

Por qué se coló: la línea 105 del `.gitignore` exceptúa `legisladores.csv`; este parquet no
tiene gemelo en CSV y quedó adentro del `*.parquet`. **Arreglado**: excepción agregada con
el diagnóstico completo como comentario.

> **Ojo con lo que se versiona:** el parquet es del **02-07**, y la canónica es del
> **06-09**. Se versiona *tal como está*, porque es el archivo con el que se calculó el
> número de hoy y el contrato de esta limpieza es que el número no cambie. Regenerarlo con
> `ficha.py` **sí lo movería**, así que es una decisión aparte, no de la limpieza.

### Una observación de frescura que no es de la limpieza pero conviene anotar

`features_proyecto.parquet` y `origen_por_acta.parquet` son del **20-08**; la canónica se
dedupliqué el 25-08 y el parser recuperó las Órdenes del Día el 06-09. O sea que las
features de origen del motor están construidas sobre una canónica anterior a los dos
cambios. Es la misma forma que los ítems **M** y **H** de URGENTE, sobre otra tabla.
No se toca acá: mover eso mueve el número.

### Veredictos por grupo

**Grupo A — 30 archivos que ningún código nombra (50,3 MB)**

| archivos | veredicto |
|---|---|
| los 8 `datos/export/data/votaciones_*.xlsx` (49,6 MB) | **SIRVEN — decisión de Franco (08-09): son el entregable y quedan versionados.** Falta corregir el README de `datos/export`, que hoy los llama "transitorio" |
| `embudo_por_origen.csv`, `embudo_por_lider.csv` | **SIRVEN** — trampa del f-string, los escribe `embudo.py:647` |
| `nowcast_*.json` (5, en `modelo/ensemble/outputs/`) | **SIRVEN** — trampa del f-string (`nowcast_{pid}.json`), son las corridas guardadas |
| `backtest_cadena.json`, `backtest_cadena_fina.json` | **SIRVEN como registro histórico**: su script está NEUTRALIZADO desde el 22-08 (ADR-0012). No tienen productor vivo y está bien que no lo tengan |
| `backtest_agregador*.json` (3), `baseline_guard_*.json` (2), `record_por_tema_2026-09-04.json`, `merge_ids_medicion_2026-09-04.json`, `beta_dictamen_ab_2026-09-04.json`, `2026-07-31_ley-de-lobby_scoring.json` | **SIRVEN como registro de medición.** Es la memoria de lo medido; sin consumidor es lo esperable |
| `_sources/decada_votada_*.parquet`, `_sources/baseline_canonico.json`, `legislador_id_duplicados_2026-09-04.csv` | ver grupo B |

**Grupo B — 35 archivos que no viajan por git (30,8 MB)**

| archivos | veredicto |
|---|---|
| `variables/legislador/data/legislador_bloques.parquet` | **FALTABA LA EXCEPCIÓN** → agregada (ver arriba) |
| `legisladores.parquet`, `legislador_periodo.parquet`, `legislador_anio.parquet` | **OK que no viajen.** El `legisladores.csv` gemelo sí viaja y es el que leen los consumidores; los otros dos los lee sólo el export, que se regenera |
| `fase0/data/*` (4, 19,2 MB) | **OK que no viajen.** Fase cerrada; su resultado (`baseline_resultados.json`) sí viaja. Candidatos a `Archivos_Borrar/` en fase 3: liberan 19,2 MB de disco y 0 del clone |
| `_decada_csv/*` (7, 8,4 MB) | **OK.** Intermedios de `export_seed.R` → `run_pipeline.py`. La atribución del inventario para estos es falsa (ver arriba) |
| `_sources/*` (9) | **OK que no viajen** — los regenera `run_pipeline.py`. **NO TOCAR: están viejos (11-07) y es el ítem H de URGENTE** |
| `datos/senado/data/clean/*.parquet` (2), `_diag_sin_cobertura.csv` | **OK.** Salida del scraper, regenerable (~20 min, cachea HTML) |
| `datos/decada_votada/data/clean/*.parquet` (2, 31 KB) | **OK.** Semilla normalizada, sin consumidor hoy |
| `desvios_por_voto.parquet` (1,3 MB) | **OK.** Intermedio de `disciplina.py` que lee el export. **Pero `disciplina.py` tampoco está en `REGENERAR.ps1`**: mismo hueco que el hallazgo, con mucho menos en juego |
| `actas_gemelas_2026-09-06.csv` (158 KB), `legislador_id_duplicados_2026-09-04.csv` (43 KB) | **VIAJAN — decisión de Franco (08-09).** Son la evidencia de dos revisiones manuales suyas; el criterio con el que ya viajaba `legislador_id_merge_aprobado` fue que la próxima persona pudiera auditar, y para auditar hace falta la evidencia, no sólo la conclusión |
| `_sources/baseline_canonico.json` (2 KB) | **RESTO.** Es una copia del que sí viaja en `evaluacion/baseline/outputs/` |

**Grupo C — 42 con productor y sin consumidor**: quedan absorbidos por A y B. Un archivo de
salida sin consumidor es lo normal en este repo (son entregables y registros de medición);
el corte útil no es "sin consumidor" sino "sin consumidor **y** sin viajar **y** sin
regenerador", que es exactamente el caso que se encontró.

## Fase 2 — Restos (hecha, commit `723acbc`)

178 archivos a `Archivos_Borrar/`, que no viaja por git. Nada se borró.

- `parches-de-un-solo-uso/` (10): los nueve `_aplicar_*.py` / `_reparar_tablero.py` /
  `_patch_tablero_v2.py` / `_aplicar_bitacoras.py` de julio, más `_prueba.txt`.
- `Aportes-sobre-dataset-congreso/` (168): `legislAr-main/` entero y `towlandia-master/`
  menos su ZIP.

**Lo que NO se movió, y era lo que la recomendación original decía mover.** El plan (y yo)
propusimos archivar `Aportes sobre dataset congreso/` completa. Estaba mal:
`towlandia-master/public/DecadaVotadaCSV.zip` es **dependencia viva** — la leen
`run_pipeline.py:29` y `rutas.py:161` por su ruta literal, en el paso 1, para la semilla
histórica. Y si falta, `run_pipeline.py` **no falla**: imprime
`[warn] no está DecadaVotadaCSV.zip; salteo la semilla histórica` y sigue, dejando una
canónica sin historia. El ZIP quedó intacto (verificado después de mover: 1.681.394 bytes).

`Aportes sobre dataset congreso/Decada Votada/` ya estaba vacía: Valle descartó su
contenido (19 MB) el 06-09 y sólo quedaron las carpetas, que Claude no puede borrar.

**Después de la fase 2:** 30 passed · 16 OK · P = 0,9801 · índice 162 → **153** archivos,
38.865 → **38.075** LOC · `--estructura` con **un** huérfano, `verificar_regeneracion.py`,
que es el entrypoint declarado. Criterio de salida cumplido.

## El test guardián (decisión de Franco, 08-09)

`tests/test_insumos_del_motor_viajan.py`. **Es una propiedad, no la lista del día**: deriva
del inventario del MAPA los datos que lee cualquier archivo del motor (hoy 28) y falla si
git ignora alguno, así que un insumo nuevo queda cubierto sin que nadie se acuerde de
agregarlo. Tres controles:

1. los insumos del motor no están ignorados;
2. el inventario está disponible — sin esto el archivo pasaría en verde sin controlar nada,
   y un test que no puede fallar entrena a creerle;
3. no quedan excepciones vencidas — una excepción que ya no aplica es una puerta abierta.

**Verificado que puede fallar**, no sólo que pasa: sacándole la única excepción declarada,
salta con `_decada_csv/diputados.csv`.

La única excepción es esa ruta, y el motivo está medido: es una atribución **falsa** del
inventario por colisión de basename (`comparar_vias_icg.py:76` lee
`datos/padron/data/padron_diputados.csv`).

> **La línea de base de la suite pasa de 30 a 33** por los tres tests nuevos. Es el único
> cambio esperado en los controles; todo lo demás se compara igual contra la fase 0.

## Fase 3 — Lote 1: los cuatro módulos más grandes (68 archivos)

`variables/proyecto` (26), `modelo/ensemble` (16), `datos/expedientes` (15),
`datos/padron` (11). Método: cruzar `importado_por` y `entrypoints` del índice contra el
docstring de cada archivo, y verificar en disco y en git todo lo que el docstring afirma.

| veredicto | cuántos | cuáles |
|---|---:|---|
| **SIRVE** | 60 | todo lo demás: o es entrypoint declarado, o alguien lo importa, o es un test |
| **SIRVE PERO MIENTE** | 5 | los cinco punteros a `Archivos_Borrar/BORRAR_*.py` — corregidos |
| **SE ARCHIVA** | 3 | `variables/proyecto/src/{classify_tema.py, classify_tema_v1.py, oficialismo.py}` |
| **SE FUSIONA** | 0 | no apareció duplicación en estos cuatro |

### Los cinco que mentían

`ensemble.py`, `backtest_cadena.py`, `nowcast_bicameral_html.py`,
`proyeccion_hipotetica_bicameral.py` y `comparar_vias_icg.py` decían que el código dado de
baja "quedó entero" en `Archivos_Borrar/BORRAR_*.py`. **Ninguna de las cinco copias existe**
— ni en disco ni en git: `Archivos_Borrar` no viaja y se vació. Quien fuera a buscar la
formulación v1 la buscaba donde no está.

Se corrigió sólo el texto. Cada uno dice ahora el comando que la recupera, verificado
commit por commit (que la versión anterior no tuviera ya el aviso de baja, y que el código
viejo estuviera vivo ahí):

| archivo | commit con la versión vieja |
|---|---|
| `modelo/ensemble/src/ensemble.py` | `5044142` — verificado: tiene el `componer(p_llega, p_mayoria)` v1 |
| `modelo/ensemble/src/backtest_cadena.py` | `e93cd65` |
| `casos/nowcast_bicameral_html.py` | `47eb783` |
| `casos/proyeccion_hipotetica_bicameral.py` | `47eb783` |
| `variables/proyecto/src/comparar_vias_icg.py` | `0a798bb` — el que todavía tiene la capa 2 |

**Ojo con el matiz de `ensemble.py`:** el módulo **está vivo** (lo importan 7 archivos). Lo
que está dado de baja es sólo su función `componer()`. No confundir una cosa con la otra.

### Los tres que se archivan

Los tres se declaran muertos ellos mismos y nadie los importa:

- `classify_tema.py` y `classify_tema_v1.py` — 5 líneas cada uno, todas comentario:
  *"DEPRECADO (2026-06-27) … (Se puede borrar este archivo.)"*
- `oficialismo.py` — *"NEUTRALIZADO 2026-08-09 — DUPLICABA `origen_lider.GOBIERNOS`"*, y
  ya levantaba `ImportError` al importarse. Su docstring dice que está anotado en
  `Archivos_Borrar/PENDIENTES-DE-BORRAR.md`, archivo que **no existía** hasta esta limpieza.
  El `data/gobiernos_oficialismo.csv` que menciona tampoco existe.

### Lo que el lote 1 NO encontró

En `modelo/ensemble`, `datos/expedientes` y `datos/padron` **no hay un solo archivo para
archivar**: los 42 son entrypoint declarado, importados, o tests. El desorden de estos
módulos no es código muerto — es tamaño (`parser_od.py` 614 LOC, `enlace_senado.py` 590) y
la carpeta inflada de `variables/proyecto/src` (17 archivos), que son problemas de otra
naturaleza y no se resuelven archivando.

**Después del lote 1:** 33 passed · 16 OK · P = 0,9801 · índice 154 → 151 archivos.

_(READMEs y sellado de estos cuatro módulos: van en la fase 4, no acá.)_

## Duplicación: medida, no estimada (2026-09-08)

Franco preguntó cuánto código redundante hay. Se instaló `.mapa/duplicados.py`, que compara
la forma del árbol sintáctico de todas las funciones del repo, y se corrió sobre los 151
archivos.

**732 funciones · 32.427 LOC de Python · ~201 LOC de duplicación exacta entre archivos =
0,6%.** La premisa de que hay mucho código redundante, medida, **da que no**. Y de esos 201,
~150 son un solo patrón: el helper `check`/`chk` copiado en 40 archivos de test, que es lo
que permite que cada test corra como script suelto.

### Lo que se fusionó (ADR-0021)

| qué | dónde estaba | por qué importaba |
|---|---|---|
| `caracter_de_dictamen` | 16 LOC idénticas en `estimar_beta_dictamen.py` y `baseline_voto_individual.py` | es la MISMA partición con la que se **estima** β y con la que se lo **evalúa**. Si divergen, nada da error |
| la raíz del repo | **9** archivos (no 7: el análisis por AST se perdió 2 que el chequeo por texto sí encontró), 4 en el motor | convivían dos criterios; el viejo se rompe si se mueve `coordinacion/` o `variables/` |

Los dos se verificaron **antes** de unificar, como pide el plan: el carácter, en las 16
entradas posibles del vocabulario — **cero diferencias**; la raíz, desde la carpeta de cada
`.py` del repo — **coinciden en todas**. Y después: **39 passed · 16 OK · P = 0,9801**, con
β₁ = 2,1045 y β₂ = 2,138 idénticos al dígito.

**Un hallazgo de paso:** `modelo/ensemble/validar_condicionamiento_votos.py` tenía un
fallback que devolvía `/sessions/wizardly-friendly-hamilton/mnt/...`, una ruta de sandbox de
una sesión vieja. Si la búsqueda de la raíz fallaba, el script **no daba error**: apuntaba a
un disco que no existe. Se sacó; `NOWCAST_REPO` se conserva.

### Lo que NO se fusionó, y por qué

- **`check`/`chk` en 40 archivos de test (~150 LOC, el 75% de la duplicación).** Fusionarlo
  obliga a que cada test importe de un lugar común y rompe la convención de que un test
  corre solo. Es una decisión de diseño de la suite. Queda abierta.
- **`_eras_de` / `eras_de` (10 LOC ×2).** Parecen duplicación y no lo son: las dos **delegan**
  en `nowcast_puertas.era_de` y sólo agregan memoización por fecha única, con el motivo
  escrito (2.800 fechas contra 1.016.058 filas). Y `nowcast_puertas.era_de` a su vez importa
  de `definiciones.py`. La parte cara ya la resolvió el ADR-0014.

### Sobre reducir la CANTIDAD de archivos

No sale de fusionar, y conviene decirlo con números: el código muerto ya se archivó (3
archivos) y `--estructura` no encuentra más. Lo que queda es organización —
`variables/proyecto/src` con 17 archivos se **subdivide** (misma cantidad) y los 10 archivos
de +500 LOC se **parten** (más cantidad). El repo no está inflado de código repetido.

## Fase 3 — Lote 2: la ingesta (11 archivos)

`datos/decada_votada` (2), `datos/ckan_diputados` (1), `datos/argentinadatos` (3),
`datos/senado` (5). Método: cruzar el índice contra quién los invoca de verdad —
`run_pipeline.py`, `REGENERAR.ps1`, los `COMMITEAR.ps1`, `.github/` y los controles.

| veredicto | cuántos | cuáles |
|---|---:|---|
| **SIRVE** | 10 | 7 los corre `run_pipeline.py`, 2 son tests, y `export_seed.R` es registro |
| **SIRVE PERO MIENTE** | 1 | `argentinadatos/src/explorar_campos.py` — corregido |
| **SE ARCHIVA** | 0 | |
| **SE FUSIONA** | 0 | |

**No hay nada para archivar en la ingesta.** Los 7 scripts de `src/` los invoca
`run_pipeline.py` por nombre; los 2 tests corren en la suite.

### `export_seed.R` (94 LOC, el único código R del repo): SIRVE

Nadie lo invoca, y el README ya dice que quedó **innecesario** —la semilla entra por
`from_csv.py` desde el ZIP, que es más rápido y trae el Senado—. Pero es la respuesta a
*"por qué hay código en R en un repo de Python"*, que es una de las dos pistas con las que
este módulo entra al router del MAPA. Archivarlo saca la respuesta y deja la pregunta.

_(El README sí se contradice: la sección "Cómo trabajar acá" propone `export_seed.R` como
el camino, y la "ACTUALIZACIÓN" del final dice que no. Se corrige en la fase 4.)_

### La sonda que llevaba un mes sin correr, y lo que apareció al correrla

`explorar_campos.py` existía desde el 08-08 con una pregunta abierta que necesitaba
internet: *¿la API de argentinadatos expone el expediente y lo estamos tirando?* Se corrió.

**Respuesta: no lo publica.** El "arreglo de dos líneas" que la sonda hipotetizaba no
existe. Diputados: 22 campos, los 22 en el 100% de las actas, ninguno es el expediente.
Senado: hay un campo `proyecto` poblado en el 95,3%, y **cero** de esas 306 trae un
expediente — el 95,3% es la Orden del Día, escrita en dos formatos distintos.
Queda en URGENTE como ítem **P**, con lo que sí abre (el enganche por OD en el Senado).

**Y apareció otra cosa, peor y más barata de arreglar.** La API publica `tipoMayoria` en
**las 1.326 actas**, y `to_canonical.py` escribe `tipo_mayoria=None` fijo para Diputados —
mientras la rama del Senado, tres líneas más abajo, **sí** lo lee. Como
`definiciones.normalizar_mayoria_valor` manda "sin dato → SIMPLE", esas actas se recuentan
contra la mitad de los emitidos.

Medido enganchando por `acta_id` (las 760 enganchan, no es extrapolación):

| | |
|---|---:|
| actas de Diputados/argentinadatos en la canónica | 760, **las 760 con `tipo_mayoria` nulo** |
| lo que la API dice de esas mismas 760 | 677 SIMPLE · 49 TRES_CUARTOS · 24 DOS_TERCIOS · 10 ABSOLUTA |
| **con el umbral equivocado** | **83 (10,9%)** |
| el Senado, misma fuente | 317 de 317 **con** el dato |

Es la falla del ítem **I** ("12 de 250 caían al default SIMPLE") sobre el flujo VIVO —
Diputados 2020-2026, el tramo que CKAN ya no cubre — y con 83 actas en vez de 12. Entre
ellas, la **Ley de Ficha Limpia**, que la API marca como mayoría absoluta. Va a URGENTE
como ítem **O**: arreglarlo mueve números, así que no se tocó.

## Fase 3 — Lote 3: la base (28 archivos)

`datos/manual_2026` (2), `datos/bot_recoleccion` (7), `datos/canonica` (7),
`datos/proyectos` (10), `datos/taxonomias` (2). `datos/expedientes` ya se vio en el lote 1.

| veredicto | cuántos |
|---|---:|
| **SIRVE** | 28 |
| SIRVE PERO MIENTE · SE FUSIONA · SE ARCHIVA | 0 |

**Segundo módulo seguido sin nada para archivar.** Lo que parecía candidato, no lo era:

- `datos/proyectos/src/{migrar_ckan, upsert_bot, verificar, cuarentena, taxonomias_backup}.py`
  no los invoca ningún pipeline ni el CI, pero se importan entre sí y el MAPA los documenta
  como entrypoints manuales (*"rehacer `proyectos.db`: `migrar_ckan.py` + `upsert_bot.py`,
  ~1 min"*, *"`verificar.py`, 14 invariantes"*).
- `schema.sql` figura como que "nadie lo importa" porque no es Python: lo lee `store.py`.
- `manual_2026/src/to_canonical.py` está fuera del pipeline desde el 06-09, pero detrás de
  su bandera (`MANUAL_2026=1`) y documentado. Es lo que el plan pide para una mejora
  apagada, aplicado a una fuente.
- `bot_recoleccion/src/explorar_tp.py` (30 LOC) es la tercera sonda "paso 0" de la misma
  familia que `explorar_ckan.py` y `explorar_campos.py`. **Las tres quedan**: son el
  registro de cómo se diseñó cada parser sobre HTML real, y la de argentinadatos acaba de
  demostrar que sirven.

**El bot está vivo**, verificado en `estado_bot.json` y no en una bitácora: última revisión
**2026-09-08**, con `tp_diputados` en el TP 127 del período 144 y `dae_normal` en el 69/2026.

### El hallazgo del lote: hay DOS carpetas de descarte, y la grande no estaba contada

El plan de limpieza declara en su tabla de estado *"`Archivos_Borrar/` **vacía**"*. Es
cierto — de la de la raíz. **Hay una segunda, `datos/Archivos_Borrar/`, con 184 MB**, que es
el **47% de los 393 MB del proyecto**:

| | |
|---|---:|
| `datos/Archivos_Borrar/senado_html` | **115 MB** |
| `datos/Archivos_Borrar/expedientes_ckan` | **69 MB** |
| `datos/Archivos_Borrar/tp_diputados` | 256 KB |
| `datos/Archivos_Borrar/crosswalk_bloques.csv` | 28 KB |
| `Archivos_Borrar/` (la de la raíz) | 4,7 MB — lo que archivó esta limpieza |

**Todo es caché regenerable y nada viaja por git**, así que no infla el clone: infla el
disco. Y las dos carpetas están en uso a propósito, no por error: `ingesta_od.py`,
`ingesta_od_senado.py`, `parser_od.py` y `entity_resolution.py` escriben en la de la raíz;
`explorar_tp.py`, `explorar_ckan.py`, `ingesta_ckan.py` y el scraper del Senado escriben en
la de `datos/`. `.mapa/indexar.py:41` ya nombra a las dos.

Lo que sí está mal es que **`CLAUDE.md` describe el régimen de descartables como si hubiera
una sola**. Quien lea la regla y vaya a `Archivos_Borrar/` a limpiar, limpia 4,7 MB y deja
184.

`crosswalk_bloques.csv` se revisó por las dudas —un CSV con nombre de curado dentro de una
carpeta de descarte es el patrón que este repo ya sufrió ocho veces— y **no lo es**: lo
escribe `entity_resolution.py:302` como diagnóstico y nadie lo lee. Se regenera solo.

**Para Franco, dos cosas y ninguna urgente:** borrar los 184 MB cuesta un re-scrape del
Senado (~20 min) y ~75 MB de descarga de CKAN; y si se unifican las dos carpetas en una,
hay que tocar cuatro rutas de caché, que es más riesgo que valor. La recomendación es
dejarlas y **arreglar el texto de `CLAUDE.md`**, que es donde está el engaño.

## Fase 3 — Lote 4: variables y los dos módulos chicos de modelo (17 archivos)

`variables/bloque` (5), `variables/legislador` (2), `variables/embudo` (5),
`variables/asistencia_quorum` (1), `modelo/voto_individual` (2),
`modelo/agregador_institucional` (2). Todo esto es **motor congelado**: sólo se ordena y se
corrige texto.

| veredicto | cuántos |
|---|---:|
| **SIRVE** | 15 |
| **SIRVE PERO MIENTE** | 2 — `asistencia.py` y (del lote 1) `postura_gobierno.py` |
| SE ARCHIVA · SE FUSIONA | 0 |

**Tercer lote seguido sin código muerto.** Los tres que figuraban sin importadores
—`embudo/src/escenarios.py`, `embudo/src/cohorte_dos_rutas.py`,
`asistencia_quorum/src/asistencia.py`— están los tres en el router del MAPA como
entrypoints con su pista propia.

### El chequeo que abrió este lote: rutas citadas que no existen

Se escaneó **todo** el código buscando rutas del repo nombradas en docstrings y comentarios,
y se verificó si existen. De 338 referencias, **7 estaban rotas** — casi todas por un
segmento `data/` o `src/` que se cayó al escribirlas:

| ruta citada | quién la nombra | qué es en realidad |
|---|---|---|
| `datos/senado/padron_bloques_senado.csv` | `argentinadatos/to_canonical.py` | falta `data/` |
| `datos/senado/padron_manual_2015_2017.csv` | ídem | falta `data/` |
| `datos/padron/padron_senado.csv` | ídem | falta `data/` |
| `evaluacion/baseline/baseline_canonico.py` | `baseline_canonico.py` (su propio encabezado) | falta `src/` |
| `tests/test_medir_guard_era.py` | `medir_guard_era.py` | es `evaluacion/baseline/tests/test_guard_era.py` |
| `variables/proyecto/features_proyecto.parquet` | `backtest_cadena.py` | falta `data/` |
| `variables/proyecto/data/postura_gobierno_por_acta.parquet` | `postura_gobierno.py` | **no existe, y es otra cosa** — ver abajo |

Las seis primeras se corrigieron. Y quedó **`tests/test_rutas_citadas_existen.py`**, que
deriva la lista de cada corrida y exceptúa lo que `rutas.py` declara en `GENERADOS`.
Verificado que puede fallar: con un archivo de prueba que citaba una ruta inventada, salta.

### `postura_gobierno.py`: funciona, y nada de lo que produce llega al número

El séptimo caso no era un typo. `postura_gobierno.py` declara como contrato
`postura_gobierno_por_acta.parquet`, y **el archivo no está en disco ni se generó nunca**.
Medido:

- `rutas.py:125` lo declara y está en `GENERADOS`, o sea exceptuado del test que exige que
  lo declarado exista. Por eso la suite nunca lo notó.
- **Ningún archivo lo lee.**
- Y `proyectar_lineas_alineacion` perdió a su único consumidor: era
  `casos/proyeccion_hipotetica_bicameral.py`, neutralizado el 25-08 por ser una tercera
  formulación del número.

O sea: el módulo funciona, sus 20 tests pasan, y nada de lo que produce llega al número
publicado. `ESTADO-DEL-PROYECTO.md` ya lo anotaba (*"queda sin consumidores en casos/ —
evaluar si se retira o se deja como utilidad. Coordinar con Franco"*). **No se archiva**: la
medición que contiene —la alineación con el gobierno— es la pieza que cerró la Puerta D y
la que hizo que la dirección dejara de ser degenerada. Se corrigió el docstring para que lo
diga, y queda como decisión de Franco.

### `asistencia.py`: el "alimenta al agregador" es en presente y está apagado

Su docstring dice que alimenta al agregador con los presentes esperados *"corrigiendo el
sesgo pesimista del motor"*. Medido: el agregador lee ese CSV **sólo con `ASIST=1`**, y por
defecto no lo toca — el número publicado no depende de él. Lo bueno: cuando la bandera está
prendida y el CSV falta, `agregador.py:311` levanta `FileNotFoundError` diciendo qué correr.
**No hay fallback silencioso**, que en este repo es la excepción y no la regla. Se corrigió
el texto.

### Y una tercera confirmación de que el inventario sobre-atribuye

El inventario da `asistencia.py` como **escritor** de `votos_resuelto.parquet` y
`actas_canonico.parquet` — o sea, como si `variables/asistencia_quorum` escribiera dentro de
`datos/canonica`, que sería una violación de límites entre módulos. **Es falso**: los lee
(líneas 83-84) y escribe sólo en su propio `outputs/`. Tercera vez que la atribución por
nombre de archivo engaña, después de `_decada_csv/diputados.csv` y `senadores.csv`.

## Fase 3 — Lote 5: los bordes (33 archivos). Fase 3 completa

`datos/export` (2), `datos/seguimiento` (2), `evaluacion/baseline` (5),
`producto/dashboard` (1), `casos` (3), `fase0` (3), `docs/taxonomias` (3), `tests` (8),
raíz (6). `coordinacion/` quedó en **0 archivos de código** — que era el objetivo de la fase 2.

| veredicto | cuántos |
|---|---:|
| **SIRVE** | 31 |
| **SIRVE PERO MIENTE** | 1 — `AGENTE-CONSOLE-config.yaml`, corregido |
| **decisión de Franco** | 1 — los dos generadores neutralizados de `casos/` |
| SE FUSIONA | 0 |

### Dos "huérfanos" de la raíz que no lo son

`mapa_modelo_datos.js` (**4.621 LOC, el archivo más grande del repo**) y `tablero_datos.js`
figuran como que nadie los nombra. **Los cargan los HTML**: `MAPA-MODELO.html` el primero y
`TABLERO-CONTROL.html` el segundo, y el primero lo genera
`producto/dashboard/src/generar_mapa_modelo.py`. El índice no parsea etiquetas `<script>`,
así que todo `.js` va a caer en esa lista: es un cuarto modo de sub-atribución, además del
f-string y del basename.

### `AGENTE-CONSOLE-config.yaml`: una segunda copia del prompt del clasificador

Tiene forma de configuración —`model:` y `system:`— y **nadie lo lee**. La variante que
describe (agente de Console referenciado por ID) fue **descartada**, y `ESTADO` es explícito:
*"si tocás el prompt del clasificador, editá `construir_prompt` en `agente_taxonomias.py` —
es EL lugar. No hay que sincronizar contra nada en Console"*.

Se comparó con el prompt vivo: dicen **lo mismo** —mismas 7 reglas, mismo formato de salida,
mismo mapeo `AUX.HOMENAJE` / `AUX.TRAMITE`— pero con otra redacción, y el `model` del yaml
está sin la fecha de versión que sí usa el código (`claude-haiku-4-5-20251001`). **Ya
empezaron a separarse.** El riesgo es concreto: alguien edita el yaml creyendo que cambia
cómo se clasifica. Se le puso una cabecera que lo dice; archivarlo queda como decisión.

### Lo que quedó sin veredicto porque lo decide Franco

`casos/nowcast_bicameral_html.py` (304 LOC) y `casos/proyeccion_hipotetica_bicameral.py`
(164 LOC) están **neutralizados** (22-08 y 25-08) y nadie los corre. Sus docstrings decían
que no se borraban *"para no perder el diseño del HTML, que se reusó"* y por *"el slider de
ICG legislador-por-legislador, que no existe en `nowcast_puertas` y puede querer rehacerse"*.
Ese argumento **se debilitó el 08-09**: ahora los dos docstrings apuntan al commit de git que
tiene la versión entera, así que el diseño no se pierde si se archivan. Son 468 LOC de dos
formulaciones muertas del número, en la carpeta donde vive la formulación viva.

---

# LAS DECISIONES QUE QUEDAN PARA FRANCO

Consolidado al 2026-09-10, con la fase 3 completa (162 archivos revisados, uno por uno).
Ordenadas por lo que cuesta equivocarse, no por lo que cuesta hacerlas.
**Ninguna se aplicó**: todas las de la primera tabla mueven el número publicado.

## 1. Las que mueven el número — no se tocan sin decidir

| # | qué | lo medido | qué costaría |
|---|---|---|---|
| **1** | **`tipo_mayoria` de Diputados** (URGENTE O) | **83 de 760 actas (10,9%)** se recuentan con el umbral equivocado. La API tiene el dato en las 1.326. La rama del Senado ya lo lee | dos líneas en `argentinadatos/to_canonical.py` + regenerar |
| **2** | **`legislador_bloques.parquet` está viejo** | es del **02-07**; la canónica es del **06-09**. Hoy viaja por git tal como está, que es lo que reproduce el número de hoy | `python variables/legislador/src/ficha.py` — y `REGENERAR.ps1` no lo corre, hay que agregarlo |
| **3** | **Las features de origen del motor están viejas** | `features_proyecto.parquet` y `origen_por_acta.parquet` son del **20-08**; el dedup fue el 25-08 y el parser el 06-09. Misma forma que URGENTE M y H, sobre otra tabla | regenerar `origen_lider.py` + `origen_por_acta.py` |
| **4** | **El enganche por Orden del Día en el Senado** (URGENTE P) | el campo `proyecto` de la API trae la OD en el **95,3%** de las 321 actas. Mejor que rescatar del título. Ojo: viene en **dos formatos** y a veces es un **rango** (`O.D. 41 al 59/24`) | desarrollo nuevo, no un arreglo |

## 2. Las de orden — no mueven el número, pero son criterio

| # | qué | lo medido | recomendación |
|---|---|---|---|
| **5** | **`postura_gobierno.py`**: ¿se retira, se deja como utilidad, o se le busca consumidor? | funciona, 20 tests pasan, su parquet **nunca se generó** y **nadie lo lee**; su función principal perdió el consumidor cuando se neutralizó `proyeccion_hipotetica_bicameral` | **dejarlo**: la alineación con el gobierno es la pieza que cerró la Puerta D |
| **6** | **Los dos generadores neutralizados de `casos/`** | 468 LOC de dos formulaciones muertas, en la carpeta donde vive la viva. El argumento de "no perder el diseño" ya no aplica: los docstrings apuntan al commit que lo tiene | **archivarlos** |
| **7** | **`docs/taxonomias/AGENTE-CONSOLE-config.yaml`** | segunda copia del prompt del clasificador. Nadie la lee, la variante fue descartada, y **ya divergió** del código en el `model` | dejarlo con la cabecera nueva, o archivarlo |
| **8** | **El helper `check`/`chk` en 40 archivos de test** | ~150 LOC, el **75% de toda la duplicación del repo**. Fusionarlo rompe la convención de que cada test corre como script suelto | **no fusionar** — es diseño de la suite, no descuido |
| **9** | **Los 184 MB de `datos/Archivos_Borrar/`** | 47% del proyecto. Todo caché regenerable, nada viaja por git | vaciarla cuesta ~20 min de re-scrape del Senado + 75 MB de CKAN. Tu llamada |
| **10** | **¿Una carpeta de descarte o dos?** | las dos están en uso a propósito por 8 scripts distintos | **dejar dos**, ya documentadas en CLAUDE.md. Unificar toca 4 rutas de caché: más riesgo que valor |

## 3. Lo que está hecho y espera una acción tuya

| # | qué | cómo |
|---|---|---|
| **11** | Borrar el descarte | `Archivos_Borrar/` — 4,7 MB, incluidos los 167 locks de git en `git-locks-huerfanos/` |
| **12** | Instalar el hook `pre-commit`, **al cerrar la limpieza** (hoy avisaría en cada commit por las bitácoras vencidas) | `powershell -ExecutionPolicy Bypass -File "Nowcast Congreso Argy\.mapa\instalar-hook.ps1"` desde la raíz git |
| **13** | Confirmar el cierre en tu máquina | `python -m pytest tests/ datos/proyectos/tests -q` y `python verificar_regeneracion.py` |

## 4. Los URGENTE que ya estaban abiertos y la limpieza no tocó

**M, D, E, H, I, 2, F, 5, 8, L** — están descritos uno por uno en `URGENTE.md`. La limpieza
no pisó ninguno. Se le agregaron dos, **O** y **P**, que salieron de medir.

Y hay dos que **ya están resueltos y todavía figuran** — se borran en la fase 6:

- **N.1** — `alias_legislador_id.csv` ya está versionado (verificado con `git ls-files`).
- **N.2** — los ocho `votaciones_*.xlsx`: decidido el 08-09, son el entregable y quedan.
