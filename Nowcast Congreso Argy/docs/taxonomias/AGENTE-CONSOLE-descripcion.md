# Agente de Taxonomías — prompt del clasificador (referencia de diseño)

> **DECISIÓN (2026-07-13, ver ESTADO): el clasificador corre por API desde el código, NO desde un agente de Console.** El `system` prompt de producción vive en `variables/proyecto/src/agente_taxonomias.py` (`construir_prompt`) — esa es la fuente de verdad. Claude Console se usa solo como *playground* para diseñar/probar/comparar modelos; no hay un agente de Console del que dependa el pipeline. Este archivo queda como la referencia legible del prompt (y del modelo híbrido de PDF); si editás el prompt, editá el código y actualizá esto.
>
> Para "conectar": solo hace falta `ANTHROPIC_API_KEY` (Console → Settings → API keys) + `model` + `system` + mensaje de usuario. El código ya arma esa llamada (`llamar_claude`).
>
> **Principio de diseño: single source of truth.** El prompt NO lleva el vocabulario ni las reglas de frontera hardcodeadas. El pipeline (`variables/proyecto/src/`) lee `docs/taxonomias/taxonomias.json` en cada corrida y le inyecta al modelo, dentro del mensaje de usuario: (1) la lista controlada, (2) las reglas de frontera y (3) el texto del proyecto. Si se edita el JSON, la corrida usa la versión nueva sin tocar nada acá.

---

## 1) Nombre
`Clasificador de Taxonomías — Proyectos de Ley (Congreso AR)`

## 2) Descripción corta (campo "Description")
Clasifica proyectos de ley del Congreso argentino asignándoles uno o varios temas de un vocabulario controlado cerrado (Área→Subtema, multi-etiqueta). La lista de temas, las reglas de frontera y el texto del proyecto se le pasan en el mensaje de usuario; el agente elige solo ids de esa lista, respeta las fronteras y devuelve JSON estricto con nivel de confianza.

## 3) Modelo sugerido
Haiku para batch masivo (tarea acotada + validación posterior de ids). Subir a Sonnet solo para casos ambiguos.

---

## 4) Instrucciones del sistema (System Prompt)

> Genérico e independiente de la versión del vocabulario. NO contiene la lista de temas ni las reglas de frontera concretas: esas llegan en el mensaje de usuario.

Sos un clasificador experto en proyectos de ley del Congreso argentino. Tu única tarea es asignar TAXONOMÍAS temáticas a un proyecto, eligiendo EXCLUSIVAMENTE de la LISTA CONTROLADA que se te entrega en el mensaje de usuario.

REGLAS

1. Multi-etiqueta. Un proyecto casi siempre trata varios temas: asigná TODOS los subtemas que apliquen, no fuerces uno solo. Lo normal es más de uno.
2. Elegí SOLO ids que aparezcan en la LISTA CONTROLADA del mensaje. No inventes ids ni nombres, no uses ids de memoria. Si dudás entre dos, incluí ambos con su confianza.
3. Proponé temas nuevos en `candidatos_nuevos` (texto libre, sin id) en dos situaciones: (a) el proyecto no encaja en ningún subtema sustantivo → además asigná `AUX.SINCLASIF`; o (b) encaja pero tuviste que FORZAR un id existente porque falta uno más preciso → asigná igual el/los id más cercanos Y dejá el candidato anotado. Solo proponés: no agregás taxonomías por tu cuenta ni inventás ids; los candidatos los revisa una persona y, si corresponde, los suma al vocabulario.
4. Homenajes y declaraciones (de interés, beneplácito, repudio, adhesión) → `AUX.HOMENAJE`. Trámite parlamentario sin contenido sustantivo (mociones, apartamientos, emplazamientos, pedidos de tratamiento) → `AUX.TRAMITE`.
5. Aplicá SIEMPRE las REGLAS DE FRONTERA que vengan en el mensaje de usuario: tienen prioridad sobre tu criterio general.
6. Confianza: para cada asignación dá un puntaje 0.0–1.0 (0 = muy dudoso, 1 = inequívoco).
7. Basá la clasificación en el CONTENIDO del articulado y los considerandos, no en el bloque ni el autor del proyecto.

FORMATO DE SALIDA

Respondé SOLO con un objeto JSON válido, sin texto adicional, sin markdown, con esta forma exacta:

{"asignaciones":[{"id":"AREA.SUB","confianza":0.0}],"candidatos_nuevos":["..."],"comentario":"breve"}

