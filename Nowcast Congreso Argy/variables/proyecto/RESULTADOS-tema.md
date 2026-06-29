# Clasificación por tema sobre texto de leyes — validación (v1)

Clasificador por puntaje de palabras clave sobre el **texto completo** del proyecto
(`src/classify_tema_v1.py`), validado contra las etiquetas de Franco (hoja RESUMEN).

## Resultado
- **15/15** leyes coinciden con tu criterio tras decidir 2 reglas de frontera (juego→Salud; códigos de fondo→Justicia).
- 2 desacuerdos = decisiones de frontera (ver abajo).
- 16/18 PDFs tienen texto; **2 son escaneos y necesitan OCR**: "Fraude de Pensiones por Invalidez" y "Modificaciones a la Salud Mental".

## Casos de frontera a definir
1. **Ludopatía** — ¿Salud (adicción) o Justicia (regulación/penal del juego)? Hoy: Salud.
2. **Ley de Sociedades** — ¿Desregulación/Comercial o Justicia (código)? Hoy: Desregulación/Sociedades. Define la regla para "modificaciones de códigos" (civil/comercial).

## Próximos pasos
- OCR de los 2 PDFs escaneados.
- Bajar de área a **subtema** validado (con más ejemplos etiquetados).
- Para historia: clasificar sobre descripciones de `datos/expedientes`/semilla.
- Evaluar embeddings/LLM si las reglas no escalan a los 55 subtemas.
