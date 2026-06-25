# Premortem (validado) — Nowcast-Congreso · Transcripción v2

**Fecha:** 25-jun-2026 (revisión con investigación de validación)
**Objeto:** Sistema B2B que estima P(aprobación de un proyecto de ley) en el Congreso argentino, agregando la probabilidad individual de voto de cada legislador según atributos del proyecto.
**Audiencia:** Clientes B2B amplios — consultoras de asuntos públicos, clientes individuales, empresas, fondos macro, prensa especializada.
**Éxito:** MVP local que predice con precisión *y valor accionable* suficiente para que al menos un cliente pague, proyectable a la nube sin re-arquitectura.

**Premisa:** Pasaron 6 meses. Se construyó, se intentó vender, fracasó. Reconstruimos por qué.

> Esta versión **revalida** el premortem original (`premortem-transcript-20260625.md`) contra fuentes y agrega tres modos de fallo nuevos surgidos de la investigación: (9) trampa del baseline mal medido, (10) sobre-ingeniería v2.1 vs MVP, (11) mercado B2B demasiado amplio.

---

## Lo que la validación confirmó

| Afirmación del doc | Veredicto | Evidencia |
|---|---|---|
| CKAN HCDN tiene votaciones nominales, expedientes, legisladores, vivos | **Confirmado** | Dataset `votaciones_nominales` períodos 129–137 (137 = período en curso), `expedientes`, `legisladores/composición actual` activos en datos.hcdn.gob.ar |
| Senado menos estructurado | **Confirmado** | senado.gob.ar/micrositios/DatosAbiertos + argentinadatos.com como agregador |
| Drift por recambio | **Confirmado y agravado** | Elecciones legislativas 26-oct-2025; nueva composición asumió ~10-dic-2025. El modelo entrenado con la cámara anterior ya está parcialmente desactualizado |
| Consultoras cualitativas dominan, sin capa cuantitativa | **Confirmado** | EGES (20+ años, reportes semanales), Directorio Legislativo (desde 2000), CIPPEC — todas cualitativas |
| Baseline de bloque >90% | **REFUTADO / mal calibrado** | Cohesión académica: Diputados 76,9%, Senado 74,3% (UDESA). El >90% solo surge contando votaciones cuasi-unánimes |

---

## Razones de fallo (premortem en bruto, v2)

Se mantienen las 8 originales (datos ex-post/sesgo de selección; disciplina de bloque; drift; pipeline ETL devora el proyecto; mercado cubierto por consultoras; éxito no verificable a tiempo; riesgo reputacional/legal; scope creep sin pagador) y se agregan:

9. **Trampa del baseline mal medido.** Si se mide la heurística de bloque sobre *todas* las votaciones (incluidas las unánimes) da ~90%+ y se "mata" el producto por error; si se mide solo sobre votaciones disputadas da ~77% y hay lugar real para el ML. Medir mal el piso lleva a la decisión estratégica equivocada en ambas direcciones.
10. **Sobre-ingeniería v2.1 antes de validar.** El `INSTRUCTIVO-MAESTRO` describe 5 servicios en Oracle Cloud, Context Engine con LLM batch nocturno, conformal prediction, calibración Beta, ensemble jerárquico — todo antes de tener un solo cliente o un baseline medido. El tiempo se va en arquitectura, no en señal.
11. **Mercado B2B demasiado amplio.** Apuntar a consultoras + individuos + empresas + fondos a la vez diluye el producto: cada segmento quiere algo distinto (la consultora quiere explicabilidad, el fondo quiere anticipación, el individuo quiere precio bajo). Sin un comprador-ancla, no hay foco de producto ni de pricing.

---

## Análisis profundo (modos nuevos)

