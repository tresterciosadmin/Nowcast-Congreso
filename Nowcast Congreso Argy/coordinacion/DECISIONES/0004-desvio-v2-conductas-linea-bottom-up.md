# ADR-0004 — Desvío v2: conductas, línea bottom-up, desempate por linaje y desvío parcial

- **Fecha:** 2026-07-02
- **Estado:** aceptada
- **Decisores:** Valle (definición), Claude (implementación)
- **Reemplaza:** la definición v1 de desvío (mayoría leave-one-out de votos sustantivos del bloque, mínimo 5, ausencias/abstenciones invisibles).

## Contexto

Valle objetó dos cosas del v1: (1) las abstenciones y ausencias no computaban, cuando en la práctica parlamentaria son LA forma elegante de desviarse sin votar en contra; (2) el nivel de análisis estaba invertido — las preferencias del bloque deben EMERGER de la agregación de sus miembros (bottom-up), no imponerse desde afuera.

## Decisión

1. **Tres conductas** por votación: AFIRMATIVO · NEGATIVO · NO_ACOMPANA (abstenerse o ausentarse — usar el escaño es una decisión).
2. **Bajada de línea del bloque** = la conducta con **mayoría simple sobre TODOS los escaños** del bloque en esa acta (los ausentes cuentan en el denominador).
3. **Desvío = conducta ≠ línea, regla ESTRICTA:** abstenerse/ausentarse cuando la línea es votar (en cualquier sentido) computa; votar cuando la línea del bloque es ausentarse, también.
4. **Bloque sin mayoría** (ej. 2-2): (a) si pertenece a un espacio político real (linaje ≠ "OTRO / PROVINCIAL"), desempata la línea del espacio entero en esa acta; (b) si no, **desvío parcial** = 1 − fracción de escaños del bloque con la misma conducta (en 2-2, todos 0,5).
5. **Exclusiones** (falso desvío estructural): presidentes de la Cámara de Diputados durante su presidencia (por costumbre no votan; lista curada `PRESIDENCIAS_DIPUTADOS` en `disciplina.py` — hallazgo de la validación: dominaban el top con 85-95%) y filas placeholder ("NO INCORPORADO"). El Senado no lo necesita (lo preside el vicepresidente de la Nación).
6. **Disputada** unificada con datos/export: ±5% de los emitidos respecto del umbral de la mayoría requerida.

## Resultados de la primera corrida (base completa, 823.001 votos medibles)

Desvío medio 18,9% — el índice ahora mide **indisciplina total** (rebeldía de voto + no acompañamiento), no solo voto cruzado. Método: 95,4% línea de bloque, 4,5% parcial, 0,1% desempate por linaje. El top pasa a estar dominado por quienes no usan la banca (N. Kirchner diputado 2010, Insaurralde 2014, bancas en licencia de funcionarios) — coherente con el marco.

## Pendientes que abre esta decisión

- **Reclasificación de la bolsa OTRO/PROVINCIAL** (45% de los votos) hacia linajes reales, manual y/o automática — amplía el universo desempatable. (Toca `entity_resolution` = módulo canonica, coordinar con Franco.)
- **Suspensiones y licencias — decisión de Valle 2026-07-02: SE EXCLUYEN**, como las presidencias. Los suspendidos ya se excluyen (la fuente los anota en el nombre, ej. "Suspendido Art 70 C.N."). Las licencias NO están en los datos actuales → **crear una herramienta que detecte y notifique suspensiones y pedidos de licencia** (módulo futuro `datos/licencias_suspensiones`; fuentes candidatas: resoluciones de cámara, versiones taquigráficas, Boletín Oficial). Hasta entonces, las bancas en licencia computan como no acompañar (caveat documentado).
- **Ponderación por trascendencia de la votación** (Ley Bases ≠ moción de trámite) — anotado para sesión futura.
- **Disciplina ideológica por taxonomía** (consistencia de voto por tema): segunda métrica del legislador; además mitiga los monobloques (disciplina partidaria 100% por definición). Depende del p