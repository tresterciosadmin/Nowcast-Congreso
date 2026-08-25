# ADR-0012 — Una sola formulación: la cadena de puertas, y la baja de la v1

**Fecha:** 2026-08-22 · **Estado:** Aceptada · **Quién:** Valle (decisión), Claude (implementación)

## Contexto

Hasta hoy convivían **dos** formulaciones del número, y el mapa las dibujaba a las dos a propósito:

- **v1, en producción:** `P(aprobación) = P(llega al recinto) × P(mayoría | recinto)`, en `modelo/ensemble/src/ensemble.py`.
- **Puertas:** `P(sanción) = P(A)·P(B|A)·P(C|A,B)·P(D|A,B,C)`, contrato en `modelo/ensemble/PUERTA-D.md`.

El 2026-08-20 Valle decidió el rumbo: **el nowcast deja de estimar si una comisión o una cámara va a TRATAR un proyecto.** Eso es agenda política, se define en labor parlamentaria a puertas cerradas y no hay estadística que la capture. `p_llega_recinto` es exactamente esa estimación.

El prerrequisito se completó el 21 y 22-08: los firmantes del dictamen, ingestados de los PDF de la Orden del Día en las dos cámaras (125.504 firmas en Diputados, 17.688 en el Senado).

## Decisión

**1. La formulación es una sola y es la de puertas.**

```
P(aprobación) = [A observada] · P(B | carácter del dictamen de origen)
              · [C observada] · P(D | carácter del dictamen de la revisora)
```

**2. A y C NO son probabilidades.** Son el **carácter observado** del dictamen en cada cámara —quién firmó, disidencias, bloques—, leído del PDF. Colapsan a 1 cuando el hecho ocurrió, y **condicionan** la votación de su cámara en vez de multiplicarla. Cuando no hay dato, el condicionante se **encoge a 0** y queda la estimación sin condicionar: el fallback no es un `if`. Tres estados, y el tercero no colapsa al segundo: *con carácter* / *sin dictamen* / *sin dato*.

**3. `p_llega_recinto` sale de la cadena.** Con él se va la cobertura de la mortandad en el cajón, y el número pasa a ser **condicional**: ya no dice «va a ser ley», dice «si las dos cámaras lo votan, ¿lo aprueban?». Eso va **en la interfaz**, no en un README.

**4. `p_sancion` no se toca y NO entra a la cadena.** Ya contiene A, B, C y D adentro; meterlo como factor haría que la cadena se multiplique por sí misma. Su lugar es la baseline.

**5. `factor_revisora_empirico` queda fuera del número publicado.** Contiene C y D juntas: con D simulada, cuenta dos veces la misma mortandad.

**6. El punto de entrada es `modelo/ensemble/src/nowcast_puertas.py`**, que corre la cadena hacia adelante sobre la configuración actual de las dos cámaras y devuelve el número **con el desagregado por legislador**: quién acompaña, quién no, sobre quién hay incógnita y a quién ir a buscar.

**7. Cómo se ejecutó la baja.** No se borró código: `componer`, `_p_llega_de_embudo`, `nowcast_proyecto`, `nowcast_auto`, `imprimir_tarjeta` y la CLI de `ensemble.py` **levantan `SystemExit` con el motivo y a dónde ir**, así quien las llame recibe una explicación en vez de un `ImportError`. `backtest_cadena.py` queda **neutralizado** por la misma razón: medía la v1 y un backtest que sigue corriendo sobre una formulación muerta produce números que alguien va a citar. Copias enteras en `Archivos_Borrar/BORRAR_modelo-ensemble-src-*.py`.

## Consecuencias

- **Le cambia el contrato a todo lo que consume el número.** `casos/` ya corría por puertas y no se rompe. `producto/` no consumía `ensemble` directamente.
- **El backtest queda sin vara y hay que decidir cuál.** Medido el 22-08 sobre la cohorte madura: `p_sancion` da skill **+0,4478** en total, pero **+0,2916** entre los 3.898 proyectos CON dictamen y **−0,0257** entre los 34.799 sin él. O sea que su mérito es sobre todo **separar con-dictamen de sin-dictamen** — justo lo que la Puerta A ahora OBSERVA en vez de estimar. Medir la cadena nueva contra `sancionado` la mide contra algo que por diseño no predice. La única salida con varianza real es el **margen** del recuento (6.237 actas de la canónica, 1.849 enganchadas a su expediente). **Queda pendiente y bloquea re-apuntar el backtest.**
- **El condicionante del carácter arranca en 0.** `estimar_delta_caracter` es un hook: la etiqueta binaria del voto en origen está degenerada (**2 RECHAZADO en 1.898 proyectos de ley con resultado**), así que ajustar sobre eso es ajustar ruido. Con `COEF_POR_DEFECTO` en cero la cadena corre en su límite no condicionado, que es el fallback del diseño y está testeado como tal.
- **Pendiente anotado (Valle, 22-08):** el **peso del firmante**. Hoy todas las firmas valen igual y no es cierto. Las fuentes ya existen: `scrape_jefes_bloque.py` y `comisiones_autoridades.parquet` (46 presidentes).
- **Enmienda a `PUERTA-D.md`** (22-08): su tabla describía A y C como probabilidades de agenda («¿sale de comisión?», «¿la tratan antes de caducar?»). Marco viejo, dado de baja. La prosa curada del mapa (`mapa_modelo_semantica.json`) arrastraba lo mismo y quedó corregida.
