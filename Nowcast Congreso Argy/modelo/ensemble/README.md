# Módulo: modelo/ensemble

<!-- huella: 07874c889fca -->

**Propósito.** La composición final del Nowcast — el nowcast **end-to-end de un proyecto**:

    P(aprobación) = P(llega al recinto) × P(mayoría | recinto)

Une las dos piezas ya validadas del sistema en un solo número (con su descomposición).

**Estado:** EN CURSO (v1: composición + nowcast por proyecto + tests)
**Owner actual:** Claude+Valle (2026-07-12)

**Resumen:** La composicion final: el nowcast end-to-end de un proyecto. Compone P(llega al recinto) x P(mayoria dado recinto) y corre el backtest de la cadena completa.

## Buscar acá si

- el numero final de P(sancion) de un proyecto
- el backtest de la cadena completa, Brier, skill o calibracion
- la Puerta D / camara revisora en el circuito bicameral
- condicionar la postura por el origen del proyecto
- P(mayoria) que da 0% o 100% (hay piso y techo por pedido de Valle)

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entradas:**
  - `variables/embudo/outputs/p_embudo.parquet` → `p_llega_recinto` por `proyecto_id` (el embudo).
  - `modelo/agregador_institucional` → función reutilizable `simular_votacion` (P mayoría|recinto como distribución). *Se importa su función pública; no se toca su código.*
- **Salida (contrato estable, `outputs/`):** `nowcast_<proyecto_id>.json` con los dos factores, P(aprobación) y la banda de votos. Función reutilizable: `nowcast_proyecto(proyecto_id, escenario, p_embudo_path)`.
- **Gate de pase:** calibración de la cadena dentro de tolerancia — **parcial**: cada factor está validado por separado (embudo skill 0,34-0,39; agregador Brier 0,0089). La calibración de la cadena COMPLETA sobre proyectos NO votados espera la posición de bloque proyectada (ver simplificación).

## Cómo se usa
```powershell
# demo autocontenida (no necesita datos): muestra la tarjeta end-to-end
python modelo\ensemble\src\ensemble.py demo

# nowcast de un proyecto real: su P(llega) sale de p_embudo por proyecto_id,
# y la postura de cada bloque se pasa en un escenario JSON
python modelo\ensemble\src\ensemble.py nowcast 1234-D-2026 escenario.json
```
Escenario JSON:
```json
{ "tipo_mayoria": "SIMPLE", "camara": "Diputados",
  "p_llega_recinto": 0.12,
  "bloques": [
    {"bloque": "UxP", "bancas": 99, "linea": "NEGATIVO",   "desvio": 0.03},
    {"bloque": "LLA", "bancas": 39, "linea": "AFIRMATIVO",  "desvio": 0.02}
  ] }
```
- `p_llega_recinto` es opcional: si falta, se busca por `proyecto_id` en `p_embudo.parquet`. Pasarlo en el JSON lo fuerza (útil para escenarios "¿y si…?").
- `linea` ∈ {AFIRMATIVO, NEGATIVO, NO_ACOMPANA}; `desvio` es la tasa de indisciplina del bloque (de `modelo/voto_individual`).
- Tipos de mayoría y cámaras: los del agregador (SIMPLE / ABSOLUTA / DOS_TERCIOS / TRES_CUARTOS).

## Qué devuelve (tarjeta)
`P(llega al recinto)` × `P(mayoría | recinto)` = **`P(aprobación)`**, más los afirmativos esperados con banda 5-95% y el umbral. Ejemplo (demo): 12,0% × 58,1% = **7,0%**, con la votación al filo (109,6 vs umbral 109,4).

## Simplificación v1 (documentada)
La **postura de cada bloque** es un dato de entrada (elegida a mano / observada), heredado del agregador. En el sistema final la proyecta un módulo de **posición de bloque por tema** (pendiente). Por eso:
- el nowcast de un proyecto YA VOTADO reproduce la historia (postura observada) → equivale al backtest del agregador (Brier 0,0089);
- el nowcast de un proyecto NO votado usa la postura que le pongas → la calibración de la cadena completa depende de esa proyección futura.

## Backtest de la cadena completa (`src/backtest_cadena.py`, opción B — 2026-08-13)
Mide la calibración del end-to-end contra la realidad: sobre la cohorte **madura** y
etiquetada del embudo (`construir_cohorte` + `cohorte_madura`, label `sancionado`),
compone `p_llega` (embudo) × `p_mayoría` (`nowcast_auto`, postura proyectada point-in-time
sobre el roster nominal de **conducta**) y lo compara con `sancionado`. **Baseline:** el
`p_sancion` que el embudo calcula solo (¿la maquinaria roster+agregador aporta encima del
embudo?). Consume contratos públicos; no reimplementa la cohorte ni las métricas (`_metricas`).

- **Point-in-time honesto:** cada proyecto se evalúa a su `fecha_publicacion`; `cohorte_madura`
  (≥2 años) evita etiquetar como "no sancionado" a proyectos que aún podrían serlo.
