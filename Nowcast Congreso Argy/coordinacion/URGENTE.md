# 🔴 URGENTE — lo primero que se lee y se resuelve en CADA sesión

> **Regla de la casa (CLAUDE.md):** cualquiera del equipo — persona o Claude —
> abre este archivo **al empezar**, antes de reclamar tarea. Si hay algo acá, se
> resuelve o se decide explícitamente postergarlo (dejando dicho por qué).
> Nada se toca "después": lo que está acá bloquea o ensucia trabajo de otros.
>
> **Cómo usarlo:** al detectar algo urgente, se agrega un bloque con fecha, quién
> lo detectó, qué hay que hacer y por qué es urgente. Al resolverlo se BORRA de
> acá (queda el registro en `ESTADO-DEL-PROYECTO.md`, que es la bitácora
> permanente). Este archivo debería estar vacío la mayor parte del tiempo.

---

## 0. Revisar las VARIABLES del embudo — hay señales que no cierran
**Detectado:** 2026-07-31 · **Franco** · **bloquea: confiar en el número que sale**

Franco marcó que **varias variables del modelo no le cierran**. Revisar el set
completo antes de seguir construyendo encima. Lo que ya sabemos que está raro:

| variable | coef. | por qué no cierra |
|---|---:|---|
| `n_giros` / `multi_comision` | **1,35 / 1,45** | son **los dos rasgos más fuertes del modelo**, por encima de quién lo firma. ¿Es causal o proxy? Un proyecto girado a más comisiones puede ser "más importante" (y por eso avanza) o **más difícil** (más vetos). El signo positivo dice lo primero; la intuición legislativa diría lo segundo. **Sospecha fuerte de leakage sutil:** los giros pueden ampliarse *después* de presentado, y entonces el rasgo estaría mirando el futuro. |
| `autor_tasa_hist` | 0,61 | correlaciona **0,874** con `origen_ejecutivo` (el autor del PE *es* el presidente). Se lleva todo el crédito y deja a `origen` y `lider` en ~0. |
| `lider` | **‑0,03** | **negativo**, cuando la tasa cruda de líderes es 6x la de no-líderes. Artefacto de la colinealidad de arriba. |
| `origen_ejecutivo` | 0,04 | ~nulo, con tasas crudas de **78,8% vs 1,4%**. Idem. |
| `mes` | ‑0,04 | tratado como **número continuo** (enero=1 … diciembre=12): implica que diciembre es "12 veces enero". Debería ser categórico o, mejor, "días hasta el fin del período de sesiones". |
| `anio_electoral` | ‑0,06 | definido como `anio % 2 == 1`. Correcto para Argentina, pero no distingue **antes/después de la elección** dentro del mismo año, que es cuando cambia el comportamiento. |

**Qué hacer:** auditar una por una (definición, signo esperado vs. obtenido,
correlaciones cruzadas), **priorizando el chequeo de leakage en `n_giros`** — si
los giros se amplían después de presentado, el rasgo más importante del modelo
está contaminado y todo el skill 0,36 queda en duda. Verificable con
`expedientes_movimientos` (fecha de cada giro vs. fecha de presentación).

---

## 1. Conectar el ICG (Di Tella) al modelo
**Detectado:** 2026-07-31 · **Franco** · **bloquea: que el modelo vea contexto político**

`variables/proyecto/src/ingesta_icg.py` **está escrito y nunca se corrió**. No
existe `variables/proyecto/data/icg_mensual.csv` y ningún módulo lo importa
(`grep icg` en embudo / ensemble / origen_lider = vacío).

**Por qué importa:** hoy **todas** las variables del embudo son procedimentales
(comisiones, autor, calendario). El ICG sería **la única señal de contexto
político**. Es plausible que explique lo que hoy no se explica: el PE convierte
87,3% con CFK y **41,7% con Milei** — el modelo no tiene con qué distinguir un
proyecto mandado en un pico de confianza de otro mandado en un piso.

```bash
pip install -r variables/proyecto/src/requirements.txt
python variables/proyecto/src/ingesta_icg.py          # serie completa
python variables/proyecto/src/ingesta_icg.py ultimo   # actualización mensual
```
Después: sumar `icg` (y `icg_delta_3m`, que probablemente importe más que el nivel)
a `construir_features` y **medir el skill con y sin** — igual que se hizo con
`origen`/`lider`, que aportaron +0,020.

⚠️ Cuidado con el leakage: usar el ICG del mes **anterior** a la presentación.

---

## 2. Padrón: pasar a la nómina oficial de HCDN + que el bot vigile las altas y bajas
**Detectado:** 2026-07-31 · **Franco** · **bloquea: exactitud de las bancas**

El padrón da **256 de 257** (falta Pitrola, con tramo `2026-04-27 → 2026-04-27` en
la API; también falta Matzkin). Se probó repararlo y da **278** o **263 con Buenos
Aires en 74 sobre 70**: la fuente no distingue quién asumió de quién cesó. Detalle
completo en el docstring de `datos/padron/src/bajar_nomina.py`.

**(a) Fuente correcta:** la **nómina oficial de HCDN** en vez de
`api.argentinadatos.com`. `ingesta_padron.py` ya acepta ese formato (alias
`DesignacionLegal`/`CeseLegal` entre otros): es cambiar el bajador, no el módulo.

