# Prompt para Claude Code — multitema v2: cerrar lo metodológico y mover el tema donde paga

> Pegá todo lo que está debajo de la línea en Claude Code, con el repo abierto.

---

Trabajás en el **Nowcast Legislativo Argentino** (probabilidad de que un proyecto se
convierta en ley en el Congreso argentino). Franco es dueño del producto y de la metodología.

## De qué viene esto

En el PASO 2 (ADR-0024) se probaron cuatro reglas para resolver la postura de bloque frente a
un proyecto multitema: `primaria`, `union`, `ponderada`, `peor_tema`. **Las tres nuevas
empeoraron** el Brier en la rama de bloque. El código quedó con las cuatro reglas, testeado y
con banderas apagadas.

**Ese experimento no puede responder la pregunta que se le hizo.** No porque esté mal hecho,
sino porque está mal diseñado — y el diseño salió de un prompt anterior, así que el error de
origen no es tuyo. Cuatro problemas, en orden de gravedad:

### 1. 🔴 Falta el brazo de control

Las cuatro reglas usan tema. **No hay un brazo `sin_tema`** (share incondicional del bloque).
Sin eso no se puede distinguir *"cuál combinación es mejor"* de **"condicionar por tema acá
hace daño"** — y la evidencia previa apunta fuerte a lo segundo. `primaria` no es una base
neutral: es otro de los brazos.

### 2. Promediar en espacio de probabilidad viola la regla IV.2 del propio proyecto

`ponderada` promedia shares $s_k$. La sección de metodología de `FORMULA-COMPLETA.md` dice:
**condicionar en logit, nunca multiplicando ni promediando probabilidades**. Promediar en
probabilidad comprime hacia el centro y aplasta los temas extremos, que son los informativos.
Es un error de especificación, no un resultado sobre la hipótesis.

### 3. `peor_tema` se midió con un estimador sesgado

$\min_k \hat{s}_k$ sobre estimaciones ruidosas es un estimador **sesgado hacia abajo** del
mínimo verdadero, y el sesgo crece con la cantidad de temas y con el ruido. Con pocas actas
por tema, el ruido es grande. **Estaba garantizado a salir demasiado pesimista aunque la
hipótesis política sea cierta.** No se testeó "un ómnibus se cae por su capítulo más
resistido": se testeó un artefacto.

### 4. La muestra está adversarialmente seleccionada

Con `MIN_HIST_INDIVIDUAL = 1` (bajado el 06-09), la rama de bloque dispara cuando el
legislador tiene **cero votos previos**: es su primera votación. Esa gente aparece justo
después de un recambio, el momento donde ya sabemos que el motor anda peor. **Es el peor
subconjunto posible para testear cualquier refinamiento**, y con ~1.263 votos clusterizados
no hay poder para detectar diferencias chicas.

### Y el hecho que ordena todo

`FORMULA-COMPLETA.md` §II.5, sobre el censo: **la rama de bloque tiene skill NEGATIVO
(−0,0586, 19.923 votos)**. Textual: *"Mandar gente ahí no es un refugio conservador: es
empeorarla."* Por eso mismo se bajó el umbral de 8 a 1, y por eso la rama quedó en **0,36%**
de las predicciones.

**O sea: el experimento optimizó el insumo de un componente que ya se sabe que resta.**

### La lectura que reordena el trabajo

La rama de bloque **no es un modelo de cómo votan los bloques: es un relleno para datos
faltantes**. Dispara cuando no sabemos nada de la persona. Condicionar *eso* por tema es hacer
una pregunta muy fina sobre alguien de quien no hay ningún dato.

Y al mismo tiempo **el tema está ausente donde sí hay datos**: el 99,6% de las predicciones
sale de $\text{rec}_i$, que es **un solo número promediado sobre todos los temas**. Un
diputado veterano vota distinto en laboral que en ambiente y el modelo no lo puede ver.

**El tema está inyectado al revés: en el rincón sin datos, y ausente donde están todos los
datos.** Eso es lo que hay que corregir, y es la FASE 1.

---

# Lo que Franco ya decidió (no lo re-discutas)

| decisión | qué eligió |
|---|---|
| **Si el control gana** | **apagar el condicionamiento por tema en la rama de bloque**, medirlo y seguir. Es revertir a algo más simple y ya probado, no agregar nada |
| **Alcance** | **las tres fases**: metodológico + récord por tema + capítulos |
| **Autonomía** | **puede prender banderas** si el censo completo mejora y queda documentado en fórmula + ADR |
| **`peor_tema`** | **revancha sólo a nivel capítulo** (FASE 2), donde el objeto coincide con la hipótesis. A nivel proyecto queda cerrado |

