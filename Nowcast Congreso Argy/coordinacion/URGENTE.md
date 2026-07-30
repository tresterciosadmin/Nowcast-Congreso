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

## 1. Re-correr los módulos tras traer cambios de datos (para Valle)
**Detectado:** 2026-07-30 · Claude+Franco · **bloquea: medición del efecto líder**

Tres señales de `variables/proyecto` cambiaron y **el código llega con el pull,
pero el efecto NO**: hay que ejecutar para que se note.

```bash
python variables/proyecto/src/origen_lider.py     # features_proyecto con las 3 señales corregidas
python variables/embudo/src/embudo.py all         # re-mide el efecto por origen/líder
```

**Por qué urgente:** el **efecto 7x del líder** se midió cuando la señal era
"haber sido jefe alguna vez" + alto productor. Ahora es distinta: jefes
*time-aware* (‑81% de falsos positivos), 46 presidentes de comisión reales
(antes 0) y roster bicameral 2002-2026. **La conclusión vigente está calculada
sobre datos que ya no existen.**

**Antecedente que justifica la regla:** el 23-07 el equipo diagnosticó el linaje
del Senado sobre un parquet anterior a nuestro fix del 11-07 y construyó un
corrector que hoy **no cambia ni una fila** (verificado sobre 831.677). Trabajo
perdido por leer datos viejos, no por error de criterio.

---

## 2. Validar 15 filas MEDIA del roster de jefes (equipo)
**Detectado:** 2026-07-30 · Claude+Franco · **bloquea: confiar en `lider_jefe_bloque`**

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
