# ROADMAP.md — PractiCV

> **Regla:** trabaja los checkpoints en orden. No saltes ninguno.
> **E2E-first:** el escenario se escribe antes de la implementación.
> **Un commit por checkpoint significativo.**
> **No avances si el E2E no pasa.**

---

## Fase 0 — Base del proyecto

- [x] Crear repo `practicv` (privado primero).
- [x] Crear estructura `backend/`, `frontend/`, `tests/e2e/`, `artifacts/e2e/`, `docs/`.
- [x] Configurar `pyproject.toml`, `ruff`, `pytest`.
- [x] Configurar `package.json`, TypeScript estricto, ESLint, Prettier.
- [x] Crear `docker-compose.yml` para desarrollo local.
- [x] Crear CI con `ruff check`, `ruff format --check`, `pnpm lint`, `pnpm typecheck`.
- [x] Crear `ADR-001: monolito modular`.
- [x] Crear `ADR-002: fuentes de datos y fallbacks`.
- [x] Crear `.env.example` y `.gitignore`.
- [x] Crear `LICENSE` (MIT recomendada).

**E2E del checkpoint:**

- [x] La app levanta con `docker compose up`.
- [x] `GET /health` responde `200`.
- [x] La UI muestra “PractiCV” y el toggle ES/EN.

**Evidencia local:**

- `backend`: `ruff format --check`, `ruff check` y `pytest tests/e2e` → 1 passed.
- `frontend`: `npm run lint`, `npm run typecheck` y `npm run build` → OK.
- `Playwright`: `npx playwright test` → 1 passed.
- `Docker Compose`: backend healthy en `http://localhost:8001/health`; frontend 200 en `http://localhost:3001`.

**Criterio de aceptación:**

- [x] CI configurado (se verifica en GitHub después del push).
- [x] `GET /health` funciona.
- [x] No hay secretos en el repo.

**Commit sugerido:**

```text
chore: initialize practicv project
```

---

## Fase 1 — Dominio y persistencia (PostgreSQL)

- [x] Configurar PostgreSQL 17 en Docker y base `practicv_test`.
- [x] Configurar SQLAlchemy 2 + `psycopg` 3.
- [x] Definir entidades y contratos:
  - `Profile`, `CVDocument`, `Skill`, `Offer`, `OfferSkill`, `Match`, `Application`, `Reminder`.
- [x] Configurar Alembic y primera migración.
- [x] Implementar repositorios por contexto.
- [x] Implementar vista `v_offer_ranking` con CTE + `ROW_NUMBER()`.
- [x] Implementar función PL/pgSQL `fn_top_offers_for_profile(profile_id)`.
- [x] Agregar índices y documentar `EXPLAIN ANALYZE`.
- [x] Implementar `request_id` y logging estructurado.
- [x] Implementar manejo de errores de dominio → HTTP.
- [x] Crear seed de demo con datos sintéticos (incluye 1,000 ofertas para volumen).

**E2E del checkpoint:**

- [x] La app arranca con una base vacía.
- [x] Las migraciones corren desde cero.
- [x] El seed de demo inserta un perfil, skills, ofertas, match, postulación y recordatorio.
- [x] Un error de dominio devuelve el formato `{error: {code, message, details}}`.
- [x] La vista `v_offer_ranking` devuelve el ranking por perfil con `ROW_NUMBER()`.
- [x] La función `fn_top_offers_for_profile` devuelve las mejores ofertas.
- [x] El health check reporta `database: ok`.

**Evidencia local:**

- `alembic upgrade head` → 2 migraciones aplicadas.
- `python -m practicv seed --demo --volume 1000` → 1,005 ofertas, 505 matches, 3 postulaciones.
- `pytest tests/e2e -v` → 7 passed.
- `ruff format` y `ruff check` → All checks passed.
- `EXPLAIN ANALYZE` → `Index Only Scan using ix_matches_profile_score_covering`, 0.517 ms.

**Criterio de aceptación:**

- [x] Migraciones idempotentes.
- [x] Repositorios testeables por E2E.
- [x] No hay lógica de negocio en rutas.
- [x] No hay PII en el seed.
- [x] Las consultas analíticas usan SQL real (CTE/window), no solo ORM.

**Commit sugerido:**

```text
feat: add domain model and postgres persistence
```

---

## Fase 2 — Perfil y CV

- [x] CRUD de perfil.
- [x] Endpoint de subida de CV (PDF/DOCX).
- [x] Extracción de texto con `pdfplumber`/`pypdf` y `python-docx`.
- [x] Detección de secciones: educación, experiencia, proyectos, habilidades, certificaciones, idiomas.
- [x] Extracción de habilidades con `skills.yaml`.
- [x] Pantalla de confirmación y edición de habilidades/niveles.
- [x] Parseo mixto: botón “analizar con IA” solo si falta información.
- [x] Redacción de correo/teléfono antes de enviar a LLM.
- [x] Persistir `parsed_json` y texto extraído.