### 9. Trampa del baseline mal medido
- **Historia:** El equipo corre "votá con tu bloque" sobre el dataset completo, obtiene 91%, concluye "el ML no tiene margen" y pivotea a un dashboard descriptivo. Pero el 91% estaba inflado por cientos de votaciones de trámite unánimes. En el subconjunto que importa —votos disputados— el piso era 77% y el ML cruzado habría aportado 8-12 puntos de valor real. Se descartó el núcleo del producto por un artefacto de medición.
- **Supuesto subyacente:** "accuracy global = dificultad real del problema".
- **Señales tempranas:** baseline reportado sin separar votaciones unánimes de disputadas; ausencia de un Rice/cohesion index por bloque; no se reporta accuracy condicionado al subconjunto contestado.

### 10. Sobre-ingeniería v2.1 antes de validar
- **Historia:** Se monta el split de repos, el Context Engine, la calibración conformal y el deploy en Oracle ARM siguiendo el instructivo v2.1. Tres meses después no hay un número de baseline ni un cliente, pero sí infra que mantener. El proyecto muere por agotamiento de scope, no por falta de señal.
- **Supuesto subyacente:** "la arquitectura final documentada es el plan de construcción".
- **Señales tempranas:** commits de infraestructura/MLOps antes del primer notebook de baseline; gasto cloud > $0 sin cliente; conformal/Beta calibration en el backlog antes de medir el piso de bloque.

### 11. Mercado demasiado amplio
- **Historia:** El pitch intenta servir a todos. La consultora pide el "por qué" auditable; el fondo pide alerta T+0 anticipada; el individuo no paga el ticket B2B. Cada demo se reescribe para el interlocutor de turno y ninguna cierra. Seis meses, cero contratos, producto sin identidad.
- **Supuesto subyacente:** "un mismo nowcast sirve a todos los compradores".
- **Señales tempranas:** pipeline comercial con 4 buyer personas distintas; pricing sin definir; cada reunión pide una feature nueva.

---

## Síntesis v2

- **Fallo más probable:** sobre-ingeniería (10) combinada con pipeline ETL (4) — se construye mucho antes de medir el baseline y antes de tener pagador.
- **Fallo más peligroso:** sesgo de selección (1) — un nowcast que no aplica al universo real de proyectos y nadie lo nota hasta una decisión cara del cliente.
- **Supuesto oculto principal:** el resultado de una ley es función de los *atributos del proyecto*; en realidad es función de la negociación de cúpula, exógena a los datos abiertos. El modelo captura disciplina de bloque, no el deal político.
- **Corrección estratégica más importante:** medir el baseline de bloque **separando votaciones unánimes de disputadas** en la semana 1, antes de construir nada. Ese único número (piso en el subconjunto disputado) decide si hay producto.

### Plan revisado
1. **Semana 1, antes de cualquier ML o infra:** baseline de bloque medido en dos cortes (todas / disputadas) + tamaño del sesgo de selección (% de proyectos que llegan a votación nominal).
2. **Elegir UN comprador-ancla** (recomendado: consultoras de asuntos públicos como augmentation) y diseñar el producto para ese, no para los cuatro.
3. **Congelar la arquitectura v2.1.** Notebooks locales hasta tener (a) baseline medido y (b) 1 LOI/piloto pago. Cloud es decisión comercial, no técnica.
4. **Modelar el embudo completo** (presentado→comisión→dictamen→recinto), no solo el voto final.
5. **Encuadre de producto:** vender radar + pivotes + explicabilidad; el número P(aprobación) es un feature interno, no el titular.

### Checklist pre-lanzamiento
1. Baseline de bloque medido en cortes todas/disputadas, con el piso del subconjunto disputado fijado como benchmark.
2. % de proyectos con votación nominal cuantificado (tamaño del sesgo de selección).
3. ID estable que cruce legislador↔bloque↔proyecto↔votación verificado (o costo de entity resolution presupuestado).
4. 1 comprador-ancla elegido y 1 LOI/piloto pago antes de gastar en nube.
5. Términos de uso B2B + disclaimer antes de exponer predicciones nominales por persona.