- **Memoización:** por defecto la postura NO se condiciona, así que `p_mayoría` depende solo de
  (cámara, mes) → se calcula una vez por mes. Corrida liviana.
- **`--origen-por-proyecto` (2026-08-14):** condiciona la postura de bloque por el ORIGEN FINO de
  cada proyecto (EJECUTIVO=mensaje del PE/JGM · OFICIALISMO=legislador del gobierno · OPOSICION),
  leído de `variables/proyecto/features_proyecto.parquet`. La memoización pasa a
  (cámara, mes, **origen**). Es opt-in y aditivo: sin el flag el comportamiento es idéntico a v1.
  Motivo (medido contra votos reales era-Milei, control `validar_condicionamiento_votos.py`,
  69.628 votos walk-forward): condicionar sube el acierto del voto de **59% a 76%**, y **separar el
  PE del oficialista es clave** — el oficialista agrupado con el PE da 42% (peor que no condicionar),
  separado da 78%. OJO: en Diputados el P(mayoría) AGREGADO satura ~1 igual (la cámara es goleada),
  así que la mejora vive en la fidelidad del voto por bloque/legislador, no necesariamente en el
  pass/fail. Salida → `outputs/backtest_cadena_origen.json`.
- **Optimizado (2026-08-13):** la canónica (1M+ votos) se carga UNA sola vez, no una por mes
  (`construir_nowcast_mes_hoisteado`, reproduce EXACTO la cadena de `nowcast_auto`). Un año de
  Diputados corre en ~20 s (antes, minutos). La corrida completa igual conviene en PowerShell.
- **Alcance real v1 = Diputados.** El Senado histórico no se puede rostear con el padrón por
  defecto de `nowcast_auto` (`padron_senado.csv` = 72 vigentes; el histórico arranca fin-2017 y
  `nowcast_auto` no expone `padron_file`). Y el hueco Diputados 2020-2023 (pausado) invalida la
  ventana de postura de los proyectos presentados ~2020-2025. El harness **saltea con aviso** los
  (cámara, mes) sin historia/roster; no inventa nada.
- **Salidas:** resumen → `outputs/backtest_cadena.json` (viaja a git); detalle por proyecto →
  `Archivos_Borrar/backtest_cadena_detalle.csv` (regenerable, `*.csv` gitignored).

```powershell
# corrida real (Valle, en su PC): Diputados, cohorte completa
python "Nowcast Congreso Argy\modelo\ensemble\src\backtest_cadena.py" --camara Diputados --n-sims 2000
# con condicionamiento por origen fino (PE/oficialista/oposicion):
python "Nowcast Congreso Argy\modelo\ensemble\src\backtest_cadena.py" --camara Diputados --n-sims 2000 --origen-por-proyecto
# control de fidelidad del voto vs votos reales (apagado/lado/fino):
python "Nowcast Congreso Argy\modelo\ensemble\validar_condicionamiento_votos.py"
```

## Puerta A / Puerta C — el carácter observado del dictamen (`src/puerta_a.py`, 2026-08-22)

**A y C no son probabilidades.** Son el carácter del trabajo en comisión —quién firmó,
disidencias, bloques— leído de los PDF de la Orden del Día. Un hecho. Condicionan la
votación de su cámara (A sobre B, C sobre D); **no multiplican el número**. La enmienda
del 22-08 en `PUERTA-D.md` es el contrato.

```
P(sanción) = [A observada] · P(B | carácter de origen)
           · [C observada] · P(D | carácter de la revisora)
```

**Tres estados, y el tercero NO colapsa al segundo** — son opuestos:

| Estado | Qué significa |
|---|---|
| `con_caracter` | hay dictamen y lo leímos |
| `sin_dictamen` | a la fecha de corte no hay dictamen |
| `sin_dato` | puede haberlo y no saberlo: la OD no se publicó (mediana 224 días), el PDF no se pudo leer, o falta el empalme |

En `sin_dato` **no se anula nada**: el condicionante se encoge a 0 y queda la estimación
sin condicionar. Se REUSA `puerta_d.ajuste_paso_origen` — mismo mecanismo, un solo modelo.

**Cobertura medida el 22-08-2026** (contra los 42.141 proyectos de `p_embudo`): 3.970 con
dictamen leído (9,4%), de los cuales **809 lo tienen en las DOS cámaras**. De los que
tienen dictamen, 1.221 terminaron sancionados (30,8%); de los que no, 109 de 38.171 (0,29%).

**`fecha_corte` no es opcional.** Un dictamen de 2015 tiene que salir `sin_dictamen` en un
corte de 2013. Y un dictamen **sin fecha utilizable** sale `sin_dato`, nunca `con_caracter`:
darlo por existente es la fuga que la guarda tiene que impedir. Esto importa porque **el
parquet del Senado no trae `od_publicacion`** — la fecha se arma en cascada
(`od_publicacion` → `fecha_impresion` con el parser de `datos/expedientes` → 31-dic de
`od_anio`), y el último escalón es tardío a propósito: equivocarse hacia adelante pierde
señal, hacia atrás fuga el futuro.

