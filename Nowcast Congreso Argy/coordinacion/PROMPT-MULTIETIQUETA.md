# Prompt para Claude Code — multietiqueta y disgregación por capítulo

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino** (probabilidad de que un proyecto se
convierta en ley en el Congreso argentino). Franco es el dueño del producto y la
metodología.

## El pedido

Los proyectos ómnibus —**Ley Bases** es el caso testigo— no se pueden describir con una sola
etiqueta temática: tocan trabajo, energía, administración pública, impuestos y privatización
a la vez. Hoy el modelo los trata como si fueran de un tema solo.

Y hay un segundo problema, más profundo, que es la **PARTE B** de este trabajo: **una ley no
sale como entró**. Se modifica en comisión y en el recinto, y hoy el modelo no lo ve. Ley
Bases "se aprobó" habiendo perdido dos tercios de su articulado, y el nowcast la cuenta
igual que una ley que pasó intacta.

Son el mismo problema a dos granularidades, y por eso van juntos: **si disgregás por
capítulo, la multietiqueta del proyecto sale sola** — cada capítulo tiene su tema y el
proyecto es la unión.

## Lo que YA está hecho (no lo rehagas)

Verificalo antes de tocar nada, pero el diagnóstico es este:

1. **El agente clasificador ya es multietiqueta.** `variables/proyecto/src/agente_taxonomias.py`,
   `SYSTEM_PROMPT`, regla 1: *"Multi-etiqueta: asigná TODOS los subtemas que apliquen (lo
   normal es más de uno)"*. Devuelve `res.asignaciones` = lista de `(taxonomia_id, confianza)`.
2. **El almacenamiento ya es multietiqueta.** `proyecto_taxonomias` en
   `datos/proyectos/data/proyectos.db` tiene PK compuesta `(denominador, taxonomia_id)`.
3. **El contrato ya la transporta.** `variables/proyecto/data/tema_por_acta.parquet` tiene
   columna `todas_ids`.

**El colapso a una etiqueta ocurre en exactamente dos lugares, los dos aguas abajo:**

- `variables/proyecto/src/tema_por_acta.py` → `_elegir_primaria()`: elige la de mayor
  confianza no-auxiliar y la escribe en `tema_id` / `tema_area`. El resto queda en
  `todas_ids`, **que hoy no lee nadie**.
- `variables/bloque/src/bloque.py` → `proyectar_postura()` → `_match()`: compara
  `str(info.get("tema_area","")).upper() != tgt_t`, **igualdad exacta contra un área**.

**Entonces la tarea no es "generar multietiqueta": es dejar de aplastarla y decidir cómo
condiciona el modelo cuando un proyecto tiene varios temas.**

## PASO 0 — Medí la superficie antes de construir (no lo saltees)

Hay una razón concreta para empezar midiendo: **el tema entra al motor sólo por la rama de
bloque, y esa rama dispara en el 2,0% de las predicciones** (14.581 de 730.574 votos en el
censo del 03-09; el otro 98% sale del récord individual). Si no se toca nada más,
multietiqueta **podría no mover el número publicado**.

Medí y reportá, antes de escribir código de producción:

1. **¿Cuánta multietiqueta hay realmente?** Distribución de etiquetas sustantivas (no `AUX.*`)
   por proyecto y por acta votada. Qué porcentaje de actas votadas tiene ≥2.
2. **¿Cómo están etiquetadas hoy las leyes ómnibus?** Buscá Ley Bases y los otros ómnibus que
   encuentres, y mostrá qué etiquetas tienen y cuál ganó como primaria. **Es el caso que
   motiva todo esto: si el agente ya les puso 5 etiquetas, el problema es 100% aguas abajo.**
3. **¿Dónde se consume `tema_area`?** Usá `python .mapa/buscar.py --archivo variables/proyecto/data/tema_por_acta.parquet`
   y grepeá `tema_area` / `tema_id` / `todas_ids`. Listá cada consumidor y **cuántas
   predicciones toca cada uno**.
4. **¿Cuántas actas condicionadas quedan por tema?** Hoy el condicionamiento cae a
   incondicional cuando no hay actas suficientes en la ventana (mirá el log
   `condicionamiento tema=... 0 actas en ventana`). Con multietiqueta por unión debería
   haber más. Cuantificá el antes y el después.

**Si el paso 0 dice que el impacto es marginal, decilo y proponé dónde sí pagaría** (el
candidato obvio es el récord por tema, URGENTE 8). No construyas algo grande sobre una
superficie de 2%.

