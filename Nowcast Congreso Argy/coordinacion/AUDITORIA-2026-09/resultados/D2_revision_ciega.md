# D2 — revisión ciega del veredicto (capa 2: piso, ε₀, τ y el mecanismo ε₀+τη)

**Revisor:** subagente Opus, ciego al veredicto del agente que midió (§11 del protocolo). **Fecha:** 2026-10-05.
**Insumos (únicos que leí):** `Archivos_Borrar/d2/revision_ciega/` → `1_protocolo_fase_D.md`, `2_preregistro_y_avance_D2.md`, `3_d2_capa2_SIN_VEREDICTO.json` (sin la clave `veredicto`), `4_d2_curvas.json`, `4_d2_seleccion.json`, `4_d2_controles.json`, `4_d2_panel_primario.json`, `5_V0_calibracion_actas_2026-10-03.json`. No abrí otro archivo del repo, no corrí `git` y no vi el veredicto del medidor.
**Código:** `Archivos_Borrar/d2/revision_ciega/codigo_revisor/revisor_d2.py` (selección, compuesto, paneles, Δ, Holm, árbol) y `chequeos_extra.py` (coherencia de brazos y sensibilidad del panel del piso). La salida completa está en `codigo_revisor/revisor_d2_salida.json`.

---

## 1. Qué hice

1. **Selección anual, rehecha desde cero**, sólo con entrenamiento: actas con fecha anterior al 1-ene-*Y*, sin las leyes de todas las actas OOS del censo del año *Y* (desvío 3 del avance).
   - **ε₀:** argmin de la suma de `ll::ε` de las curvas en 0–0,30. Si hay empate relativo < 1e-12 gana V0, y si V0 no está entre los empatados, el más bajo.
   - **τ:** `tau_mediana` en la variante (b), sin ε₀, sobre las actas de entrenamiento de ≥ 20 votos de todos los tipos. Identifiqué la fórmula desde los momentos (n, A, Σp, Σp²): τ = √mediana[((A − Σp)² − V) / V²], con V = Σp − Σp². Reproduce exacto los valores con todo el panel: **1,1882 sin ε₀ y 1,156 con ε₀ 0,035**. La variante «con» aplica el afín p̃ = ε₀ + (1 − 2ε₀)p sobre los momentos.
   - **Piso:** suma de Brier de P(aprobación), recortada a [1e-4; 1 − 1e-4], en las actas SIMPLE de entrenamiento con resultado, sobre las columnas `p::piso=v` y `p::v0`. El empate lo gana V0.
2. **Compuesto WF del piso:** en cada acta OOS, la P del brazo del piso elegido ese año (0,02 → `p::v0`).
3. **Los cinco Δ**, sobre `actas_del_panel` de cada contraste:
   - IC 95% por ley y por mes (`fecha[:7]`), con bootstrap de Poisson: 2.000 réplicas, `default_rng(7).poisson(1, (2000, k))` sobre los grupos ordenados como texto.
   - p con la fórmula del §5, p\* = máx(p_ley; p_mes), MDE = 2,8 × el error estándar mayor.
   - Brier relativo en %. Cobertura como |c_alt − 0,90| − |c_base − 0,90| en pp, con las dos coberturas recalculadas en cada réplica. En el mecanismo, la base es el clip.
4. **Holm** a 0,05 con m = 5. **Subgrupos del veto E**, dentro del panel primario, con IC por ley y el de mes al lado: era vigente (desde 2023-12-10), Diputados y Senado.
5. **Paneles reconstruidos sin leer `y`**, desde las columnas P y banda, y comparados con `actas_del_panel`.
6. **Coherencia de los brazos.** No re-simulé ningún brazo: no tengo el censo ni el simulador. Verifiqué:
   - igualdades que tienen que cumplirse por construcción;
   - `in::` recalculado desde `af`, `lo` y `hi`;
   - la dirección del efecto por año: ancho de banda contra τ_Y, y extremidad de P contra ε₀_Y.

## 2. Reproducción

| qué | resultado |
|---|---|
| **Selección anual** (ε₀, τ, τ «con», piso; 21 años) | **idéntica al runner en los 84 valores**. Valores finales: ε₀ 0,035, τ 1,1882 y piso 0, iguales. El entrenamiento más chico tiene 1.058 actas para ε₀ y τ y 977 para el piso: ningún año queda bajo 20, ninguno apagado |
| **Bordes** | ε₀ no toca 0,30. El piso no toca 0,04. **El piso toca 0 en 2025–26**: es el borde no extensible, y se dice |
| **Poblaciones OOS** | Brier: 4.214 actas y 2.681 leyes. Cobertura: 4.230 actas y 2.683 leyes. Coinciden con el pre-registro. La columna `oos` coincide con la regla (Diputados ≥ 2006, Senado ≥ 2007) |
| **Paneles primarios** | ε₀ 3.894, τ 2.564, mec (i) 4.184 y mec (i′) 4.230: **idénticos** acta por acta. Piso 3.796: idéntico a **la unión de la grilla** (alguno de 0; 0,01; 0,04 difiere de V0). Si el panel fuera «donde el compuesto difiere», serían 2.801 (ver hallazgo M1) |
| **Los cinco Δ, IC por ley y por mes, p\*** | **idénticos al runner al cuarto decimal** |

