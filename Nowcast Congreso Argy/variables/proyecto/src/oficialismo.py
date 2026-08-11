"""⛔ NEUTRALIZADO 2026-08-09 — DUPLICABA `origen_lider.GOBIERNOS`.

Este módulo (y `data/gobiernos_oficialismo.csv`) se crearon el 2026-08-09 sin ver
que la tabla de oficialismo por gobierno YA EXISTÍA en
`variables/proyecto/src/origen_lider.py` (`GOBIERNOS` + `oficialista_por_fecha`).
Mantener dos tablas es el modo de falla que el repo advierte: se desincronizan.

USAR LA QUE EXISTE:
    from origen_lider import oficialista_por_fecha, GOBIERNOS

El único aporte de esta versión —sumar PRO al oficialismo de Milei— ya se aplicó
en `origen_lider.GOBIERNOS` (2026-08-09).

Pendiente de borrado en Archivos_Borrar/PENDIENTES-DE-BORRAR.md. No se importa
desde ningún lado en producción (sólo se usó en diagnósticos de esa sesión).
"""
raise ImportError(
    "oficialismo.py fue neutralizado: usá origen_lider.oficialista_por_fecha, "
    "que es la tabla canónica. Ver el docstring.")
