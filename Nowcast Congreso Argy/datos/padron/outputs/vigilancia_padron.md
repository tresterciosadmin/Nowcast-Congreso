<<<<<<< Updated upstream
# Padrón vivo — 2026-08-24 11:15 UTC
=======
# Padrón vivo — 2026-08-21 14:16 UTC
>>>>>>> Stashed changes

## 🟡 Hay novedades en la composición

### DIPUTADOS
- Bancas vigentes: **256** (esperadas 257) · padrón versionado: 257 · fuente: `api:argentinadatos`
- 🟡 **banca_vacante** — 256/257 — dentro de tolerancia (vacante transitoria).

**Bajas (1)**

  - Pitrola, Nestor — PO-FIT-U-PARTIDO OBRERO EN EL FRENTE DE LA IZQUIERDA Y DE TRABAJADORES - UNIDAD (nan)

**Cambios de bloque (3)** — señal política, no ruido administrativo

  - Bregman, Myriam: OTRO / PROVINCIAL → IZQUIERDA
  - Del Caño, Nicolas: OTRO / PROVINCIAL → IZQUIERDA
  - Del Pla, Romina: OTRO / PROVINCIAL → IZQUIERDA

**Composición por linaje**

  - LA LIBERTAD AVANZA: 95
  - FdT-UxP (kirchnerismo): 93
  - OTRO / PROVINCIAL: 43
  - PRO: 12
  - RADICALISMO: 6
  - IZQUIERDA: 3
  - COALICION CIVICA: 2
  - PERONISMO FEDERAL: 2

### SENADO
- Bancas vigentes: **72** (esperadas 72) · padrón versionado: 72 · fuente: `archivo:raw_versionado`

**Composición por linaje**

  - FdT-UxP (kirchnerismo): 21
  - LA LIBERTAD AVANZA: 21
  - OTRO / PROVINCIAL: 17
  - RADICALISMO: 10
  - PRO: 3

---

**Qué hacer.** Regenerar el padrón y volver a correr lo que depende de él:

```bash
python datos/padron/src/bajar_nomina.py diputados --padron
python datos/padron/src/ingesta_padron.py senado
```
