# SUPERPROMPT — Nowcast Legislativo, versión 2 (repo nuevo, desde cero)

> Pegá este texto completo como primer mensaje de una conversación nueva de Claude Code, abierta en la carpeta del repo
> nuevo. Escrito el 2026-10-06 a pedido de Franco, al cerrar el trabajo en el repo viejo («Nowcast Congreso»).
> Los puntos marcados **[DECIDE FRANCO]** se le preguntan antes de ejecutar la fase que los necesita.

---

## 0. Quién soy y qué te pido

Soy Franco, dueño del proyecto. Reviso yo las decisiones del modelo: quiero **evidencia medida, no p-valores sueltos ni
afirmaciones**. Vamos a **rehacer desde cero**, en un repo y una carpeta nuevos, un modelo que ya existe en otro repo y
que auditamos durante semanas. Del repo viejo nos quedamos **sólo con la fórmula y la idea madre**. La base de datos y el
código no se heredan, porque la base estaba mal construida (ver §3). Todo se reconstruye desde las **fuentes oficiales**,
parte por parte, comprobando en cada paso que los problemas de antes no vuelvan a aparecer.

Antes de hacer nada:
1. Leé este prompt completo.
2. Usá la skill **`mapa-de-proyectos`** (`anthropic-skills:mapa-de-proyectos`) para crear el sistema de mapa y
   bitácoras del repo nuevo: `MAPA.md` y `BITACORA.md` por carpeta, y el índice que la skill genere. Es el primer ítem de
   la Fase 0.
3. Proponeme el plan de la Fase 0 y esperá mi OK.

---

## 1. El objetivo del modelo (va textual al `README.md` y al `CLAUDE.md` del repo nuevo)

> El objetivo del modelo es encontrar **la probabilidad de que un legislador apruebe o rechace cierto proyecto de ley**.
> **El legislador es la unidad de medida del modelo, contra un acta de votación específica.** Esa probabilidad está
> condicionada por:
> - la **lealtad** que tiene ese legislador a su bloque;
> - **cómo vota en ciertos temas**;
> - **cómo salió la votación en la cámara precedente**, si corresponde;
> - **de quién es el proyecto** (el origen);
> - **la aprobación (ICG) del oficialismo**, que afecta a opositores y dialoguistas.
>
> La idea es reconocer dentro del recinto, y dependiendo de cada acta, **cuáles son los legisladores «clave»** en esa
> votación: los que no tienen su voto asegurado, es decir, los que **pivotean** entre votaciones diferentes.

Consecuencias para el diseño:
- **La predicción primaria es por legislador y por acta:** P(afirmativo | legislador i, acta a), con lo que se sabe
  **antes** de esa votación.
- **La salida que importa al usuario es la lista de pivotes de cada acta,** con su probabilidad y por qué.
- El agregado (P de que el acta se apruebe, recuento esperado, banda) es **secundario**: se arma desde las P individuales
  y se mide aparte. En el repo viejo, P(aprobación) de mayoría simple no le ganaba a una constante, porque el 97,5% de
  esas actas se aprueba; no es la vara principal.

---

## 2. La cadena de producción (el orden en que el sistema trabaja)

1. **Entra un proyecto de ley** con un número de **expediente único**, por ejemplo **7-PE-2026**.
   - Diputados: https://www.hcdn.gob.ar/proyectos/detalle_tp_adjunto/index.html?id=293445
   - Senado (como venido en revisión, **CD-7/26**): https://www.senado.gob.ar/parlamentario/comisiones/verExp/7.26/CD/PL
