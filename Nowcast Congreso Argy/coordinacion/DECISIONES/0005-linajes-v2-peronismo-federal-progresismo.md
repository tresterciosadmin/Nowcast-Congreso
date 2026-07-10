# ADR-0005 — Linajes v2: PERONISMO FEDERAL, PROGRESISMO y ventanas del JUSTICIALISTA

- **Fecha:** 2026-07-10
- **Estado:** aceptada
- **Decisores:** Franco (definición), Claude (implementación)
- **Responde a:** pedido explícito del ADR-0004 ("reclasificación de la bolsa OTRO/PROVINCIAL, coordinar con Franco")

## Contexto

El 45,5% de los votos (380k) caía en el linaje residual OTRO/PROVINCIAL, lo que
limitaba el desempate por linaje del desvío v2 (ADR-0004) y empobrecía el
análisis macro. Adentro convivían: variantes de linajes existentes con otro
nombre, todo el peronismo no kirchnerista, el progresismo no kirchnerista y
los provinciales genuinos.

## Decisión (Franco, 2026-07-10)

1. **Dos linajes nuevos** (la taxonomía pasa de 8 a 10):
   - **PERONISMO FEDERAL**: peronismo no kirchnerista (Peronista Federal,
     Justicialista Nacional, Unión Peronista/Solá, Justicialista 8 de
     Octubre/Romero, Santa Fe Federal/Reutemann, Córdoba Federal, Compromiso
     Federal y sellos puntanos, Federalismo y Liberación/Menem, PAUFE,
     Producción y Trabajo/Basualdo, Unidad Federal 2023, etc.).
   - **PROGRESISMO**: progresismo no kirchnerista (Partido Socialista, GEN,
     Frepaso, Unidad Popular/Lozano, Proyecto Sur/Solanas).
2. **JUSTICIALISTA a secas se parte por fecha** (tres eras políticas con el
   mismo nombre; verificadas en los datos):
   - hasta 24/05/2003 (Duhalde) → PERONISMO FEDERAL;
   - 25/05/2003 (asunción de Néstor) a 09/12/2015 → FdT-UxP (PJ oficialista K);
   - 10/12/2015 a 09/12/2019 (bloques Bossio/Pichetto) → PERONISMO FEDERAL;
   - desde 10/12/2019 (el sello vuelve al tronco; en 2024+ es el bloque UxP
     del Senado) → FdT-UxP.
3. **Variantes claras reasignadas a linajes existentes**: Justicialista-FpV
   (Senado 2004-14, semilla) y De la Concertación (radicales K) → FdT-UxP;
   Frente PRO → PRO; A.R.I → Coalición Cívica; UNA → Frente Renovador.
4. Sin fecha no hay ventana aplicable: queda OTRO (conservador, ~160 votos).

## Resultado (dry-run sobre 834.749 votos)

OTRO/PROVINCIAL cae de **45,5% a ~19%**; lo que queda es provincial genuino
(Frente Cívico por Santiago, MPN, Fuerza Republicana, Renovador de Salta,
bloquismo, juecismo…) más SIN BLOQUE (Senado 2024-25, retro-completable).
Nuevos: PERONISMO FEDERAL ~71k votos, PROGRESISMO ~23k. FdT-UxP crece a ~344k
(el PJ oficialista 2003-2015 se incorpora al tronco).

## Consecuencias

- El desempate por linaje del desvío v2 gana ~200k votos de universo.
- `modelo/voto_individual` y `datos/export` deben re-correrse tras regenerar
  `votos_resuelto.parquet` (los valores del linaje cambian para 45% menos bolsa).
- El detalle por bloque y la trazabilidad quedan en `datos/canonica/BLOQUES.md`.
- Caveat 2001-2003: el PJ de la era Duhalde queda como PERONISMO FEDERAL por
  decisión (es pre-división K/federal; alternativa descartada: fundirlo en
  FdT-UxP).
