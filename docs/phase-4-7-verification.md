# Fases 4–7 — Evidencia de verificación

> Fecha: 17 de noviembre de 2026.
> Motor: PostgreSQL 17 local.
> Base de test: `practicv_test`.
> Demos y screenshots con datos sintéticos.

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
56 files left unchanged
All checks passed!

collected 18 items

tests\e2e\test_analytics.py ...          [ 16%]
tests\e2e\test_applications.py .         [ 22%]
tests\e2e\test_cv_upload.py .            [ 27%]
tests\e2e\test_full_flow.py .            [ 33%]
tests\e2e\test_health.py ..              [ 44%]
tests\e2e\test_matching.py ...           [ 61%]
tests\e2e\test_offers.py .....           [ 88%]
tests\e2e\test_profile_persistence.py .. [100%]

18 passed in 13.29s
```

---

## 2. Matching explicable

- `skills.yaml` y alias (`PowerBI` → `Power BI`).
- Clasificación must / nice / unknown.
- Niveles básico=1, intermedio=2, avanzado=3.
- `overall_score` y `must_have_score` deterministas.
- Decisión `apply` / `apply_with_gaps` / `improve_cv`.
- Explicación por habilidad con evidencia y sugerencia.
- `confidence` del análisis.
- Override manual persistido (`overridden`, `override_reason`).

Casos E2E:

- Cobertura completa → 100/100, `apply`.
- Must-have faltante (Databricks) → 50/50, `improve_cv`, brecha visible.
- Nice-to-have faltante (Tableau) → 100 must, 75 overall, `apply_with_gaps`.
- Override a `apply` con motivo → `overridden: true`.

---

## 3. Postulaciones, Kanban y recordatorios

- Kanban de cinco estados.
- Movimiento por drag-and-drop y selector accesible por teclado.
- Notas, próxima acción e historial de eventos.
- Recordatorios por fecha.
- Filtros por estado, vencimiento y match.
- `PATCH /applications/{id}` actualiza estado y `applied_at`.
- `POST /applications/{id}/events`.
- `POST /applications/{id}/reminders`.
- `GET /profiles/{id}/reminders`.

E2E:

- Crear postulación y evitar duplicado.
- Mover a `interview`.
- Agregar evento y recordatorio.
- Verificar recordatorio por perfil.

---

## 4. Exportaciones

### Excel

Hojas verificadas:

- `Postulaciones`
- `Ofertas`
- `Matches`
- `Brechas`
- `Timeline`
- `Habilidades`

El archivo abre con `openpyxl` sin reparaciones.

### CSV

Cabecera:

```text
empresa,puesto,estado,match,must_have,decision,postulada,proxima_accion,nota
```

### ICS

Incluye:

- `BEGIN:VCALENDAR`
- `BEGIN:VEVENT`
- fechas límite,
- próximas acciones,
- recordatorios.

---

## 5. Frontend

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
✓ Generating static pages (7/7)
```

Rutas:

```text
┌ ○ /          4.39 kB
├ ○ /_not-found
├ ○ /ofertas   7.22 kB
├ ƒ /ofertas/[id]
├ ○ /perfil    6.50 kB
└ ○ /postulaciones 6.32 kB
```

i18n ES/EN persistente con `localStorage`.

---

## 6. Playwright

```powershell
npx playwright test --reporter=list
```

Resultado:

```text
Running 5 tests using 5 workers

ok 1 phase0.spec.ts
ok 2 phase2-profile.spec.ts
ok 3 phase3-offers.spec.ts
ok 4 phase4-5-match-kanban.spec.ts — match/override/application
ok 5 phase4-5-match-kanban.spec.ts — kanban/reminder

5 passed (17.9s)
```

Demo:

```powershell
npx playwright test tests/e2e/demo.spec.ts
```

Resultado:

```text
1 passed (29.4s)
```

Video: `docs/assets/demo.webm` (~22 s).

---

## 7. Artefactos E2E

`backend/tests/e2e/test_full_flow.py` escribe:

```text
artifacts/e2e/
├─ run_manifest.json
├─ matches.json
├─ applications.xlsx
├─ applications.csv
├─ calendar.ics
└─ checksums.sha256
```

Verificación local:

```text
applications.csv     820 bytes
applications.xlsx  12264 bytes
calendar.ics        2776 bytes
matches.json         950 bytes
run_manifest.json    989 bytes
checksums.sha256     325 bytes
```

---

## 8. Capturas

- `docs/assets/landing.png`
- `docs/assets/profile-cv.png`
- `docs/assets/offers.png`
- `docs/assets/match.png`
- `docs/assets/kanban.png`
- `docs/assets/demo.webm`

---

## 9. Pendiente manual (no bloquea el MVP)

- **Dogfooding real:** usar PractiCV con 3–5 ofertas reales del usuario y registrar tiempos/brechas. El producto está listo; falta la ejecución con datos reales.
- **Video de 2–3 minutos con narración:** hay una demo corta sin narración; la versión larga requiere grabación manual.

---

## 10. Archivos clave

- `backend/practicv/services/matching.py`
- `backend/practicv/services/applications.py`
- `backend/practicv/services/exports.py`
- `backend/practicv/api/routes/matches.py`
- `backend/practicv/api/routes/applications.py`
- `backend/practicv/api/routes/exports.py`
- `backend/tests/e2e/test_matching.py`
- `backend/tests/e2e/test_applications.py`
- `backend/tests/e2e/test_full_flow.py`
- `frontend/app/ofertas/[id]/page.tsx`
- `frontend/app/postulaciones/page.tsx`
- `frontend/lib/useLocale.ts`
- `tests/e2e/phase4-5-match-kanban.spec.ts`
- `tests/e2e/demo.spec.ts`
- `docs/assets/`