2. **El proyecto se gira a una o varias comisiones.**
3. **Para tratarlo en el recinto se trabaja sobre una Orden del Día (OD),** que sale de las comisiones. **Una OD trata un
   tema y puede traer varios dictámenes (mayoría y minorías), y cada dictamen agrupa uno o varios expedientes.** En la
   sesión **se discute y se vota sólo el dictamen de mayoría.** Por eso **el acta NO se vincula al tema de la OD**: eso
   mezclaría dictámenes distintos. Se vincula al **expediente (o los expedientes) del dictamen de mayoría**. La regla de
   Franco: «mirar sólo el orden del día, ir a ese orden y sacar el nombre del proyecto de ley del DICTAMEN DE MAYORÍA,
   que es el que se trata en la sesión».
4. **La votación:**
   - cada votación es **un acta individual**: la general, cada artículo o título en particular, las mociones;
   - se buscan **todas las actas de ese proyecto** (votación general y, si existen, las particulares) y se recopila **el
     voto de cada legislador en cada acta**;
   - un legislador puede votar distinto de un acta a otra de la misma ley: esa diferencia **es la señal** de pivote.
5. **Esos votos pasan por el modelo de §1** y se transforman en capacidad predictiva para el próximo proyecto o acta.
6. **Si el proyecto pasa a la otra cámara,** se repite la cadena. La votación de la cámara precedente es un insumo de la
   revisora.

**Fuentes oficiales** (los PDF se bajan de los sitios oficiales; los consigue el agente, no Franco):
- **Diputados, actas de votación nominal:** https://votaciones.hcdn.gob.ar/ (el PDF «acta_online_NNNN»).
- **Diputados, proyectos y OD:** https://www.hcdn.gob.ar/ (detalle del proyecto, tramitación, OD en PDF).
- **Senado, expedientes, OD y actas de votación:** https://www.senado.gob.ar/ (en `parlamentario/`).
- **ICG:** Índice de Confianza en el Gobierno, Universidad Torcuato Di Tella (UTDT), mensual.

---

## 3. Por qué empezamos de cero: lo que encontramos en la base vieja (que NO se repita)

La base vieja («canónica») mezclaba cuatro fuentes no oficiales o de terceros (Década Votada, argentinadatos, CKAN de
Diputados, un scraper del Senado y una carga manual). Problemas medidos el 2026-10-05/06:

1. **Se perdía qué se votaba.** Cada fila sí era una votación, pero muchas fuentes no traían la **descripción** («SE VOTA
   EN GENERAL», «ARTICULO 18», «TÍTULO I»). Por ejemplo, la sesión del Senado del 07/08/2026 (Inviolabilidad de la
   Propiedad Privada, O.D. 104/26) aparecía como **5 filas con el mismo título**, sin saber cuál era la general.
   Clasificar «general / particular / moción» desde el título era adivinar.
2. **Faltaban actas**: sesiones incompletas y un hueco grande en Diputados 2020–2023 (25 actas en cuatro años).
3. **Duplicados entre fuentes:** la misma votación con dos ids (259 actas de CKAN eran copias de argentinadatos). La API de
   argentinadatos devolvía 295 actas dos veces.
4. **Un dedup silencioso:** el armado deduplicaba por (acta, nombre del legislador) y se quedaba con el primero. Así se
   puede esconder una mezcla de votaciones sin que nadie lo vea.
5. **Tipo de mayoría y resultado escritos de muchas formas:** 20 textos para el tipo y 15 para el resultado, más vacíos,
   empates y canceladas. **La base de la mayoría cambia de acta a acta:** «votos emitidos», «legisladores presentes» o
   «miembros del cuerpo». En el Senado, dentro de la misma sesión del BCRA, el art. 22 se votó con base «votos emitidos»
   y los demás con «legisladores presentes».
6. **Etiquetas de origen sin validar** (43% «desconocido»), y eran el insumo que más pesaba en el skill. En la cadena
   nueva **el origen sale del expediente** (quién lo inició: Poder Ejecutivo, diputado o senador y su bloque).
7. **Fugas de información en el modelo viejo:** récord con `shift(1)` por fila (veía el mismo día y la misma ley), ficha
   de lealtad calculada con toda la historia, el ICG estandarizado con la serie entera.

