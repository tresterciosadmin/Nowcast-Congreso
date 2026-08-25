# ADR-0011 — El chequeo del `.gitignore` estaba mal documentado

**Fecha:** 2026-08-21 · **Estado:** Aceptada · **Quién:** Claude (con Valle)

## Contexto

`PROTOCOLO-GIT.md` documenta desde hace meses un chequeo de 10 segundos, que es la
defensa del repo contra las reglas `*.csv` / `*.parquet` / `**/data/clean/`:

```powershell
git check-ignore -q <archivo>   # si sale 0, está IGNORADO y no viaja
```

**Ese comentario es falso**, y falla justo en el caso que importa. El 21-08-2026,
al agregar `padron_diputados_historico.csv` (un CSV nuevo, con su excepción `!`
recién puesta en el `.gitignore`), el chequeo devolvió `exit=0` en la PC de Valle.
Leído según el protocolo, eso significa «está ignorado, no viaja» — y era mentira:

```
git check-ignore -v "datos/padron/data/padron_diputados_historico.csv"
Nowcast Congreso Argy/.gitignore:120:!datos/padron/data/padron_diputados_historico.csv   datos/padron/data/padron_diputados_historico.csv
exit=0

git add -n "datos/padron/data/padron_diputados_historico.csv"
add 'Nowcast Congreso Argy/datos/padron/data/padron_diputados_historico.csv'
```

La regla que matcheó es **la excepción** (empieza con `!`) y `git add -n` confirma
que el archivo se agrega. `check-ignore` devuelve 0 cuando la ruta **matchea alguna
regla**, y una negación es una regla. El `-q` esconde cuál fue.

**Por qué es grave y no un detalle:** el chequeo da el resultado equivocado
**exactamente sobre los archivos que el equipo rescató a mano**, que son los únicos
que tienen una línea `!`. Cada vez que alguien agregó una excepción y volvió a
chequear, el comando le dijo que no había servido de nada. El `.gitignore` tiene
hoy cinco tandas de comentarios cada vez más enfáticos sobre el mismo problema;
esta es al menos una parte de por qué.

## Segundo error, en la misma línea del protocolo

`PROTOCOLO-GIT.md` también dice que los comandos de git que reciben una ruta
«hay que correrlos desde la raíz con ruta root-relative, **o fallan**».

No fallan: **contestan otra cosa.** Correr, desde adentro de `Nowcast Congreso
Argy/`, el comando con el prefijo `"Nowcast Congreso Argy/"` produce la ruta
inexistente `Nowcast Congreso Argy/Nowcast Congreso Argy/datos/...`, que no le pega
a ninguna excepción y cae en la regla general:

```
.gitignore:5:*.csv   Nowcast Congreso Argy/datos/padron/data/padron_diputados_historico.csv
exit=0
```

Reproducido en un repo limpio del sandbox con el mismo `.gitignore`. Un archivo
perfectamente versionable se ve idéntico a uno ignorado. Es la misma falla del
21-08 mirada desde el otro lado, y las dos juntas explican por qué el chequeo
generó una falsa alarma en vez de tranquilidad.

## Decisión

1. **Para un archivo NUEVO —el caso de esta regla— el chequeo es `git add -n
   <archivo>`.** No simula reglas: le pregunta a git qué haría. Si imprime
   `add '<ruta>'`, el archivo viaja. Si no imprime nada, está ignorado.

   ⚠️ **`add -n` NO sirve para auditar archivos YA TRACKEADOS.** Un archivo que ya
   está en el repo y no cambió no imprime nada, exactamente igual que uno ignorado.
   Se comprobó el 21-08 al intentar auditar las 39 excepciones del `.gitignore`:
   dio "8 de 68 viajan" y **60 de esos 60 estaban perfectamente bien**, simplemente
   ya commiteados. Es la misma clase de error que este ADR vino a corregir, cometido
   al reusar el comando fuera de su caso.

   **Para auditar rutas existentes:** `git check-ignore -v --non-matching -- <rutas>`,
   que imprime una línea por ruta con la regla que matchea. Está ignorada si la regla
   **no** empieza con `!` y no es `::` (que significa "ninguna regla matchea", o sea
   que viaja).
2. **Si se quiere ver POR QUÉ, `git check-ignore -v` y se lee la regla**, nunca
   `-q`. Una regla que empieza con `!` significa que **viaja**.
3. **Se prohíbe leer el código de salida de `check-ignore` como «ignorado sí/no».**
   Tiene **tres** valores y ninguno significa eso: `0` = la ruta matcheó alguna
   regla (¡incluida una excepción!), `1` = no matcheó ninguna, `128` = error — por
   ejemplo, correrlo fuera del repo, que es lo que pasa si uno abre PowerShell y no
   hace `cd` (arranca en `C:\WINDOWS\system32`). Tres códigos, tres significados,
   y el que uno quiere saber no es ninguno de los tres.
4. **La ruta se escribe relativa a donde uno está parado.** El prefijo
   `"Nowcast Congreso Argy/"` es correcto **desde la raíz git** y veneno desde
   adentro del proyecto. Ante la duda, `git add -n` con ruta relativa a la carpeta
   actual, que es lo que uno tiene a mano.

## Consecuencias

- Se corrige `PROTOCOLO-GIT.md` (sección «Antes de commitear»).
- Los `git check-ignore -q` que quedan mencionados en `TABLERO.md`,
  `ESTADO-DEL-PROYECTO.md` y `producto/dashboard/README.md` son **registro
  histórico de sesiones ya cerradas**: no se reescriben. Lo que se corrige es la
  instrucción vigente, que vive en el protocolo.
- **La pregunta abierta se contestó el mismo día: NINGUNA excepción está rota.** Se
  pasaron las **39 excepciones de datos** del `.gitignore` por
  `git check-ignore -v --non-matching`, en la PC de Valle: **68 archivos en disco, cero
  ignorados**. O sea que el chequeo viejo mentía, pero el `.gitignore` en sí siempre
  estuvo bien y ninguno de los archivos rescatados en las cuatro tandas anteriores se
  perdió. (Se dejaron afuera `*.md`, `*.html`, `*.docx` y los `.gitkeep`, que no son
  contratos de datos.)
