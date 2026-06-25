# Resultado Fase 0 — Baseline de bloque

**Fecha:** 25-jun-2026 · **Fuente:** CKAN HCDN votaciones nominales, períodos 129–137 (2011-03 a 2020-01)
**Muestra:** 899 actas · 231.043 filas diputado-voto · 113 bloques · método leave-one-out

## Números

| Corte | Universo | Accuracy bloque | n votos |
|---|---|---|---|
| Todas | Dirección sustantiva (AFIRM/NEG) | **0,989** | 163.587 |
| Disputadas (minoría ≥10%) | Dirección sustantiva | **0,984** | 89.229 |
| Todas | 4 clases (incl. ausente/abstención) | 0,807 | 215.433 |
| Disputadas | 4 clases | 0,820 | 110.399 |

## Lectura (corrige la hipótesis previa)

La hipótesis del informe de validación —"el baseline real es ~77%, hay lugar para el ML"— **queda refutada por los datos**. El ~77-80% de la literatura mide **asistencia y abstención** (coincide con nuestro corte de 4 clases, 0,81). Pero la **dirección del voto** (afirmativo vs negativo), condicionada a que el legislador vote, la predice la mayoría del bloque con **~0,99, incluso en las votaciones disputadas**.

**Conclusión de gate:** predecir el voto individual de dirección es un callejón sin salida; la heurística de bloque ya es casi perfecta. El ML no tiene margen ahí. El valor del producto **no** es "predecir cómo vota cada legislador".

## Hacia dónde migra el valor (incertidumbre genuina)

1. **Asistencia / quórum** — el corte de 4 clases cae a ~0,81 porque ausencia y abstención son idiosincráticas y no las explica el bloque. Quién da quórum y quién se ausenta es donde se ganan o pierden las leyes.
2. **Capa de embudo** — P(el proyecto llega al recinto): comisión → dictamen → tratamiento. La mayoría de los proyectos mueren antes de votarse.
3. **Posición del bloque** — la negociación de cúpula que fija la línea. Es el "supuesto oculto" del premortem: el resultado es función del deal político, no de los atributos del proyecto.

## Corrección de datos (importante)

- El dataset CKAN de votaciones **dejó de actualizarse el 2020-02-03** (período 137 termina 2020-01-29). No hay datos oficiales 2020–2026 ahí.
- Gap cubierto por **argentinadatos.com**: Diputados 2020→oct-2025 (295 actas), Senado jul-2024→nov-2025 (120 actas), con votos por legislador y bloque.
- Pendiente: cuantificar el **sesgo de selección** (proyectos presentados vs. con votación nominal) cruzando con `expedientes`.

## Próximo paso sugerido

Reorientar Fase 1: dejar el voto-dirección como baseline cerrado (~0,99) y atacar (a) modelo de asistencia/quórum, (b) embudo de supervivencia del proyecto, (c) cross-check del baseline sobre datos recientes (argentinadatos) para medir drift post-recambio dic-2025.