---

## 4. La fórmula del repo viejo (punto de partida, NO dogma)

Se conserva **la forma** y se re-estima **todo** con datos nuevos, walk-forward. Ningún parámetro se hereda como valor.
Para el legislador i del linaje (bloque) ℓ, un proyecto de origen o, a la fecha F (todo con datos de fecha < F):

- **Récord propio:**
  rec_i = afirmativos / emitidos de i en la ventana del gobierno vigente, con el mismo origen.
- **Postura proyectada del bloque**, condicionada por tema y origen y encogida hacia la incondicional:
  s_ℓ = (n^c·s^c + k·s^u) / (n^c + k).
- **Probabilidad base:**
  P_i = (n_i·rec_i + k·s_ℓ)/(n_i + k) si i tiene historia; si no, P_i = s_ℓ(1−d_i) + (1−s_ℓ)·d_i/2.
- **Lealtad (desvío) point-in-time, encogida hacia su bloque y con piso:**
  d_i = máx((n_i^disp·d_i^obs + k·d̄_ℓ)/(n_i^disp + k), d_min).
- **Dictamen (β):**
  logit P_i^dict = logit P_i + β₁·F_i + β₂·(1−d_i)·J_ℓ, donde F_i = firmó el dictamen de mayoría y J_ℓ = su jefe de
  bloque lo firmó.
- **Cámara precedente (ψ):** el voto de la misma ley en la cámara de origen, leído por el legislador de la revisora. En el
  viejo se midió grande y nunca se implementó.
- **ICG (γ):** la aprobación del oficialismo modula a opositores y dialoguistas. Se midió significativo y nunca se
  conectó.
- **Sobre tablas (θ):** la moción de habilitación es su propia votación, no una mezcla.
- **Incertidumbre:** P̃_i = ε₀ + (1−2ε₀)·P_i y un shock común τ·η por acta en la simulación. Ojo: en el viejo, el mismo τ
  daba ancho a la banda del recuento pero empeoraba el Brier de P(aprobación). Son dos piezas que conviene separar.
- **Agregado:** Monte Carlo sobre los presentes con el umbral de **la mayoría y la base de esa acta**. El +1 de la
  mayoría simple corre: un empate no aprueba.

La fórmula completa vieja, con la historia de cada término, está en (sólo lectura):
`C:\Users\Franco\OneDrive\Desktop\TresTercios\Nowcast Congreso\Nowcast Congreso Argy\coordinacion\FORMULA-COMPLETA.md`.
Lo medido en la auditoría está en `...\coordinacion\QUE-SE-MIDE.md` y en
`...\coordinacion\AUDITORIA-2026-09\ESTADO-EJECUCION.md`.

**Lo que ya se sabía en el viejo** (es referencia, no vara): el voto individual tenía skill **0,153 [0,099; 0,208]**
contra la tasa base. Casi todo venía del origen, y el récord por tema medido limpio **empeoraba** (+2,1%).

---

## 5. Reglas de trabajo (van al `CLAUDE.md` del repo nuevo)

1. **Todo es un ítem del plan** (`coordinacion/ESTADO-EJECUCION.md`). Lo que no está en el plan no se hace: se anota en una
   línea en `coordinacion/PENDIENTES.md` y se vuelve al ítem en curso.
2. **El alcance cambia sólo con la frase `CAMBIO DE ALCANCE:` de Franco,** y se registra en la bitácora de alcance antes de
   ejecutar. Las preguntas se responden; preguntar no abre trabajo.
3. **Una fase a la vez,** con la evidencia del criterio de salida (comando y salida, o sha) antes de pasar a la siguiente.
4. **Pre-registro antes de medir:** qué se mide, con qué panel y corte, y qué umbral decide. Se escribe, pasa por el
   `advisor` y se commitea **antes** de mirar resultados. Nada se elige mirando el panel de evaluación.
