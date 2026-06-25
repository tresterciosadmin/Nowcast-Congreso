# Lecciones de GovTrack y adopciones para el Nowcast Argentino
**Fecha:** 2026-05-28
**Fuentes estudiadas:** github.com/govtrack (28 repos), github.com/unitedstates/congress (scrapers oficiales), govtrack.us-web (frontend Django), página de datos de GovTrack.

---

## 1. Por qué GovTrack es la referencia correcta

GovTrack lleva operativo desde 2004. Fue construido por Josh Tauberer (JoshData en GitHub) y la Sunlight Foundation, y se mantiene activo hoy con un equipo pequeño y trece años de continuidad operativa. Procesa todos los proyectos de ley del Congreso estadounidense, sus votaciones nominales, las composiciones de comisiones, los perfiles de legisladores y produce predicciones de probabilidad de sanción. Es exactamente el problema que estamos resolviendo, en una escala mayor, con catorce años más de aprendizaje acumulado.

Su valor para nosotros no está en copiar el código (Django de 2010 sobre Vagrant es una decisión defensiva, no de vanguardia), sino en absorber las decisiones arquitectónicas y operativas que les permitieron sobrevivir trece años con un equipo mínimo.

---

## 2. La lección arquitectónica más importante: separar el dato del análisis

**Lo que hace GovTrack:** existen dos proyectos distintos, mantenidos por separado.

- `unitedstates/congress` es el pipeline de captura de datos. Es de dominio público (CC0), tiene mil estrellas, treinta y seis contribuidores, y se mantiene con el esfuerzo conjunto de toda la comunidad de civic tech estadounidense. GovTrack lo usa pero no lo posee.
- `govtrack/govtrack.us-web` es el frontend Django y la lógica analítica propia. Acá vive la base de usuarios, las features comerciales, el modelo predictivo, los reportes.

**Por qué esta separación es estratégica:** al hacer el pipeline de datos público y compartido, GovTrack consigue tres cosas. Primero, otros proyectos (Sunlight Foundation, ProPublica, OpenSecrets) usan el mismo dataset, lo que reduce el costo de mantenimiento para cualquiera. Segundo, cuando una fuente upstream cambia, la corrección la puede hacer cualquier contributor de la comunidad, no solo GovTrack. Tercero, el pipeline se vuelve un activo de infraestructura cívica con valor en sí mismo, y GovTrack queda asociado con haberlo creado.

**Adopción al Nowcast Argentino:** dividir el proyecto en dos capas claramente separadas desde el día uno.

| Capa | Repositorio sugerido | Licencia | Contenido |
|---|---|---|---|
| Datos | `congreso-argy-data` | CC0 (dominio público) | Adapter HCDN, Senado, BORA; canonical resolver de legisladores; cache de PDFs; outputs JSON estructurados |
| Analítica + Producto | `nowcast-engine` | Propietaria | Feature engine, ensemble de modelos, Context Engine, Narrator, dashboard, API comercial |

La capa de datos puede ser publicada en GitHub bajo licencia CC0 desde el inicio. Esto no compromete el modelo de negocio (el activo defendible es el modelo y la calibración, no la limpieza de datos), pero sí construye una posición estratégica: cualquier otro proyecto de civic tech argentino que quiera trabajar sobre Congreso va a usar nuestros datos, validando nuestra autoridad técnica.

---

## 3. Patrón CLI por tipo de dato

**Lo que hace GovTrack:** comando único con sub-comandos.

```
usc-run bills
usc-run votes
usc-run nominations
usc-run committee_meetings
usc-run govinfo --bulkdata=BILLSTATUS
```

Cada sub-comando es un scraper independiente. Cualquier fallo aísla la fuente, no tira al resto. Los datos van a un directorio `data/` con estructura predecible. Las páginas se cachean en `cache/`.

**Adopción:**

```
argcongress-run bills --camara=diputados
argcongress-run bills --camara=senado
argcongress-run votos --periodo=2024
argcongress-run dictamenes --comision=presupuesto
argcongress-run legisladores
argcongress-run atn-tesoro
argcongress-run icg-ditella
argcongress-run boletin --fecha=2026-05-28
```

Esto reemplaza la idea de "9 agentes orquestados" con algo mucho más simple: ocho comandos CLI independientes que el cron del sistema dispara según corresponda. Si un comando falla, los otros siguen. Si necesitás re-procesar una fecha, corrés el comando con `--force`. Es operativamente trivial y debuggable.

---

## 4. Preferir bulk data oficial sobre scraping de la web

**Lo que hace GovTrack:** no scrapea congress.gov. Va al endpoint de bulk data del Government Publishing Office (`usgpo/bill-status`), que es la fuente oficial estructurada en XML, mantenida por el propio Estado, con un contrato de schema más estable que la web.