- `asignaciones`: lista de {id, confianza}. Siempre al menos un elemento.
- `candidatos_nuevos`: lista de textos (vacía si no hay).
- `comentario`: una frase breve justificando (opcional).

---

## 5) Mensaje de usuario (lo ARMA EL PROGRAMA en cada corrida, no se escribe a mano)

El programa rellena los tres bloques `{…}` leyendo `taxonomias.json` (lista + reglas de frontera) y el PDF ya extraído a texto:

```
LISTA CONTROLADA DE TAXONOMÍAS (id = nombre):
{LISTA_CONTROLADA}      ← generada desde taxonomias.json (áreas + subtemas + auxiliares)

REGLAS DE FRONTERA (tienen prioridad):
{REGLAS_FRONTERA}       ← generadas desde taxonomias.json → reglas_frontera

TEXTO DEL PROYECTO DE LEY (articulado y considerandos):
"""
{TEXTO_PROYECTO}        ← texto del PDF, recortado a ~18.000 caracteres
"""

Devolvé el JSON de clasificación.
```

---

## 6) Automatización — qué hace el programa (no el agente)

Todo el flujo debe estar automatizado. El agente de Console es solo el paso de razonamiento; lo rodea un programa que se encarga de todo lo demás. Esto ya existe en `variables/proyecto/src/` y hay que apuntar el agente a este pipeline:

1. **Buscar/bajar el PDF (modelo híbrido texto / PDF-documento — reemplaza el OCR).** Un programa toma el `pdf_url` del proyecto (tabla `proyectos` en `datos/proyectos`) y descarga el PDF. El agente NUNCA busca ni navega: el programa siempre baja el archivo. Después decide cómo pasárselo:
   - **PDF con texto** (la mayoría): extrae el texto (`pdf_text.py`), lo recorta a ~18.000 caracteres y lo manda como `{TEXTO_PROYECTO}`. Ruta barata, la de siempre.
   - **PDF escaneado / imagen** (antes se salteaba con "OCR pendiente): ya NO hace falta OCR aparte. El programa manda el PDF **como documento** en el mensaje (bloque `document`, no texto) y Claude lo lee con su visión nativa — convierte cada página a imagen y extrae el texto solo. Es el "OCR" incorporado al modelo.

   Cómo mandar el PDF-documento (API de Messages, tres opciones): por **URL** (`source.type=url`), por **base64** (`source.type=base64`, `media_type: application/pdf`), o subiéndolo a la **Files API** y referenciándolo por `file_id` (recomendado si el PDF es grande o se reusa, mantiene el payload chico).

   **Límites de PDF (doc oficial, jul-2026):** máximo **32 MB** por request y **600 páginas** (100 si la ventana de contexto es < 1M tokens); PDF estándar sin contraseña/encriptación. Los PDFs muy densos pueden llenar el contexto antes de llegar al límite de páginas: si pasa, trocear.

   **Costo del modelo híbrido:** un PDF con texto cuesta ~1.500–3.000 tokens por página. Un PDF-documento suma además el costo de imagen por página (visión), así que es más caro — por eso se usa esa ruta SOLO para los escaneados. Para lotes grandes conviene la **Batch API** (procesamiento asíncrono) y **prompt caching** si se reusa el mismo PDF. Recomendación de modelo: Haiku para los PDFs con texto; escalar a Sonnet los escaneados, donde la visión rinde mejor sobre texto legal denso.
2. **Cargar el vocabulario.** El programa lee `docs/taxonomias/taxonomias.json` (vía `loader.py`) y arma `{LISTA_CONTROLADA}` y `{REGLAS_FRONTERA}`. Fuente de verdad única: nada se duplica en el prompt.
3. **Llamar al agente** con el system prompt fijo (bloque 4) + el mensaje de usuario armado (bloque 5).
4. **Validar la salida.** El programa descarta ids que no existan en el JSON (inventados por el modelo) y, si no queda ninguno válido, fuerza `AUX.SINCLASIF`.
5. **Persistir** en `datos/proyectos` → `proyecto_taxonomias`, con la regla "el humano gana": nunca pisa una taxonomía cargada a mano (`fuente='humano'`).

Estas responsabilidades (fetch de PDF, inyección del vocabulario, validación de ids, humano-gana, persistencia) viven en el CÓDIGO, no en el prompt. Así el agente queda chico, barato y estable, y el único lugar donde se edita el vocabulario sigue siendo `taxonomias.json`.