5. **Historia estricta, siempre:** para predecir el acta a sólo existen datos con fecha anterior. En el backtest, además,
   sin la misma ley. **Todo insumo es point-in-time:** padrón, bloque, ficha de lealtad, ICG, firmas y temas. Un test
   corrompe el futuro y verifica que la predicción no cambia.
6. **Cada veredicto de una fase de medición lo revisa un segundo agente Opus que no vio la conclusión.** Si difiere, no
   se aplica nada y va a Franco con los dos.
7. **«Funciona» tiene definición numérica**, escrita en la Fase C y aprobada por Franco antes de medir. **No se cambia a
   mitad de camino.**
8. **Los datos crudos no se tocan:** se guardan tal como se bajaron (PDF/HTML con su sha256 y la URL), y toda corrección
   es una capa encima, con su evidencia. Ninguna corrección de datos sin el visto bueno de Franco.
9. **El estado vive en el repo, no en el chat:** al cerrar cada ítem y cada sesión se actualizan `ESTADO-EJECUCION.md`,
   las bitácoras y el mapa. Si la conversación se alarga, se abre una nueva con un prompt de reanudación.
10. **Commits chicos, con la suite en verde.** El `git push` lo hace Franco, salvo que diga otra cosa.

**Correcciones de Franco que no se repiten:**
- **Nunca presentes como regla obvia ni como base de comparación el «el legislador vota con su bloque» (≈ 0,99).** Sale
  de conocer después qué votó el bloque: es un oráculo. Predecir la postura del bloque y de los pivotes **antes** de la
  votación es justamente el trabajo del modelo.
- **No digas «el modelo no sirve».** Decí exactamente qué se midió y contra qué.
- **La vara de «funciona» no se cambia en medio de una fase.**

---

## 6. Plan por fases

Cada ítem tiene su pre-registro y su evidencia de cierre. El detalle de cada fase se escribe al empezarla. Lo de abajo es
el esqueleto que hay que respetar.

### Fase 0 — Arranque del repo
- **0.1** Crear el repo y la carpeta [DECIDE FRANCO: nombre, ubicación y remoto], `README.md` con el objetivo de §1,
  `CLAUDE.md` con las reglas de §5, `.gitignore`, `requirements.txt` con pines (Python 3.11 en el CI) y CI en GitHub
  Actions.
- **0.2** Mapa y bitácoras con la skill `mapa-de-proyectos`: `MAPA.md`, una `BITACORA.md` por carpeta, el índice y el hook
  si la skill lo trae (instalado y probado).
- **0.3** Los documentos vivos:
  - `coordinacion/ESTADO-EJECUCION.md` (este plan, la bitácora de alcance y la evidencia por ítem);
  - `coordinacion/PENDIENTES.md`;
  - `coordinacion/QUE-SE-MIDE.md` (vacío hasta la Fase C);
  - `coordinacion/FORMULA.md` (la de §4, término por término, con su estado).
- **0.4** Los PDF de prueba de §7 copiados a `tests/fixtures/` con su sha256: son el **caso de control** de toda la Fase A.
- **Salida:** repo en verde en el CI, mapa generado, plan aprobado por Franco.

### Fase A — La base nueva desde fuentes oficiales: muestra chica, sólo el mandato de Milei
**Alcance:** las dos cámaras, desde el **10-12-2023** hasta hoy, **todas las actas de cada sesión** (generales,
particulares, mociones y otras). Después de cerrar todas las fases se extiende a todos los años.
- **A1 — Inventario de fuentes.** Qué publica cada sitio y desde cuándo, en qué formato (PDF o HTML), cómo se recorre, si
  hay límites de tasa y qué condiciones de uso tiene. Se mide la cobertura antes de bajar en masa. El crudo se guarda con
  la URL, la fecha de descarga y el sha256.
