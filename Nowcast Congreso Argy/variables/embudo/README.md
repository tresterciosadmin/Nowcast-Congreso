# Módulo: variables/embudo

<!-- huella: e3b0c44298fc -->

**Propósito.** Supervivencia del proyecto de ley: `presentado → comisión →
dictamen → recinto → sanción`. La mayoría de los proyectos mueren en un cajón,
no son rechazados. Estimar **cuáles salen del cajón** es el diferencial del
nowcast (la mitad de la ecuación `P(aprobación) = P(llega al recinto) × P(mayoría|recinto)`).

**Estado:** EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)
**Owner actual:** Claude+Valle (2026-07-12)

**Resumen:** Supervivencia del proyecto: presentado -> comision -> dictamen -> recinto -> sancion. Estima P(llega al recinto), la mitad de P(aprobacion). Es el diferencial del nowcast.

## Buscar acá si

- por que la mayoria de los proyectos nunca se votan
- P(llega al recinto), cohorte, o proyectos maduros vs. en curso
- escenarios y contrafactuales (`escenarios.py`) — los coeficientes de la logistica NO son efectos
- el skill del embudo o su backtest temporal
- leer de `proyectos.db` vs. del parquet (`EMBUDO_FUENTE=parquet`)
- medir la cohorte por las DOS rutas (parquet vs `proyectos.db`): `src/cohorte_dos_rutas.py`, que consume `datos/proyectos`

<!-- Las dos cosas de arriba las levanta `.mapa/indexar.py` al MAPA.md de la
     raiz: el `Resumen:` va a la columna "Que es" y las pistas al router
     "Donde buscar que". Si cambia lo que hace el modulo, actualizalas aca. -->

## Contrato
- **Entradas:** `datos/expedientes/data/clean/*.parquet` (contrato estable) y —cuando
  exista— `variables/proyecto/data/features_proyecto.parquet` (tema, origen).
- **Salida (contrato estable, `outputs/`):**

  | Archivo | Contenido |
  |---|---|
  | `embudo_etapas.csv` | tasas globales del embudo por etapa (absolutas y condicionales) |
  | `embudo_por_anio.csv` / `embudo_por_camara.csv` | el embudo abierto por año y por cámara |
  | `embudo_por_comision.csv` | supervivencia por comisión (cementerios vs. rápidas) |
  | `p_embudo.parquet` | `proyecto_id, anio, etapa_actual, p_llega_recinto, p_sancion` — **el contrato que consume el ensemble** |
  | `backtest_embudo.json` | Brier / AUC / calibración walk-forward vs. baseline (tasa base) |

- **Depende de:** datos/expedientes. Lo consume: `modelo/ensemble` (multiplica P(embudo) × P(agregador)).
- **Gate de pase:** el backtest temporal supera la tasa base (skill > 0) → CUMPLIDO en la corrida local (ver ESTADO).

## Diseño (decisiones clave)
- **Etapas y target.** `llega_recinto` = tuvo resultado no nulo (media sanción /
  aprobado) **o** fue ley. `sancionado` = está en `expedientes_leyes`. Se modelan
  ambos; el headline es `p_sancion`.
- **Sin leakage.** Los rasgos son SOLO los conocidos **al momento de presentar**:
  año, mes, cámara, nº de comisiones giradas, one-hot de las comisiones más
  frecuentes, año electoral, y la **tasa histórica de éxito del autor** calculada
  únicamente sobre el train. El dictamen/resultado son *targets*, nunca rasgos.
- **Caducidad (Ley 13.640).** Los proyectos caducan si no avanzan. El modelo se
  entrena/backtestea sobre **cohortes maduras** (presentadas hasta `MADUREZ_ANIOS=2`
  antes del último año con datos) para no contar como "muerto" lo que sigue vivo.
  Los proyectos inmaduros SÍ se scorean (es el uso real: predecir el futuro).
- **Backtest walk-forward.** Para cada año T: entrena con años < T, predice T. Sin
  ver el futuro. Compara Brier contra el baseline de tasa base.
- **Probabilidades calibradas.** Regresión logística sin `class_weight` balanceado
  (el balanceo mejora el ranking pero rompe la calibración, y el nowcast necesita P reales).
- **Hooks a variables/proyecto.** Si aparece `features_proyecto.parquet` con `origen`
  (oficialismo/oposición) o columnas `tema_*`, el modelo las incorpora solo. Son los
  rasgos más predictivos del embudo; hoy corre sin ellos.

## Cómo correr (PC de Valle, tiene los parquets de expedientes)
```powershell
# desde la raíz del repo
python variables\embudo\src\embudo.py funnel   # caracterización (segundos, no requiere sklearn)
python variables\embudo\src\embudo.py modelo   # survival v1 + backtest + p_embudo.parquet
python variables\embudo\src\embudo.py all       # todo
```
Variables de entorno opcionales: `EXP_CLEAN=<dir>` (si los parquets están en otro
lado), `OUT=<dir>`. Requisitos: `pip install -r variables\embudo\src\requirements.txt`.

## Tests
```bash
python variables/embudo/tests/test_embudo.py   # 18 chequeos offline (fixture sintética)
```

## Pendientes / v2
- Enchufar `origen` (oficialismo/oposición) y `tema` cuando `variables/proyecto`
  los publique — es el salto de calidad esperado del embudo.