> **Orden entre las dos partes.** Hacé el PASO 0 de la Parte A y el **B0 de la Parte B**
> antes de construir nada de ninguna de las dos: son mediciones baratas y entre las dos
> definen dónde está el valor. Puede perfectamente pasar que la Parte B sea la que paga y la
> A sea plomería — o al revés. **Que lo decidan los números, no el orden en que están
> escritas acá.**

## PASO 1 — La decisión de diseño: cómo se condiciona con N temas

Ésta es la parte que necesita criterio, no plomería. Un bloque puede estar a favor del
capítulo laboral de un ómnibus y en contra del energético.

**Implementá al menos dos de estas y comparálas empíricamente:**

| regla | qué hace | a favor | en contra |
|---|---|---|---|
| **Unión (OR)** | la ventana condicionada son las actas que comparten **algún** tema | más muestra, simple | promedia temas opuestos |
| **Ponderada por confianza** | share condicional de cada tema, combinado por confianza | usa la señal del agente | la confianza del LLM no está calibrada |
| **Peor capítulo** | toma el tema donde el bloque está **más en contra** | un ómnibus se cae por su capítulo más resistido | puede ser demasiado pesimista |
| **Jerárquica** | encoge cada tema contra el incondicional (Empirical-Bayes, `k=5`) y después combina | consistente con lo que ya hace `proyectar_postura` | más partes móviles |

**La regla ponderada es la que mejor encaja con la doctrina** (ver abajo): el legislador lee
un proyecto que trata varios temas y pesa cada uno. Pero **eso es una hipótesis, no un
teorema: medila.**

Dejá el `_elegir_primaria` actual funcionando como **fallback** y la regla nueva detrás de un
parámetro, para poder comparar sin romper.

## PASO 2 — Validación empírica

El proyecto tiene baseline. **Cualquier cambio se mide contra él, con el mismo conjunto de
actas antes y después:**

```
python evaluacion\baseline\src\baseline_voto_individual.py
```

**El número a batir (censo del 03-09, 6.091 actas, 730.574 votos):**

| métrica | valor |
|---|---:|
| Brier | **0,13819** |
| skill vs climatología | 0,1304 |
| accuracy | 0,8051 |
| MAE del margen por acta | 0,1408 |

Mirá también los cortes `por_era`, `por_camara` y `por_fuente_direccion` que el script ya
produce. **Y reportá el efecto sobre el subconjunto que realmente toca** (las predicciones
de la rama de bloque), no sólo el agregado: un cambio que mejora el 2% de los casos se
diluye a cero en el promedio y eso no significa que no sirva.

---

# PARTE B — Disgregar la ley por capítulo

## Lo que ya existe y hoy se TIRA (verificalo primero)

**El insumo está en la casa y lo estamos descartando.** Cuando un proyecto tiene varias
actas —la votación **en general** y después las **en particular**, artículo por artículo—,
la función `elegir_votacion` **elige una y descarta el resto**. Deja rastro en
`tipo_votacion_dip` / `tipo_votacion_sen` (`unica | general | primera | primera_particular`)
y en `n_actas_dip` / `n_actas_sen`. El control documentado es Ley Bases: toma el acta del
**02-02-2024** (la general) y no la del último artículo.

**O sea: las votaciones en particular están en la canónica, votante por votante, y hoy se
tratan como ruido a deduplicar.** Es exactamente el insumo para medir qué sobrevive y qué se
cae, **sin parsear una sola palabra de articulado**.

Segundo hallazgo anotado y sin enchufar: **el Senado publica `descripcion = "SE VOTA EN
PARTICULAR"`** en argentinadatos, un campo explícito para algo que hoy se infiere leyendo
títulos. También `quorumTipo`, `miembros` y `amn`. No está en la canónica porque sumar
columnas al schema **pide un ADR** (regla de `CLAUDE.md`). Buscá esto en
`ESTADO-DEL-PROYECTO.md` antes de arrancar.

## Las decisiones ya tomadas por Franco (no las re-discutas)

| decisión | qué eligió |
|---|---|
| **Output** | **vector de probabilidades por capítulo**; la P del proyecto se deriva |
| **Unidad** | **híbrido**: artículo ahora (ya observable), capítulo después (requiere texto) |
| **Número publicado** | **dos números separados y etiquetados**: P(se sanciona algo) y P(sobrevive sustancialmente) |
| **Alcance** | **los proyectos que tuvieron votación en particular** — el criterio sale del dato, no de una lista curada |

## 🔴 Cómo se compone la P del proyecto — leé esto antes de escribir una línea

**La P del proyecto NO es el promedio de las P de los capítulos, y tampoco es el producto.**

Un promedio de probabilidades no es la probabilidad de ningún evento. Y "la P del proyecto"
no es un evento: **son tres eventos distintos.**

