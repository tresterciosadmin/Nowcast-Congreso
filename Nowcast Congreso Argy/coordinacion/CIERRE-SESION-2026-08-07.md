# Cierre de sesión — 2026-08-07 (Valle + Claude)

**Titular:** se cerró el pendiente más viejo del repo. El bot recolectaba desde marzo y ningún
módulo leía sus datos; ahora `proyectos.db` es la fuente de verdad de los proyectos y el embudo
lee de ahí.

---

## 1 · Lo que hay que hacer a mano (Valle)

| # | qué | por qué |
|---|---|---|
| 1 | **Commitear y pushear** | nada de hoy está en GitHub |
| 2 | `Remove-Item ".git\index.lock" -Force` | lo dejé yo al verificar el `.gitignore`; traba GitHub Desktop |
| 3 | Borrar lo anotado en `Archivos_Borrar/PENDIENTES-DE-BORRAR.md` | ~85 MB de pruebas + un `.tmp` vacío + `proyectos.db-journal` |

**Nada más queda pendiente de correr.** Verificado en disco al cerrar:
`variables/embudo/outputs/p_embudo.parquet` tiene **42.141 proyectos** y el backtest guardado da
**0,363 / 0,4195** — o sea que la promoción ya quedó hecha en la última corrida.

### Texto para el commit

```
ADR-0009: proyectos.db es la fuente de verdad de los proyectos

DATOS
- CKAN refrescado (llevaba 1 mes sin correr): 112.793 -> 113.177 proyectos,
  02-jun -> 30-jun. HCDN publica con ~5 semanas de atraso. OJO: la ingesta usa
  cache salvo REFRESH=1 (la 1ra corrida no bajo nada y el log lo dice bajito).
- proyectos.db creada: 114.708 proyectos = backfill CKAN + bot. NO viaja a git
  (89 MB); se rehace en ~1 min con migrar_ckan.py + upsert_bot.py.
- EL BOT YA ENTREGA: +1.531 proyectos, 514 de ley del SENADO, y por primera vez
  los COFIRMANTES (1.222 proyectos, max 15 firmantes). El universo del modelo
  pasa de estar congelado en junio a llegar al 5 de agosto.
- giros_iniciales recalculado: el giro MEDIDO al ingresar sube de 1.889 a 2.267
  proyectos (y de 2.927 a 4.449 contando la reconstruccion).

MODELO
- variables/embudo lee de SQLite; la ruta parquet queda de fallback
  (EMBUDO_FUENTE=parquet).
- VERIFICADO: cohorte identica celda por celda entre las dos rutas (41.470
  filas, 13 columnas, cero diferencias) y backtest 0,3643 / 0,4195 por ambas.
- p_embudo regenerado con 42.141 proyectos (era del 12-jul, con un bug ya
  corregido).

CALIDAD
- Cuarentena (decision de Valle): lo que no se pudo leer va a cuarentena.db,
  una base APARTE. La carga no se frena por una fila rara; una avalancha (>5%,
  con piso de 10 filas) si. cuarentena.db SI viaja a git.
- verificar.py: 14 invariantes que cortan con exit 1. Los cargadores lo corren
  solos. test_verificar.py rompe la base a proposito para probar que el control
  se dispara (10 tests).

INFRA
- Los 3 workflows a Node 24 (checkout v5, setup-python v6, github-script v8) y
  verificados en verde. github-script NO estaba en la lista y tenia el mismo
  problema: es el que abre los avisos.
- bot-diario.yml renombrado: se llamaba "Bot diario (padron vivo)" —el nombre
  del OTRO workflow— y el job "dae-senado" de cuando solo traia el Senado.

CORRECCIONES A DOCUMENTOS QUE MENTIAN
- "es pegar dos contratos que existen" (URGENTE): FALSO. upsert_proyecto
  reemplaza las hijas completas; dos upserts seguidos pierden datos.
- El README de datos/proyectos decia "la base nunca se creo".
- El de bot_recoleccion decia "recolecta pero no entrega".
- El "blocker es proyectos.db + M1" de las taxonomias: desbloqueado.
- El git pull --rebase que ESTADO daba como pendiente ya estaba hecho.
```

---

## 2 · Lo que cambió, en orden de importancia

| | antes | ahora |
|---|---:|---:|
| el modelo ve proyectos hasta | **2 de junio** | **5 de agosto** |
| cohorte de proyectos de ley | 41.470 | **42.141** |
| proyectos de ley del Senado incorporados | — | **514** |
| proyectos con cofirmantes | 0 | **1.222** |
| skill (sancionado / recinto) | — | **0,3643 / 0,4195** |

---

## 3 · Los tres errores del día, que valen más que los números

**Ninguno dio error.** El programa terminaba bien y estaba mal:

1. La carga informó **1.531 proyectos** y el modelo vio **uno** — las altas del bot no tienen id
   de CKAN y todos los nulos colapsaban en una fila.
2. El log dijo **559** giros corregidos donde antes decía **633** — el bot pisaba el giro
   acumulado con el del día de ingreso.
3. **34 expedientes** descartados como *"formato inesperado"* eran los del **Poder Ejecutivo**,
   los de mayor peso del modelo.

Los tres aparecieron **mirando si el número que salió era el que tenía que salir.** Ninguno se
habría notado viendo si el programa terminaba bien. De ahí salió `verificar.py`.

**Y un cuarto, en mi propio control:** `migrar_ckan` reportaba *"falló 1 de 8"* cuando no fallaba
nada. **Un control que grita cuando todo está bien es peor que no tenerlo.** Corregido con etapas.

---

## 4 · Decisiones de Valle que quedaron en el diseño

1. **Opción B directa** para el ADR-0009, con el Senado en la misma tanda: *"con el modelo ya
   andando, el incentivo para migrar se evapora"*.
2. **Cuarentena en vez de freno** — frenó mi primer diseño: *"trabajamos con muchos datos de
   manera constante"*. Tenía razón: un cron que aborta por una fila rara vuelve al problema que
   el `continue-on-error` ya había resuelto.
3. **Base separada, no etiqueta:** *"los pendientes van a una base de datos distinta y los que
   están bien pasan a la general"*.
4. **El sesgo del Senado no se parchea de a un síntoma** → nace la línea **Revisión de las
   Comisiones**.

---

## 5 · Qué queda abierto

**`URGENTE.md` tiene 2 ítems y ninguno bloquea:**
- las 15 jefaturas de bloque por validar (viene del 30-07);
- prolijidad: el padrón 256/257, y **exportar `proyecto_taxonomias` a un archivo versionado antes
  de que el agente escriba** — es lo único de la base que no se reconstruye gratis.

**La línea nueva: `REVISIÓN DE LAS COMISIONES`** (en `PLAN-DE-TRABAJO.md`), con dos insumos:
1. **El universo del Senado está sesgado por supervivencia** — el modelo le da 48% de
   probabilidad a un proyecto del Senado contra 1,7% a uno de Diputados, porque la base sólo tiene
   los que ya cruzaron a Diputados. **Precaución vigente: no publicar P(sanción) de proyectos con
   origen Senado.**
2. **74.440 proyectos con giros que no están en la tabla principal**, sin explicación. Si son
   legítimos, la tasa base del 3,4% está mal calculada.

**Anotado, no urgente:** `test_modulador_shrink.py` y `test_store.py` no son tests de pytest (son
scripts con `SystemExit` al importarse) y **rompen la colección** si se corre `pytest` sobre todo
el repo de una vez.
