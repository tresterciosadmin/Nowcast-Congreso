# Taxonomías de proyectos de ley — vocabulario controlado

**Fuente de verdad:** `taxonomias.json` (este `.md` es la vista humana). Si editás, editá el JSON; el agente lee el JSON.

**Qué es.** La lista cerrada de temas con la que se clasifican los proyectos de ley. Está en dos niveles: **Área → Subtema**. Se etiqueta al **subtema**; el área se deriva sola. Cada entrada tiene un **id estable** (`ECON.TRIB`) además del nombre legible: el id **no cambia** aunque renombres el tema, así los cruces históricos nunca se rompen.

## Reglas de uso (las sigue el agente)
- **Multi-etiqueta.** Un proyecto casi siempre tiene **varios** subtemas. Asignar **todos** los que apliquen (no forzar uno solo).
- **Elegir solo de la lista.** El agente asigna únicamente ids que existan en `taxonomias.json`. **No inventa** ids ni nombres.
- **Si no encaja.** Marcar `AUX.SINCLASIF` y **proponer** un candidato (texto libre) para revisión humana. El agente **no agrega** taxonomías por su cuenta; las agrega una persona editando el JSON.
- **Confianza.** El agente puede registrar un puntaje 0–1 por etiqueta (se guarda en `proyecto_taxonomias.confianza`).
- **Auxiliares** (`AUX.*`) no son temas sustantivos: homenajes/declaraciones, trámite puro, o sin clasificar.

## Reglas de frontera (decididas con Franco)
- **Juego / apuestas / ludopatía → `SALUD.ADICC`** (no Justicia).
- **Reforma de un código de fondo** (Penal, Civil, Comercial, de Sociedades) **→ `JUST.PENAL` o `JUST.CIVCOM`**, cualquiera sea la materia económica de fondo.

## Cómo agregar / quitar / editar
1. Editar `taxonomias.json`.
2. **Agregar:** nueva entrada con un `id` **nuevo y único** (área en mayúsculas + punto + código corto, p. ej. `ENER.NUCLEAR`). No reutilizar un id viejo para otra cosa.
3. **Renombrar:** cambiar solo el `nombre`, **dejando el `id` igual** (así no se rompe nada).
4. **Quitar:** preferir **no borrar** ids ya usados; si un tema queda obsoleto, marcarlo en el nombre (p. ej. "(obsoleto)") en vez de eliminar el id.
5. Correr `python src/loader.py validar taxonomias.json` para chequear que no haya ids duplicados.

Le podés pedir a Claude/una IA "agregá el subtema X al área Y" o "separá Z en dos" y que edite el JSON respetando estas reglas.

## Áreas y subtemas (v1)

| Área | Subtemas (id — nombre) |
|---|---|
| **ECON** Economía y Finanzas Públicas | `ECON.PRESU` Presupuesto · `ECON.TRIB` Tributario · `ECON.DEUDA` Deuda · `ECON.MON` Monetario/cambiario · `ECON.COPART` Coparticipación · `ECON.EMERG` Emergencia económica |
| **PROD** Producción, Comercio e Inversión | `PROD.INVER` Inversiones (RIGI) · `PROD.INDPYME` Industria/PyMEs · `PROD.AGRO` Agro/ganadería/pesca · `PROD.COMEX` Comercio · `PROD.REGESP` Regímenes especiales |
| **DESREG** Desregulación y Reforma del Estado | `DESREG.DESECO` Desregulación · `DESREG.MODEST` Modernización del Estado · `DESREG.EMPUB` Empresas públicas/privatizaciones · `DESREG.SOCIED` Sociedades/comercial |
| **TRAB** Trabajo y Seguridad Social | `TRAB.LABOR` Laboral · `TRAB.PREV` Previsional/jubilaciones · `TRAB.SINDIC` Sindical · `TRAB.ART` ART · `TRAB.EMPLEOPUB` Empleo público |
| **ENER** Energía | `ENER.HIDRO` Hidrocarburos · `ENER.ELEC` Eléctrica · `ENER.RENOV` Renovables · `ENER.TARIFA` Tarifas/subsidios · `ENER.COMBUS` Combustibles |
| **AMB** Ambiente y Recursos Naturales | `AMB.BOSQUE` Bosques/glaciares · `AMB.AGUA` Agua · `AMB.MINER` Minería · `AMB.RESID` Residuos · `AMB.CLIMA` Cambio climático |
| **INFRA** Infraestructura, Obras y Transporte | `INFRA.OBRA` Obra pública · `INFRA.TRANSP` Transporte/trenes · `INFRA.VIVIENDA` Vivienda/hábitat · `INFRA.TELECOM` Telecomunicaciones |
| **SALUD** Salud | `SALUD.SISTEMA` Sistema/hospitales/obras sociales · `SALUD.MENTAL` Salud mental · `SALUD.MEDIC` Medicamentos/vacunas · `SALUD.DISCAP` Discapacidad · `SALUD.ADICC` Adicciones/ludopatía |
| **EDU** Educación | `EDU.BASICA` Básica/media · `EDU.SUPERIOR` Superior/universidades |
| **CYT** Ciencia y Tecnología | `CYT.CIENCIA` Ciencia y técnica · `CYT.INNOV` Innovación/economía del conocimiento/software · `CYT.IA` Inteligencia artificial · `CYT.CIBER` Ciberseguridad/datos · `CYT.PI` Propiedad intelectual/patentes |
| **CULT** Cultura, Deporte y Medios | `CULT.CULTURA` Cultura/patrimonio · `CULT.DEPORTE` Deporte · `CULT.MEDIOS` Medios/comunicación |
| **JUST** Justicia y Seguridad | `JUST.PENAL` Penal · `JUST.PENALJUV` Penal juvenil · `JUST.JUDIC` Organización judicial · `JUST.SEGINT` Seguridad interior · `JUST.NARCO` Narcotráfico · `JUST.CIVCOM` Civil/comercial (códigos) · `JUST.PROPIED` Propiedad |
| **DEF** Defensa y Relaciones Exteriores | `DEF.DEFENSA` Defensa/FFAA · `DEF.TRATADO` Tratados/acuerdos · `DEF.EXTERIOR` Política exterior |
| **DERSOC** Derechos, Género y Sociedad | `DERSOC.DDHH` Derechos humanos · `DERSOC.GENERO` Género/diversidad · `DERSOC.NINEZ` Niñez · `DERSOC.ORIGIN` Pueblos originarios · `DERSOC.MIGRA` Migraciones |
| **POLINST** Régimen Político e Institucional | `POLINST.ELECT` Electoral · `POLINST.PARTIDOS` Partidos · `POLINST.CONST` Reforma constitucional · `POLINST.ETICA` Transparencia/lobby/ética · `POLINST.ORGEST` Organización del Estado |
| **DESSOC** Desarrollo Social | `DESSOC.ASIST` Asistencia social/planes · `DESSOC.PNC` Pensiones no contributivas |
| **Auxiliares** | `AUX.HOMENAJE` Homenajes/declaraciones · `AUX.TRAMITE` Trámite · `AUX.SINCLASIF` Sin clasificar |

## Relación con el resto
- El agente de taxonomías (próximo módulo) lee este JSON, lee el PDF del proyecto y escribe en `datos/proyectos` → tabla `proyecto_taxonomias` (con el `taxonomia_id` de acá).
- Reemplaza como fuente de verdad a `variables/proyecto/TAXONOMIA.md` (que queda como apunte histórico). El clasificador por keywords de `variables/proyecto` puede migrar a leer este JSON.
