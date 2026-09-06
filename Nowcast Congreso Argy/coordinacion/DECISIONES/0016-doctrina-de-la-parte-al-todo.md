# ADR-0016 — Doctrina: la probabilidad se construye DE LA PARTE AL TODO

**Fecha:** 2026-08-26 · **Estado:** Aceptada · **Quién:** Franco (doctrina), Claude (auditoría y registro)

## La regla

> **Todo factor que afecte la probabilidad de aprobación entra en la decisión del
> LEGISLADOR, no en el agregado de la cámara.** El clima político, el dictamen, la
> proximidad electoral, lo que hizo la otra cámara: todo eso es información que una
> persona lee y procesa según su historial, su lealtad y el tema. La probabilidad de
> la cámara es la CONSECUENCIA de sumar esas decisiones, nunca un lugar donde se
> aplican correcciones.

Franco (26-08):

> *"La probabilidad de aprobación de un proyecto, a nivel general, debe estar siempre
> desde la óptica del legislador. A nivel secuencial. Siempre debe ser secuencial
> desde el legislador hacia el general, de la parte al todo, no al revés."*

## Por qué

**1. Es el cimiento del proyecto, no una preferencia estética.** La Fase 0 midió que
la regla de bloque predice la dirección del voto individual con ~0,99 de acierto. La
conclusión que ordenó todo el sistema fue que **el valor no está en el promedio sino
en las partes**: quién asiste, quién se desvía, quiénes son las 10-20 bisagras.
Aplicar correcciones al agregado contradice el hallazgo que justifica el producto.

**2. Un corrimiento agregado no dice a quién ir a buscar.** El ADR-0007 fija que cada
informe entrega dos respuestas: la probabilidad **y** los nombres. Un $\delta$ sobre
$P_c$ mueve el número sin decir sobre quién actuó; el mismo efecto aplicado a $P_i$
produce las dos cosas a la vez, del mismo cálculo.

**3. Evita el doble conteo, que es el error concreto que ya cometimos.** El
condicionante del dictamen asignaba al bloque entero cuando firmaba su jefe
($a_\ell = 1$), y dos pasos después el modelo aplicaba $d_i$, que dice que la
disciplina no es perfecta. Dos supuestos opuestos sobre lo mismo. Se detectó
justamente porque el término estaba en el nivel equivocado.

**4. Hace las interacciones explícitas.** A nivel legislador, "el clima mueve más a
los díscolos" o "la firma del jefe arrastra a los leales" son términos del modelo. A
nivel agregado son promedios que esconden a quién le pasó qué.

**5. El agregado emerge y encima queda mejor.** Si el jefe de un bloque de 90 firma,
son 90 legisladores los que reciben el empujón y la suma sale de la simulación
($\approx b_\ell \beta (1-\bar{d}_\ell)$) — **modulada por la disciplina del bloque**,
que un término $b_\ell/M_c$ escrito a mano no captura.

## Cómo se aplica

Todo término nuevo se ubica en la cadena así:

```
información  →  P_i (decisión del legislador)  →  simulación  →  P_c  →  P_aprob
```

**Si un término se aplica a la derecha de la simulación, está mal ubicado** — salvo
las dos excepciones de abajo.

Al proponer un término, la pregunta es: *¿esto lo lee una persona y decide, o es una
regla del cuerpo?* Si lo primero, va en $P_i$.

## Las dos excepciones legítimas

1. **Reglas institucionales del cuerpo.** Umbrales de mayoría, quórum, cantidad de
   bancas, el gate de admisibilidad del dictamen ($\mathcal{C}_c$). No son decisiones
   de nadie: son el reglamento. Viven en la simulación o antes de ella.
2. **Shocks correlacionados que afectan a todos a la vez.** Que se caiga la sesión,
   que el oficialismo cambie la línea a último momento. **Pero se implementan como un
   shock COMÚN dentro de la simulación** ($\eta_j$ compartido por todos los $P_i$ de
   la corrida $j$), no como un recorte sobre el resultado.

## Consecuencias

- **`FORMULA-COMPLETA.md` marca el nivel de cada término.** Un término agregado que no
  entre en las dos excepciones queda señalado como deuda.
- **Auditoría del 26-08 (cerrada):** de doce términos, cinco cumplían, dos son
  excepciones legítimas y **cuatro se corrigieron el mismo día**. Detalle en la sección
  "Auditoría de la doctrina" de `FORMULA-COMPLETA.md`.
- **Bajar un término al legislador no es sólo prolijidad: cambia lo que el modelo puede
  decir, y a veces lo desmiente.** Los tres casos del 26-08:
  1. el arrastre entre cámaras **reveló** que $\psi$ depende del bloque (oficialismo y
     oposición leen la misma media sanción al revés) — invisible en la versión agregada;
  2. el $\varepsilon$ bajado a $P_i$ **mostró que no alcanzaba**: medido, un piso
     individual de 0,05 deja la cámara en 99,8%, porque el problema era la independencia
     y no los extremos. Hacen falta las dos piezas;
  3. el sobre tablas, al escribirse por legislador, **obligó a preguntar qué lee esa
     persona** — y la medición contestó que lee a su bloque (95,4% de acierto) y que su
     récord propio ahí es peor que tirar una moneda (Brier 0,435 vs 0,250).
- **Aplica también a lo que todavía no existe.** Dos de las tres violaciones son
  propuestas sin implementar (el arrastre entre cámaras y el sobre tablas): se
  corrigen antes de escribir código, que es cuando sale gratis.

## Enmienda 2026-09-03 — $\beta_3$ ($W_{-\ell}$) sale; entra el carácter del dictamen

**Decidido por Franco.** La formulación del dictamen por legislador queda con **dos**
términos, no tres:

$$\text{logit}(P_i^{\text{dict}}) = \text{logit}(P_i) + \beta_1 F_i + \beta_2 (1-d_i) J_{\ell(i)} + \delta(\text{carácter})$$

**Por qué sale $W_{-\ell}$ — y no es por el p-valor.** Al agregar el carácter del dictamen,
$W_{-\ell}$ **cambia de signo**: +0,262 → −1,458. Un coeficiente que se da vuelta al
agregar un control no mide un efecto, mide **lo mismo que el control**. Tiene sentido:
"firmaron muchos bloques" y "el dictamen salió único en vez de disputado" son dos maneras
de decir cuánto consenso hubo, y están tan correlacionadas que la regresión no las separa.

**El carácter lo mide mejor:** es discreto, viene directo de la fuente, y da −2,285 con
$p<0{,}0001$ aguantando controles de tema y origen.

**Lo que NO cambia:** $\beta_1$ (firmó él) y $\beta_2$ (firmó su jefe × su lealtad) se
quedan. $\beta_2$ es el término que Franco agregó el 26-08 y **estuvo a punto de caerse por
un bug de matcheo de nombres**, no por el dato. Sigue atenuado por los 30 jefes sin
resolver (URGENTE 10): su valor verdadero es mayor que +0,645.

