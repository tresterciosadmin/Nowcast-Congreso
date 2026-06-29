# Baseline 'votá con tu grupo' sobre la base canónica (2011–2025)

Leave-one-out, solo votos sustantivos (afirmativo/negativo). Excluye "SIN BLOQUE".
Reproducir: `python evaluacion/baseline/src/baseline_canonico.py`.

## 1. Según nivel de agrupación (votos disputados = minoría ≥10%)
| Predigo con… | Todas | Disputadas |
|---|---|---|
| **bloque_norm** (bloque específico) | 0,979 | **0,969** |
| bloque_linaje (espacio político) | 0,946 | 0,919 |
| coalicion | 0,945 | 0,918 |

**Lectura:** con el bloque específico se acierta ~97% incluso en votaciones disputadas → predecir la dirección del voto individual sigue siendo un callejón sin salida para el ML (confirma Fase 0 sobre la base ampliada). Pero al subir a coalición/linaje cae a ~92%: **la disidencia intra-coalición (~8%) es señal real y modelable** (qué miembros se despegan de la línea, y cuándo).

## 2. Por cámara
- **Diputados:** 0,969 (disputadas). 
- **Senado:** sin medición — todos los votos recientes del Senado están "SIN BLOQUE" (argentinadatos no trae bloque). Pendiente resolver el bloque del Senado.

## 3. Por año (disputadas) — DRIFT
~0,97–0,99 estable de 2011 a 2023, y **cae en 2024 (0,946) y 2025 (0,923)**. Coincide con la fragmentación post-2023 (gobierno LLA en minoría, rupturas de PRO/UCR). 
- Es un **signo de drift real y reciente**: la disciplina se afloja justo ahora.
- Advertencia: parte de la caída 2024–2025 puede deberse también a ruido del cruce padrón→bloque (matching imperfecto). A confirmar al refinar la resolución de entidades del Senado/Diputados reciente.

## Implicancia para el producto
1. El voto-dirección por bloque sigue casi resuelto (no abrir ML ahí).
2. El valor migra a: **disidencia intra-coalición**, **asistencia/quórum**, **embudo**, y el **régimen 2024–2025** donde la disciplina baja.

## Actualización: primer baseline de Senado (Excel 2026)
Con el bloque del Senado resuelto vía el padrón de `manual_2026`:
- **Diputados:** 0,969 (disputadas).
- **Senado:** **0,938** (disputadas, n=388 — muestra chica, solo leyes 2026).
El Senado aparece algo menos disciplinado que Diputados, pero la muestra es chica; a confirmar al sumar la semilla (Senado 2004–2013).

## Actualización: base 2001–2025 completa (semilla CSV)
Con la semilla Década Votada integrada (ambas cámaras):
- **Diputados:** 0,965 (disputadas). **Senado:** **0,971** (disputadas, n=26.359 — ya robusto).
- El Senado histórico (2004–2014) resulta tan o más disciplinado que Diputados.
- Confirma sobre 25 años y 781k votos: el voto-dirección por bloque es un callejón sin salida; el valor sigue en disidencia intra-coalición, asistencia y el régimen 2024–2025.