## 3. Los cinco contrastes

| # | contraste (alt · base) | panel (actas · leyes) | Δ | IC 95% por ley | IC 95% por mes | p\* | MDE | Holm (m = 5) | veto E (era vigente · Dip · Sen, IC por ley) | **salida** |
|---|---|---|---:|---|---|---:|---:|---|---|---|
| 1 | **piso**: WF · V0 (Brier, %) | 3.796 · 2.451 | **−2,94%** | [−4,48; −1,91] | [−4,77; −1,54] | 0,0010 | 2,31 | rechaza | adoptar es un cambio. Ningún subgrupo se daña: −5,97 [−10,52; −2,88] · −5,29 [−8,11; −3,31] · −0,68 [−1,22; −0,32] | **A** |
| 2 | **ε₀ (ii)**: WF · V0 (Brier, %) | 3.894 · 2.519 | **−5,48%** | [−7,44; −4,00] | [−8,57; −3,42] | 0,0010 | 3,69 | rechaza | recalibrar es un cambio. Ningún subgrupo se daña: −1,03 [−1,96; −0,34] · −7,09 [−10,36; −4,89] · −2,80 [−5,17; −1,45] | **A** |
| 3 | **τ (ii)**: WF · V0 (cobertura, pp) | 2.564 · 1.771 | **+1,21 pp** (56,36% contra 57,57%) | [+0,75; +1,70] | [+0,67; +1,78] | 0,0010 | 0,81 | rechaza | **no se evalúa**: con Δ > 0 en un contraste (ii), la acción es conservar V0, y eso no es un cambio. Al lado: −0,74 [−2,28; 0,00] · +0,45 [+0,17; +0,78] · +2,90 [+1,54; +4,31] | **B** |
| 4 | **mec (i)**: WF · clip (Brier, %) | 4.184 · 2.663 | **+21,09%** | [+9,39; +37,44] | [+5,55; +46,33] | 0,0020 | 29,66 | rechaza | apagar es un cambio. En ningún subgrupo el clip pierde: +45,6 [+15,3; +110,7] · +29,0 [+9,5; +63,5] · +11,5 [+4,0; +23,7] | **B** |
| 5 | **mec (i′)**: WF · clip (cobertura, pp) | 4.230 · 2.683 | **−43,83 pp** (60,6% contra 16,8%) | [−47,01; −40,73] | [−47,31; −40,29] | 0,0010 | 5,08 | rechaza | con cualquiera de las dos lecturas de la acción, ningún subgrupo se daña: −52,2 [−65,6; −35,9] · −40,7 [−45,4; −35,9] · −47,2 [−50,6; −43,8] | **A** |

Ningún contraste es Z: en todos los paneles la alternativa difiere de la base. Ninguno es C: ningún IC queda entero dentro de ±1% o ±1 pp. F no aplica en la capa 2 (pre-registro §2). Holm rechaza los cinco: el p\* más grande, 0,0020, queda bajo 0,05 en el último paso.

## 4. Salida del mecanismo y acciones

- **Mecanismo:** (i) = **B** y (i′) = **A**. Por la regla 3.8 del pre-registro, A en uno y B en el otro → **E**, y lo mismo por la regla por término del §6. Es exactamente la salida esperada en el pre-registro.
- **«Si el mecanismo termina en E, no se aplica ninguno de los cinco contrastes, tampoco el del piso, y todo va a Franco con las mediciones»** (3.8). **No se cambia nada del motor y no hay lote.**
- **Qué correspondería a cada parámetro si Franco levanta el bloqueo** (informativo; hoy no se aplica):
  - **Piso:** hiperparámetro en A → recalibrar al valor WF final, **0**. Ese valor está en el borde inferior no extensible y sólo se eligió en 2025–26. En 2006–2024 el compuesto usó 0,01.
  - **ε₀:** (ii) A. Su acción depende de (i), y (i) está en E. Aunque se aplicara, **el valor WF final es 0,035 = V0**: no cambia ningún número. Es el caso «el óptimo cambió en el tiempo».
  - **τ:** (ii) B → **conservar 1,19**.
  - **Mecanismo:** E → no se cambia; va a Franco con la tensión entre Brier (el clip gana) y cobertura (el mecanismo gana).
