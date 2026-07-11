# Validación del vocabulario con muestra manual — 2026-07-11

> Paso previo a la corrida del agente de taxonomías (decisión de Valle: validar el
> vocabulario a mano antes de gastar en batch). Clasificación manual de Claude sobre
> una **muestra estratificada por año de 88 actas** de la canónica (2001–2025, ambas
> cámaras, títulos informativos). Datos: `outputs/muestra_manual_taxonomias.csv`.

## Resultado global

| métrica | valor |
|---|---|
| Actas en la muestra | 88 |
| Clasificables por título | 72 (82%) |
| Títulos OPACOS (sin tema en el título) | 11 (12%) |
| PROCEDIMENTALES (mociones, apartamientos, emplazamientos) | 5 (6%) |
| Confianza alta / media / baja (sobre las 72) | 47 / 17 / 8 |
| Multi-etiqueta | 16/72 (22%) |

**Veredicto: el vocabulario FUNCIONA.** De las 72 clasificables, el 89% encuentra id con
confianza alta o media. La regla de frontera existente (juego→SALUD.ADICC) aplicó perfecto
en los 3 casos de ludopatía 2024. La multi-etiqueta (22%) confirma que el diseño
multi-etiqueta era necesario.

## Hallazgo operativo: el título no alcanza para la historia

El 18% de las actas no se puede clasificar por título: los expedientes del CKAN vienen como
"Expediente NNNN-D-AA - Orden del Día X" y el Senado agrupa "Temas Varios". El agente ya
resuelve esto para proyectos NUEVOS (lee el PDF), pero para clasificar la HISTORIA
(features_votacion_bloque) va a hacer falta el enlace acta→expediente (`datos/expedientes`,
pendiente) o aceptar `NO_TEMA` en esas actas. Los PROCEDIMENTALES son una categoría real y
recurrente: conviene una etiqueta técnica fuera del vocabulario (p. ej. `_PROCEDIMENTAL`)
para no forzar un tema donde no lo hay.

## Huecos del vocabulario detectados (candidatos a subtemas nuevos)

Por frecuencia en la muestra:

1. **Control parlamentario** (4 casos: DNU/Bicameral 26.122, cuentas de la Administración,
   pedido de informes e interpelaciones $LIBRA). Hoy caen forzados en POLINST.ORGEST o
   POLINST.ETICA. Propuesta: `POLINST.CTRL`.
2. **Transferencias de inmuebles / bienes del Estado** (3 casos, típico del Senado). Sin
   subtema; propuesta: absorber en POLINST.ORGEST con regla de frontera explícita, o
   subtema propio si se confirma la frecuencia en el batch.
3. **Sistema financiero / bancario** (2 casos: ahorro infantil ×2). ECON.MON queda forzado.
   Propuesta: `ECON.FINAN`.
4. **Áreas protegidas / biodiversidad** (1 caso: parque marino costero). AMB no tiene
   subtema; propuesta: `AMB.BIODIV`.
5. **Federalismo / intervención federal** (1 caso). Menor; puede vivir en POLINST.CONST.

## Fronteras a fijar (reglas nuevas propuestas para `reglas_frontera`)

- **Tratados temáticos** → llevan SIEMPRE ambos ids: `DEF.TRATADO` + el área de la materia
  (así se comportó bien en Estocolmo/CERD/OMC/minas antipersonal).
- **Juicio político** a magistrados → ¿JUST.JUDIC o POLINST? (2 casos 2002).
- **Asignaciones familiares** → ¿TRAB.PREV o DESSOC.ASIST?
- **Código Procesal Penal** → ¿JUST.PENAL o JUST.JUDIC?

## Qué sigue

1. Valle/equipo decide sobre huecos y fronteras (cambiar `docs/taxonomias` es contrato
   compartido: versionado según TAXONOMIAS.md).
2. Con el vocabulario ajustado, correr el **agente en batch** (necesita API key) sobre los
   proyectos vivos; esta muestra manual queda como set de referencia para medir el acuerdo
   agente-vs-humano.