**E2E del checkpoint:**

- [x] Subir un CV medio-difícil:
  - [x] una sección sin título,
  - [x] habilidades en una tabla,
  - [x] un alias (“PowerBI”),
  - [x] correo y teléfono.
- [x] Verificar:
  - [x] texto extraído,
  - [x] habilidades detectadas,
  - [x] edición manual,
  - [x] que el correo/teléfono no se envíen a la IA.

**Evidencia local:**

- `pytest tests/e2e -v` → 8 passed (7 de Fase 1 + 1 de Fase 2).
- `ruff format` y `ruff check` → All checks passed.
- `npm run lint`, `npm run typecheck`, `npm run build` → OK.
- `npx playwright test` → 2 passed (landing + perfil/CV).
- PDF y DOCX generados en el test; `PowerBI` se mapea a `Power BI`.
- `analyze-ai` sin consentimiento → 422; con consentimiento → texto con `[EMAIL]` y `[PHONE]`.

**Criterio de aceptación:**

- [x] El usuario puede corregir todo.
- [x] Sin IA, el flujo funciona.
- [x] El CV original se guarda localmente (`file_bytes`).
- [x] No se envía PII a terceros sin consentimiento.

**Commit sugerido:**

```text
feat: add profile and CV parsing
```

---

## Fase 3 — Ofertas y fuentes

- [x] Captura manual con formulario y validación.
- [x] Importación CSV/Excel con plantilla y previsualización.
- [x] Captura desde URL con JSON-LD/OpenGraph.
- [x] Adaptador MCP `practicas-pe`:
  - `listar_filtros`,
  - `buscar_practicas`,
  - `obtener_practica`.
- [x] Normalización de ofertas.
- [x] Deduplicación por URL canónica y `dedupe_hash`.
- [x] Procedencia (`source_type`, `source_url`, `captured_at`).
- [x] Fallback claro si el MCP falla.

**E2E del checkpoint:**

- [x] Agregar 4 ofertas:
  1. manual completa,
  2. CSV sin sueldo,
  3. URL con JSON-LD (fixture local),
  4. MCP (fixture).
- [x] Agregar una duplicada por URL.
- [x] Verificar:
  - [x] 4 ofertas únicas,
  - [x] duplicado detectado,
  - [x] campos faltantes visibles,
  - [x] procedencia correcta,
  - [x] fallback si el MCP no responde.

**Evidencia local:**

- `pytest tests/e2e -v` → **13 passed** (Fases 1–3).
- `ruff format` y `ruff check` → All checks passed.
- `npm run lint`, `npm run typecheck`, `npm run build` → OK; `/ofertas` generada.
- `npx playwright test` → **3 passed** (landing, perfil/CV, ofertas).
- CSV: 1 creada + 1 duplicada + warning por sueldo faltante.
- URL: JSON-LD parseado, HTML strippeado, `source_type=url`.
- MCP: 2 resultados, 2 importadas, segunda importación 2 duplicadas.
- Fallback: `MCPUnavailableError` con código `mcp_unavailable` y status 503.
- Plantilla: `frontend/public/plantilla_ofertas.csv`.

**Criterio de aceptación:**

- [x] Ninguna fuente es obligatoria.
- [x] La app funciona sin MCP.
- [x] No se guarda HTML crudo.
- [x] No se llama al sitio real en tests.

**Commit sugerido:**

```text
feat: add multi-source offer ingestion
```

---

## Fase 4 — Matching explicable

- [x] Cargar `skills.yaml` y resolver alias.
- [x] Clasificar requisitos must/nice/unknown.
- [x] Detectar niveles (“básico”, “intermedio”, “avanzado”).
- [x] Implementar fórmula `overall_score` y `must_have_score`.
- [x] Implementar decisión `apply` / `apply_with_gaps` / `improve_cv`.
- [x] Generar explicación con evidencia.
- [x] Mostrar brechas y recomendaciones.
- [x] Permitir override manual.
- [x] Mostrar confianza del análisis.

**E2E del checkpoint:**

- [x] Perfil con skills y oferta con must/nice.
- [x] Verificar score, must-have, brecha, decisión y explicación.
- [x] Verificar override manual.
- [x] Verificar confianza del match.

**Criterio de aceptación:**

- [x] La fórmula es determinista.
- [x] La explicación coincide con el cálculo.
- [x] El usuario puede corregir y recalcular.
- [x] No hay LLM en el score.

**Commit sugerido:**

```text
feat: add explainable matching
```

---

## Fase 5 — Postulaciones y recordatorios

- [x] Kanban con cinco estados.
- [x] Crear postulación desde una oferta.
- [x] Mover tarjetas con drag-and-drop y con teclado.
- [x] Notas y próxima acción.
- [x] Historial de eventos.
- [x] Recordatorios por fecha.
- [x] Exportación `.ics`.
- [x] Filtros por estado, match y vencimiento.