- **A2 — Expedientes:**
  - el número único y su forma en cada cámara (7-PE-2026 ↔ CD-7/26);
  - el iniciador, que es **el origen** (Poder Ejecutivo, legislador y bloque);
  - las fechas, los giros a comisión, la tramitación y el pase entre cámaras.
- **A3 — Órdenes del día:**
  - cada OD con su número, cámara, fecha, comisiones y sumario;
  - **sus dictámenes (mayoría y minorías), los expedientes de cada uno** y las **firmas** (con disidencias, total o
    parcial).
- **A4 — Actas, una fila por votación:**
  - **identificación:** cámara, período, sesión y reunión, número de acta, fecha y hora;
  - **qué se vota:** proyecto/OD, **descripción** textual y tipo de votación derivado **de la descripción** (general,
    particular con los artículos o títulos, general y particular, moción, en bloque u otra);
  - **reglas de la votación:** tipo de quórum, **mayoría y su base**, miembros, presentes, AMN;
  - **resultado:** afirmativos, negativos, abstenciones y ausentes, con el desdoble diputados / presidente / desempate en
    Diputados; el resultado y el presidente;
  - **votos:** **una fila por legislador**, con su voto, **su bloque y su distrito en esa votación**.
- **A5 — El vínculo:** acta → OD → **dictamen de mayoría** → expediente(s) → proyecto, y el puente entre cámaras.
  [DECIDE FRANCO, al pre-registrar A5:]
  - si el dictamen de mayoría unifica varios expedientes, ¿se vinculan todos o sólo el principal?
  - las votaciones sin OD (mociones, apartamiento, sobre tablas, acuerdos), ¿al expediente que mencionan, o sin
    proyecto con su tipo propio?
  - si el dictamen no se encuentra, ¿queda «sin vincular» para revisión manual?
- **A6 — Legisladores:** un id estable por persona a través de las dos cámaras y de las grafías de los nombres. Su bloque
  en cada fecha (el que figura en el acta) y su linaje de bloque.
- **A7 — Controles de calidad** (umbral: 0 fallas, o cada excepción explicada y aprobada):
  - el recuento desde los votos individuales coincide con el declarado;
  - el resultado coincide con el umbral de **su** mayoría y **su** base;
  - los números de acta de cada sesión son correlativos (los faltantes se listan);
  - no hay duplicados;
  - cada acta tiene descripción y tipo de votación;
  - cada votación de un proyecto está vinculada a su expediente;
  - **el caso de control de §7 se reproduce entero desde las fuentes.**
- **A8 — Contraste con la base vieja**, en sólo lectura, sobre las actas que se solapan: qué tenía bien, qué tenía mal y
  qué le faltaba. Se informa, no se copia.
- **Salida:** la base de la muestra Milei, con sus controles en verde y su contraste. Franco la aprueba antes de la
  Fase B.

### Fase B — Las variables, todas point-in-time
Cada una es su propio ítem, con su test de invariancia al futuro.
- **B1** Lealtad al bloque: el desvío individual, encogido y con piso.
- **B2** Récord individual.
- **B3** Postura proyectada del bloque.
- **B4** Tema del proyecto: la taxonomía y cómo se asigna. [DECIDE FRANCO: reusar la taxonomía vieja o definirla de
  nuevo; el récord por tema y el multitema se rediseñan acá, no se prende lo que ya se midió peor].
- **B5** Origen, desde el expediente.
- **B6** Votación en la cámara precedente.
- **B7** ICG point-in-time: el mes M cuenta desde el 1 del mes M+1, y lo que se derive se calcula con datos anteriores.
  Ojo: el parser viejo de UTDT se rompía con `&nbsp;`.
- **B8** Firmas del dictamen y del jefe de bloque.
- **Salida:** una tabla legislador × acta con todas las variables a la fecha de cada acta, y su invariancia probada.