---

# FASE 0 — El re-test que sí puede cerrar la discusión

Reusa todo lo de ADR-0024 (`proyectar_postura(combinar_temas=...)` y
`baseline_voto_individual.py --combinar-temas`). No hay que reescribir nada.

**Sobre el CENSO completo (6.091 actas), no sobre la muestra.** La limitación ya estaba
anotada en ADR-0024 y es una de las razones por las que el resultado no es concluyente.

### Los brazos

| brazo | qué es |
|---|---|
| **`sin_tema`** 🆕 | **el control**: share incondicional del bloque, sin condicionar por nada |
| `primaria` | lo de hoy |
| `union` | ya implementado |
| `ponderada_logit` 🆕 | **en logit**, no en probabilidad, y con **pesos reales** de confianza (`proyecto_taxonomias` ya está poblada: 1.182 proyectos con confianza por etiqueta) |

**No re-corras `peor_tema` a nivel proyecto**: queda cerrado por decisión de Franco.

### Cómo comparar

- **Sobre la rama de bloque**, que es lo que el cambio toca. El agregado global no sirve:
  con 0,36% de peso, cualquier efecto es invisible ahí.
- **Clusterizando por acta.** Los votos de una misma acta no son observaciones
  independientes; tratarlos como tales infla el poder aparente.
- **Reportá el intervalo, no sólo el punto.** Con esta muestra, lo más probable es que las
  diferencias no sean distinguibles de cero — **y eso también es un resultado**, que hay que
  decir en vez de rankear cuatro números que se pisan.
- Cortá también **por era**, porque la rama es casi toda post-recambio.

### El criterio de decisión

- **Si `sin_tema` ≥ `primaria`:** apagá el condicionamiento por tema en la rama de bloque,
  dejalo medido y documentado, y **la pregunta de cómo combinar temas a nivel bloque queda
  cerrada** — no hay nada que combinar.
- **Si `primaria` > `sin_tema` y además `ponderada_logit` > `primaria`:** hay señal real y la
  especificación anterior la estaba destruyendo. Prendela si el censo mejora.
- **Si nada se distingue de cero:** decilo. Es el resultado más probable y cierra la
  discusión igual.

---

# FASE 1 — Mover el tema a donde hay datos: `rec_i^tema` (URGENTE 8)

**Es la fase que convierte el hallazgo en valor.** Hoy $\text{rec}_i$ cubre el 99,6% de las
predicciones y no sabe nada de temas.

### Medí primero (esto decide el diseño)

1. **¿Cuántos pares (legislador, tema) tienen muestra suficiente?** Distribución de
   $n_i^{\text{tema}}$. Ojo: con el umbral global en 1, "suficiente" no es 8 — **medí la
   curva de skill contra el umbral**, como se hizo en §II.5 con `MIN_HIST_INDIVIDUAL`, en vez
   de fijar un número a mano.
2. **¿Cuánta cobertura de tema hay por acta?** Usá la tabla **ANCHA**
   (`acta_expediente_todas.parquet`, 5.036 actas), **no** la angosta (892, sólo
   ckan_diputados). Esa confusión ya costó dos veces.
3. **¿El récord por tema discrimina?** Antes de integrarlo: ¿la varianza entre temas de un
   mismo legislador es mayor que el ruido? Si un diputado vota igual en todos los temas, el
   récord temático no agrega nada y conviene saberlo antes de construirlo.

### El diseño

**Encoger, no cortar.** Empirical-Bayes contra el récord general del legislador —el mismo
esquema $k=5$ que ya usan el share y el desvío—, no un umbral duro:

$$\hat{r}_i^{\,k} = \frac{n_i^k\, r_i^k + k_{\text{shrink}}\, r_i}{n_i^k + k_{\text{shrink}}}$$

Con muestra chica manda el récord general; con muestra grande, el temático. **Degrada solo y
no necesita umbral.**

**Y acá sí aparece la multietiqueta con superficie real:** si el proyecto toca varios temas,
el récord del legislador se combina **en logit** y ponderado por la confianza de cada
etiqueta. Es la misma pregunta que falló a nivel bloque, pero ahora con datos suficientes
por unidad — que es justamente la diferencia que hace que pueda funcionar.

**Validación:** censo completo, cortes por era y por cámara, y **reportá el efecto sobre el
subconjunto que toca**, no sólo el agregado.

---

# FASE 2 — Capítulos (independiente, puede ir en paralelo)

B1/B2 ya existen (`votacion_por_articulo.py`, `extraer_titulo_capitulo`, ADR-0023).

