# ADR-0008 — El ICG como modulador de coyuntura, no como rasgo predictivo

**Fecha:** 2026-08-04 · **Estado:** ACEPTADA · **Quién:** Valle (diseño y decisiones), Claude (estimación e implementación)

## Contexto

El ICG (Índice de Confianza en el Gobierno, UTDT) estaba enchufado al embudo como
una columna más de la regresión logística. Medido con ablación walk-forward, su
aporte era **cero** (−0,0003 en sanción, 0,0000 en llegar al recinto) y pesaba el
**0,3%** de la ponderación, contra 68% de las comisiones.

Diagnóstico de Valle: *el ICG no es un atributo del proyecto de ley, es el estado
del sistema en el que ese proyecto se juega*. Como atributo no podía funcionar.

## Decisión

El ICG deja de ser un rasgo y pasa a ser un **modulador**, con dos mecanismos
independientes que se aplican en momentos distintos de la cadena.

### Matemática común

    odds' = odds × k        k = exp(γ · s · z)
    logit(p') = logit(p) + γ · s · z

Se multiplican las **chances**, no la probabilidad: `P × k` puede superar 1, las
odds no. `s` = +1 si el proyecto lo impulsa el gobierno, −1 la oposición, 0
consenso. La inversión por origen sale del signo del exponente.

### Mecanismo 1 — VARIACIÓN (medido, individual)

`z = log(ICG del mes / promedio del propio gobierno)`, aplicado **legislador por
legislador antes de agregar**. γ depende de cuán díscolo sea cada uno:

| desvío en disputadas | γ | IC 95% | signif. |
|---|---:|---|---|
| ≥ 0,40 | 0,555 | [0,39; 0,78] | sí |
| ≥ 0,30 | 0,354 | [0,17; 0,51] | sí |
| ≥ 0,20 | 0,333 | [0,13; 0,46] | sí |
| ≥ 0,10 | 0,220 | [0,06; 0,34] | sí |
| < 0,10 | 0,094 | [−0,03; 0,24] | **no** |

Estimado sobre **409.841 votos individuales, 1.618 legisladores, 167 meses**, con
efectos fijos por legislador (cada uno se compara consigo mismo) y bootstrap de
bloque por mes. **Patrón dosis-respuesta:** γ crece monótonamente con el desvío y
se mantiene significativo mientras la muestra cae de 410k votos a 22k.

**Validación cualitativa:** sin que se le diera ninguna información política, el
modelo ordenó la cámara poniendo a los bloques provinciales y federales —los
negociadores de siempre— como los más sensibles, y a LLA, el kirchnerismo y el
PRO como núcleo duro. En la cámara de hoy: 51 legisladores con γ > 0 y 206 en cero.

### Mecanismo 2 — NIVEL (declarado, agregado)

`z = d^1,5` si `d ≥ 0`, `z = −2,0 · |d|^1,5` si `d < 0`, con `d = ICG − 1,90`.

Break-even fijo en **1,90**. Acelera hacia arriba (cada +0,5 suma 11, 24, 38 y 60
puntos de multiplicador) y **castiga entre 1,4x y 1,8x más de lo que premia**.
Razonamiento de Valle: *"las personas no son sensibles a éxitos a menos que sean
notables; mientras que son muy sensibles a la pérdida"* — es, sin haberla buscado,
la función de valor de la teoría prospectiva.

**γ lo asigna un analista humano.** No se estima ni tiene default silencioso.

## Por qué el mecanismo 2 no se estima

Con seis presidencias en 25 años, el nivel promedio de un gobierno es constante
dentro de ese gobierno: "ICG alto" y "esta presidencia" son la misma columna. Con
efectos fijos por gobierno el nivel es inestimable por construcción; sin ellos, el
estimador confunde clima con identidad del gobierno.

> **Nota sobre una mala interpretación (corregida por Valle):** las bancas del
> oficialismo correlacionan −0,54 con el ICG, pero eso **no** significa que los
> gobiernos con buen clima lleguen sin bancas. Es el **calendario de recambio**
> argentino —Diputados renueva por mitades, el Senado por tercios—: un presidente
> asume habiendo ganado la elección pero hereda un Congreso de ciclos anteriores,
> y ese arranque coincide con la luna de miel del ICG. Van juntas por el
> calendario, no por causalidad.

## Preparación de la serie

- **Traspasos presidenciales imputados PLANO** con el promedio de los últimos 12
  meses del saliente. El ICG de nov-2015 no califica a CFK: califica a Macri, que
  no asumió — aplicárselo a un proyecto kirchnerista invierte el signo. Los 8
  meses más volátiles de la serie son 8 de 8 pegados a un traspaso. Plano y no
  tendencia porque en esas ventanas hay **más** votaciones peleadas (7,8% vs 4,3%).
- **Sólo el traspaso presidencial contamina.** Medido: transición 0,325 · midterm
  0,171 · normal 0,156 · campaña PASO 0,146. Las legislativas no mueven el ICG.
- **Fuera de escala:** los meses con ICG bajo el piso de 1,0 (crisis 2002-03) se
  excluyen del ajuste.
- **Neutro point-in-time:** el promedio de cada gobierno se calcula expandiendo,
  sólo con los meses transcurridos. Usar el promedio completo sería leakage.

## Alternativa considerada y descartada

**Neutro por curva del ciclo presidencial** (`curva_ciclo_presidencial.csv`): el
neutro cambia según el mes de mandato (2,55 recién asumido, 1,82 en el valle del
mes 30). Premia estar mejor de lo esperable a esa altura. Se construyó, quedó
implementada (`modo="ciclo"`) y **se descartó como default**: Valle eligió el
break-even fijo. Las dos dan casi lo mismo en un mandato maduro y se separan
sólo al arranque, donde la diferencia es una lectura política —si la luna de miel
da poder real sobre el Congreso o los legisladores ya descuentan que todo gobierno
arranca alto—. Se conserva por si el equipo quiere volver sobre ella.

## Consecuencias

1. **Ningún nowcast se publica sin evaluación de coyuntura registrada.** Requisito
   operativo nuevo. Se asigna en `PANEL-COYUNTURA.html` / `PANEL-MOVIL.html` y se
   deja constancia con fecha, ICG, γ y justificación.
2. Los γ de intensidad (0 / 0,05 / 0,10 / 0,20 / 0,30) **no son comparables** con
   los de la versión anterior: al cambiar la forma a acelerada, la escala cambió.
3. El mecanismo 1 corre solo y no depende del analista.
4. Queda pendiente: los **104 legisladores sin historial** (camada dic-2025) se
   tratan como núcleo duro por defecto, que es un supuesto y no una medición.

## Lo que se midió y NO funcionó

- **La volatilidad no modula la elasticidad.** γ₀·λ = +0,045 con IC [−0,12; +0,09].
  La hipótesis (con el ICG planchado no hay tracción; agitado, la sociedad está
  permeable) sigue siendo plausible pero los datos no la respaldan.
- **No hay efecto a nivel cámara.** γ estimado sobre el share de afirmativos por
  acta: −0,19 [−0,56; +0,26], y se achica hacia cero al restringir a las peleadas.
  Con ~69 votos emitidos por acta, un efecto de 10-20 bisagras mueve 4% del share
  contra un ruido de 18%: el promedio de cámara no tiene resolución para verlo.

## Archivos

`variables/proyecto/src/{icg_contexto,estimar_gamma,estimar_gamma_individual,modulador_icg,comparar_vias_icg}.py`
· `data/{calendario_electoral,curva_ciclo_presidencial}.csv` · `data/icg_contexto.parquet`
· `outputs/gamma_icg*.json` · `tests/test_icg_contexto.py` · `COMPARADOR-ICG.html`
· `PANEL-COYUNTURA.html` · `PANEL-MOVIL.html`
