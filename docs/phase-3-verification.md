# Fase 3 — Evidencia de verificación

> Fecha: 17 de noviembre de 2026.
> Motor: PostgreSQL 17 local.
> Base de test: `practicv_test`.
> MCP: modo fixture, sin llamadas al sitio real.

---

## 1. Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest tests/e2e -v
```

Resultado:

```text
45 files left unchanged
All checks passed!

collected 13 items

tests\e2e\test_analytics.py ...          [ 23%]
tests\e2e\test_cv_upload.py .            [ 30%]
tests\e2e\test_health.py ..              [ 46%]
tests\e2e\test_offers.py .....           [ 84%]
tests\e2e\test_profile_persistence.py .. [100%]

13 passed in 8.47s
```

---

## 2. Captura manual y deduplicación

- `POST /api/v1/offers/manual` → `201`, `duplicate: false`, `source_type: manual`.
- Misma URL otra vez → `200`, `duplicate: true`, mismo `offer.id`.
- `GET /api/v1/offers/{id}` devuelve la oferta persistida.

---

## 3. CSV/Excel

CSV de prueba:

```text
titulo,empresa,url,ubicacion,modalidad,sueldo,descripcion,requisitos,fecha_limite
Practicante CSV Sin Sueldo,CSV Corp,https://example.com/offers/csv-1,Lima,Remoto,,Oferta CSV,Excel,2026-12-15
Practicante Duplicada,Duplicada Corp,https://example.com/offers/manual-1,Lima,Híbrido,1000,Duplicada,SQL,2026-12-20
```

Resultado:

```json
{
  "created": 1,
  "duplicates": 1,
  "total_rows": 2,
  "warnings": ["Row 2: offer has no salary/subvención."],
  "preview": [
    {"title": "Practicante CSV Sin Sueldo", "salary_amount": null},
    {"title": "Practicante Duplicada", "salary_amount": 1000.0}
  ]
}
```

- Plantilla descargable: `frontend/public/plantilla_ofertas.csv`.
- Se aceptan `.csv` y `.xlsx`; máximo 500 filas.

---

## 4. URL con JSON-LD

Servidor HTTP local de fixture (sin llamar a un portal real):

```html
<script type="application/ld+json">
{
  "@type": "JobPosting",
  "title": "Practicante de Analítica Web",
  "hiringOrganization": {"name": "WebData Perú"},
  "baseSalary": {"currency": "PEN", "value": {"value": 1350}},
  "validThrough": "2026-12-20"
}
</script>
```

Resultado:

```text
POST /api/v1/offers/capture-url → 201
title: Practicante de Analítica Web
company: WebData Perú
salary_amount: 1350.0
source_type: url
description sin etiquetas HTML
```

Segunda captura de la misma URL → `200`, `duplicate: true`.

**No se guarda HTML crudo**: solo el texto extraído de `description` y `requisitos`.

---

## 5. MCP `practicas-pe` en modo fixture

Fixtures:

- `backend/tests/e2e/mcp_fixtures/filters.json`
- `backend/tests/e2e/mcp_fixtures/search.json`
- `backend/tests/e2e/mcp_fixtures/offer.json`

Resultado:

```text
GET  /api/v1/offers/sources/status → mcp: available
POST /api/v1/offers/mcp/search      → 2 resultados
POST /api/v1/offers/mcp/import      → created: 2, duplicates: 0
POST /api/v1/offers/mcp/import      → duplicates: 2
GET  /api/v1/offers?source_type=mcp_practicas_pe → 2 ofertas
```

Fallback:

```text
FixtureMCPClient(tmp_path).search()
→ MCPUnavailableError(code="mcp_unavailable", status_code=503)
```

La UI muestra “MCP no disponible; usa texto, CSV o URL” y mantiene las otras fuentes.

---

## 6. Frontend

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

Resultado:

```text
✔ No ESLint warnings or errors
tsc --noEmit (sin errores)
✓ Compiled successfully
✓ Generating static pages (6/6)

┌ ○ /          3.35 kB
├ ○ /_not-found
├ ○ /ofertas   5.91 kB
└ ○ /perfil    5.30 kB
```

La página `/ofertas` incluye:

- Pestañas Manual, CSV/Excel, URL y MCP.
- Formulario manual.
- Plantilla CSV descargable.
- Resultado de importación con creadas, duplicadas, errores y advertencias.
- Captura por URL.
- Búsqueda MCP con selección e importación.
- Lista de ofertas registradas con fuente y sueldo.

---

## 7. E2E de UI

```powershell
npx playwright test --reporter=list
```

Resultado:

```text
Running 3 tests using 3 workers

ok 1 [chromium] › tests\e2e\phase0.spec.ts
ok 2 [chromium] › tests\e2e\phase2-profile.spec.ts
ok 3 [chromium] › tests\e2e\phase3-offers.spec.ts

3 passed (11.8s)
```

El test de Fase 3 mockea la API y verifica:

- Guardar oferta manual.
- Ver la oferta en la lista.
- Buscar en MCP.
- Ver 2 resultados.
- Importar seleccionadas.
- Ver “Creadas: 2”.

---

## 8. Endpoints nuevos

- `POST /api/v1/offers/manual`
- `POST /api/v1/offers/import/csv`
- `POST /api/v1/offers/capture-url`
- `GET /api/v1/offers`
- `GET /api/v1/offers/{id}`
- `GET /api/v1/offers/sources/status`
- `POST /api/v1/offers/mcp/search`
- `POST /api/v1/offers/mcp/import`

---

## 9. Archivos clave

- `backend/practicv/services/offers.py`
- `backend/practicv/adapters/sources/practicas_pe_mcp.py`
- `backend/practicv/api/routes/offers.py`
- `backend/practicv/api/schemas.py`
- `backend/tests/e2e/test_offers.py`
- `backend/tests/e2e/mcp_fixtures/`
- `frontend/app/ofertas/page.tsx`
- `frontend/lib/api.ts`
- `frontend/public/plantilla_ofertas.csv`
- `tests/e2e/phase3-offers.spec.ts`
- `docs/phase-3-verification.md`
