# Nowcast Congreso Argy — integración de "La Década Votada"

Implementación en Python de los datos del paquete R [`legislAr`](https://github.com/PoliticaArgentina/legislAr),
que a su vez expone el proyecto **La Década Votada** de Andy Tow.

## Qué es esta fuente

`legislAr` no contiene los datos: es un wrapper que descarga CSVs alojados en el
repo `PoliticaArgentina/data_warehouse`. Esos CSVs son lo valioso. Por cámara
(`diputados` / `senadores`) hay cuatro bases:

| Base | Contenido | Columnas usadas |
|------|-----------|-----------------|
| `bloques` | partidos / bloques | id, nombre, color |
| `diputados` | legisladores | id, nombre, provincia, color |
| `votaciones` | voto individual por proyecto | asunto_id, legis_id, bloque_id, voto |
| `asuntos` | proyectos votados | id, fecha (col 5), descripción (col 17) |

Código del voto: `0=AFIRMATIVO, 1=NEGATIVO, 2=ABSTENCION, 3=AUSENTE, otro=PRESIDENTE`.

Cobertura: histórica (la "década votada"), llega aproximadamente hasta 2019. Útil
como **base de entrenamiento histórica**, no como feed en tiempo real.

## Cómo se implementa (Python + base propia + modelo)

Dos scripts, pensados para tu stack:

### 1. `legislar_data.py` — ingesta a base propia

Descarga las 4 bases × 2 cámaras y las carga en una SQLite local, con índices.

```bash
pip install pandas
python legislar_data.py --db legislar.db
```

Resultado: `legislar.db` con las tablas `bloques`, `legisladores`, `votaciones`,
`asuntos` (cada una con columna `camara`). A partir de acá podés consultarlo con
SQL libremente o conectarlo a PostgreSQL/DuckDB cambiando solo la capa de conexión.

### 2. `features.py` — tabla analítica para el nowcast

Arma un registro por legislador-votación y deriva variables predictivas,
calculadas **solo con el pasado** de cada legislador (sin fuga de información):

- `disciplina_bloque` — % histórico de veces que vota con la mayoría de su bloque.
- `tasa_afirmativa` — propensión histórica a votar AFIRMATIVO.
- `tasa_ausencia` — propensión histórica a estar ausente.
- `aprobado` — target a nivel proyecto (mayoría simple de presentes).

```bash
python features.py --db legislar.db --out features.parquet
```

## Propuesta de modelo de pronóstico

El nowcast tiene dos niveles posibles:

1. **Nivel legislador (recomendado).** Modelo de clasificación que predice el voto
   de cada legislador (afirmativo / negativo / ausente) a partir de bloque,
   provincia, disciplina histórica y tipo de proyecto. Luego se **agregan** los
   votos predichos para estimar la probabilidad de aprobación. Es más interpretable
   y aprovecha que la disciplina partidaria argentina es muy predictiva.

2. **Nivel proyecto.** Modelo directo sobre la composición del recinto (escaños por
   bloque) que estima P(aprobación). Más simple, menos granular.

Para que sea un *nowcast* real (Congreso actual, 2026) hay que sumar la composición
vigente de bancas, que esta fuente no trae más allá de ~2019. Esa pieza se obtiene
de otra base (p. ej. datos abiertos de [HCDN](https://datos.hcdn.gob.ar/) o el
Senado) y se combina con las tasas históricas por bloque que sí salen de acá.

## Limitaciones a tener presente

- Los datos llegan hasta ~2019: sirven para entrenar/calibrar, no para el estado actual.
- `aprobado` es una heurística de mayoría simple; ajustar según quórum y tipo de ley
  (algunas requieren mayorías especiales).
- La fuente puede cambiar de ubicación; el origen es el repo `data_warehouse`.

## Atribución

Datos: proyecto **La Década Votada** de Andy Tow (https://decadavotada.andytow.com/doc.html).
Wrapper original en R: `{legislAr}`, parte del universo **polAr** (PolíticaArgentina).