- **Confirmación conjunta (3.9):** hoy no se dispara, porque E frena todo. **Pero si Franco decide conservar el mecanismo y aplicar lo demás, piso A + ε₀ (ii) A obligan al brazo conjunto** antes de adoptar cualquiera de los dos.
  - El brazo usa los valores de cada año del piso y de ε₀ juntos, contra V0 y sin Holm.
  - Vale aunque el ε₀ final sea V0, porque los valores anuales difieren.
  - Ver el hallazgo I2.

## 5. Auditoría de los controles y del panel

| control | ¿alcanza? | comentario |
|---|---|---|
| A/B: el simulador sin argumentos reproduce el 03-10 (5.858) y el 28-09 (5.852), 0 diferencias en todas las columnas | sí | es el control positivo del §7, completo |
| C/D: V0 explícito, escalar y por año | sí | descarta que la vía `{año: valor}` introduzca diferencias |
| E: clip = `p_sin` | sí | la base del mecanismo es el régimen del motor |
| el piso no actúa donde no puede (1.144 y 478 actas, 0 distintas) | sí | |
| anti-vacuidad (cada brazo difiere en miles de actas) | sí | |
| estimador con todo el panel = `ESPERADO_HOY` (0,035; 1,1882) | sí | lo reproduje independientemente desde las curvas, con la fórmula identificada |
| **invariancia de la selección** (`y` corrompida en el test y en las leyes de test: 0 cambios en 21 años; control positivo: cambia en los 15 años desde 2012) | sí | además, **mi re-selección con filtros de entrenamiento escritos por mí da lo mismo en los 84 valores**. Es evidencia independiente de que la selección miró sólo entrenamiento |
| **coherencia de los brazos** (mío, sin re-simular) | sí | `eps_wf` = V0 exacto en 2025–26, cuando ε₀_Y = 0,035. `mec_wf` = `tau_wf` exacto (P, lo, hi) en 2025–26: números aleatorios comunes y el mismo (ε₀, τ_Y). `in::` recalculado: 0 diferencias en los cinco brazos. Por año, el ancho de banda de `tau_wf` es menor que V0 donde τ_Y < 1,19 (2006–2017) y mayor donde τ_Y > 1,19 (2018–2025). La P de `eps_wf` es más extrema donde ε₀_Y < 0,035. Las direcciones son las correctas |
| paneles sin leer `y` | sí | los reconstruí sólo desde P y bandas. Coinciden; el del piso, con la lectura «unión de la grilla» |

**Conclusión de la auditoría:** los controles alcanzan para confiar en la medición. No encontré nada que invalide un contraste. Lo que sí encontré afecta la **interpretación** (I1) y la secuencia de adopción (I2).

## 6. Hallazgos

### BLOQUEANTE
Ninguno.

### IMPORTANTE

**I1. ε₀ contradice lo esperado, y los tres «A/B» de Brier son una sola señal.**
- **Lo esperado y lo medido.** El pre-registro esperaba |Δ| ≤ 2%, signo incierto, con trayectoria en 0,02–0,06. Lo medido es −5,48%, y ε₀_Y = 0,01–0,015 en 2006–2010, debajo del rango.
- **Consecuencia formal: ninguna.** F no aplica en la capa 2.
- **Qué implica:**
  - **La ganancia en la capa 2 no viene de calibrar mejor ε₀ en los votos.** El informativo de la capa 1 muestra que ε₀_Y **empeora** el Brier de los votos OOS en +0,21% [+0,06; +0,35], y el log-loss en +0,34% [−0,05; +0,69]. Lo que hace un ε₀ más bajo es afilar P(aprobación), que está subconfiada.
  - **Es el mismo fenómeno que piso A y que mec (i) B.** En el panel del mecanismo, el Brier medio es: clip 0,0219, `eps_wf` 0,0266, `mec_wf` 0,0265, compuesto del piso 0,0272, V0 0,0277. La constante (la tasa) da 0,0220.
  - **Holm cuenta como independientes tres contrastes que empujan en la misma dirección.** No cambia ninguna salida, porque los p son ≈ 0,001, pero Franco debería leerlos como una sola señal: el agregado de P(aprobación) de V0 es peor que una constante en Brier, y lo que la acerca a la constante gana.
  - **Hay una tensión de diseño, declarada en el protocolo pero relevante acá.** ε₀ se elige por el log-loss de la capa 1 y se juzga por el Brier de la capa 2, y las dos apuntan en sentidos opuestos.

