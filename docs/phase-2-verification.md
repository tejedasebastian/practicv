# Fase 2 — Evidencia de verificación

> Fecha: 17 de noviembre de 2026.
> Motor: PostgreSQL 17 local.
> Base de test: `practicv_test`.
> Documentación: español. UI: español e inglés.

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
40 files left unchanged
All checks passed!

collected 8 items

tests\e2e\test_analytics.py ...          [ 37%]
tests\e2e\test_cv_upload.py .            [ 50%]
tests\e2e\test_health.py ..              [ 75%]
tests\e2e\test_profile_persistence.py .. [100%]

8 passed in 7.02s
```

El E2E de CV cubre:

- Crear perfil y actualizarlo (`PATCH`).
- Subir PDF y DOCX.
- Extraer texto y tablas.
- Detectar secciones.
- Mapear `PowerBI` → `Power BI`.
- Detectar correo y teléfono.
- Confirmar y editar habilidades/niveles.
- Verificar que el CV activo es el último subido.
- Rechazar archivos no soportados.
- Rechazar `analyze-ai` sin consentimiento.
- Redactar `[EMAIL]` y `[PHONE]` antes de la IA.
- Eliminar el perfil y verificar `404`.

---

## 2. Parser con PDF y DOCX

Salida de verificación directa:

```text
--- pdf ---
sections: ['otros', 'experiencia', 'proyectos', 'habilidades', 'certificaciones', 'idiomas']
skills: ['Python', 'SQL', 'Power BI', 'Excel', 'FastAPI', 'Docker', 'Inglés']
contact: {'email': 'sebas.demo@example.com', 'phone': '+51 987 654 321'}
warnings: []

--- docx ---
sections: ['otros', 'experiencia', 'habilidades', 'idiomas']
skills: ['Python', 'SQL', 'Power BI', 'FastAPI', 'Docker', 'Excel', 'Inglés']
contact: {'email': 'sebas.demo@example.com', 'phone': '+51 987 654 321'}
warnings: []
```

El PDF incluye una tabla de habilidades y una sección sin título (`otros`). El DOCX conserva el orden de párrafos y tablas.

---

## 3. Migración

```text
1252308bc7b7_add_cv_file_bytes_and_active_index.py
```

Agrega:

- `cv_documents.file_bytes` (`LargeBinary`) para guardar el archivo original.
- Índice único parcial `uq_cv_documents_active_profile` para un solo CV activo por perfil.

---

## 4. Frontend

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
✓ Generating static pages (5/5)
```

Rutas generadas:

```text
┌ ○ /          2.63 kB
├ ○ /_not-found
└ ○ /perfil    4.33 kB
```

La página `/perfil` incluye:

- Formulario de perfil.
- Subida de PDF/DOCX.
- Secciones detectadas.
- Habilidades con nivel 0–3 y confirmación.
- Botón “Analizar con IA” solo cuando hay advertencias.
- Consentimiento explícito.
- Texto redactado y sugerencias.

---

## 5. E2E de UI

```powershell
npx playwright test --reporter=list
```

Resultado:

```text
Running 2 tests using 2 workers

ok 1 [chromium] › tests\e2e\phase2-profile.spec.ts › profile, CV, skills and AI consent flow
ok 2 [chromium] › tests\e2e\phase0.spec.ts › PractiCV landing loads and toggles ES/EN

2 passed (12.7s)
```

El test de Fase 2 mockea la API y verifica:

- Guardar perfil.
- Subir CV.
- Ver `Power BI`.
- Cambiar nivel y confirmar.
- Guardar habilidades.
- Aceptar consentimiento.
- Ver texto redactado y sugerencias.

---

## 6. Endpoints nuevos

- `POST /api/v1/profiles`
- `GET /api/v1/profiles`
- `PATCH /api/v1/profiles/{id}`
- `DELETE /api/v1/profiles/{id}`
- `POST /api/v1/profiles/{id}/cv`
- `GET /api/v1/profiles/{id}/cv`
- `PATCH /api/v1/profiles/{id}/cv/skills`
- `POST /api/v1/profiles/{id}/cv/analyze-ai`

---

## 7. Archivos clave

- `backend/practicv/adapters/cv/parser.py`
- `backend/practicv/adapters/llm/stub.py`
- `backend/practicv/data/skills.yaml`
- `backend/practicv/api/routes/profiles.py`
- `backend/practicv/api/schemas.py`
- `backend/practicv/adapters/db/repositories.py`
- `backend/migrations/versions/1252308bc7b7_add_cv_file_bytes_and_active_index.py`
- `backend/tests/e2e/fixtures.py`
- `backend/tests/e2e/test_cv_upload.py`
- `frontend/app/perfil/page.tsx`
- `frontend/lib/api.ts`
- `frontend/messages/es.json`
- `frontend/messages/en.json`
- `tests/e2e/phase2-profile.spec.ts`