**Por qué esta fase no hereda el problema de las otras dos:** no es una quinta forma de
mezclar temas. **Cambia la unidad.** Ley Bases no es una ley multitema: son varias leyes
monotema encuadernadas juntas. Si cada capítulo tiene su tema dominante, **el problema de
combinar temas se disuelve** en vez de resolverse.

### La composición de la P del proyecto — leé esto antes de escribir una línea

**La P del proyecto NO es el promedio de las P de los capítulos, y tampoco es el producto.**

"La P del proyecto" no es un evento: son tres eventos distintos, y sólo uno es un promedio.

Los capítulos **se caen juntos**: si se cae el capítulo laboral es porque el bloque que lo
sostenía se dio vuelta, y ese giro arrastra al energético. Multiplicar supone independencia
y subestimaría. Ya sabemos lo que cuesta ese supuesto acá: el Nivel 0 lo tiene marcado como
*"supuesto activo y falso"* entre cámaras, y sobre votos individuales se midió **39× de
sobredispersión** contra la independencia.

**La forma correcta: no componer, simular.** En cada corrida $j$ se simula el voto de cada
legislador para cada capítulo **con el shock común $\eta_j$ COMPARTIDO entre capítulos** —esa
es la pieza que captura que se caen juntos, y **ya está implementada y prendida (ADR-0025)**—,
se cuenta y se aplica el umbral:

$$P_k = \frac{1}{N}\sum_j \mathbb{1}[k \text{ pasa}] \qquad P_{\text{todo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasan todos}]$$

$$P_{\text{algo}} = \frac{1}{N}\sum_j \mathbb{1}[\text{pasa alguno}] \qquad \mathbb{E}[\text{superv.}] = \frac{1}{N}\sum_j \frac{\sum_k a_k \mathbb{1}[k \text{ pasa}]}{\sum_k a_k}$$

con $a_k$ = artículos del capítulo $k$. **Cero supuestos nuevos.**

### La revancha de `peor_tema`, acá sí

A nivel capítulo la hipótesis *"un ómnibus se cae por su capítulo más resistido"* es
**medible directamente**: $P_{\text{todo}}$ vs $\min_k P_k$ sale de la simulación, sin
estimar ningún mínimo de shares ruidosos. **Si $P_{\text{todo}} \approx \min_k P_k$, la
intuición de Franco era correcta** y lo que falló antes fue el estimador, no la idea.

### Pasos

- **B0 — medir el histórico.** Cuántos proyectos tuvieron votación en particular, cuántos
  artículos se cayeron, y **Ley Bases reconstruida artículo por artículo**. Si el método no
  reproduce lo que pasó con Ley Bases, está mal. **Este número es producto en sí mismo:
  nadie tiene la medición de cuánto se modifican las leyes en el recinto.**
- **B1 — el contrato.** Dejar de descartar en `elegir_votacion`. **Agregá, no reemplaces**:
  su elección de la general es correcta para lo que el motor hace hoy.
- **B2 — agrupar artículos en capítulos** depende de conseguir el articulado, que hoy no
  tenemos (sólo títulos). **Medí qué haría falta y reportalo; no arranques una adquisición
  de datos grande sin decírselo a Franco.**
- **Los dos números publicados** (P(se sanciona algo) y supervivencia) van **apagados** hasta
  que Franco los revise: redefinir qué cuenta como "aprobado" cambia la variable dependiente
  e invalida la comparación con el baseline. **Si tocás la definición del target, reportá los
  dos mundos por separado** — no presentes un Brier nuevo como comparable con el viejo.

---

# Reglas de la casa

**Leé primero, en este orden:** `coordinacion/URGENTE.md` → `MAPA.md` (y `.mapa/buscar.py`
para ubicar código sin releer el repo) → `CLAUDE.md` → `coordinacion/FORMULA-COMPLETA.md` →
ADRs **0016** (doctrina), **0015** (fórmula), **0023**, **0024**, **0025**.

**La doctrina (ADR-0016): de la parte al todo.** Todo factor —incluido el tema— es
información que **un legislador lee y procesa**; la P de la cámara es la consecuencia de
sumar decisiones individuales, nunca un lugar donde se aplican correcciones. **Es el
argumento de fondo de la FASE 1**: el tema tiene que vivir en $P_i$, no en un agregado de
bloque que después se vuelve a agregar.

**ADR-0015:** todo cambio al motor se presenta en tres niveles — la función, el motor en
conjunto (quién consume lo que cambió), y **cómo queda la fórmula**. Se actualiza
`FORMULA-COMPLETA.md` en el mismo commit. Si no se puede ubicar en la fórmula, es señal de
que no se entiende del todo qué se está cambiando.

### Autonomía y barandillas

