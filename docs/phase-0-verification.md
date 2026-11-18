# Fase 0 — Evidencia de verificación

> Fecha: 17 de noviembre de 2026.
> Entorno: Windows 11, Python 3.13.3, Node 24.15.0, npm 11.12.1, Docker 29.5.3.
> Nota: Docker Compose usa 3001/8001 porque 3000/8000 están ocupados por otros proyectos locales.

## Backend

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest tests/e2e -v
```

Resultado:

```text
7 files left unchanged
All checks passed!
tests/e2e/test_health.py . [100%]
1 passed in 2.62s
```

El test levanta `uvicorn` en un puerto libre y verifica por HTTP:

- `GET /health` → `200` con `status=ok`, `service=PractiCV`, `version=0.1.0`.
- `GET /` → `200` con `service=PractiCV` y `health=/health`.

## Frontend

```powershell
cd frontend
npm install
npm run lint
npm run typecheck
npm run build
```

Resultado:

```text
✔ No ESLint warnings or errors
tsc --noEmit (sin errores)
✓ Compiled successfully
✓ Generating static pages (4/4)
```

## E2E de UI

```powershell
npx playwright test --reporter=list
```

Resultado:

```text
Running 1 test using 1 worker
ok 1 [chromium] › tests\e2e\phase0.spec.ts:3:1 › PractiCV landing loads and toggles ES/EN
1 passed
```

El test verifica:

- La landing muestra `PractiCV`.
- El subtítulo en español.
- El toggle a inglés cambia el subtítulo.
- El toggle vuelve a español.

Puerto dedicado del E2E: `3101`, para no chocar con otros proyectos.

## Docker Compose

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://127.0.0.1:8001/health
Invoke-WebRequest http://127.0.0.1:3001
```

Resultado:

```text
practicv-backend-1    Up (healthy)   0.0.0.0:8001->8000/tcp
practicv-frontend-1   Up             0.0.0.0:3001->3000/tcp

{"status":"ok","service":"PractiCV","version":"0.1.0","environment":"docker"}

Frontend status: 200
Contains PractiCV: True
```

## Vulnerabilidades de producción

```powershell
cd frontend
npm audit --omit=dev
```

Resultado:

```text
found 0 vulnerabilities
```

Las vulnerabilidades restantes de `npm audit` son de dependencias de desarrollo (ESLint), no del runtime de producción.

## Archivos clave de la Fase 0

- `backend/practicv/main.py`
- `backend/practicv/api/routes/health.py`
- `backend/tests/e2e/test_health.py`
- `frontend/app/page.tsx`
- `frontend/messages/es.json`
- `frontend/messages/en.json`
- `tests/e2e/phase0.spec.ts`
- `playwright.config.ts`
- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.github/workflows/ci.yml`
- `docs/adr/ADR-001-modular-monolith.md`
- `docs/adr/ADR-002-data-sources-and-fallbacks.md`
