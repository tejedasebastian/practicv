# PractiCV v0.1.0

**Copiloto de postulaciones para estudiantes.** Primer MVP completo y local-first.

PractiCV convierte una oferta de prácticas en una decisión: extrae requisitos, calcula un match explicable contra el CV, muestra las brechas concretas y organiza la postulación en un Kanban con recordatorios y exportaciones.

---

## Qué incluye

### Perfil y CV

- CRUD de perfil académico y roles objetivo.
- Subida de CV en **PDF y DOCX** con extracción de texto y tablas.
- Detección de secciones: perfil, educación, experiencia, proyectos, habilidades, certificaciones e idiomas.
- Catálogo `skills.yaml` con alias (`PowerBI` → `Power BI`).
- Edición manual de habilidades y niveles 0–3.
- El archivo original se guarda localmente en PostgreSQL (`bytea`).
- Análisis con IA **opt-in**, con redacción de correo/teléfono antes de enviar.

### Ofertas multi-fuente

- Captura manual con validación.
- Importación CSV/XLSX con plantilla, previsualización y errores por fila.
- Captura por URL con JSON-LD `JobPosting` y OpenGraph.
- MCP `practicas-pe` opcional (búsqueda, detalle e importación).
- Normalización y deduplicación por URL canónica + `dedupe_hash`.
- Procedencia en cada oferta: `source_type`, `source_url`, `captured_at`.
- Si el MCP falla, la app sigue funcionando con texto, CSV y URL.

### Matching explicable

- Clasificación de requisitos must-have / nice-to-have / unknown.
- Detección de niveles: básico = 1, intermedio = 2, avanzado = 3.
- Fórmula determinista:

```text
coverage = min(user_level, required_level) / required_level
overall_score    = 100 * Σ(weight * coverage) / Σ(weight)
must_have_score  = 100 * Σ(weight * coverage must) / Σ(weight must)
```

- Decisión `apply` / `apply_with_gaps` / `improve_cv`.
- Explicación por habilidad con evidencia y sugerencia.
- Confianza del análisis.
- Override manual persistido con motivo.

### Postulaciones y recordatorios

- Kanban de cinco estados: guardada, postulada, entrevista, rechazada y oferta.
- Movimiento por drag-and-drop y por selector accesible con teclado.
- Notas, próxima acción e historial de eventos.
- Recordatorios por fecha.
- Filtros por estado, vencimiento y match.

### Exportaciones

- **Excel** con hojas `Postulaciones`, `Ofertas`, `Matches`, `Brechas`, `Timeline` y `Habilidades`.
- **CSV** del embudo de postulaciones.
- **ICS** con fechas límite, próximas acciones y recordatorios.

### UI

- Español e inglés.
- Idioma persistente en `localStorage`.
- Páginas: `/`, `/perfil`, `/ofertas`, `/ofertas/[id]`, `/postulaciones`.

### SQL avanzado (PostgreSQL 17)

- Modelo relacional normalizado con `JSONB`, constraints e índices.
- Vista `v_offer_ranking` con CTE + `ROW_NUMBER()`.
- Función PL/pgSQL `fn_top_offers_for_profile(uuid)`.
- Índice covering `ix_matches_profile_score_covering`.
- `EXPLAIN ANALYZE` documentado en `docs/sql-performance.md`.

---

## Arquitectura

- **Backend:** Python 3.13, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, psycopg 3.
- **Base de datos:** PostgreSQL 17 local (Docker).
- **Frontend:** Next.js 15, TypeScript estricto, Tailwind CSS.
- **Testing:** pytest E2E + Playwright.
- **CI:** GitHub Actions con servicio PostgreSQL 17.
- **Patrón:** monolito modular con boundaries de microservicios.

---

## Verificación

| Verificación | Resultado |
|---|---|
| Backend E2E (`pytest tests/e2e -v`) | **18 passed** |
| Ruff format + check | **All checks passed** |
| Frontend lint + typecheck + build | **OK** |
| Playwright E2E | **5 passed** |
| Demo Playwright | **1 passed** |
| CI | **success** |
| Checksums de artefactos | **5/5 OK** |

Rendimiento SQL medido:

```text
WindowAgg + Index Only Scan using ix_matches_profile_score_covering
Execution Time: 0.517 ms
```

---

## Artefactos de release

- `applications.xlsx` — exportación Excel con 6 hojas.
- `applications.csv` — embudo de postulaciones.
- `calendar.ics` — calendario con fechas y recordatorios.
- `matches.json` — match completo con score, brechas y explicación.
- `quality_report.json` — checks del flujo, métricas por paso y hashes de los artefactos.
- `run_manifest.json` — manifiesto del run E2E.
- `checksums.sha256` — hashes SHA-256 de los cinco artefactos de payload.

---

## Cómo ejecutar

```powershell
docker compose up -d db

cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:PRACTICV_DATABASE_URL="postgresql+psycopg://practicv:practicv@localhost:5434/practicv"
alembic upgrade head
python -m practicv seed --demo --volume 1000
uvicorn practicv.main:app --reload

cd ..\frontend
npm install
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5434`

Con Docker Compose completo: frontend `3001`, backend `8001`.

### Modo demo

```powershell
python -m practicv seed --demo --volume 1000
```

Inserta 1,005 ofertas sintéticas, 505 matches, 3 postulaciones y 2 recordatorios. Sin PII real.

---

## Limitaciones conocidas

- v0.1 es local-first y de un solo usuario.
- El parseo de CV puede fallar en formatos muy complejos; el usuario corrige.
- La captura por URL es best effort; algunos portales bloquean o no exponen JSON-LD.
- El MCP `practicas-pe` es opcional y puede no estar disponible.
- El match es una estimación explicable, no una probabilidad de contratación.
- No incluye auto-postulación, app móvil, multiusuario ni scraping masivo.
- El análisis con IA usa un adaptador local (`stub`); no hay proveedor externo conectado.
- El dogfooding con 3–5 ofertas reales queda como paso manual del usuario.
- La demo en video es corta y sin narración (`docs/assets/demo.webm`).

---

## Créditos

- Fuente de ofertas: [practicas.pe](https://www.practicas.pe/). PractiCV no está afiliado.
- Inspiración de producto: Practilizate, el observatorio de prácticas del Perú.
- Licencia: MIT.

**Repo:** https://github.com/kuki236/practicv
