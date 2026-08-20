# tests/ — los controles que NO son de un modulo

<!-- huella: 07465b16e4ae -->

**Resumen:** Tests que cruzan modulos y por eso no pueden vivir dentro de ninguno. Cada modulo tiene sus propios tests en `<modulo>/tests/`; acá van solo los que verifican acuerdos ENTRE modulos.

## Buscar acá si

- dos modulos tienen una copia de la misma funcion y hay que ver si siguen de acuerdo
- una definicion compartida (periodo parlamentario, tipo de mayoria, bancas por camara) cambio en un lado
- un test falla y no pertenece a ningun modulo en particular

## Que hay acá

| Archivo | Que verifica |
|---|---|
| `test_definiciones_compartidas.py` | que las 4 copias de `periodo_parlamentario`, las 3 de `normalizar_mayoria` y las constantes `MIEMBROS` / `MARGEN_DISPUTADA` / `CONDUCTAS` / presentes sigan diciendo lo mismo, sobre fechas borde y los dos backends de dtype |

## Como correr

```powershell
python -m pytest tests/ -q            # desde la raiz del proyecto
```

En PowerShell **no hay `bash` en el PATH**. Si un instructivo de este repo dice
`bash algo.sh`, buscá el equivalente `.ps1` al lado (por ejemplo
`.mapa/instalar-hook.ps1`).

## ⚠️ Ojo: en este repo los tests son SCRIPTS, no modulos de pytest

**Descubierto el 2026-08-20 al correr la suite entera por primera vez.** De los
~36 archivos `test_*.py` del repo, casi ninguno define funciones `test_`: los
chequeos corren **al importar el archivo**, cuentan con un `check()` propio, y al
final imprimen `N chequeos OK, M fallas` y salen con `raise SystemExit(1 if fail)`.
Por eso se corren de a uno, como los documenta su docstring:

```powershell
python datos/proyectos/tests/test_verificar.py
python variables/embudo/tests/test_embudo.py
```

Eso funciona y **no hay que cambiarlo**. Lo que NO hay que hacer es correr pytest
sobre todo el repo, por dos razones:

1. **Aborta.** Un `raise SystemExit` a nivel de modulo se dispara cuando pytest
   IMPORTA el archivo para recolectarlo, y mata la corrida entera con
   `INTERNALERROR` antes de ejecutar un solo test — incluidos los de otras
   carpetas. Pasa hoy en `datos/bot_recoleccion/tests/test_votaciones.py` (L71) y
   `variables/proyecto/tests/test_modulador_shrink.py` (L120).
2. **Peor: puede mentir en verde.** Un archivo sin funciones `test_` corre sus
   chequeos al importarse; si un `check()` falla, imprime `FALLA:` pero pytest
   no lo ve como test fallado. Un control que no grita cuando algo esta mal es
   exactamente lo que este repo viene evitando.

`datos/proyectos/tests/test_taxonomias_backup.py` era del tipo (1) y se arreglo:
su cuerpo vive en `_correr()` y sirve para las dos cosas — sigue andando como
script y ademas expone `test_respaldo_de_taxonomias` para pytest. Es el patron a
usar si algun dia se convierte el resto; **no se convirtio nada mas a proposito**,
son ~30 archivos de modulos con dueño.

**Comando correcto para esta carpeta:**

```powershell
python -m pytest tests/ -q                      # solo lo que cruza modulos
python -m pytest tests/ datos/proyectos/tests -q # + el unico modulo ya migrado
```

## Trampas

- **Un test de acá que falla no se arregla tocando el test.** Falla porque dos modulos dejaron de estar de acuerdo: hay que decidir cual tiene razon y corregir el otro.
- Hay un `xfail` vivo: las cuatro copias de `periodo_parlamentario` revientan con backend `pyarrow` (`pd.to_numeric` conserva `int64[pyarrow]` y `a % 2` no esta implementado). No se nota en produccion porque `read_parquet` devuelve numpy. El arreglo es una linea por copia; esta anotado en ESTADO.
