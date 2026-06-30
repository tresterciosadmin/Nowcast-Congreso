# (Movido) Taxonomía de temas

La **fuente de verdad** es ahora **`docs/taxonomias/taxonomias.json`** (vista humana: `docs/taxonomias/TAXONOMIAS.md`), del sistema del equipo.

Este archivo y el clasificador por keywords (`classify_tema*.py`) quedaron **deprecados**. Las reglas de frontera que definimos (juego/ludopatía → `SALUD.ADICC`; reforma de códigos de fondo → `JUST.*`) ya están incorporadas en el vocabulario controlado. La clasificación la hace `variables/proyecto/src/agente_taxonomias.py` (agente LLM).