| pregunta | qué es |
|---|---|
| ¿se aprueba **todo** tal como entró? | probabilidad conjunta |
| ¿se aprueba **algo**? | 1 − P(no pasa ningún capítulo) |
| ¿**cuánto** sobrevive? | valor esperado de la fracción, **ponderado por artículos** |

**Y multiplicar sería peor.** Los capítulos de un ómnibus **se caen juntos**: si se cae el
capítulo laboral es porque el bloque que lo sostenía se dio vuelta, y ese mismo giro arrastra
al energético. El producto supone independencia y **subestimaría gravemente**.

> Ya sabemos lo que cuesta ese supuesto en este proyecto: el Nivel 0 de la fórmula tiene
> marcado como **"supuesto activo y falso"** la independencia entre cámaras, y sobre votos
> individuales medimos una **sobredispersión de 39×** contra lo que predice la
> independencia. **No agregues un tercer supuesto de independencia.**

### La forma correcta: no componer, SIMULAR

El motor ya sabe hacer esto. **Los cuatro números salen de la misma corrida, contados
distinto.** En cada simulación $j$ se simula el voto de cada legislador para cada capítulo,
**con el shock común $\eta_j$ COMPARTIDO entre capítulos** —esa es la pieza que captura que
se caen juntos—, se cuenta y se aplica el umbral:

$$P_k = \frac{1}{N}\sum_j \mathbb{1}[k \text{ pasa en } j] \qquad\qquad P_{\text{todo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasan todos en } j]$$

$$P_{\text{algo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasa alguno en } j] \qquad \mathbb{E}[\text{superv.}] = \frac{1}{N}\sum_j \frac{\sum_k a_k\,\mathbb{1}[k \text{ pasa en } j]}{\sum_k a_k}$$

con $a_k$ = cantidad de artículos del capítulo $k$. **Cero supuestos nuevos:** la correlación
entre capítulos sale del $\eta_j$ que ya está formulado en §III.A.3, y los umbrales son los
de §I.2b. Los dos números que Franco quiere publicar —P(algo) y supervivencia— son dos de
esos contadores.

**Ojo con $\eta_j$:** hoy está formulado pero **no implementado** (§III.A.3, $\tau \approx 1{,}197$
estimado el 03-09, sin prender). Si no está disponible cuando llegues acá, **dejá la
composición escrita y marcá la dependencia** en vez de simular capítulos independientes —
que sería justamente el error.

## Los pasos de la Parte B

**B0 — Medir el histórico primero.** Antes de modelar nada:

1. ¿Cuántos proyectos tuvieron votación en particular? Por cámara y por era.
2. De ésos, **¿cuántos artículos se cayeron?** Compará el resultado de la general contra el
   de cada particular. **Este número es el producto**: es la primera medición de cuánto se
   modifican las leyes en el recinto, y nadie la tiene.
3. **Ley Bases como caso testigo**: reconstruí su secuencia completa de votaciones y mostrá
   qué pasó artículo por artículo. Si el método no reproduce lo que pasó con Ley Bases, está
   mal.
4. ¿Qué tan seguido un artículo se cae mientras la ley pasa? Es la brecha entre los dos
   números que Franco quiere publicar.

**B1 — El contrato.** Una tabla nueva tipo `votacion_por_articulo` (proyecto_id, acta_id,
artículo o rango, resultado, es_general). Sale de dejar de descartar en `elegir_votacion`.
**No borres el comportamiento actual**: `elegir_votacion` alimenta el motor de hoy y su
elección de la general es correcta para lo que hace. Agregá, no reemplaces.

**B2 — El agrupamiento en capítulos** queda para después y **depende de conseguir el texto**
del articulado, que hoy no tenemos (sólo títulos). **Medí y reportá qué haría falta**; no
arranques una adquisición de datos grande sin decírselo a Franco.

**B3 — Los dos números publicados** sólo se prenden con aprobación de Franco. Dejá la
implementación detrás de bandera con su medición.

## Advertencia sobre el backtest en la Parte B

Redefinir qué cuenta como "aprobado" **cambia la variable dependiente**, y eso invalida la
comparación con el baseline actual (Brier 0,13819). **Si tocás la definición del target,
decilo explícitamente y reportá los dos mundos por separado** — no presentes un Brier nuevo
como si fuera comparable con el viejo. Es el mismo cuidado que ya se tuvo cuando se descubrió
que medir contra `sancionado` no servía (ADR-0012).

---

## Reglas de la casa (no negociables)

**Leé primero, en este orden:** `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`
para ubicar código sin releer el repo) → `CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` →
`coordinacion/DECISIONES/0016-doctrina-de-la-parte-al-todo.md`.

