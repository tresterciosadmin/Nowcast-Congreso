> **SUPERSEDIDO (2026-06-29):** la fuente de verdad ahora es el documento controlado
> `docs/taxonomias/taxonomias.json` (con id estable por taxonomía) + `docs/taxonomias/TAXONOMIAS.md`.
> Este archivo queda como apunte histórico de la v1. El clasificador puede migrar a leer ese JSON.

# Taxonomía de temas — v1 GRANULAR (2 niveles, a ajustar)

Estructura **Área → Subtema**. Se clasifica al subtema; el área se deriva. Pensada
con tus 8 etiquetas del Excel (Económico/Fiscal, Laboral, Ambiente, Judicial, Acuerdo
internacional, Educación, Desregulación, Político) abiertas a mayor granularidad.

## Áreas y subtemas
1. **ECONOMÍA Y FINANZAS PÚBLICAS** → Presupuesto y gasto · Tributario/Impuestos · Deuda y financiamiento · Monetario y cambiario · Coparticipación/federalismo fiscal · Emergencia económica
2. **PRODUCCIÓN, COMERCIO E INVERSIÓN** → Promoción de inversiones (RIGI) · Industria y PyMEs · Agro, ganadería y pesca · Comercio interior y exterior · Regímenes especiales (p. ej. Zonas Frías)
3. **DESREGULACIÓN Y REFORMA DEL ESTADO** → Desregulación económica · Modernización del Estado · Empresas públicas/privatizaciones · Régimen de sociedades/comercial
4. **TRABAJO Y SEGURIDAD SOCIAL** → Relaciones laborales (reforma laboral) · Previsional/jubilaciones · Sindical · Riesgos del trabajo (ART) · Empleo público
5. **ENERGÍA** → Hidrocarburos (petróleo y gas) · Energía eléctrica · Renovables · Tarifas energéticas · Combustibles
6. **AMBIENTE Y RECURSOS NATURALES** → Bosques/glaciares/áreas protegidas · Agua · Minería · Residuos · Cambio climático
7. **INFRAESTRUCTURA, OBRAS Y TRANSPORTE** → Obra pública · Transporte · Vivienda y hábitat · Telecomunicaciones/digital
8. **SALUD** → Sistema de salud/hospitales · Salud mental · Medicamentos/vacunas · Discapacidad · Adicciones/ludopatía
9. **EDUCACIÓN** → Educación básica/media · Educación superior/universidades/financiamiento
10. **CIENCIA Y TECNOLOGÍA** → Ciencia y técnica · Innovación/economía del conocimiento · Propiedad intelectual/patentes
11. **CULTURA, DEPORTE Y MEDIOS** → Cultura/patrimonio · Deporte · Medios/comunicación
12. **JUSTICIA Y SEGURIDAD** → Derecho penal/código penal · Régimen penal juvenil · Organización judicial/magistratura · Seguridad interior · Narcotráfico · Derecho civil/comercial (códigos) · Propiedad (inviolabilidad)
13. **DEFENSA Y RELACIONES EXTERIORES** → Defensa/FFAA · Tratados y acuerdos internacionales (Mercosur-UE, PCT…) · Política exterior
14. **DERECHOS, GÉNERO Y SOCIEDAD** → Derechos humanos · Género/diversidad · Niñez e infancia · Pueblos originarios · Migraciones
15. **RÉGIMEN POLÍTICO E INSTITUCIONAL** → Reforma electoral · Partidos políticos · Reforma constitucional · Transparencia/lobby/ética pública · Organización del Estado/ministerios
16. **DESARROLLO SOCIAL** → Asistencia social/planes · Pensiones no contributivas (p. ej. fraude pensiones invalidez)

Auxiliares (no sustantivos): **HOMENAJES Y DECLARACIONES** · **TRÁMITE PARLAMENTARIO** · **SIN CLASIFICAR**

## Mapeo de tus 8 etiquetas → áreas
Económico/Fiscal→1 · Desregulación→3 · Laboral→4 · Ambiente→6 (Energía sale a 5) · Educación→9 (Ciencia→10, Cultura→11) · Judicial→12 · Acuerdo internacional→13 · Político→15.

## Las 18 leyes del zip → subtema (validación)
Presupuesto 2026→1.Presupuesto · Inocencia Fiscal/Compromiso Nacional→1.Tributario · Super RIGI→2.Inversiones · Modif. Sociedades→3.Sociedades · Modernización Laboral→4.Laboral · Zonas Frías→2.Regímenes especiales/Energía-tarifas · Glaciares→6.Bosques/glaciares · Financiamiento Universitario→9.Superior · Patentes PCT→10.Propiedad intelectual · Salud Mental/Ludopatía→8 · Régimen Penal Juvenil/Inviolabilidad Propiedad→12 · Acuerdo Mercosur-UE→13.Tratados · Reforma Electoral→15.Electoral · Lobby→15.Transparencia · Hojarasca→3.Desregulación · Fraude Pensiones Invalidez→16.

## Para ajustar
Decime granularidad (más/menos subtemas), nombres, o si querés un 3er nivel. Edito acá y el clasificador lo toma.

## Reglas de frontera (decididas con Franco, 2026-06-27)
- **Juego / apuestas / ludopatía → SALUD** (subtema adicciones), no Justicia.
- **Reformas de códigos de fondo (Penal, Civil, Comercial, de Sociedades) → JUSTICIA**, cualquiera sea la materia económica. Subtema "Código civil/comercial/sociedades" o "Penal".
- Con estas reglas, el clasificador concuerda 15/15 con las etiquetas manuales.
