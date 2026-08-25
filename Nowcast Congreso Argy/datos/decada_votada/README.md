# Módulo: datos/decada_votada

<!-- huella: 7f85c976b02b -->

**Propósito.** Usar el trabajo de Andy Tow ("La Década Votada") vía el paquete R **legislAr** como **semilla histórica de un solo uso** para arrancar nuestra base canónica. **No copiamos su dataset ni dependemos de que él lo siga actualizando**: lo exportamos una vez, lo normalizamos a nuestro esquema y de ahí en adelante mantenemos los datos nosotros (ver `datos/canonica` y `datos/bot_recoleccion`).

**Estado:** HECHO — semilla integrada vía CSV (Diputados 2001-2010 + Senado 2004-2014).
El export en R quedó **innecesario**: ver "ACTUALIZACIÓN: vía CSV" al final.
**Owner actual:** Claude+Franco (cerrado 2026-06-29)

> ⚠️ **Dependencia viva, no la muevas:** `datos/canonica/src/run_pipeline.py` lee
> `Aportes sobre dataset congreso/towlandia-master/public/DecadaVotadaCSV.zip`. Es el
> único archivo de esa carpeta que el pipeline necesita para reconstruirse de cero.

**Resumen:** Semilla historica de un solo uso: el dataset de Andy Tow ('La Decada Votada') exportado una vez y normalizado. No se depende de el en vivo (ADR-0002).

## Buscar acá si

- de donde salen las votaciones anteriores a 2011
- por que hay codigo en R en un repo de Python

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Qué aporta
- Votos individuales con `voto`, `nombre_bloque`, `nombre_legislador`, `provincia` desde **1998/2001**.
- Cobertura: Diputados ~1998–2019 y **Senado 2004–2013** (la única fuente histórica de Senado que tenemos hoy).
- Funciones legislAr: `show_available_bills()`, `get_bill_result()`, `get_bill_votes()`.

## Contrato
- **Entradas:** paquete R `politicaargentina/legislAr` (datos de decadavotada.com.ar). Uso único.
- **Salida (contrato estable):** `data/clean/decada_votada_*.parquet` con el esquema canónico de `docs/schemas` (mismas columnas que el detalle de CKAN).
- **Depende de:** `docs/schemas`.
- **Gate de pase:** export reproducible a parquet validado; rangos de fecha y cobertura por cámara documentados en ESTADO.

## Cómo trabajar acá
1. Reclamá el módulo en `coordinacion/TABLERO.md`.
2. **Límite R↔Python (ver ADR-0002):** legislAr corre en **R una sola vez** y vuelca a parquet; el resto del stack sigue en Python. No reimplementamos su scraping.
3. Script R sugerido (`export_seed.R`): instalar legislAr, iterar `show_available_bills()` por cámara, traer `get_bill_votes()` por acta, escribir parquet con `schema_version`.
4. Registrá el avance en `coordinacion/ESTADO-DEL-PROYECTO.md` y abrí PR.

## Importante
Esta es la **semilla**, no la fuente viva. Una vez cargada en `datos/canonica`, este módulo no se vuelve a correr salvo para auditar/rellenar historia. Las votaciones nuevas las trae `datos/bot_recoleccion` desde fuentes oficiales.

## ACTUALIZACIÓN: vía CSV (preferida, sin R)
Los Aportes incluyen `DecadaVotadaCSV.zip` (dump crudo de Andy Tow, 2014) con votaciones
de **ambas cámaras**. Es más rápido y confiable que el scraping de R, e incluye el **Senado**.
- Script: `src/from_csv.py`. Pasos: descomprimir el zip a una carpeta y `CSV=<carpeta> python src/from_csv.py`.
- Códigos de voto decodificados: 0=AFIRMATIVO, 1=NEGATIVO, 2=ABSTENCION, 3=AUSENTE.
- Cobertura: Diputados 2001–2014 (se **recorta a ≤2010** para no solapar con CKAN), Senado 2004–2014 (completo).
- `export_seed.R` queda como alternativa (llega hasta ~2019 en Diputados, pero CKAN ya cubre ese tramo).
