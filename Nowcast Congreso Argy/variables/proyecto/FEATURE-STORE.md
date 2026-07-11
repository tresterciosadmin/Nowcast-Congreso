# Feature store por proyecto / votación — diseño

> Diseño en papel (decisión de Valle, 2026-07-11): antes de clasificar y recolectar,
> definir QUÉ rasgos lleva cada proyecto, DE DÓNDE sale cada uno y A QUÉ parte del
> modelo alimenta. Este documento es el plano; no se implementa acá.

## 1. Para qué sirve
El Nowcast no predice el voto mirando un solo número: descompone. La probabilidad de
sanción de un proyecto se arma como

```
P(sanción) = P(llega al recinto)              ← EMBUDO
           × P(hay quórum / quién asiste)      ← ASISTENCIA
           × recuento sobre la posición de cada bloque, ajustada por desvío individual
                                                ← POSICIÓN DE BLOQUE → AGREGADOR (ya existe)
```

El **feature store** es la ficha de rasgos que alimenta esas tres piezas. La idea central
—y la que ordenó este diseño— es que casi todo es **condicional al proyecto**: un bloque no
tiene "una" posición ni un legislador "un" presentismo; los tiene **según el tipo de
proyecto** (tema, quién lo presenta, el clima político). Sin estos rasgos no se puede
condicionar nada; con ellos, cada pieza del modelo se vuelve específica.

## 2. Dos unidades de análisis
- **Proyecto** (clave: `denominador`, ej. `2832-D-2026`): sus rasgos intrínsecos y de
  contexto. Alimenta el embudo y define el "tipo de votación".
- **Votación × bloque** (clave: `acta_id` × `bloque`): la posición esperada de cada bloque
  y la asistencia esperada de sus miembros PARA ESE proyecto. Es donde los rasgos del
  proyecto se cruzan con los antecedentes de cada actor.

## 3. Familias de features

### A. Identidad y trámite del proyecto  — fuente: `datos/seguimiento` + `datos/proyectos`
| feature | definición | estado |
|---|---|---|
| `denominador` | id del expediente (NNNN-X-AAAA) | ✅ disponible |
| `camara_origen` | dónde se presentó (diputados/senado) | ✅ |
| `tipo_proyecto` | ley / resolución / declaración / comunicación | ✅ (del trámite) |
| `comisiones_giro` | comisiones a las que fue girado (y orden) | ✅ (extractor validado en vivo) |
| `n_giros`, `dias_en_comision` | cuántas comisiones y cuánto tardó | ✅ derivable |
| `estado_tramite` | ingresado→en_comisión→dictamen→media_sanción→sanción/rechazo | ✅ |

### B. Tema — fuente: `variables/proyecto` (agente de taxonomías) + `docs/taxonomias`
| feature | definición | estado |
|---|---|---|
| `taxonomias[]` | 1..n ids del vocabulario controlado (74 ids, 16 áreas) | 🟡 agente listo, falta correr en vivo |
| `area_principal` | área temática dominante (ECON, SALUD, JUST…) | 🟡 idem |
| `es_multitema` | si cruza varias áreas | 🟡 idem |

Es la **llave** de todo el condicionamiento: habilita "posición de bloque por tema",
"presentismo por tema" y "disciplina por tema".

### C. Autoría y alineación política — fuente: `datos/proyectos.proyecto_autores` + `datos/canonica` (bloques por fecha)
| feature | definición | estado |
|---|---|---|
| `autor_principal_bloque` | bloque del primer firmante a la fecha de presentación | ✅ derivable (autores ya se extraen) |
| `origen` | **oficialismo / oposición / mixto**: alineación del autor principal vs. el gobierno de turno | 🟡 falta la regla oficialismo-por-fecha |
| `n_firmantes`, `firmas_transversales` | cuántos firman y de cuántos espacios distintos (germen del Mapa de Influencia, Módulo B) | ✅ derivable |
| `impulsa_ejecutivo` | si es mensaje del Poder Ejecutivo | 🟡 marcar en seguimiento |

`origen` es clave para la asistencia: un legislador tiende a faltar cuando el proyecto lo
presenta su oposición, o cuando es un debate incómodo dentro de su propio espacio.

