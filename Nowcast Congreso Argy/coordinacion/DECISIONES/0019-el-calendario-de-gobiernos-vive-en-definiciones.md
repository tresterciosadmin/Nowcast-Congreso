# ADR-0019 — El calendario de gobiernos vive en `definiciones.py` (y el del ICG NO)

**Fecha:** 2026-09-06 · **Estado:** APLICADO · **Decide:** Franco · **Extiende:** ADR-0014

## Contexto

Las ventanas de recambio presidencial (10-dic) estaban escritas **tres veces**:

| dónde | forma | comentario que tenía |
|---|---|---|
| `variables/bloque/src/bloque.py` | `_GOBIERNOS` = (desde, hasta, nombre) | *"MANTENER SINCRONIZADAS con origen_lider y origen_por_acta"* |
| `variables/proyecto/src/origen_lider.py` | `GOBIERNOS` = (desde, hasta, oficialistas) | *"Fechas de recambio presidencial (10-dic)"* |
| `variables/proyecto/src/origen_por_acta.py` | `GOBIERNO_NOMBRES` | *"ALINEADOS 1:1 con las ventanas de GOBIERNOS"* |

Las tres con la misma frontera y el mismo control: que alguien se acuerde. Es
literalmente el caso que el ADR-0014 describe, y llevaba meses así.

**Lo que obligó fue el cuarto consumidor.** El guard de era del récord individual
(ADR-0018) necesita saber en qué era cae la fecha del nowcast. Si el récord se corta
por una lista y `proyectar_postura` por otra, **el número no cierra y nada falla** — que
es exactamente cómo fallan las cosas en este repo.

## Decisión

`definiciones.GOBIERNOS` es la única frontera. Expone además `gobierno_por_fecha(fecha)`
y `era_de(fecha)`. Los tres módulos la consumen y **re-exportan sus nombres con la misma
forma** (`_GOBIERNOS` sigue siendo (desde, hasta, nombre), `GOBIERNOS` sigue siendo
3-tuplas), así que ningún consumidor aguas abajo se entera.

**La carga útil se queda en su módulo.** Quién era oficialista en cada ventana es lógica
de `origen_lider` y ahí queda, en `OFICIALISTAS`, alineada 1:1. Lo compartido es la
frontera, no la política.

## Lo que NO se unificó, y es la mitad de la decisión

`variables/proyecto/src/icg_contexto.py::GOBIERNOS` se llama igual, tiene fechas de
recambio y **no es la misma regla**:

| | calendario compartido | el del ICG |
|---|---|---|
| ventanas | 4 | **9** |
| arranca en | 1900 (todo lo pre-2015 junto) | **De la Rúa (1999)** |
| CFK | una sola ventana | **partida en I y II** |
| tramos raros | ninguno | **"Crisis", 11 días** |
| cierre de ventana | el día del recambio, **exclusivo** (`2019-12-10`) | el día **anterior, inclusive** (`2019-12-09`) |

El del ICG necesita mandatos presidenciales a resolución mensual para calcular el neutro
del índice; el compartido necesita las cuatro eras que cambian **la composición de la
cámara**. Unificarlas sería el error que `definiciones.py` advierte en su sección "Qué va
acá y qué NO": *"Dos parsers de fecha que leen formatos distintos NO son la misma regla:
son dos reglas que se llaman parecido. Unificarlas es peor que dejarlas."*

`tests/test_definiciones_compartidas.py::test_icg_contexto_NO_es_la_misma_lista_y_no_se_unifica`
existe para que la próxima persona que las vea juntas no las "arregle".

## Verificación

El refactor no puede haber movido una frontera, así que el test compara contra las
**literales viejas transcritas del código del 04-09**, no contra sí mismo:

- `bloque._GOBIERNOS` y `origen_lider.GOBIERNOS` idénticas a las literales.
- `gobierno_por_fecha` de las tres implementaciones da lo mismo que la copia vieja en 14
  fechas, incluidos los dos bordes de cada ventana (`2015-12-09` / `2015-12-10`), fuera
  de rango, `None`, `""` y basura.
- `origen_por_acta.GOBIERNO_NOMBRES` **es el mismo objeto** que el de `definiciones`
  (identidad, no igualdad — el mismo criterio que usa el ADR-0014).

## Consecuencias

- Un cambio de frontera es una línea, no cuatro claims de módulo.
- `definiciones.py` gana su primera regla que no es una función de fechas ni una
  constante: una tabla. Sigue cumpliendo la regla 2 del archivo (≥2 consumidores: son 4).
- Queda pendiente lo mismo de siempre: si aparece un quinto consumidor con **otra**
  granularidad, la respuesta correcta es un archivo nuevo, no estirar éste.
