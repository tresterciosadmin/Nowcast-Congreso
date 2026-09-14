# docs/taxonomias/ — el catalogo de temas

<!-- huella: d4ed62fdd164 -->

**Resumen:** La lista curada de taxonomias (temas/materias) contra la que se clasifican los proyectos, y su cargador. Es un CATALOGO, no un modelo. El PROMPT del clasificador NO vive aca: es `SYSTEM_PROMPT` en `variables/proyecto/src/agente_taxonomias.py`, y es el unico lugar donde se toca.

**Estado:** HECHO (vocabulario v1 completo desde el 30-06-2026: 74 ids, areas + auxiliares + reglas de frontera, con loader y test). El vocabulario nunca fue el cuello de botella de la clasificacion — lo que falta es poblar `tema_por_acta` y `proyecto_taxonomias` (ver `datos/taxonomias/`), frenado por creditos de API.
**Owner actual:** — (sin reclamar; el catalogo no necesita mantenimiento activo salvo que se agregue/renombre un id)

## Buscar acá si

- que temas existen, como se llaman, y como se agrega, renombra o fusiona uno
- el prompt con el que se clasifica un proyecto: esta en `variables/proyecto/src/agente_taxonomias.py`, no aca
- un id de taxonomia duplicado o mal escrito (`loader.py` lo detecta)

## Trampas

- El clasificador **NO es un agente**: es una llamada a la API contra este catalogo (`variables/proyecto/src/agente_taxonomias.py`). La API key esta resuelta desde el 14-jul-2026; si algun documento dice "esperando la API key", quedo viejo.
- Un proyecto puede tener MAS DE UNA taxonomia (ADR-0006, multitaxonomia por titulo).