- Modelo de supervivencia con tiempo-hasta-evento (hoy es clasificación binaria
  sobre cohortes maduras); permitiría censura a la derecha explícita.
- Cofirmantes (red de autoría) del bot como rasgo de tracción.

## Convenciones
Resiliencia obligatoria: errores específicos, parsing defensivo (columnas por
nombre, tolerante a NA), logging estructurado. Consumir contratos, no código.

## ICG — contexto político (2026-08-04, URGENTE 1)

Entran tres rasgos desde `variables/proyecto/data/icg_mensual.csv`: `icg`,
`icg_delta_3m` e `icg_sin_dato`, **rezagados un mes** — un proyecto presentado en
M ve el ICG de M-1, nunca el de M. Es la única variable no procedimental.

`cmd_modelo` imprime una **ablación de tres escalones**:

| escalón | sancionado | llega_recinto |
|---|---:|---:|
| solo procedimental | 0,3429 | 0,3992 |
| + origen/líder | **0,3643** | **0,4195** |
| + ICG | 0,3630 | 0,4195 |
| **aporte del ICG** | **‑0,0013** | **0,0000** |

> 📅 **Cifras medidas el 07-08-2026** sobre la cohorte de 42.141 proyectos de ley
> (CKAN refrescado al 30-jun + los proyectos del bot, vía `proyectos.db`).
> **Reemplazan a las del 04-08 (0,3628 / 0,4112) y al 0,3647 del 07-08 mediodía:**
> las tres son correctas para sus datos, pero **los datos cambiaron**. Cualquier
> comparación de skill tiene que decir contra qué cohorte se midió — es la tercera
> vez en el proyecto que un número se repite sin su fecha.

**El ICG NO aporta.** Pesa el **0,3%** de la ponderación (suma de |coeficientes|
estandarizados), contra 68% de las comisiones y 22% del trámite. Se deja
enchufado porque no molesta, es barato de mantener y puede empezar a valer
cuando el modelo se condicione por tema — pero **hoy no es la variable que
faltaba**, y el techo del modelo no está acá.

> ⚠️ **Fe de erratas.** La primera medición del 04-08 dio +0,003 y estaba mal:
> salió de una cohorte cacheada en parquet, donde las listas de `comisiones`
> vuelven como `numpy.ndarray` y el `isinstance(v, (list, tuple))` del one-hot
> las rechazaba **en silencio** — las 25 columnas quedaban en cero y el modelo
> corría sin su bloque de rasgos más importante. Corregido con `_como_lista()`.
> Señal de que el número corregido es el bueno: el skill de `sancionado` da
> 0,3628, que coincide con el 0,363 que ya figuraba en el caso de la Ley de Lobby.
> *(Ese 0,3628 era el valor con los datos del 04-08; ver la nota de fecha arriba.)*

Si falta el CSV, el modelo corre igual sin la variable.

## ⚠️ Cómo (no) leer este modelo

**Los coeficientes de la logística NO son efectos.** Auditado el 2026-08-07:
`autor_tasa_hist` correlaciona **0,874** con `origen_ejecutivo` —el autor de un
proyecto del PE *es* el presidente—, así que la regresión le adjudica el crédito
a la tasa del autor (coef. 0,61) y deja `origen_ejecutivo` en **0,04** y `lider`
en **−0,03**, cuando las tasas crudas son **78,8% vs 1,4%** y 6x respectivamente.

No es un defecto a corregir: se probó encoger `autor_tasa_hist` y el skill **cae
0,016**, porque esa variable es el canal por el que entra la señal del Ejecutivo.
El modelo predice bien; lo que no se puede es leerlo como atribución de causas.

**Para leer efectos, usar contrafactuales:** `src/escenarios.py` scorea el mismo
proyecto cambiando quién lo firma y mueve `origen`, `lider` y `autor_tasa_hist`
**a la vez** (moverlos por separado da un contrafactual falso). Es la única vía
válida para responder "¿cuánto vale que lo mande el PE?".

Lo mismo aplica al desglose de importancia por grupo de rasgos: sirve para
detectar bloques muertos (así apareció el bug del one-hot el 04-08), no para
repartir mérito entre variables colineales.

## Variables: qué mide cada una (auditoría 07-08)

| rasgo | qué es | estado |
|---|---|---|
| `n_giros` · `multi_comision` | comisiones **al ingresar** (contrato `giros_iniciales.parquet`; antes era el acumulado de hoy) | ✅ sin leakage; los más fuertes. Miden **alcance**, no dificultad |
| `com__<COMISIÓN>` | one-hot de las 25 más frecuentes | ✅ el bloque de mayor peso (68%) |
| `autor_tasa_hist` | tasa histórica del autor, solo sobre train | ⚠️ colineal con el origen — ver arriba |
| `origen_*` · `lider` | de `features_proyecto` | ⚠️ coeficientes canibalizados |
| `mes` | mes de presentación, continuo | ⚠️ el patrón real es un escalón (enero 9,5% · marzo 2,5%), no una recta; categorizarlo da −0,002 |
| `anio_electoral` | año impar | ⚠️ no discrimina (3,51% vs 3,32%) |
| `icg` · `icg_delta_3m` | contexto político, rezagado 1 mes | aporte ~0 (ADR-0008) |