**I2. La confirmación conjunta es condicional, pero obligatoria si se levanta E.**
- Piso y ε₀ dan A, y los dos afilan P(aprobación).
- Adoptarlos por separado, cada uno medido con el otro en V0, puede sobre-afilar.
- Si Franco resuelve el mecanismo a favor de conservarlo, **ninguno de los dos se adopta sin el brazo conjunto de 3.9**. Ese brazo debería informar también la cobertura, que el piso y ε₀ no miden.

### MENOR

- **M1. El panel del piso es la unión de la grilla, no «donde el compuesto difiere».**
  - Es lo pre-registrado («alguna alternativa de la grilla final»), así que no es un desvío.
  - Incluye 995 actas en las que el compuesto WF es idéntico a V0, porque sólo 0,04 las mueve. Eso diluye el Δ relativo.
  - Restringido a las 2.801 actas donde el compuesto difiere, da −4,12% [−6,35; −2,65] por ley y [−7,24; −2,11] por mes, con subgrupos −8,62 / −7,75 / −0,92, todos con IC < 0. **La salida no cambia.**
  - Hay una asimetría con ε₀, cuyo panel es «donde el brazo WF difiere». Conviene escribirlo en la regla del panel para los ítems con grilla.
- **M2. El piso final de 0 está en el borde no extensible y sólo se eligió en 2025–26.**
  - Casi toda la ganancia del compuesto es del 0,01.
  - Como respaldo (descriptivo, no decide): el piso fijo en 0 contra V0 en la población OOS da −2,59% [−3,60; −1,83] por ley y [−3,89; −1,62] por mes. El de 0,01, −1,58% [−2,18; −1,12]. El de 0,04 empeora: +4,98%.
- **M3. El B de τ sale de 37 actas: 34 salen de la banda y 3 entran.**
  - La era vigente invierte el signo: −0,74 [−2,28; 0,00].
  - Es coherente con el sesgo contra el WF declarado. τ_Y crece con el tiempo (1,13 → 1,21), así que los años tempranos usan τ más chicos que el 1,19 ajustado en muestra.
  - Además, el estimador (una mediana) no apunta al 90%: V0 y WF cubren ≈ 57–60%.
- **M4. Los brazos WF simulan las 209 actas del Senado de 2006 con los valores del año 2006** (el mapa `{año: valor}` no distingue cámara).
  - Esas actas no son OOS y no se evalúan. La selección de ε₀ y τ usa las curvas, no los brazos, y los brazos del piso son de valor fijo. **Es inocuo**, pero el avance dice «los brazos WF usan V0 en los años que sólo entrenan», y para el Senado de 2006 no es así.
- **M5. En mec (i) el MDE da 29,7 contra un Δ de 21.**
  - Es la cola del cociente: la base es el clip, ≈ 0,99 casi constante, con Brier chico en algunos subconjuntos (2019–2023: se ≈ 2.300).
  - No contradice que los dos IC por percentiles excluyan 0, pero el número puntual del Δ relativo es frágil. El signo no lo es.
- **M6. Las P se guardan con 4 decimales.** La identidad que define los paneles y la Z se juzga sobre P redondeada. Por ejemplo, 30 actas quedan fuera de mec (i) por tener 0,99 en los dos brazos. No mueve nada.

### Límites de esta revisión
1. **No re-simulé ningún brazo:** sólo verifiqué su coherencia interna y la dirección del efecto.
2. **El bootstrap coincide al decimal porque repliqué la convención del runner** (semilla 7, grupos ordenados como texto). Eso confirma la implementación, no que el IC sea el adecuado.
3. **La selección del piso se hace con ε₀ y τ en V0**, ajustados con todo el panel. Es un sesgo de segundo orden y está declarado.
4. **El IC no incluye la variabilidad de la selección** (§5 del protocolo).

## 7. Veredicto final del revisor

| parámetro | salida del árbol | acción |
|---|---|---|
| **piso** (0,02) | **A** (−2,94%, Holm, sin veto) | **no se cambia: bloqueado por el mecanismo en E (3.8); va a Franco.** Si se levanta: recalibrar a 0 (borde no extensible), y sólo después del brazo conjunto con ε₀ |
| **ε₀** (0,035) | **A** en (ii) (−5,48%, Holm, sin veto) | **no se cambia; va a Franco.** Aunque se aplicara, el WF final es 0,035 = V0 |
| **τ** (1,19) | **B** en (ii) (+1,21 pp) | **se conserva 1,19**, y en todo caso el bloqueo lo deja igual; va a Franco con lo demás |
| **mecanismo ε₀+τη** | (i) **B** (+21,1%) · (i′) **A** (−43,8 pp) → **E** | **no se cambia, sigue prendido; va a Franco** con la tensión entre el Brier y la cobertura |
| **ítem D2** | — | **sin lote. Confirmación conjunta no disparada hoy; obligatoria (piso + ε₀) si Franco conserva el mecanismo y quiere aplicar el piso** |
