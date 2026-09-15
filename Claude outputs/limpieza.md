---
description: Retoma la limpieza y reordenamiento del repo con las reglas de la casa
---

Sos el que sigue la **limpieza y reordenamiento del Nowcast Legislativo Argentino**.
Vas archivo por archivo decidiendo qué sirve y qué no.

## Restricciones duras (no negociables)

1. **No cambies el número publicado.** No tocás el comportamiento efectivo de
   `modelo/ensemble/`, `modelo/agregador_institucional/`, `modelo/voto_individual/`,
   `variables/bloque/`, `variables/proyecto/` (modulador y origen) ni `variables/embudo/`.
   Mejoras sólo detrás de un flag apagado por defecto, con test y con medición.
   **El número publicado es P = 0,9801** (β₁ 2,1078 · β₂ 2,1487, medidos el 2026-09-14).
   Si al final de una tanda cambió, **la limpieza está mal, no el número** — salvo que
   el cambio venga de datos nuevos y esté explicado con la medición al lado.
2. **Nada de `git push`, ni borrar datos, ni reescribir historia.** Commits locales sí:
   mensajes claros, en castellano, uno por tarea.
3. **Nada se borra: se mueve a `Archivos_Borrar/`.** Ojo: hay DOS carpetas de descarte
   (la de la raíz y `datos/Archivos_Borrar/`, con 184 MB sin decidir).

## Reglas de la casa

- **Un porcentaje imposible es un bug, no un fenómeno.** Ante un número absurdo,
  sospechá del cruce antes que de la hipótesis.
- **Medí antes de creer.** No concluyas sobre el estado del repo sin mirar el disco.
  Antes de repetir un número que leíste en una bitácora, verificalo contra el archivo.
- **No reimplementes contratos de otros módulos** (`definiciones.py`, ADR-0014).
- **Todo cambio del motor se presenta a tres niveles** en `coordinacion/FORMULA-COMPLETA.md`,
  en el mismo commit (ADR-0015).
- **Toda variable entra a nivel legislador** (ADR-0016).
- **Un control se escribe como propiedad, no como el número del día.**
- La prosa vive en el README de cada módulo (`**Resumen:**` + `## Buscar acá si`).
  `MAPA.md` y `.mapa/` son **generados**: no se editan a mano.

## Cómo trabajamos

- De a **tandas de 3-4 módulos**; parás y mostrás veredictos.
- Lo que no tenga **90% de certeza, lo preguntás**. No adivines.
- **Castellano, directo, números antes que principios generales.**
- Los errores se reconocen sin adorno y sin autoflagelarse: qué pasó, qué medición
  lo demuestra, qué se hace.
- Las corridas largas se corren y se esperan (acá no hay límite de 45 s).

## Antes de empezar, en este orden

1. `coordinacion/URGENTE.md` — si tiene algo, se resuelve o se posterga explícitamente.
2. `CLAUDE.md` completo (arranca por la tabla "¿dónde estoy corriendo?").
3. `coordinacion/PLAN-LIMPIEZA-2026-09.md` — las fases 0-6 y en cuál quedamos.
4. `MAPA.md` — el índice. Para ubicar algo: `python .mapa/buscar.py "<término>"`.
   Para un dato: `python .mapa/buscar.py --dato <término>`.
5. `git --no-optional-locks status` y `git log --oneline -15` — qué quedó sin commitear.

Después decime en qué estado encontraste todo y cuál proponés que sea la próxima tanda.
