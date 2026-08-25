# docs/taxonomias/ — el catalogo de temas

<!-- huella: 44eb79257943 -->

**Resumen:** La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, su cargador y el prompt del clasificador. Es un CATALOGO, no un modelo.

## Buscar acá si

- que temas existen y como se llaman
- agregar, renombrar o fusionar una taxonomia
- el prompt con el que se clasifica un proyecto por titulo
- un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta)

## Trampas

- El clasificador **NO es un agente**: es una llamada a la API contra este catalogo (`variables/proyecto/src/agente_taxonomias.py`). La API key esta resuelta desde el 14-jul-2026; si algun documento dice "esperando la API key", quedo viejo.
- Un proyecto puede tener MAS DE UNA taxonomia (ADR-0006, multitaxonomia por titulo).
