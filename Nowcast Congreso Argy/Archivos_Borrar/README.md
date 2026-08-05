# Archivos_Borrar

Régimen definido en `CLAUDE.md`. **Nada de acá es fuente de verdad.** Es todo
descartable: cachés, salidas intermedias, pruebas, y —desde el 04-08-2026—
**los archivos que Claude tiene que descartar pero no puede eliminar por sí
mismo** (tiene permiso de lectura y escritura sobre la carpeta, no de borrado).

## Cómo funciona

Cuando Claude necesita que un archivo desaparezca:

1. Deja acá una copia, con el nombre `BORRAR_<ruta-original-con-guiones>`.
2. **Neutraliza el original** para que no haga daño mientras espera (un workflow
   se deja sin disparadores automáticos, un script se deja sin `__main__`, etc.).
3. Lo anota en `PENDIENTES-DE-BORRAR.md`, con la ruta exacta y por qué.

El dueño humano borra cuando quiera. Nada rompe si tarda.

## Por qué importa neutralizar y no sólo avisar

El 04-08 quedó un workflow duplicado en `.github/workflows/` que, de haber
llegado al repo activo, habría corrido en paralelo con el bot real y los dos se
habrían pisado al pushear. Un archivo que "hay que borrar" y mientras tanto
sigue funcionando no es un pendiente: es un problema activo.
