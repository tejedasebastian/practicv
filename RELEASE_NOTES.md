# PractiCV v0.2.0

**Captura desde el navegador, alertas de correo, Practilizate y dashboard.**

v0.2 amplía el MVP local-first sin cambiar su alcance: sigue siendo una app de un
solo usuario, sin auto-postulación y sin promesas de empleo.

---

## Qué incluye

### Bookmarklet

- Botón instalable desde `/bookmarklet`; arrastrar a la barra de marcadores.
- Lee JSON-LD, título y texto visible de la oferta.
- Abre `/captura` con los datos en el hash, previsualiza, permite editar y
  confirma antes de guardar.
- No guarda HTML crudo ni hace POST cross-origin.
- `source_type=bookmarklet` y deduplicación estándar.

### Alertas de correo `.eml`

- Importa un `.eml` exportado desde Gmail u Outlook.
- Extrae enlaces del HTML y del texto plano; el usuario elige cuáles importar.
- Captura cada enlace con JSON-LD/OpenGraph y deduplica.
- No guarda el correo original ni tokens.
- Límite: OAuth en vivo queda pendiente de credenciales de una app registrada.

### Adaptador Practilizate

- Importa el CSV de Practilizate con mapeo explícito de columnas.
- Desactivado por defecto (`PRACTICV_PRACTILIZATE_ENABLED=false`).
- Sin dependencia de código ni base de datos de Practilizate.
- La app sigue funcionando si el adaptador está apagado.

### Dashboard Power BI

- PBIP en `dashboard/PractiCV.pbip`.
- Página `Embudo`: tarjetas, funnel por etapa, slicer de estado y tabla.
- Medidas: total, postuladas, entrevistas, ofertas y match promedio.
- Datos sintéticos de demo (24 postulaciones), sin PII.
- Validación: **0 errores / 0 warnings**.
- Captura: `docs/assets/practicv-dashboard.png`.

### Recordatorios con Power Automate

- Flujo manual `PractiCV Recordatorios` en la cuenta UNMSM.
- Archivo de entrada + `Send an email (V2)` con adjunto.
- Ejecución real del 2026-11-23 12:19: **985 ms, Succeeded**.
- No es programado: Microsoft retiró PA para cuentas personales y el OneDrive
  UNMSM está bloqueado. Se documenta como flujo manual, no como automatización.

---

## Calidad

- Backend: **25/25 tests E2E**.
- Playwright: **9/9 tests**.
- Power BI: **0 errores / 0 warnings** y captura revisada.
- Sin datos crudos, correos reales, CVs reales ni secretos en el repo.

---

## Cómo probarlo

```powershell
# Base de datos
docker compose up -d db

# Backend
cd backend
.venv\Scripts\Activate.ps1
alembic upgrade head
python -m practicv seed --demo --volume 1000
uvicorn practicv.main:app --reload

# Frontend
cd ..\frontend
npm install
npm run dev
```

Abrir `http://localhost:3000`.

- Bookmarklet: `/bookmarklet`.
- Correo `.eml`: Ofertas → Correo.
- Practilizate: definir `PRACTICV_PRACTILIZATE_ENABLED=true` y subir el CSV.
- Power BI: abrir `dashboard/PractiCV.pbip` con el junction
  `C:\Users\Public\practicv` (ver `docs/powerbi.md`).

---

## Límites conocidos

- OAuth Gmail/Outlook en vivo no está validado; se importa `.eml`.
- El bookmarklet requiere la app local abierta en el mismo origen.
- El dashboard usa datos sintéticos y refresh manual.
- El adaptador Practilizate no sincroniza automáticamente.
- El match es una heurística explicable, no asesoría legal ni garantía de empleo.

## Atribución

Datos de prácticas: practicas.pe / MCP `practicas-pe`, según sus términos.
Practilizate es una fuente opcional y no una dependencia.
