# ADR-0018 — El récord individual se corta por ERA, y la era sale de la fecha del nowcast

**Fecha:** 2026-09-06 · **Estado:** PRENDIDO POR DEFECTO (06-09, decisión de Franco) · **Decide:** Franco

## Contexto

El 98,0% de las predicciones del motor sale del récord individual $\text{rec}_i$. El censo
del 03-09 midió que su skill cae de ~0,20 en las eras buenas a **+0,024 en la era vigente**
y **−0,011 en 2015-2019**. Los dos valles arrancan en un recambio de gobierno (dic-2015 y
dic-2023): tras un recambio, el récord acumulado describe **otra cámara**.

## Lo que estaba mal en el diagnóstico

URGENTE 9 decía que `proyectar_postura` ya tenía el guard y que el récord individual **no**.
Al ir a implementarlo apareció que **sí lo tiene**, con una fecha clavada:

```python
def alineacion_individual(votos, origen_map, origen, era_desde="2023-12-10", hasta=None):
```

Para el gobierno vigente esa fecha **es** la era correcta. Para atrás, `fecha >= 2023-12-10`
y `fecha <= hasta` no se cruzan, y los 478 legisladores caen enteros a la rama de bloque:

| nowcast al | gobierno | con récord propio |
|---|---|---:|
| 2026-06-01 | Milei | 478 |
| 2022-06-01 | A. Fernández | 0 |
| 2018-06-01 | Macri | 0 |
| 2013-06-01 | Kirchner | 0 |

**Y hay un segundo hallazgo, más incómodo:** `baseline_voto_individual` —el harness que
produjo el número que motivó este ítem— calcula el récord con `shift(1).expanding()` sobre
**toda** la historia, sin condicionar por origen. O sea que **medía un modelo distinto del
que corre**. Sobre los mismos 475 legisladores al 2026-06-01 la mediana de la diferencia es
0,004, pero el 12,2% difiere en más de 0,10 y el peor caso es 0,73. La cola son justo los
que cambiaron de lado con el recambio.

## Decisión

1. **La era se deduce de la fecha del nowcast**, no se clava. El calendario es el de
   `variables/bloque/src/bloque.py:_GOBIERNOS`, el mismo que usa `proyectar_postura` desde
   el 22-07. **No se escribe un calendario nuevo:** ya hay tres copias en el repo y por el
   ADR-0014 deberían vivir en `definiciones.py` — unificarlas toca tres módulos con dueño
   y queda anotado, no hecho.
2. **PRENDIDO por defecto** desde el 06-09 (`GUARD_ERA=0` para volver atrás). El número
   publicado **no se movió**: verificado corriendo el nowcast completo (Diputados,
   2026-06-01, origen EJECUTIVO, 2.000 sims, seed 0) en las tres configuraciones —
   **P = 0,9801 en las tres**. Lo único que se mueve son los afirmativos esperados
   (150,5 → 151,2 en Diputados, 45,5 → 45,6 en el Senado), muy adentro de la banda
   5-95 (143-158): hay ~28 votos de holgura sobre el umbral, así que la probabilidad no
   se entera. Para el gobierno en curso la era deducida **es** 2023-12-10.
3. **El harness se corrige también**, con `--guard-era {off,corte,shrink}`. Un espejo que
   no refleja es peor que no tener espejo.
4. **Encoger, no cortar.** También PRENDIDO (`SHRINK_RECORD=0` para volver atrás). En el
   motor el encogimiento vive en `perfil_legislador`, contra `share_linaje` — el **mismo
   objeto** que usa la rama de bloque, no otro parecido:

   $$\text{rec}_i^{\text{enc}} = \frac{n_i \cdot \text{rec}_i + k\, s_\ell}{n_i + k}, \qquad k = 5$$

   Con 145 votos mueve 0,024; con 10 votos, 0,24. Nunca cruza al otro lado: el resultado
   queda siempre entre el récord y el share.

## Medición

`evaluacion/baseline/src/medir_guard_era.py`, 741.275 votos emitidos, comparación pareada:

| modo | skill | hasta 2011 | 2011-2015 | 2015-2019 | 2019-2023 | desde 2023 | dip | sen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `off` | 0,1334 | 0,1551 | 0,2191 | **−0,010** | 0,2164 | **0,0242** | 0,133 | 0,073 |
| `corte` | 0,1643 | 0,1551 | 0,2191 | 0,0917 | 0,3828 | 0,0611 | 0,163 | 0,114 |
| **`shrink`** | **0,1680** | 0,1594 | 0,2214 | **0,0967** | **0,3876** | **0,0642** | **0,167** | **0,115** |

Los dos valles se cierran y **ninguna era baja**. La rama de bloque sube del 2,41% al
3,14% de las predicciones —era lo esperado: con menos historia, más gente no llega a
$n_i \ge 8$— y **su propio skill sube de 0,055 a 0,102**, que es la confirmación de que
los que dejan de calificar estaban usando historia de otra cámara.

