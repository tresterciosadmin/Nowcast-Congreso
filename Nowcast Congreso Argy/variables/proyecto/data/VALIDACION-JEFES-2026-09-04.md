# Validación del roster de jefes de bloque — URGENTE 5, 2026-09-04

Las **15 filas con confianza MEDIA** de `jefes_bloque.csv`, buscadas contra fuente
explícita. Resultado: **4 confirmadas y pasadas a ALTA, 2 eliminadas por estar mal, 9 sin
fuente concluyente todavía.**

## Primero: cuánto aporta cada fila

Antes de buscar nada se midió el volumen, porque la prioridad la fija el daño posible.
Proyectos presentados por esa persona **dentro de la ventana de la fila**, contra
`proyectos.db`:

| fila | proyectos en ventana | como 1er firmante |
|---|---:|---:|
| DEL CAÑO / Frente de Izquierda | **349** | 286 |
| FERRARO / Coalición Cívica | **291** | 240 |
| CAMAÑO / Frente Renovador | **225** | 225 |
| CAMAÑO / UNA | **150** | 150 |
| PINEDO / PRO (Diputados) | 85 | 85 |
| MASSA / UNA | 62 | 62 |
| THOMAS / Frente Peronista | 48 | 48 |
| PICHETTO / Justicialista | 11 | 11 |
| PINEDO / PRO (Senado) | 8 | 8 |
| ZAMORA / Frente Cívico | 2 | 2 |
| FERNÁNDEZ SAGASTI / Unidad Ciudadana | 1 | 1 |
| ATAUCHE · LOSADA · CICILIANI · MAYANS | **0** | 0 |

> **Cinco de las quince aportan cero proyectos**, casi todas del Senado: la base de
> proyectos es sobre todo de Diputados. Validarlas no mueve $\beta_2$ — pero sí importan
> para el Mapa de Influencia y para no repetir el caso Bianchi.

## Confirmadas → ALTA

| fila | fuente | detalle |
|---|---|---|
| **PINEDO / PRO / Diputados 2013-2015** | La Nación, 01-12-2015 (`nid1850460`) | Massot *"será desde el 10 de diciembre el jefe del bloque Pro"*, sucediendo a Pinedo, que *"partirá al Senado"*. **Se corrigió la fecha:** el `hasta` decía `2015-12-01` (la fecha de la nota); el recambio es el 10-dic, así que cierra el **2015-12-09**. |
| **ATAUCHE / LLA / Senado 2023-** | El Tribuno de Jujuy, 03-12-2023 + elDiarioAR | *"El jujeño Atauche presidirá el bloque de La Libertad Avanza en el Senado"*, con Abdala de vice. Electo el 3-dic, asume con el recambio del 10. |
| **MAYANS / Frente Nacional y Popular / Senado 2022-2023** | Diario Río Negro, 20-04-2022 | Al partirse el FdT, Mayans preside **Frente Nacional y Popular (21 senadores)**. La misma nota da el otro bloque, y es la que desmiente la fila de abajo. |
| **CAMAÑO / Frente Renovador / Diputados 2015-2019** | Wikipedia ES + Chequeado, 08-03-2018 | Presidenta del bloque Federal-UNA desde 2015; tras la salida de Massa en 2017 queda al frente del bloque **y** del interbloque FR-UNA. Chequeado la registra conduciendo 17 diputados en marzo de 2018. Dos fuentes independientes. |

## Eliminadas — estaban mal

Se borran con el motivo escrito como comentario `#` en el propio CSV, igual que se hizo
con Bianchi.

**LOSADA, CAROLINA / UCR / Senado / 2021-12-10 → 2023-12-09.**
No presidió el bloque UCR. **Naidenoff siguió siendo el jefe hasta diciembre de 2023**:
letrap (06-12-2023) cuenta que Vischi lo sucede, *"Naidenoff, quien dejará una banca
después de 18 años"*. Lo de Losada en diciembre de 2021 fue la **vicepresidencia del
Senado**, en reemplazo de Lousteau, y el interbloque de JxC quedó para Cornejo (Infobae,
08-12-2021). Son dos cargos distintos y la fila confundía uno con el otro.