**E2E del checkpoint:**

- [x] Crear postulaciones (seed + flujo).
- [x] Mover una a “Entrevista”.
- [x] Agregar nota y próxima acción.
- [x] Crear recordatorio para una fecha.
- [x] Exportar `.ics` y verificar el evento.

**Criterio de aceptación:**

- [x] El estado persiste.
- [x] El Kanban es accesible por teclado.
- [x] El `.ics` abre en Google Calendar/Outlook.
- [x] No se pierden cambios si falla una petición (la UI mantiene el estado anterior).

**Commit sugerido:**

```text
feat: add application tracking and reminders
```

---

## Fase 6 — Exportaciones y UI bilingüe

- [x] Exportación Excel con hojas:
  - `Postulaciones`,
  - `Ofertas`,
  - `Matches`,
  - `Brechas`,
  - `Timeline`,
  - `Habilidades`.
- [x] Exportación CSV.
- [x] i18n ES/EN en toda la UI.
- [x] Toggle de idioma persistente (`localStorage`).
- [x] Revisión de accesibilidad:
  - labels,
  - foco,
  - teclado,
  - contraste básico.
- [x] Estados `loading`, `empty`, `error`, `success` en las pantallas principales.
- [x] Modo demo con datos sintéticos (`python -m practicv seed --demo`).

**E2E del checkpoint:**

- [x] Cambiar idioma a inglés y verificar textos clave.
- [x] Exportar Excel y verificar las hojas.
- [x] Verificar que el modo demo no usa PII.
- [x] Navegar el Kanban con teclado mediante el selector de estado.

**Criterio de aceptación:**

- [x] No hay strings críticos hardcodeados.
- [x] El Excel abre sin reparaciones.
- [x] La UI es usable en ambos idiomas.
- [x] El modo demo es reproducible.

**Commit sugerido:**

```text
feat: add exports and bilingual UI
```

---

## Fase 7 — E2E final, demo y release

- [x] E2E medio-difícil completo:
  - 1 perfil,
  - 2 CVs,
  - 5+ ofertas,
  - duplicado,
  - fecha vencida,
  - must-have faltante.
- [x] Artefactos con checksums.
- [x] `quality_report.json` con checks del flujo, métricas por paso y hashes.
- [x] README con capturas y métricas reales.
- [x] README.en.md.
- [x] Video demo corto (`docs/assets/demo.webm`).
- [ ] Dogfooding con ofertas reales (manual; requiere que el usuario use la app con sus ofertas).
- [x] Tag `v0.1.0`.
- [x] Release con artefactos.

**E2E del checkpoint:**

- [x] Ejecutar desde cero en una base limpia.
- [x] Verificar todos los flujos.
- [x] Confirmar que no hay llamadas a sitios reales.
- [x] Verificar checksums.

**Criterio de aceptación:**

- [x] Todos los checkpoints técnicos anteriores marcados.
- [x] E2E verde y reproducible.
- [x] README y README.en.md completos.
- [x] Demo funciona sin Practilizate ni MCP.
- [x] No hay PII ni secretos.
- [x] Tag y release creados.

**Commits sugeridos:**

```text
test: add medium-hard e2e scenario
docs: finalize v0.1.0
chore: release v0.1.0
```

---

## Definición de terminado

Un checkpoint está terminado cuando:

- [x] El E2E del checkpoint pasa.
- [x] El artefacto correspondiente existe.
- [x] El checkbox está marcado.
- [x] `README.md` está actualizado si cambió algo visible.
- [x] `ruff format` y `ruff check` pasan.
- [x] `pnpm lint` y `pnpm typecheck` pasan.
- [x] No hay PII, secretos ni datos crudos.
- [x] El commit está hecho.

El proyecto está terminado cuando:

- [x] Todos los checkpoints técnicos están marcados.
- [x] El E2E medio-difícil pasa desde cero.
- [x] La demo funciona con datos sintéticos.
- [x] README y README.en.md están completos.
- [x] La UI funciona en español e inglés.
- [x] No hay dependencia de Practilizate ni del MCP para arrancar.
- [x] La licencia y los créditos están claros.

---

## Reglas de avance

- No avances si el E2E falla.
- No modifiques fixtures para hacer pasar un test.
- No agregues features fuera del alcance del MVP.
- Si un requisito es ambiguo, detente y propón opciones.
- Si una fuente de datos falla, implementa el fallback antes de seguir.
- Si rompes un boundary, justifícalo en un ADR.

---

## Backlog v0.2 (no ahora)

- Bookmarklet.
- Correos de alerta (Gmail/Outlook).
- Adaptador Practilizate.
- Flujo Power Automate.
- Dashboard Power BI de embudo.
- Múltiples versiones de CV.
- Traducción de docs internas al inglés.
- Deploy público de la demo.