### Fase C — La métrica de verdad y la vara
- **C1 — El panel:** cada par (legislador, acta) con voto emitido. La ausencia se modela aparte, si se decide.
- **C2 — Las métricas:**
  - Brier y log-loss de P_i;
  - **skill contra la tasa base**;
  - **IC 95% por bootstrap sobre leyes**, y por mes;
  - por cámara, por era y por tipo de votación (general, particular, moción).
- **C3 — Las líneas de base:** tasa base, récord propio solo y postura del bloque proyectada **ex ante**. **Nunca el
  bloque ex post.**
- **C4 — «Funciona»:** la definición numérica, propuesta y aprobada por Franco **antes** de medir el modelo. Como
  referencia, la vara vieja era:
  - el skill de la era vigente con un IC de ±0,10;
  - la cobertura de la banda entre 85% y 95%;
  - el Brier de P(aprobación) menor que la constante, en cada cámara;
  - un AUC ≥ 0,75 en las disputadas;
  - las etiquetas de origen con ≥ 90% de precisión.
- **Salida:** un comando que da la métrica, con su test en el CI.

### Fase D — El modelo, término por término, walk-forward
- **D0** El modelo base: la P_i de §4 sin términos extra.
- **D1…** Un término por ítem, en este orden: lealtad, tema, origen, dictamen (β), cámara precedente (ψ), ICG (γ),
  sobre tablas (θ) e incertidumbre (ε₀, τ).
- **Protocolo de cada término:**
  - reajuste anual con ventana creciente, sin la misma ley;
  - el contraste contra el modelo anterior;
  - Holm sobre los contrastes de cada ítem y margen de equivalencia;
  - un árbol de veredicto escrito antes de medir;
  - revisión ciega.
- **Un término entra sólo si mejora medido.** Si no, queda apagado y documentado; no se borra.
- **Salida:** la fórmula final con cada término justificado por su medición.

### Fase E — Pivotes: los legisladores clave de cada acta
- **E1 — La definición:** un pivote es un legislador cuyo voto no está asegurado en esa acta. Se define desde P_i y su
  incertidumbre, desde su variación entre actas del mismo proyecto o de proyectos parecidos, y desde su peso para cruzar
  el umbral.
- **E2 — La medición:**
  - ¿los que el modelo marca como pivotes son los que después se apartan?
  - ¿la postura predicha de cada bloque, sobre todo de los que negocian, es la que vota?
- **E3 — La salida para el usuario:** por acta, la lista de pivotes con su P, la razón y el margen.

### Fase F — Extensión y operación
- **F1** Todos los años, con la misma cadena y los mismos controles.
- **F2** La automatización: bots que bajan las actas y las OD nuevas, con controles que fallen ruidosamente.
- **F3** El agregado por acta y por proyecto (las dos cámaras), como capa secundaria y medida.

---

## 7. El caso de control: 7-PE-2026, reforma de la Carta Orgánica del BCRA

