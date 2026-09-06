# Baseline 'votá con tu grupo' sobre la base canónica

> **Se lee de abajo hacia arriba: la última "Actualización" manda.** Corregido el
> 2026-08-06 — el título decía "(2011–2025)" y las medidas de más abajo hablan de
> 781k votos, cifras del run de junio. **La base hoy tiene 1.016.632 votos / 6.231
> actas y cubre 2001–2026.** Los números de acá **no se re-midieron** (es otro
> módulo, sin dueño y marcado HECHO): valen como lo que eran al momento de
> correrlos, y la conclusión de fondo —el voto-dirección por bloque acierta ~0,99
> y por eso no es el negocio— se sostuvo en todas las re-mediciones posteriores.
> Para re-medir: `python evaluacion/baseline/src/baseline_canonico.py`.

Leave-one-out, solo votos sustantivos (afirmativo/negativo). Excluye "SIN BLOQUE".
Reproducir: `python evaluacion/baseline/src/baseline_canonico.py`.

## 1. Según nivel de agrupación (votos disputados = minoría ≥10%)
| Predigo con… | Todas | Disputadas |
|---|---|---|
| **bloque_norm** (bloque específico) | 0,979 | **0,969** |
| bloque_linaje (espacio político) | 0,946 | 0,919 |
| coalicion | 0,945 | 0,918 |

**Lectura:** con el bloque específico se acierta ~97% incluso en votaciones disputadas → predecir la dirección del voto individual sigue siendo un callejón sin salida para el ML (confirma Fase 0 sobre la base ampliada). Pero al subir a coalición/linaje cae a ~92%: **la disidencia intra-coalición (~8%) es señal real y modelable** (qué miembros se despegan de la línea, y cuándo).

## 2. Por cámara
- **Diputados:** 0,969 (disputadas). 
- **Senado:** sin medición — todos los votos recientes del Senado están "SIN BLOQUE" (argentinadatos no trae bloque). Pendiente resolver el bloque del Senado.

## 3. Por año (disputadas) — DRIFT
~0,97–0,99 estable de 2011 a 2023, y **cae en 2024 (0,946) y 2025 (0,923)**. Coincide con la fragmentación post-2023 (gobierno LLA en minoría, rupturas de PRO/UCR). 
- Es un **signo de drift real y reciente**: la disciplina se afloja justo ahora.
- Advertencia: parte de la caída 2024–2025 puede deberse también a ruido del cruce padrón→bloque (matching imperfecto). A confirmar al refinar la resolución de entidades del Senado/Diputados reciente.

## Implicancia para el producto
1. El voto-dirección por bloque sigue casi resuelto (no abrir ML ahí).
2. El valor migra a: **disidencia intra-coalición**, **asistencia/quórum**, **embudo**, y el **régimen 2024–2025** donde la disciplina baja.

## Actualización: primer baseline de Senado (Excel 2026)
Con el bloque del Senado resuelto vía el padrón de `manual_2026`:
- **Diputados:** 0,969 (disputadas).
- **Senado:** **0,938** (disputadas, n=388 — muestra chica, solo leyes 2026).
El Senado aparece algo menos disciplinado que Diputados, pero la muestra es chica; a confirmar al sumar la semilla (Senado 2004–2013).

## Actualización: base 2001–2025 completa (semilla CSV)
Con la semilla Década Votada integrada (ambas cámaras):
- **Diputados:** 0,965 (disputadas). **Senado:** **0,971** (disputadas, n=26.359 — ya robusto).
- El Senado histórico (2004–2014) resulta tan o más disciplinado que Diputados.
- Confirma sobre 25 años y 781k votos: el voto-dirección por bloque es un callejón sin salida; el valor sigue en disidencia intra-coalición, asistencia y el régimen 2024–2025.

---

# BASELINE DEL VOTO INDIVIDUAL — 2026-09-03 (paso 0 del plan de implementación)

**Script:** `src/baseline_voto_individual.py` · **Salida:** `outputs/baseline_voto_individual.json`
**Corrida:** 895 actas de Diputados (muestra aleatoria, seed 7), **166.935 votos emitidos**,
walk-forward, ventana 730 días.

## Por qué esta vara y no las anteriores

`backtest_cadena` está neutralizado (ADR-0012) y `backtest_agregador` mide contra "¿se
aprobó el acta?" con tasa base 95,15% — 4.542 de 4.890 actas en el bin superior. Un Brier
lindo sobre una variable casi constante no distingue un motor bueno de uno mediocre.
**El voto individual tiene 22,5% de negativos** y es el nivel donde la doctrina (ADR-0016)
manda que entren todos los términos nuevos.

