# Agrupamiento de bloques — decisiones (revisable)

Tres niveles, sin destruir información:
- **`bloque`** (crudo): tal como viene de la fuente. Nunca se modifica.
- **`bloque_norm`**: unifica variantes del **mismo** bloque (acentos, mayúsculas, abreviaturas). Decisión segura.
- **`bloque_linaje`**: agrupa el **espacio político en el tiempo**. Decisión de modelado, revisable. Algunas reglas son **time-aware** (dependen de la fecha del voto).

## Merges en `bloque_norm` (mismo bloque)
UCR ← (Unión Cívica Radical, UCR, UCR - Unión Cívica Radical) · PRO ← (PRO, Unión PRO, Propuesta Republicana) · COALICION CIVICA ← (Coalición Cívica, CC - ARI) · FRENTE DE IZQUIERDA ← (FIT, FIT-U, PTS - Frente de Izquierda, Fte. de Izquierda…) · UNIDOS POR UNA NUEVA ARGENTINA ← (Unidos…, Federal Unidos…) · + unificación de acentos/mayúsculas en el resto.

## Grupos de `bloque_linaje` (8)
| Linaje | Incluye | Nota |
|---|---|---|
| FdT-UxP (kirchnerismo) | Frente para la Victoria → Frente de Todos → Unión por la Patria; **+ Peronismo para la Victoria, Nuevo Encuentro, Libres del Sur** (aliados); **+ Frente Renovador desde dic-2019** | decisión del usuario |
| FRENTE RENOVADOR (massismo) | Frente Renovador **hasta 2019-12-10** | time-aware |
| RADICALISMO | UCR, Evolución Radical | |
| PRO | PRO (ex Unión PRO) | |
| COALICION CIVICA | Coalición Cívica | |
| IZQUIERDA | Frente de Izquierda y afines | |
| LA LIBERTAD AVANZA | LLA | |
| OTRO / PROVINCIAL | resto (justicialismos provinciales, bloques de provincia, SIN BLOQUE, massismo/federal UNA…) | |

## Reglas time-aware
- **Frente Renovador:** `fecha < 2019-12-10` → "FRENTE RENOVADOR (massismo)"; `fecha ≥ 2019-12-10` → FdT-UxP. (En los datos: grueso 2013–2015 separado; cola 2020–2022 ya kirchnerista.)

## Decisiones y banderas a revisar
- **Libres del Sur:** fundido en FdT-UxP por decisión del usuario, pero su alineamiento **cambió en el tiempo** (estuvo en oposición en tramos). Candidato a regla time-aware si se quiere más precisión.
- **Massismo/Federal (UNA, 2015–2017):** queda en OTRO/PROVINCIAL (sin linaje propio).
- **Juntos por el Cambio / Cambiemos:** NO se construyó como coalición (composición dependiente del tiempo, 2015–2023). Tarea futura con ventanas de fecha.
- **Separación por TEMA del proyecto:** pendiente, se modela en `variables/proyecto` (clasificación de materia del expediente). Confirmado como prioridad.

## Cómo extender
Editá `BLOQUE_ALIAS`, `LINAJE` o las reglas time-aware en `src/entity_resolution.py` y re-corré.

## Cuarto nivel: `coalicion` (alianza electoral, time-aware)
Por encima del linaje, agrupa por coalición según la **fecha** del voto.

| Coalición | Miembros (núcleo) | Ventana |
|---|---|---|
| Juntos por el Cambio (Cambiemos) | UCR, PRO, Coalición Cívica, Evolución Radical | **2015-12-10 → 2023-12-10** |
| FdT-UxP (kirchnerismo) | = linaje kirchnerista | toda la serie |
| La Libertad Avanza | LLA | desde su aparición |
| (resto) | coalicion = su `bloque_linaje` | — |

Fuera de su ventana, los miembros de JxC vuelven a su espacio propio (pre-2015: UCR/PRO/CC por separado; pos-2023: idem, porque la coalición se fragmenta).

### Banderas a revisar (coalición)
- **Aliados provinciales de JxC** (Compromiso Federal, Juntos por Argentina, etc.): **NO** incluidos en JxC (membresía ambigua/provincial). Revisar si se quieren sumar.
- **2024–2025:** tras el recambio, PRO se acercó a La Libertad Avanza y la UCR se dividió. Hoy quedan como su espacio propio; si querés modelar "oficialismo LLA+PRO 2024–2025" es una regla nueva a definir.
- La ventana usa el recambio legislativo (10-dic) como corte; ajustable.