**(b) Idea de Franco — que el bot la vigile.** Las bancas cambian todo el año por
renuncias, licencias, fallecimientos y reemplazos, y hoy nos enteramos de casualidad.
Agregar al bot una corrida **periódica** (semanal o mensual; no hace falta diaria)
que baje la nómina y **compare contra el padrón versionado**, avisando:
- altas nuevas (asumió alguien),
- bajas (cesantías, renuncias),
- cambios de bloque (los pases entre bloques son señal política en sí misma),
- y **el total de bancas ≠ 257 / 72**, que es la alarma más barata que tenemos.

Mismo patrón que `votaciones.py`: estado en `estado_bot.json`, idempotente, commit
solo si hay diferencias. **Es la versión "padrón vivo" de lo que ya hacemos con
expedientes y votaciones** — cierra la última pata que sigue dependiendo de que
alguien se acuerde.

---

## 3. ⚠️ SENADO sin bloques desde el 10-dic-2025 (queda del incidente de las 229 actas)
**Detectado:** 2026-07-31 · Claude+Franco · **bloquea: `P(mayoría)` en el SENADO**

✅ **Resuelto el 31-07:** las 229 actas se ingestaron. La canónica pasó de 5.333 a
**6.231 actas** (+898) y de 834.749 a **1.016.632 votos**; llega al 25-06-2026
(Diputados) y 16-07-2026 (Senado). Se creó `datos/padron/src/bajar_nomina.py`: el
proyector devolvía **383 bancas sobre 257** por sumar los padrones de antes y
después del recambio, y ahora da **256 con `_bancas_de: "padron"`**. El bot ya trae
votaciones (`datos/bot_recoleccion/src/votaciones.py`, en el workflow diario).

❌ **LO QUE QUEDA — el Senado 2026 está 100% SIN BLOQUE** (6.192 votos). El padrón
curado `datos/senado/data/padron_bloques_senado.csv` **termina el 2025-12-09**: los
senadores que asumieron el 10-dic-2025 no tienen bloque asignado.

**Por qué no se resolvió automáticamente:** ninguna fuente publica el *bloque
parlamentario* del Senado en formato usable.
- `api.argentinadatos.com/v1/senado/senadores` y el listado oficial dan **la alianza
  por la que ingresó**, que no es el bloque (Atauche entra por el Partido Renovador
  Federal y bloquea en LLA).
- `senado.gob.ar/senadores/listados/agrupados-por-bloques` da bloque + **cantidad**
  de integrantes, no los nombres, y anida sub-tablas de asesores — **es la página
  que el 30-07 nos hizo leer 123 bloques falsos**. Tocarla sin los 3 filtros
  anti-staff de `scrape_jefes_bloque.py` es repetir el error.

**Camino recomendado (el que ya usa el módulo y está validado):** anexo de Wikipedia
del período 2025-2027 → `datos/senado/src/bajar_anexos_wiki.py` +
`padron_bloques.py`, que ya parsean ese formato. Alternativa: curar a mano 72 filas
(hay precedente: `padron_manual_2015_2017.csv`).

**Mientras tanto:** Diputados está sano (0,5% sin bloque en 2026) — el nowcast de
Diputados es utilizable, el del Senado no.

---

## 4. Validar 15 filas MEDIA del roster de jefes (equipo)
**Detectado:** 2026-07-30 · Claude+Franco · **bloquea: confiar en `lider_jefe_bloque`**

> **Prioridad rebajada el 31-07.** Medido el efecto real, `lider_jefe_bloque` aporta
> **1,25x** (no el 7x que se creía): el jefe de bloque es *aceite del motor*, no
> propositor. Estas 15 filas siguen valiendo para interpretabilidad y para el Mapa
> de Influencia, pero **ya no contaminan una señal predictiva fuerte**. Se resuelve
> después del padrón del Senado.

En `variables/proyecto/data/jefes_bloque.csv` hay **15 filas con confianza
MEDIA** (marcadas "VALIDAR"/"REVISAR" en la nota): son jefaturas inferidas de
contexto, no confirmadas por fuente explícita.

**Prioridad por volumen de proyectos que aportan:**

| Nombre | Bloque | Período | Aporta |
|---|---|---|---|
| FERRARO, MAXIMILIANO | Coalición Cívica | 2019– | 140 |
| CAMAÑO, GRACIELA | Frente Renovador / UNA | 2015-2019 | 124 |
| DEL CAÑO, NICOLÁS | Frente de Izquierda | 2014– | 101 |
| PINEDO, FEDERICO | PRO | 2013-2019 | 76 |
| + 11 filas menores | (Losada, Atauche, Massa, Ciciliani, Zamora, Thomas, Mayans/FNyP, Fernández Sagasti/UC, Pichetto/etiqueta "Justicialista") | | |

**Caso especial — Del Caño:** el FIT **rota** la jefatura entre PTS y PO;
probablemente requiera tramos más finos que una fila única.

**Por qué urgente — el caso Bianchi:** el 30-07 se detectó que
"BIANCHI, IVANA MARÍA" figuraba como jefa de Compromiso Federal aportando **610
proyectos (27% de la señal)**. La investigación mostró que **no presidía el
bloque**: era la diputada con más proyectos de toda la Cámara en 2017 (240), o
sea el perfil de `lider_alto_productor` — la señal se habría **duplicado a sí
misma disfrazada de otra**, rompiendo la interpretabilidad ("el nowcast explica
por qué"). Una sola fila mal puesta contaminó cientos de casos. Estas 15 tienen
el mismo riesgo.

**Cómo validar:** buscar fuente explícita ("presidente/jefe del bloque X"),
actualizar `confianza` a ALTA con la fuente, o eliminar la fila dejando el
motivo como comentario `#` en el propio CSV (como se hizo con Bianchi).
