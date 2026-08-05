# ⚠️ BORRAR `bot-diario.yml` — es un DUPLICADO

`bot-diario.yml` de esta carpeta **duplica el workflow que ya viene corriendo**
("Bot diario (padrón vivo)", corrida #22 al 04-08). No pude borrarlo desde acá
(la carpeta montada no permite eliminar). **Borralo a mano.**

Si los dos llegaran a correr, se pisarían al pushear.

## Lo único que vale rescatar del duplicado

Dos mejoras que el workflow actual no tiene. Si te parecen útiles, se le agregan
al que ya existe:

1. **Aviso de canónica pendiente.** El bot detecta actas nuevas pero
   `run_pipeline.py` no corre solo — las actas quedan en un parquet que el modelo
   no mira. La mejora abre un issue con los comandos exactos, sin duplicar si ya
   hay uno abierto.
2. **Crear el label si no existe.** `issues.create` con un label inexistente
   falla, y el aviso se pierde en silencio.

Están escritas en `bot-diario.yml`, en los pasos "¿Hay actas nuevas sin
incorporar a la canónica?" y "Avisar que hay que reconstruir la canónica".