**Adopción:** esta decisión valida nuestro v2.1 (que ya prioriza `rest.hcdn.gob.ar` y `datos.hcdn.gob.ar` sobre el scraping del frontend HCDN). Pero vale reforzar el principio: **cuando hay tres fuentes para un mismo dato, elegir siempre la más cercana al productor oficial, en formato estructurado, aunque el delay sea mayor.**

Aplicación práctica:
- Para proyectos: `datos.hcdn.gob.ar` (CSV/JSON) antes que `rest.hcdn.gob.ar` (API) antes que scraping del HTML.
- Para votos: dataset oficial del Senado/HCDN antes que reconstruir desde actas en PDF.
- Para ATN: dataset MECON de transferencias antes que parsear BORA.

---

## 5. Modelo de datos: la "persona" como dominio de primera clase

**Lo que hace GovTrack:** el frontend tiene un módulo `person/` dedicado exclusivamente a legisladores como entidades. Cada persona tiene biografía estructurada, historial de partidos, historial de comisiones, estadísticas de patrocinio, registro de votos, foto, pronunciación del nombre, base de datos de misconduct.

**Adopción:** nuestro Canonical Legislator Resolver no es solo una tabla auxiliar. Es un servicio de primera clase con su propio schema. El `Person Service` propuesto:

```
person.canonical_id          # ID inmutable interno
person.dni                   # cuando esté disponible
person.nombre_completo       # ground truth
person.nombres_alternativos  # variantes registradas
person.fecha_nacimiento
person.bloque_actual
person.bloque_historia       # log temporal de bloques
person.distrito
person.camara
person.periodo_inicio
person.periodo_fin
person.comisiones_actuales
person.comisiones_historia
person.sponsorship_stats     # % éxito histórico
person.fidelidad_partidaria  # score actualizable
person.pagerank_actual
person.cluster_ideologico
person.foto_url
person.bio_md                # biografía estructurada
person.pronunciacion         # cuando aplique
```

Cada legislador tiene una página dedicada en el dashboard final con todo este perfil. Es contenido SEO valioso y construye autoridad temática del producto.

---

## 6. Repositorios modulares de datos auxiliares

**Lo que hace GovTrack:** mantienen ocho repos separados de datos curados a mano que complementan el pipeline automatizado:

- `congress-legislators` (YAML maestro de legisladores)
- `historical-committee-membership` (composiciones históricas)
- `caucuses` (membresías de caucus informales)
- `misconduct` (base de datos de inconductas)
- `advocacy-organization-scorecards` (scorecards de ONGs)
- `pronunciation` (pronunciación de nombres)
- `congress-maps` (mapas de distritos)

Todos public domain. Todos en YAML/JSON editable a mano. Todos con historial git.

**Adopción:** mantener nuestros propios datasets curados como repos separados (o como directorios versionados dentro del repo de datos). Sugeridos:

| Dataset | Formato | Equivalente GovTrack |
|---|---|---|
| `legisladores-canonical/` | YAML | congress-legislators |
| `comisiones-historicas/` | YAML | historical-committee-membership |
| `bloques-historicos/` | YAML | (no tiene equivalente; nuestro propio aporte) |
| `interbloques-y-frentes/` | YAML | caucuses |
| `leyes-etiquetadas/` | JSON | (no tiene equivalente; nuestro dataset de validación) |
| `dictamenes-con-disidencia/` | YAML | (no tiene equivalente) |

Estos datasets son donde reside el trabajo manual valioso. Versionarlos en git con commit messages que documenten cambios crea trazabilidad auditable y permite revertir errores específicos.

---

## 7. Compromisos de compatibilidad backward

**Lo que hace GovTrack:** los scrapers tienen un flag `--govtrack` que produce output con IDs y schema retrocompatibles con su histórico. Cuando el upstream cambia, GovTrack puede seguir sirviendo data en el formato viejo sin romper a los usuarios.

**Adopción:** desde el día uno, cada output JSON debe llevar un campo `schema_version`. Cuando cambiemos schema, mantenemos la versión anterior con un converter automático y un período de gracia documentado de noventa días.

```json
{
  "schema_version": "2026.1",
  "expediente": "1472-D-2024",
  "..."
}
```

Esto importa porque los usuarios institucionales (consultoras, fondos) que integren nuestra API contra sus propios sistemas no pueden tolerar breaking changes silenciosos.

---

## 8. Sistema de eventos y suscripciones

**Lo que hace GovTrack:** un módulo `events/` permite a usuarios suscribirse a "trackers" sobre proyectos, legisladores, comisiones, temas. El sistema dispara emails cuando algo relevante ocurre. Es la principal palanca de retención y monetización: usuarios que se suscriben vuelven semanalmente.