> **Consecuencia que queda abierta:** la fila **ALTA** de `PETCOFF NAIDENOFF` cierra en
> `2021-12-09` y, según esa misma fuente, debería llegar a **`2023-12-09`**. **No se
> extendió**: agrega cobertura en vez de sacarla, y eso lo decide Franco.

**FERNÁNDEZ SAGASTI, ANABEL / UNIDAD CIUDADANA / Senado / 2022-04-01 → 2025-12-09.**
El bloque Unidad Ciudadana (14 senadores), nacido de la división del FdT del 19-20 de
abril de 2022, lo presidió **JULIANA DI TULLIO** (Diario Río Negro, 20-04-2022, que da los
dos bloques con su presidente y su número de bancas).

> **Es la misma forma de error que el caso Bianchi:** una referente del espacio anotada
> como jefa. **Propuesta para Franco:** reemplazarla por `DI TULLIO, JULIANA` con esa misma
> ventana. No se agregó sola.

## Las 9 que siguen MEDIA, y qué falta para cada una

| fila | qué se encontró | qué falta |
|---|---|---|
| **DEL CAÑO / FIT** (349 proyectos) | Wikipedia confirma que el FIT **rota las bancas** por acuerdo, pero **no dice nada de la jefatura del bloque**. | Una fuente que nombre al presidente del bloque del FIT y sus tramos. Si la jefatura rota entre PTS y PO, una fila única desde 2014 es **estructuralmente incorrecta**, no sólo imprecisa. Es la de más volumen: vale la media hora. |
| **FERRARO / Coalición Cívica** (291) | La CC-ARI lo llama *"el presidente del bloque de Diputados Nacionales de la CC ARI"* en su cuenta oficial, y él firma comunicados por el bloque. Pero lo que aparece fechado (15-12-2018, 13-12-2020) es la presidencia **del partido**, no la del bloque. | La fecha de inicio de la **jefatura del bloque**. Son dos cargos que tiene la misma persona y las fuentes los mezclan. |
| **MASSA / UNA** (62) | 🔴 **Dudosa.** Chequeado (08-03-2018) atribuye la presidencia del bloque UNA 2015-2017 a **CLAUDIA RUCCI** (6 diputados), y la de Federal-UNA a Camaño. Massa aparece como referente del **interbloque**. | Decidir qué mide la columna `bloque`: si es el bloque parlamentario, la fila es de Rucci o de Camaño, no de Massa. **Es la forma exacta del caso Bianchi** y aporta 62 proyectos. |
| **CAMAÑO / UNA** (150) | Misma ambigüedad bloque/interbloque que la anterior. | Lo mismo. |
| **CICILIANI / Partido Socialista** | Chequeado (08-03-2018): **asume la jefatura del bloque socialista en 2015**. La jefatura queda confirmada; la fecha no. | El `desde` de la fila dice `2017-12-10` y puede estar **dos años corto**. Extenderlo agrega cobertura, así que no se tocó. |
| **PINEDO / PRO / Senado 2015-2019** (8) | Fue **presidente provisional del Senado** en ese período — un cargo del cuerpo, no del bloque. | Quién presidía el bloque PRO del Senado. La nota original ya dudaba de esto. |
| **PICHETTO / Justicialista** (11) | Sin fuente nueva. | Es una variante de etiqueta del bloque peronista bajo Pichetto: hay que validar el **alcance de la etiqueta**, no la jefatura. |
| **ZAMORA / Frente Cívico** (2) | Sin fuente nueva. | La fecha de inicio. |
| **THOMAS / Frente Peronista** (48) | Sin fuente nueva. | Jefatura formal del peronismo disidente mendocino 2011-2015. |

## Lo que este trabajo deja como regla

**Dos de quince estaban mal, y las dos tenían la misma forma:** confundir un cargo del
cuerpo (vicepresidencia del Senado) o el liderazgo de un espacio (referente del
interbloque) con la **presidencia del bloque parlamentario**, que es lo único que mide esta
tabla. Es la misma familia del caso Bianchi. Cuando una fila dice "referente", "conduce" o
"lidera" en vez de "preside el bloque", conviene tratarla como no validada.
