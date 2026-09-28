# ADR-0026 — `rec_i^tema`: el récord del legislador condicionado por tema (URGENTE 8, FASE 1)

**Fecha:** 2026-09-16 · **Estado:** IMPLEMENTADO, MEDIDO sobre el censo completo
y **PRENDIDO** (`RECORD_POR_TEMA=1` por defecto) · **Decide:** Claude, con
autonomía delegada explícitamente por Franco en `coordinacion/
PROMPT-MULTITEMA-V2.md` ("podés prender banderas si el censo completo mejora
y queda documentado en fórmula + ADR") · **Toca:**
`modelo/ensemble/src/nowcast_puertas.py`, `evaluacion/baseline/src/
{medir_rec_por_tema,fase1_rec_por_tema}.py` (nuevos) · **Se relaciona con:**
ADR-0016 (doctrina de la parte al todo), ADR-0024 (multitema a nivel bloque,
negativo), ADR-0025 ($\eta_j$, el otro término prendido por censo), URGENTE 8
(pendiente desde el 04-09, medido y descartado esa vez por falta de dato)

> **⚠️ ENMENDADO POR ADR-0034 (28-09-2026): `RECORD_POR_TEMA` está APAGADO.** El 11,06% de
> abajo se midió con fuga (`shift(1)` por fila: el récord por área veía los artículos de la
> misma ley, votados el mismo día). Con la misma metodología e historia estricta da −2,91%; en
> el censo con el harness que importa el motor, el récord por tema **empeora** el Brier 2,1%
> (IC por ley [0,8; 3,5]) y 6,4% en los votos donde actúa. Se apagó con el criterio simétrico
> al que lo prendió. La implementación queda; lo de abajo se conserva como registro.

## Contexto — por qué esto es distinto de ADR-0024

`PROMPT-MULTITEMA-V2.md` diagnosticó que el experimento de ADR-0024 (multitema
a nivel BLOQUE) no podía responder la pregunta que se le hizo: la rama de
bloque dispara para legisladores con **cero historia propia** — es un relleno
para datos faltantes, no un modelo de cómo vota cada bloque — y condicionarla
por tema es hacer una pregunta fina sobre alguien de quien no hay dato. **Al
mismo tiempo, el tema está AUSENTE justo donde sí hay datos**: el 99,6% de las
predicciones sale de $\text{rec}_i$ (el récord del legislador), un solo número
promediado sobre TODOS los temas. Un diputado veterano vota distinto en
laboral que en ambiente y el motor no lo podía ver. **FASE 1 mueve el término
adonde está el dato: el legislador, no el bloque.**

## FASE 1 — medí primero (esto decidió el diseño)

`evaluacion/baseline/src/medir_rec_por_tema.py`, sin gastar créditos de API
(no corre `agente_taxonomias`; mide con la cobertura que `tema_por_acta.parquet`
tiene HOY), contestó las tres preguntas del prompt:

1. **Cobertura de tema por acta** (tabla ANCHA, `acta_expediente_todas.parquet`,
   no la angosta — la misma trampa que ya costó dos veces): **56,9%** sobre la
   ancha (5.043 actas), **51,4%** sobre el universo completo de la canónica.
   De las clasificadas, 80,4% tiene al menos un área sustantiva (no-AUX).
2. **Curva de skill contra el umbral $n_i^{\text{área}}$**: el récord por área
   (encogido Empirical-Bayes $k{=}5$ hacia el récord GENERAL de la misma
   persona) **le gana al récord general en TODO el rango útil** —8,1% menos
   Brier con $n_i^{\text{área}}\geq 1$ (100% de cobertura del subconjunto),
   bajando gradualmente a 6,1% en $n\geq 8$ (78,5% de cobertura) y volviéndose
   negativo recién en $n\geq 32$ (39% de cobertura, posible efecto de
   composición de la submuestra, no investigado más). No hace falta ningún
   umbral fijo: el encogimiento ya hace el trabajo solo.
3. **Discriminación real vs. ruido**: sobre 1.419 legisladores con $\geq 8$
   votos en $\geq 2$ áreas, el rango REAL entre sus áreas (mediana 0,4286) es
   MUCHO mayor que el que produciría el puro ruido de muestreo (shuffle test:
   mediana 0,2308, p95 0,4792) — **44,75% de los legisladores superan el p95
   del ruido**. La gente vota distinto según el tema, de verdad, no por azar.

## Decisión — el diseño

**Un solo grado de libertad, aislado** (mismo principio que el brazo de
control de FASE 0): para el mismo voto, la única variable que cambia es QUÉ
récord se usa —general vs. por-tema-combinado—, nunca cuánto se confía en
tener un récord (eso sigue viniendo de $n$ del récord GENERAL).

$$\hat{r}_i^{k} = \frac{n_i^k\, r_i^k + k_{\text{shrink}}\, r_i}{n_i^k + k_{\text{shrink}}}
\qquad k_{\text{shrink}}=5$$

Encoge hacia el récord GENERAL de la MISMA persona (información INDIVIDUAL,
no el share del bloque — es la doctrina de FASE 1, no ADR-0018 que encoge
hacia el bloque). Con varias áreas objetivo (la multietiqueta del proyecto),
se combinan **en LOGIT**, ponderadas por la confianza REAL de cada etiqueta
(regla IV.2 de `FORMULA-COMPLETA.md`: nunca promediar en probabilidad — el
mismo error que ADR-0024 detectó a nivel bloque, corregido acá desde el
diseño, no como parche).

**Implementación** (`nowcast_puertas.py`):
- `alineacion_individual_por_area(votos, cond_por_acta, origen_map, origen, areas_objetivo, ind_general, ...)`
  — nueva función; reusa `_alineacion_base` (extraída de `alineacion_individual`,
  refactor sin cambio de comportamiento, 49/49 tests sin regresión) para
  garantizar la MISMA ventana walk-forward que el récord general.
- La multietiqueta del proyecto se resuelve **independiente de `TEMA_AUTO`**
  (`_resolver_multietiqueta`, extraída de `_tema_auto`): son dos mecanismos
  distintos — `TEMA_AUTO` condiciona la POSTURA DE BLOQUE (sigue apagado,
  ADR-0024 negativo) y `RECORD_POR_TEMA` condiciona el RÉCORD DEL LEGISLADOR
  (prendido, esta evidencia). Que uno esté prendido y el otro no es
  intencional, no una inconsistencia.
- Manual `tema=` (si el llamador lo pasa) sigue ganando siempre, igual que en
  el resto del archivo.

## FASE 1 — validación sobre el CENSO completo

`evaluacion/baseline/src/fase1_rec_por_tema.py` — comparación PAREADA voto a
voto (`rec_general` vs. `rec_tema_combinado`, la MISMA fórmula que
`perfil_legislador`/`combinar_logit` usan en producción), sobre el
subconjunto que toca (318.564 votos de actas con $\geq 1$ área sustantiva):

| corte | Brier general | Brier tema | mejora relativa |
|---|---:|---:|---:|
| **global** | 0,13924 | 0,12384 | **11,06%** |
| Diputados | 0,15111 | 0,13365 | 11,56% |
| Senado | 0,09014 | 0,08324 | 7,65% |
| hasta 2011 | 0,11796 | 0,10285 | 12,81% |
| 2011-2015 | 0,10810 | 0,09470 | 12,40% |
| 2015-2019 | 0,17447 | 0,15449 | 11,46% |
| 2019-2023 | 0,09695 | 0,09149 | 5,63% |
| desde 2023 | 0,18525 | 0,17195 | 7,18% |

**Positivo en TODOS los cortes — cámara, era, y cantidad de áreas por voto (de
9,8% con 1 área a 39,9%-59,8% con 5+ áreas, n chico ahí, pero nunca negativo)**.
A diferencia de ADR-0024 (negativo en las tres reglas, en la rama que las
tocaba), acá no hay ningún subconjunto que empeore. Salida completa:
`evaluacion/baseline/outputs/fase1_rec_por_tema_censo.json`.

## Activación

Franco delegó el criterio en el propio prompt: activar si el censo completo
mejora y queda documentado. El censo mejora, sin excepción, en todos los
cortes medidos — se activa.

**`RECORD_POR_TEMA=1` por defecto** en `nowcast_puertas.py`.
`RECORD_POR_TEMA=0` en el entorno vuelve al récord general de siempre.
Verificado contra un caso real: `HCDN272347` (Ley Bases) @2024-01-15,
Diputados, pasa de $P(\text{aprobación})=0{,}8380$ a $0{,}8756$ con la bandera
prendida — la dirección es la esperada (el legislador promedio de este
proyecto tiene más historial afín en sus áreas —POLINST/DESREG/ECON— que en
su promedio general).

## Verificación

- `modelo/ensemble/tests/test_record_por_tema.py` (8 checks, sintéticos): el
  récord por área se mueve en la dirección correcta con datos claramente
  direccionales; $n$/presencia/n\_emit no cambian (un solo grado de libertad);
  la combinación multi-área cae ENTRE los extremos (logit, no promedio simple
  degenerado); área sin datos de esa persona cae al récord general; sin
  `areas_objetivo` o sin `cond_por_acta` degrada limpio a `ind_general`.
- `modelo/ensemble/tests/test_nowcast_puertas.py` (49/49) y
  `test_tema_auto.py` (9/9) sin regresión tras el refactor de
  `alineacion_individual` (extracción de `_alineacion_base`).
- Reproducible: `python evaluacion/baseline/src/medir_rec_por_tema.py` (las
  tres preguntas) y `python evaluacion/baseline/src/fase1_rec_por_tema.py`
  (la validación pareada).

## Lo que queda pendiente

1. **La caída de mejora en $n\geq 32$** (curva de skill, pregunta 1) no se
   investigó a fondo — podría ser composición de la submuestra (legisladores
   con mucha historia en un área concentrada, ej. presidentes de comisión) o
   ruido genuino (39% de cobertura ahí). No cambia la decisión de activar
   (el rango útil, $n$ chico a mediano, es donde vive la mayoría del dato),
   pero queda anotado para quien lo retome.
2. **Cobertura de tema sigue en 51-57%**, no 100% — sin correr el clasificador
   (decisión explícita de no gastar créditos sin permiso). El término no
   ayuda en el ~45% restante (cae a récord general, sin daño, pero sin
   ganancia tampoco).
3. Con `proyecto_taxonomias` ahora poblada para el universo VOTADO (1.182
   proyectos, ver bitácora 16-09), el `RECORD_POR_TEMA` en producción ya
   puede resolver la multietiqueta de un proyecto REAL vía
   `_resolver_multietiqueta` sin depender de `TEMA_AUTO` — pero el universo
   de proyectos NO votados (los que este motor más necesita, porque son los
   que todavía no se sabe si se aprueban) sigue sin clasificar.
