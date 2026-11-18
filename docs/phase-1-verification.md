# Fase 1 — Evidencia de verificación

> Fecha: 17 de noviembre de 2026.
> Motor: PostgreSQL 17 (Docker local, puerto 5434).
> Base de test: `practicv_test`.
> Dataset: 1,005 ofertas, 505 matches, 3 postulaciones, 2 recordatorios.

---

## 1. Migraciones desde cero

```powershell
$env:PRACTICV_DATABASE_URL="postgresql+psycopg://practicv:practicv@localhost:5434/practicv"
.\.venv\Scripts\alembic.exe upgrade head
```

Resultado:

```text
INFO  [alembic.runtime.migration] Running upgrade  -> d88dd96dd657, initial schema
INFO  [alembic.runtime.migration] Running upgrade d88dd96dd657 -> 3ba0135828de, add analytics view and function
```

Migraciones:

- `d88dd96dd657_initial_schema.py` — tablas, constraints e índices.
- `3ba0135828de_add_analytics_view_and_function.py` — vista `v_offer_ranking`, función `fn_top_offers_for_profile`, índices covering/parcial.

---

## 2. Seed sintético

```powershell
.\.venv\Scripts\python.exe -m practicv seed --demo --volume 1000
```

Resultado:

```json
{
  "profile_id": "4cdcabf2-5ba6-4e53-8867-3bcc58881f0c",
  "offer_ids": ["3d3d005a-5753-4162-9446-5c2be582c614", "..."],
  "application_ids": ["ba5ca3e5-f73c-4987-b1b4-e3a10da7a239", "..."],
  "offers_total": 1005,
  "matches_total": 505,
  "applications_total": 3,
  "reminders_total": 2
}
```

No se usa PII real. El perfil es `demo@practicv.local`.

---

## 3. Ruff

```powershell
.\.venv\Scripts\python.exe -m ruff format .
.\.venv\Scripts\python.exe -m ruff check .
```

Resultado:

```text
33 files left unchanged
All checks passed!
```

---

## 4. E2E contra PostgreSQL

```powershell
.\.venv\Scripts\python.exe -m pytest tests/e2e -v
```

Resultado:

```text
collected 7 items

tests\e2e\test_analytics.py ... [ 42%]
tests\e2e\test_health.py .. [ 71%]
tests\e2e\test_profile_persistence.py .. [100%]

7 passed in 4.89s
```

Cobertura del checkpoint:

- Migraciones desde cero en `practicv_test`.
- Seed idempotente.
- `GET /health` con `database: ok`.
- `GET /api/v1/profiles/{id}` con datos persistidos.
- Error de dominio `404` con formato `{error: {code, message, details}}`.
- `v_offer_ranking` con `ROW_NUMBER()`.
- `fn_top_offers_for_profile` PL/pgSQL.
- `application_funnel` con `GROUP BY`.
- `X-Request-ID` en la respuesta.

---

## 5. SQL avanzado

Ver [`docs/sql-performance.md`](sql-performance.md).

Resumen:

- Vista con CTE + `ROW_NUMBER()`.
- Función PL/pgSQL con `RETURNS TABLE`.
- Índice covering `ix_matches_profile_score_covering`.
- `EXPLAIN ANALYZE` con `Index Only Scan` y `Execution Time: 0.517 ms`.

---

## 6. Docker y API en contenedores

```powershell
docker compose up -d --build
docker compose ps
```

Resultado:

```text
practicv-db-1         Up (healthy)   0.0.0.0:5434->5432/tcp
practicv-backend-1    Up (healthy)   0.0.0.0:8001->8000/tcp
practicv-frontend-1   Up             0.0.0.0:3001->3000/tcp
```

Health:

```json
{"status":"ok","service":"PractiCV","version":"0.1.0","environment":"docker","database":"ok"}
```

Perfil:

```text
HTTP 200
X-Request-ID: 00eb5275-346a-4048-ad6a-e3582d4d2385
{"full_name":"Estudiante Demo","career":"Ingeniería de Software","locale":"es"}
```

Ranking SQL (`v_offer_ranking`):

```json
{
  "value": [
    {"title": "Oferta demo 0249", "overall_score": 99.0, "rank": 1},
    {"title": "Oferta demo 0099", "overall_score": 99.0, "rank": 2},
    {"title": "Oferta demo 0399", "overall_score": 99.0, "rank": 3},
    {"title": "Oferta demo 0049", "overall_score": 99.0, "rank": 4},
    {"title": "Oferta demo 0349", "overall_score": 99.0, "rank": 5}
  ]
}
```

Función PL/pgSQL (`fn_top_offers_for_profile`):

```json
{
  "value": [
    {"title": "Oferta demo 0249", "overall_score": 99.0, "decision": "apply_with_gaps"},
    {"title": "Oferta demo 0099", "overall_score": 99.0, "decision": "apply_with_gaps"}
  ]
}
```

Error de dominio:

```json
{"error":{"code":"not_found","message":"Profile not found","details":{"profile_id":"00000000-0000-0000-0000-000000000000"}}}
```

Frontend y Playwright:

```text
✔ No ESLint warnings or errors
tsc --noEmit (sin errores)
✓ Compiled successfully
1 passed (11.1s)
```

---

## 7. Archivos clave

- `backend/practicv/domain/entities.py`
- `backend/practicv/domain/enums.py`
- `backend/practicv/domain/errors.py`
- `backend/practicv/adapters/db/models.py`
- `backend/practicv/adapters/db/repositories.py`
- `backend/practicv/adapters/db/session.py`
- `backend/practicv/observability.py`
- `backend/practicv/api/errors.py`
- `backend/practicv/api/routes/health.py`
- `backend/practicv/api/routes/profiles.py`
- `backend/practicv/api/routes/analytics.py`
- `backend/practicv/seed.py`
- `backend/practicv/__main__.py`
- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/versions/d88dd96dd657_initial_schema.py`
- `backend/migrations/versions/3ba0135828de_add_analytics_view_and_function.py`
- `backend/tests/e2e/conftest.py`
- `backend/tests/e2e/test_health.py`
- `backend/tests/e2e/test_profile_persistence.py`
- `backend/tests/e2e/test_analytics.py`