**Adopción:** incorporar al roadmap (Fase 5 o post-lanzamiento) un módulo de suscripciones:

- Tracker por proyecto: notificación cuando cambia el predicted_prob, cuando entra a dictamen, cuando se vota.
- Tracker por legislador: notificación cuando firma, vota, cambia de bloque, cambia de comisión.
- Tracker por tema: notificación cuando nuevos proyectos del tema son ingestados.
- Tracker por comisión: agenda semanal de dictámenes esperados.

Implementación mínima: tabla `subscriptions` en Postgres, cron diario que evalúa eventos contra suscripciones, envío de email (servicio gratis tipo Mailtrap free tier o Postmark con tier de USD 10/mes para 10.000 emails). Esto vuelve al producto recurrente y mejora retención.

---

## 9. Módulo de análisis como dominio separado

**Lo que hace GovTrack:** carpeta `analysis/` en el repo del web, donde viven los outputs de análisis estadísticos: predicciones de bills, scorecards, métricas de legisladores. Es servido como API independiente de la lógica de scraping.

**Adopción:** nuestras tablas de la Fase 3.5 (`historical_predictions`, `failure_modes_catalog`, `mu_calibration_curve`, `regime_performance`, `feature_importance_walkforward`) deben vivir en un namespace `analysis.*` y servirse como API independiente. Esto permite que el frontend, terceros, o academia consuman datos analíticos sin tocar la capa de captura.

---

## 10. Documentación de schemas en wiki público

**Lo que hace GovTrack:** mantiene un wiki en GitHub con documentación detallada del schema de cada tipo de dato (`bills`, `votes`, `amendments`, `nominations`, `committee_meetings`, `bill text`). Ejemplos, campos, semántica, edge cases conocidos.

**Adopción:** mantener `docs/schemas/` en el repo de datos, en Markdown, con un archivo por tipo de dato. Cada cambio de schema actualiza el documento. La methodology page pública del producto puede linkear directo a esta documentación.

---

## 11. Humildad sobre la sofisticación del modelo

**Lo que se sabe del modelo de GovTrack:** Tauberer publicó research sobre su modelo predictivo. Es esencialmente una regresión logística con features curadas a mano (rol del autor, número de cofirmantes, comisión de referencia, success rate histórico). Reporta ~90 por ciento de accuracy en proyectos importantes.

**Lección incómoda:** un modelo simple, con features bien curadas, sobre datos limpios, supera a arquitecturas complejas mal calibradas. Nuestra propuesta v2.1 con ensemble + Context Engine + bandas conformal es más sofisticada, pero la sofisticación es costo, no virtud, salvo que se traduzca en mejor calibración o mejor lift contra baselines.

**Adopción operativa:** durante la Fase 3.5 (backtesting), comparar explícitamente nuestro ensemble contra un "baseline GovTrack-style": regresión logística simple con seis a ocho features hand-curated. Si nuestro ensemble no supera al baseline simple por al menos 0.03 de Brier score, hay que considerar simplificar el modelo. La complejidad debe ganarse.

Este "baseline Tauberer" se agrega al checklist de Fase 3.5 como benchmark obligatorio.

---

## 12. Patrón operativo: cron + email alerts

**Lo que hace GovTrack:** crontab simple ejecuta los scrapers en horarios escalonados. Cuando un parser falla, envía un email vía sendmail/msmtp con el contexto del error. Es trivial, robusto, gratis. Llevan trece años con este patrón.

**Adopción:** validamos nuestra decisión de APScheduler/cron sobre frameworks complejos. Agregar email alert via msmtp como segundo canal (Telegram bot es el primero) para fallas de parser. Si Telegram cae, email; si email cae, Telegram. Dos canales, dos proveedores.

---

## 13. Stakeholder positions como módulo de comunidad

**Lo que hace GovTrack:** módulo `stakeholder/` permite a organizaciones registradas postear su posición oficial sobre un proyecto de ley. Sindicatos, NGOs, cámaras empresariales pueden marcarlo "Apoyamos", "Oponemos", "Neutral" con razón documentada.

**Adopción (post-lanzamiento, no Fase inicial):** incorporar un módulo donde organizaciones argentinas verificadas (CGT, UIA, Sociedad Rural, IDEA, FAA, CAME, CRA, ADEPA, AmCham, etc.) puedan registrar posiciones. Esto crea:

- Feature para el modelo predictivo (presión de stakeholders).
- Contenido único en cada página de proyecto.
- Red de instituciones que linkean al sitio.
- Posible vector de monetización (acceso premium para postear posiciones).

No es prioridad inicial, pero arquitecturalmente debe estar contemplado: dejar el schema de `stakeholder_positions` previsto desde el v1.