## Consecuencias

- **El merge de `legislador_id` deja de ser dañino** (aplicado el 06-09, ver abajo).
- El backtest fuera de la era vigente pasa a ser posible. Hoy no lo es.
- `MIN_HIST_INDIVIDUAL` **bajó de 8 a 1 el 06-09**: el encogimiento lo dejó sin trabajo (con
  $n=1$ el récord ya queda en $\tfrac56 s_\ell$) y encima costaba, de forma monótona
  (skill 0,1665 con 8 contra 0,1702 con 1; en la era vigente 0,0616 contra 0,0726).

## El merge de ids, que este ADR desbloquea — y lo que costó

Medido el 04-09, el merge **solo** empeora (0,1317 → 0,1301): la fragmentación de ids
funcionaba como guard de era accidental, y mergear sin el guard saca la muleta antes que
la pierna. Con el guard puesto se aplicó (143 alias, 25.030 filas, 2.302 ids → 2.159).

**Y con el guard puesto tampoco sale gratis, aunque casi.** Medido el 06-09 con la clave
que usa el motor (cámara, id, era):

| era | sin merge | con merge | Δ |
|---|---:|---:|---:|
| hasta 2011 | 0,1609 | 0,1612 | +0,0003 |
| 2011-2015 | 0,2236 | 0,2216 | −0,0020 |
| **2015-2019** | 0,0967 | 0,0967 | **0,0000** |
| 2019-2023 | 0,3897 | 0,3757 | **−0,0140** |
| **desde 2023** | 0,0642 | 0,0641 | **−0,0001** |
| **global** | **0,1691** | **0,1684** | **−0,0007** |

Casi toda la pérdida está en **2019-2023**, que es la era con menos votos (3,5% de la
base) y por lo tanto la más ruidosa; 0,035 × 0,014 = 0,0005 explica sola el Δ global. Las
dos eras que le importan al producto no se mueven.

**Se aplicó igual, y el motivo no es métrico: son la misma persona.** Una métrica que
mejora manteniendo partida una carrera está midiendo un beneficio accidental. Queda
anotado acá para que nadie lo descubra después y crea que se ocultó.

**Un artefacto del proxy, verificado:** con la clave `(id, era)` la pérdida es −0,0015 y
con `(cámara, id, era)` es −0,0007. La mitad era el proxy mezclando cámaras en la carrera
de quien pasó de Diputados al Senado (Snopek es el caso). El motor siempre agrupó por
cámara; el proxy no.

## Confirmado con el censo (06-09, 579,9 min)

Baseline completo, 6.091 actas / 730.574 votos:

| | `off` | `shrink` |
|---|---:|---:|
| skill | 0,1304 | **0,1611** |
| 2015-2019 | −0,0105 | **0,0954** |
| 2019-2023 | 0,1971 | **0,3308** |
| desde 2023 | 0,0235 | **0,0474** |
| Diputados / Senado | 0,130 / 0,072 | **0,158 / 0,120** |

El proxy había dicho 0,1306 → 0,1665; el censo, 0,1304 → 0,1611: **misma dirección,
ganancia real 15% menor**, que es lo que corresponde a un proxy que aísla la rama del
récord.

**Y el censo agregó una razón que el proxy no daba:** la rama de bloque tiene skill
**NEGATIVO** (−0,0586 con `off`, −0,1024 con `shrink`, sobre 19.923 votos). Mandar gente
ahí no es conservador, es empeorarla — que es el argumento definitivo para haber bajado
`MIN_HIST_INDIVIDUAL` de 8 a **1** el mismo día.

**Lo único que empeora:** el sesgo medio del margen (−0,0151 → −0,0201) y el p90 del error
(0,2500 → 0,2541). El MAE baja (0,1408 → 0,1390). Chico, y en la dirección conservadora.

## Alternativas descartadas

- **Ventana móvil de N días** en vez de era. Se descarta: el problema no es que la historia
  sea vieja sino que es de **otra configuración**. Una ventana de 730 días a caballo de un
  recambio mezcla las dos, que es el bug.
- **Cortar sin encoger.** Mide peor que `shrink` en las cinco eras, y tira información de
  quien tiene poca historia en la era nueva.
- **Reescribir el calendario de gobiernos acá.** Sería la cuarta copia.

## Archivos

`modelo/ensemble/src/nowcast_puertas.py` (`era_de`, `GUARD_ERA`, `ERA_FIJA`),
`evaluacion/baseline/src/baseline_voto_individual.py` (`--guard-era`),
`evaluacion/baseline/src/medir_guard_era.py` (nuevo),
`evaluacion/baseline/tests/test_guard_era.py` (nuevo, 28 checks),
`coordinacion/FORMULA-COMPLETA.md` §II.5 (ADR-0015).