**Acumulados: observados, pero MARCADOS** (decisión de Valle, 22-08). Una OD dictamina
varios expedientes; son 1.433 de 4.806 filas. Se marcan con `acumulado` y `n_expedientes`
porque su destino está atado al texto unificado: al medir son casos correlacionados.
⚠️ La columna `cabecera` de `expedientes_resultados` **no sirve** para reconstruir el grupo:
verificado sobre las 117.412 filas, nunca apunta a otro proyecto — es un flag con dos
grafías, no una estructura de enlace. El acumulado se deduce de `expedientes_sumario`.

**El estimador del delta está PENDIENTE y el motivo está medido.** No se puede ajustar
contra «¿ganó la votación en su cámara?»: de **1.898 proyectos de ley con resultado en el
recinto, 2 son RECHAZADO**. Es la misma degeneración que la bitácora del 13-08 ya había
encontrado por otro lado. `COEF_POR_DEFECTO` deja todo en cero, o sea el límite no
condicionado — que es exactamente lo que el sistema calcula hoy. Las dos salidas con
varianza real (el margen, o la revisora) están en el docstring de `estimar_delta_caracter`.

**Pendiente anotado (Valle, 22-08): el peso del firmante.** Hoy todas las firmas valen
igual y no es cierto — un jefe de bloque o un presidente de comisión carga más señal. Las
fuentes ya existen: `variables/proyecto/src/scrape_jefes_bloque.py` y
`comisiones_autoridades.parquet` (46 presidentes con su cargo).

## Las guardas contra la sobreconfianza (2026-08-22)

`simular_con_guardas` (en `src/ensemble.py`) es el **único** lugar donde viven las dos
guardas que pidió Valle el 14-08. Todo lo que simule una votación pasa por ahí:

| Guarda | Qué hace | Por qué |
|---|---|---|
| `DESVIO_MIN_INDIVIDUAL = 0.02` | piso de desvío **por legislador** antes de simular | un 0% medido sobre historia finita no es un 0 real: hay ausencia, enfermedad, sorpresa |
| `P_INCERTIDUMBRE = 0.01` | P(mayoría) se reporta en **[ε, 1-ε]** | riesgo SISTÉMICO que el supuesto de votos independientes no capta |

Poner las dos en 0 devuelve el agregador crudo: son **opt-out exacto**, no un camino aparte.
La salida trae `p_aprobacion_cruda`, `desvio_min_aplicado` y `p_incertidumbre_aplicada`
para que el acotado **nunca sea invisible**.

⚠️ **Antes del 22-08 las dos vivían adentro de `nowcast_proyecto`, o sea sólo en el camino
de la formulación v1.** `puerta_d.p_voto_revisora` devolvía `p_aprobacion` **cruda** —un
roster unánime le daba `1.0` exacto— y `casos/proyeccion_hipotetica_bicameral.py` tenía su
**propia copia** del clamp. Tres lugares, dos definiciones y una ausencia. Al dar de baja
v1, la producción se quedaba sin techo de confianza justo en la puerta que sobrevive, y
nada lo iba a avisar: el número seguía saliendo. `test_guardas_confianza.py` incluye el
chequeo que **falla con el código anterior** y uno que recorre el repo verificando que las
constantes se **definan en un solo archivo**.

Contrato de `p_voto_revisora`: además de lo que ya devolvía, ahora trae `p0_cruda` y
`guardas: {desvio_min, p_incertidumbre}`.

## Tests
```bash
python modelo/ensemble/tests/test_ensemble.py            # 36 chequeos offline (sin datos)
python modelo/ensemble/tests/test_puerta_d.py            # 24 chequeos offline
python modelo/ensemble/tests/test_guardas_confianza.py   # 14 chequeos; falla con el codigo viejo
python modelo/ensemble/tests/test_puerta_a.py            # 31 chequeos; incluye la guarda point-in-time
python modelo/ensemble/tests/test_backtest_cadena.py     # 53 chequeos offline, dos backends de dtype
```

## Pendientes / v2
- **Posición de bloque proyectada por tema** (desbloquea la calibración de la cadena completa y el nowcast automático sin escenario a mano). Depende de `variables/proyecto` (tema) + un módulo de posición de bloque.
- Propagar incertidumbre del embudo a una **banda sobre P(aprobación)** (hoy es un punto).
- Conectar la asistencia condicional (`variables/asistencia_quorum` escalón 2) al factor de mayoría.

## Convenciones
Resiliencia: errores específicos, parsing defensivo, logging estructurado. Se consume el
CONTRATO de los otros módulos (parquet del embudo, función pública del agregador); no se
edita su código.