Los PDF están en `C:\Users\Franco\Downloads\`. Se copian a `tests/fixtures/` en la Fase 0, y la Fase A tiene que
reproducir todo esto **bajando las fuentes por su cuenta**:

| paso | documento | qué contiene |
|---|---|---|
| proyecto | 7-PE-2026 (mensaje 226/26 del 30/07/2026) | las URL de §2 |
| OD Diputados | `144-211.pdf` — O.D. Nº 211/2026, impresa el 18/08/2026, Comisiones de Finanzas y de Presupuesto y Hacienda | **I. Dictamen de mayoría** (expedientes 7-PE-2026, 171-D-2025 y 2.888-D-2025), II y III dictámenes de minoría |
| actas Diputados | `acta_online_5971/5972/5973.pdf` — 144° período ordinario, 5ª sesión especial, 6ª reunión, 26/08/2026 | **Acta 6** (18:14) «O.D. 211 … DICT. DE MAY. VOT. EN GRAL.» 144-102-9 · **Acta 7** (18:52) «TÍTULO I» 138-110-7 · **Acta 8** (18:54) «TÍTULO II». Base: votos emitidos, más de la mitad. Entre la 6 y la 7 cambian 10 diputados (Coletta, Frade, Juliano, Lousteau y Massot pasan de abstención a NO; Falcone y Zago de SI a NO; García Aresca, Gutiérrez y Schiaretti de SI a abstención) |
| OD Senado | `51678.pdf` — O.D. Nº 367/2026, 09/09/2026, Comisiones de Economía Nacional e Inversión y de Presupuesto y Hacienda, sobre **CD-7/26** | dictamen que aconseja aprobar, 15 firmas y Fama en disidencia parcial |
| actas Senado | `ACTA_2` … `ACTA_19.pdf` — 24/09/2026, «OD 367/26 - BCRA» | **2** en general (17:08) 46-22-0 · 3 art. 1 · 4 art. 2 · **5** art. S/N y 3, 66-2-0 · 6 art. 4 · 7 arts. 5 y 6 · 8 art. 7 · 9 arts. 8 a 11 · *10 a 12 no están en la carpeta: la Fase A tiene que encontrarlas* · 13 art. 15 · 14 arts. 16 y 17, 46-22 · 15 art. 18, 46-22 · **16** art. 19, 45-23 (Royon pasa de SI a NO) · 17 art. 20 · 18 art. 21 · **19** art. 22, 65-2-1, **con base «votos emitidos»** (las demás: «legisladores presentes») |

**Otras actas de prueba del Senado** (mismo formato):
- `ACTA 8.pdf` (con espacio en el nombre; no confundir con `ACTA_8.pdf`): 07/08/2026, «OD 104/26 - INVIOLABILIDAD», se
  vota en general, 37-33-0.
- `ACTA_21.pdf`: 24/09/2026, «OD 402/26 - ZONAS FRIAS», se vota en general y en particular, 38-8-0.

Los números de esta tabla salieron de una lectura rápida del texto de los PDF. **La Fase A los verifica, no los da por
buenos.**

---

## 8. Trampas conocidas de la PC de Franco (Windows)

- **`PYTHONUTF8=1` siempre.** Sin eso, un `print` con «Δ» o tildes revienta con cp1252, a veces después de escribir los
  archivos.
- **No pongas el repo nuevo dentro de OneDrive.** En el repo viejo, `git pull` y `git merge` fallaban dentro de OneDrive
  («unable to unlink … Directory not empty») y había que hacer el pull a mano. [DECIDE FRANCO la ubicación.]
- **Para esperar corridas largas,** `run_in_background` con un `until … grep`, no `sleep`.
- **Disco:** quedaban ≈ 50 GB. Un test viejo dejaba copias de 87 MB en `%TEMP%`: los temporales se borran en un
  `finally`.
- **Los nombres de comisión tienen comas** («FAMILIA, MUJER, NIÑEZ Y ADOLESCENCIA»). Se matchean contra el catálogo
  oficial, del nombre más largo al más corto. **Nunca se parten por separadores.** Este error apareció tres veces en el
  repo viejo.
- **El `.gitignore` del viejo ignoraba `*.csv`**, y un archivo que tenía que viajar se quedó afuera sin aviso. Los
  archivos que viajan se listan y un test verifica que estén en git.
- **Subagentes:** se lanzan de a uno (el límite de tasa cortó trabajo dos veces) y escriben su resultado a un archivo
  apenas lo tienen.

---

## 9. Decisiones abiertas para Franco (se preguntan en la Fase 0, antes de ejecutar lo que dependa de ellas)

1. Nombre, ubicación (fuera de OneDrive) y remoto de GitHub del repo nuevo.
2. El modelo: ¿Opus como principal, o Sonnet como principal y Opus como revisor y `advisor`?
3. Las tres dudas del vínculo de A5.
4. La taxonomía de temas (B4).
5. La vara de «funciona» (C4).
6. ¿Se puede leer el repo viejo como consulta, sin copiar datos ni código sin pasar por el plan?