## EL NÚMERO A BATIR

| métrica | valor |
|---|---:|
| **Brier** | **0,15197** |
| Brier climatología | 0,17462 |
| **Skill** | **0,1297** |
| Accuracy | 0,7823 |
| Log-loss | 0,48072 |
| **MAE del margen por acta** | **0,1502** |
| sesgo medio del margen | −0,0187 |
| p90 del error de margen | 0,2501 |

## Tres hallazgos que el baseline deja servidos

### 1. 🔴 La rama de bloque se usa en el 1,9% de los casos — y ahí es PEOR que nada

| fuente de dirección | votos | % | skill |
|---|---:|---:|---:|
| **récord individual** | 163.790 | **98,1%** | +0,1356 |
| **rama de bloque** | 3.145 | **1,9%** | **−0,1476** |

El corte `n_i >= 8` manda casi todo al récord propio. **Toda la maquinaria de share
condicionado por tema/origen, encogimiento Empirical-Bayes y linajes está corriendo para
el 1,9% de las predicciones**, y cuando corre lo hace peor que la tasa base.

Esto no invalida el trabajo del share: es el insumo de los novatos y de la rama de sobre
tablas (§III.A.5, donde el corte se desactiva). Pero **cambia dónde está el margen de
mejora del motor** y hay que decidir si `MIN_HIST_INDIVIDUAL = 8` es el valor correcto.

### 2. 🎯 El techo de δ, cuantificado — y es donde el motor MÁS pierde

| carácter del dictamen | votos | tasa real | Brier | **skill** |
|---|---:|---:|---:|---:|
| **ÚNICO (consenso)** | 13.241 | **98,26%** | 0,0726 | **−3,2527** |
| DISPUTADO | 20.436 | 73,22% | 0,1509 | +0,2303 |
| mayoría sin minoría | 6.900 | 67,32% | 0,1989 | +0,0958 |
| sólo minoría | 1.403 | 86,89% | 0,0980 | +0,1403 |
| sin dictamen | 124.955 | 76,40% | 0,1586 | +0,1206 |

**Con dictamen unánime el modelo es 4 veces peor que decir "98% que sí".** No sabe que
hubo consenso en comisión, así que subestima sistemáticamente el acompañamiento. Donde el
dictamen está disputado, en cambio, el motor aporta (+0,23).

**Ese contraste ES la oportunidad de δ**, y explica por qué el efecto medido era de −3,2
en logit: no es sólo que el dictamen informa, es que el motor hoy está ciego justo en el
caso más fácil.

### 3. 🎯 El modelo está SOBRE-CONFIADO — evidencia directa para ε₀

| bin | n | predicho | real | gap |
|---:|---:|---:|---:|---:|
| 0 | 1.059 | 0,054 | 0,186 | **+0,132** |
| 1 | 1.471 | 0,149 | 0,275 | **+0,126** |
| 2 | 3.024 | 0,252 | 0,359 | +0,107 |
| 3 | 5.019 | 0,351 | 0,461 | +0,110 |
| 4 | 7.269 | 0,454 | 0,588 | **+0,133** |
| 5 | 18.430 | 0,552 | 0,637 | +0,085 |
| 6 | 21.544 | 0,648 | 0,675 | +0,027 |
| 7 | 19.165 | 0,750 | 0,732 | −0,019 |
| 8 | 23.551 | 0,855 | 0,812 | −0,043 |
| 9 | 66.403 | 0,952 | 0,928 | −0,024 |

**Las predicciones están demasiado desparramadas en los dos extremos**: abajo predice más
bajo de lo que la realidad justifica, arriba predice más alto. Es exactamente el síntoma
que ataca el encogimiento afín $\tilde{P_i} = \varepsilon_0 + (1-2\varepsilon_0)P_i$ de
§III.A.3. **La corrección tiene evidencia directa antes de implementarla.**

## Limitaciones honestas de este baseline

- **Muestra, no censo:** 895 de 3.075 actas de Diputados. El sandbox corta a ~3 min; la
  corrida completa hay que hacerla en PowerShell (`--muestra 0`).
- **Sólo Diputados.** El Senado queda pendiente.
- **No simula:** compara $P_i$ contra el voto individual. No mide el paso por Monte Carlo
  ni el umbral. El MAE del margen es una aproximación de eso, no un sustituto.
- El **sesgo medio del margen es −0,0187**, o sea que el motor subestima el apoyo por ~2
  puntos porcentuales en promedio. Consistente con el hallazgo 2.