**Podés prender banderas** si el **censo completo** mejora y queda documentado en la fórmula
y en un ADR — el mismo criterio con el que se prendieron el guard de era y $\eta_j$.

**Pero:**
- **el backtest es la barandilla, y es sobre el censo, no sobre una muestra**;
- **los dos números publicados de la FASE 2 van apagados** hasta que Franco los vea;
- **no `git push`.** Commits locales, en español, uno por tarea.

### Las trampas de estos datos

| trampa | síntoma que la delató |
|---|---|
| nombres de comisión con comas → matchear contra el **catálogo**, nunca partir por separadores | una comisión faltaba **100%** de las veces |
| **dos tablas de enlace acta↔expediente**: usar la ANCHA (5.036), no la angosta (892) | la cobertura de tema daba 24,6% y parecía un techo — era la tabla equivocada |
| `expedientes_giros` mezcla las dos cámaras | cobertura 2,1% en vez de 63,6% |
| nombres de personas en formatos distintos → clave `APELLIDO\|PRIMER-NOMBRE` | un coeficiente daba **p=0,88** |
| defaults silenciosos | **0%** de dictámenes de mayoría en el Senado |
| regex de títulos que envejece | Diputados pasó a decir "HABILITACIÓN DEL TRATAMIENTO" y quedó en **cero** actas sobre tablas desde 2020 |

> **La regla madre: un porcentaje imposible es un bug, no un fenómeno.** Cuando un número
> esperado da nulo, cero o absurdo, **sospechá del cruce antes que de la hipótesis**.

### Higiene estadística — lo que este proyecto ya aprendió a los golpes

- **Medí antes de creer, y elegí bien la unidad.** Dos mediciones correctas del mismo fenómeno
  dieron resultados **opuestos** según qué mantenían fijo: comparando actas, el desvío subía
  con $p=2\cdot10^{-4}$; comparando **legisladores consigo mismos**, el efecto desaparecía.
- **Un $p$ chico sobre unidades mal elegidas es efecto de composición con cara de hallazgo.**
- **Los estratos se leen sobre el censo, no sobre la muestra.** El skill de la era reciente
  pasó de −0,189 (muestra de 300) a +0,024 (censo). Una muestra chica sobre un estrato chico
  da un número que parece titular y no lo es.
- **Sin brazo de control no hay conclusión.** Es el error que motivó todo este prompt.
- **Si el resultado contradice la hipótesis, decilo.** Este proyecto viene descartando ideas
  propias con datos y así es como mejora. Un resultado negativo bien medido vale más que uno
  positivo forzado.

---

# Qué dejar escrito

1. **`coordinacion/ESTADO-DEL-PROYECTO.md`** — entrada de bitácora arriba de todo: qué se
   hizo, **qué se midió**, qué se decidió. Escribí para alguien que no estuvo. Los hallazgos
   negativos y los errores propios también van.
2. **`coordinacion/FORMULA-COMPLETA.md`** — actualizada en el mismo commit; si algo no la
   afecta, decilo con una línea.
3. **ADRs** (fijate el próximo número libre):
   - el **cierre metodológico de la FASE 0** — qué se midió, con qué brazos, y qué queda
     cerrado. Debería enmendar explícitamente al ADR-0024;
   - el **récord por tema** de la FASE 1;
   - lo que salga de la FASE 2;
   - si sumás columnas a la canónica, **ADR propio** (regla de `CLAUDE.md` sobre
     `docs/schemas`).
4. **`coordinacion/EN-HUMANO.md`** — un párrafo en prosa, sin jerga.
5. **`coordinacion/URGENTE.md`** — borrá lo resuelto (URGENTE 8 si la FASE 1 lo cierra),
   agregá lo nuevo.
6. Reindexá: `python .mapa/indexar.py .`
7. **Tests.** Que no se rompa la suite existente (18 checks en
   `test_bloque_v3_multietiqueta.py` y relacionadas), y agregá:
   - **el brazo de control** como caso testeable;
   - **combinación en logit**: que promediar dos temas opuestos no dé lo mismo que en
     probabilidad;
   - **composición por simulación**: con capítulos perfectamente correlacionados,
     $P_{\text{todo}}$ tiene que dar $\approx \min_k P_k$ y **no** el producto. Es el test que
     atrapa el error de independencia si alguien lo reintroduce.

# Cerrá con

- Qué quedó prendido, qué apagado y **detrás de qué bandera**
- El censo antes y después, **en el agregado y en el subconjunto afectado**
- **Qué esperabas y salió distinto**
- Lo que necesita a Franco, con la pregunta concreta de cada cosa

Empezá por `URGENTE.md` y la **FASE 0**.