**La doctrina (ADR-0016):** la probabilidad se construye **de la parte al todo**. Todo factor
—incluido el tema— es **información que un legislador lee y procesa**; la probabilidad de la
cámara es la consecuencia de sumar decisiones individuales, nunca un lugar donde se aplican
correcciones. **La combinación de temas va en $P_i$, no en el agregado.**

**ADR-0015:** todo cambio al motor se presenta en tres niveles — la función, el motor en
conjunto (quién consume lo que cambió), y **cómo queda la fórmula**. Actualizá
`FORMULA-COMPLETA.md` en el mismo commit. Si el cambio no se puede ubicar en la fórmula, es
señal de que no se entiende del todo qué se está cambiando.

**No cambies el número publicado sin aprobación de Franco.** Podés implementar detrás de una
bandera apagada por defecto, con su medición. `modelo/ensemble`,
`modelo/agregador_institucional`, `modelo/voto_individual`, `variables/bloque`,
`variables/proyecto` son motor.

**Las trampas de estos datos, que ya costaron caro:**

| trampa | síntoma que la delató |
|---|---|
| nombres de comisión con comas → matchear contra el **catálogo**, nunca partir por separadores | una comisión faltaba **100%** de las veces |
| **dos tablas de enlace acta↔expediente**: usar la ANCHA (`acta_expediente_todas.parquet`, 5.036 actas), no la angosta (892, sólo ckan_diputados) | la cobertura de tema daba 24,6% y parecía un techo — era la tabla equivocada |
| `expedientes_giros` mezcla las dos cámaras | cobertura 2,1% en vez de 63,6% |
| nombres de personas en formatos distintos → clave `APELLIDO\|PRIMER-NOMBRE` | un coeficiente daba **p=0,88** |
| defaults silenciosos (`clase="unico"` cuando no matchea) | **0%** de dictámenes de mayoría en el Senado |

> **La regla madre: un porcentaje imposible es un bug, no un fenómeno.** Cuando un número
> esperado da nulo, cero o absurdo, **sospechá del cruce antes que de la hipótesis**. Las
> cuatro veces que pasó, era el cruce.

**Medí antes de creer, y elegí bien la unidad.** Dos mediciones correctas del mismo fenómeno
pueden dar resultados opuestos según qué mantengan fijo. Un $p$ chico sobre unidades mal
elegidas es efecto de composición con cara de hallazgo.

**Si el resultado contradice la hipótesis, decilo.** Este proyecto viene descartando ideas
propias con datos y así es como mejora. Un resultado negativo bien medido vale más que uno
positivo forzado.

## Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — entrada de bitácora arriba de todo: qué se
   hizo, **qué se midió**, qué se decidió. Escribí para alguien que no estuvo.
2. **`coordinacion/FORMULA-COMPLETA.md`** — si afecta la fórmula, actualizala; si no, decilo
   con una línea.
3. **ADRs** en `coordinacion/DECISIONES/` (fijate cuál es el próximo número libre):
   - la **regla de combinación de temas** elegida y por qué, incluyendo las descartadas y con
     qué número;
   - la **disgregación por artículo** y la composición por simulación — es cambio de
     contrato y de semántica del número publicado, así que amerita el suyo;
   - si sumás columnas a la canónica desde argentinadatos (`descripcion`, `quorumTipo`),
     **eso pide ADR propio** por la regla de `CLAUDE.md` sobre `docs/schemas`.
4. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
5. **`coordinacion/URGENTE.md`** — si aparece algo que bloquea a otros.
6. Reindexá: `python .mapa/indexar.py .`
7. **Tests.** Hay suite en `variables/proyecto/tests/` (`test_tema_por_acta.py`,
   `test_agente.py`) y en `variables/bloque/tests/`. Que el cambio no las rompa, y agregá dos
   casos nuevos:
   - **ómnibus multietiqueta:** un proyecto con 5 etiquetas tiene que sobrevivir entero hasta
     el consumidor, sin colapsarse en el camino;
   - **composición por simulación:** con capítulos perfectamente correlacionados,
     $P_{\text{todo}}$ tiene que dar ≈ $\min_k P_k$ y **no** el producto. Es el test que
     atrapa el error de independencia si alguien lo reintroduce.

**No hagas `git push`.** Commits locales, en español, uno por tarea.

## Cerrá con

- Qué quedó implementado y **detrás de qué bandera**
- El baseline antes y después, **en el agregado y en el subconjunto afectado**
- **Qué esperabas y salió distinto**
- Qué necesita decisión de Franco, con la pregunta concreta de cada cosa

Empezá por el PASO 0.
