# Módulo: variables/embudo

**Propósito.** Supervivencia del proyecto de ley: `presentado → comisión →
dictamen → recinto → sanción`. La mayoría de los proyectos mueren en un cajón,
no son rechazados. Estimar **cuáles salen del cajón** es el diferencial del
nowcast (la mitad de la ecuación `P(aprobación) = P(llega al recinto) × P(mayoría|recinto)`).

**Estado:** EN CURSO (v1: embudo por etapas + modelo de supervivencia + backtest temporal)
**Owner actual:** Claude+Valle (2026-07-12)

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