### D. Institucionales — fuente: `datos/canonica` (actas) + `datos/proyectos`
| feature | definición | estado |
|---|---|---|
| `tipo_mayoria` | simple / absoluta / dos tercios / … (define el umbral) | ✅ (ya lo usa el agregador) |
| `afinidad_comision` | si los firmantes integran la comisión a la que se giró (Committee Overlap) | 🟡 derivable (giros + autores) |
| `veto_legal` | regla dura: nulidad de reformas electorales en años comiciales (Gatekeeper) | 🟡 regla a codificar |

### E. Contexto temporal (varía en el tiempo, no por proyecto) — fuente: nuevas ingestas
| feature | definición | estado |
|---|---|---|
| `gobierno` | gobierno de turno a la fecha | ✅ (ya en datos/export) |
| `ICG_ditella` | Índice de Confianza en el Gobierno (UTDT), mensual — "gravedad presidencial": el costo de oponerse al Ejecutivo | 🔴 falta ingestar la serie mensual de UTDT |
| `proximidad_electoral` | meses hasta la próxima elección nacional (penaliza según cercanía de urnas) | 🟡 derivable de un calendario electoral |
| `composicion_congreso` | escaños por bloque en el período (define mayorías posibles) | ✅ derivable de la canónica |
| `es_anio_electoral` | si la fecha cae en año de elección | 🟡 derivable |

### F. Derivadas históricas CONDICIONADAS — el corazón del modelo. Fuente: cruce de A–E con la historia
| feature | definición | depende de | estado |
|---|---|---|---|
| `posicion_bloque_por_tema` | cómo suele votar cada bloque en proyectos de ESE tema/origen | B, C | 🔴 necesita B corrido |
| `presentismo_condicionado` | P(presente) de cada legislador **según tema, origen e importancia** del proyecto (no un promedio) | B, C, D | 🔴 el escalón 2 de asistencia_quorum |
| `disciplina_por_tema` | tasa de desvío del legislador dentro de cada área temática | B | 🟡 disciplina existe; falta la dimensión tema |
| `saliencia` | qué tan "peleada/importante" es la votación (proxy: disputada, cobertura, tipo) | A, D | 🟡 parcial (disputada ya existe) |

## 4. Cómo se ensambla (el flujo)
1. Un proyecto entra con sus rasgos **A–D**.
2. El **contexto E** se le pega por fecha.
3. Con **B (tema)** y **C (origen)** se buscan las **derivadas F**: la posición esperada de
   cada bloque y el presentismo esperado de cada legislador PARA ESTE proyecto.
4. Eso alimenta las tres piezas: **embudo** (A+D+E → ¿llega al recinto?), **asistencia**
   (F → ¿quién viene?), **posición de bloque** (F → ¿cómo vota cada bloque?).
5. El **agregador** (ya construido) toma posición + asistencia + desvío y devuelve
   `P(sanción)` como distribución.

## 5. Estado y orden de construcción sugerido
1. **Correr el agente de taxonomías** (B): sin tema, nada de F se puede condicionar. Es el
   desbloqueo #1. (Falta: API key o clasificar una muestra a mano para validar.)
2. **Regla `origen` oficialismo/oposición por fecha** (C): barata, alto valor para asistencia.
3. **Ingesta del ICG Di Tella** (E): serie mensual de UTDT → "gravedad presidencial".
4. **Derivadas condicionadas** (F): recién con B–E se puede recalcular la posición de bloque
   por tema y el presentismo condicionado (escalón 2 de asistencia).
5. Calendario electoral → `proximidad_electoral` y `es_anio_electoral`.

## 6. Notas
- **Oficialismo por fecha:** definir con una tabla presidente→espacio y sus aliados por
  período (reusar los cortes de gobierno de `datos/export`). Un bloque es "oficialista" si
  pertenece a la coalición de gobierno vigente ese día.
- **ICG Di Tella:** índice mensual de la Universidad Torcuato Di Tella; hay que ingerir la
  serie histórica y actualizarla (fuente a confirmar; posible scraping/planilla). Entra como
  variable de contexto, igual para todos los proyectos de un mes.
- **Nada de esto reemplaza al agregador ya hecho:** lo hace específico. Hoy el agregador usa
  la posición de bloque OBSERVADA; el objetivo es proyectarla desde estos rasgos para
  proyectos que todavía no se votaron.
- **Contrato:** cuando se implemente, la salida es una tabla `features_proyecto` (una fila
  por `denominador`) y una `features_votacion_bloque` (una fila por `acta_id`×`bloque`),
  que consumen el embudo, la asistencia y el agregador. Congelar ese contrato requerirá un
  ADR (afecta a varios módulos).
