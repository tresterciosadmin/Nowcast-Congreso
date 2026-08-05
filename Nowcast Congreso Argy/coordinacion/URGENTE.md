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

## 1. Confirmar el padrón contra la API (la regeneración ya se aplicó)
**Detectado:** 2026-08-04 · Claude · **bloquea: que `P(mayoría)` cuente bien**

El vigilante nuevo detectó que el padrón versionado había quedado viejo: faltaban
**Matzkin** y **Pitrola** (los dos que el 31-07 dábamos por perdidos) y sobraba
**Ravier**. **Ya se regeneró y da 257 exacto** (el anterior quedó en
`padron_diputados.ANTES-2026-08-04.csv.bak`).

**Lo que falta:** esa regeneración salió del crudo en disco, porque el entorno de
Claude no llega a internet. Hay que confirmarla contra la API, que es la fuente
viva:

```bash
python datos/padron/src/bajar_nomina.py diputados --padron
python datos/padron/src/vigilar_padron.py --camara ambas   # verificar que quede limpio
```

Es una corrida corta y sin riesgo. Después de hacerla, este ítem se borra.

---

## 2. Validar 15 filas MEDIA del roster de jefes (equipo)
**Detectado:** 2026-07-30 · Claude+Franco · **bloquea: confiar en `lider_jefe_bloque`**

> **Prioridad rebajada el 31-07.** Medido el efecto real, `lider_jefe_bloque` aporta
> **1,25x** (no el 7x que se creía): el jefe de bloque es *aceite del motor*, no
> propositor. Estas 15 filas siguen valiendo para interpretabilidad y para el Mapa
> de Influencia, pero **ya no contaminan una señal predictiva fuerte**.

En `variables/proyecto/data/jefes_bloque.csv` hay **15 filas con confianza
MEDIA** (marcadas "VALIDAR"/"REVISAR"): jefaturas inferidas de contexto, no
confirmadas por fuente explícita.

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

**Por qué sigue acá — el caso Bianchi:** el 30-07 se detectó que
"BIANCHI, IVANA MARÍA" figuraba como jefa de Compromiso Federal aportando **610
proyectos (27% de la señal)**. No presidía el bloque: era la diputada con más
proyectos de toda la Cámara en 2017 — la señal se habría **duplicado a sí misma
disfrazada de otra**. Una sola fila mal puesta contaminó cientos de casos.

**Cómo validar:** buscar fuente explícita ("presidente/jefe del bloque X"),
actualizar `confianza` a ALTA con la fuente, o eliminar la fila dejando el
motivo como comentario `#` en el propio CSV (como se hizo con Bianchi).

---

## ✅ Resueltos el 2026-08-04 (el detalle está en ESTADO)

- **~~Conectar el ICG al modelo~~** — el CSV ya existía (296 meses); faltaba
  enchufarlo. Hecho, rezagado un mes. Aporta **+0,003** de skill: real y
  consistente, pero una séptima parte de lo que dio origen/líder. **La deriva a
  3 meses pesa 6x más que el nivel** (hipótesis de Franco, confirmada).
- **~~Padrón oficial + padrón vivo~~** — `vigilar_padron.py` + workflow semanal.
  El padrón ya se regeneró a 257; queda confirmarlo contra la API (ítem 1).
- **~~SENADO sin bloques desde el 10-dic-2025~~** — **estaba mal diagnosticado.**
  `datos/padron/data/padron_senado.csv` tiene los **72 senadores vigentes con
  bloque y linaje**, incluidos los 24 que asumieron el 10-dic. El archivo no
  llegaba al repo porque el `.gitignore` se lo comía (cuarta vez que ese bug
  esconde trabajo; primera que genera una urgencia falsa). Excepción agregada.
  **No hay que curar 72 filas a mano ni ir a Wikipedia.**
  ⚠️ **Queda un residuo real:** la INGESTA (`datos/argentinadatos/src/to_canonical.py`)
  todavía lee el padrón viejo `datos/senado/data/padron_bloques_senado.csv`, que
  termina el 2025-12-09 — por eso los votos del Senado 2026 entran a la canónica
  sin bloque. El fix es apuntarla también a `padron_senado.csv`, mandate-aware.
  Es la regla que el propio equipo escribió el 30-07: **los huecos se tapan en la
  entrada, no en cada consumidor.**