---

## 14. Caucus / interbloques como dataset curado

**Lo que hace GovTrack:** repo `caucuses` mantiene YAMLs con membresías de caucus (agrupaciones informales transversales: Black Caucus, Climate Solutions Caucus, etc.).

**Adopción:** en Argentina existen agrupaciones políticas informales que no aparecen en el bloque formal y que tienen poder predictivo: por ejemplo el interbloque oficialista informal, los "diálogos" entre bloques, frentes electorales que aún no se formalizaron en bloque parlamentario, agrupaciones temáticas (parlamentarios federales, frente provincial).

Mantener `interbloques-y-frentes/` con archivos YAML editados manualmente capta esa estructura latente que el grafo de cofirmas insinúa pero no explicita. Estos datos alimentan features adicionales del modelo.

---

## 15. Misconduct database como signal de transparencia

**Lo que hace GovTrack:** `misconduct/` es una base de datos pública (CC0) de inconductas y acusaciones a legisladores estadounidenses. Es un señal fuerte de transparencia institucional.

**Adopción:** para Argentina existe equivalente útil: pliegos pendientes, denuncias judiciales en curso, citaciones a indagatoria, sanciones de la cámara, ausencias prolongadas sin licencia. Mantener `incidencias-legislativas/` como dataset CC0 con criterios estrictos de inclusión (fuentes citables, no rumores) construye un activo de credibilidad y SEO. Feature para el modelo: legisladores con incidencias activas pueden tener performance distinto en votaciones.

---

## 16. Resumen de adopciones priorizadas

### P0 (incorporar antes de empezar Fase 0)

1. **Separar el proyecto en dos repos:** `congreso-argy-data` (CC0) y `nowcast-engine` (propietario).
2. **Adoptar patrón CLI** `argcongress-run <data-type>` para cada scraper.
3. **`schema_version` en todos los outputs JSON.**
4. **Mantener `legisladores-canonical/` como dataset YAML versionado** desde el día uno.
5. **Agregar `baseline-tauberer` al checklist de Fase 3.5** como modelo simple de referencia obligatoria.

### P1 (incorporar durante Fase 1-3)

6. **Person Service de primera clase** con todos los campos enumerados en sección 5.
7. **`comisiones-historicas/`, `bloques-historicos/`, `interbloques-y-frentes/`** como datasets YAML versionados.
8. **Module `analysis/` separado** sirviendo outputs de Fase 3.5 vía API.
9. **`docs/schemas/`** con documentación markdown de cada tipo de dato.
10. **Email alerts via msmtp** como segundo canal de alertas operativas.

### P2 (post-lanzamiento)

11. **Sistema de suscripciones/trackers** por proyecto, legislador, comisión y tema.
12. **Módulo `stakeholder_positions`** para organizaciones registradas.
13. **`incidencias-legislativas/`** como dataset CC0 con criterios estrictos.

---

## 17. Lo que NO copiamos de GovTrack

Para evitar arrastrar deuda técnica innecesaria:

- **No Django.** Stack pesado, conceptualmente sobrecargado para nuestro caso. FastAPI + HTMX es más eficiente.
- **No Xapian/Solr/Haystack.** PostgreSQL full-text search alcanza para v1.
- **No Vagrant.** Docker Compose ya es nuestro target.
- **No nginx + supervisor + gunicorn + uwsgi.** Caddy + Granian/Uvicorn es más simple.
- **No Python 2 legacy.** Python 3.11+ desde el inicio.

La arquitectura es de 2010-2013. Lo que tomamos son sus decisiones operativas y de estructura de datos, no el stack tecnológico.

---

## 18. Impacto en el roadmap

Las adopciones P0 modifican la Fase 0 e incorporan trabajo adicional menor pero estructural. Roadmap revisado:

| Fase | Semanas | Cambio respecto del v2.1 |
|---|---|---|
| 0 | 1-2 (+1 semana) | Agregar: split en dos repos, scaffolding CLI argcongress-run, `legisladores-canonical/` inicial con ~330 legisladores actuales, `docs/schemas/` esqueleto |
| 3.5 | 10-13 | Agregar al gate: ensemble debe superar baseline-Tauberer por ≥0.03 Brier score |
| Otras | sin cambios | |

Total: una semana adicional en Fase 0. El resto se absorbe sin extender el roadmap.

---

## 19. Cita y atribución

Este documento debe citarse en la methodology page pública del producto como reconocimiento explícito a la inspiración recibida de GovTrack.us, Josh Tauberer y la comunidad de civic tech estadounidense. La transparencia sobre fuentes intelectuales refuerza credibilidad y se alinea con los compromisos de transparencia del proyecto.
