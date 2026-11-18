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

- [ ] CRUD de perfil.
- [ ] Endpoint de subida de CV (PDF/DOCX).
- [ ] Extracción de texto con `pdfplumber`/`pypdf` y `python-docx`.
- [ ] Detección de secciones: educación, experiencia, proyectos, habilidades, certificaciones, idiomas.
- [ ] Extracción de habilidades con `skills.yaml`.
- [ ] Pantalla de confirmación y edición de habilidades/niveles.
- [ ] Parseo mixto: botón “analizar con IA” solo si falta información.
- [ ] Redacción de correo/teléfono antes de enviar a LLM.
- [ ] Persistir `parsed_json` y texto extraído.

**E2E del checkpoint:**

- Subir un CV medio-difícil:
  - una sección sin título,
  - habilidades en una tabla,
  - un alias (“PowerBI”),
  - correo y teléfono.
- Verificar:
  - texto extraído,
  - habilidades detectadas,
  - edición manual,
  - que el correo/teléfono no se envíen a la IA.

**Criterio de aceptación:**

- El usuario puede corregir todo.
- Sin IA, el flujo funciona.
- El CV original se guarda localmente.
- No se envía PII a terceros sin consentimiento.

**Commit sugerido:**

```text
feat: add profile and CV parsing
```

---

## Fase 3 — Ofertas y fuentes

- [ ] Captura manual con formulario y validación.
- [ ] Importación CSV/Excel con plantilla y previsualización.
- [ ] Captura desde URL con JSON-LD/OpenGraph.
- [ ] Adaptador MCP `practicas-pe`:
  - `listar_filtros`,
  - `buscar_practicas`,
  - `obtener_practica`.
- [ ] Normalización de ofertas.
- [ ] Deduplicación por URL canónica y `dedupe_hash`.
- [ ] Procedencia (`source_type`, `source_url`, `captured_at`).
- [ ] Fallback claro si el MCP falla.

**E2E del checkpoint:**

- Agregar 4 ofertas:
  1. manual completa,
  2. CSV sin sueldo,
  3. URL con JSON-LD (fixture),
  4. MCP (fixture).
- Agregar una duplicada por URL.
- Verificar:
  - 4 ofertas únicas,
  - duplicado detectado,
  - campos faltantes visibles,
  - procedencia correcta,
  - fallback si el MCP no responde.

**Criterio de aceptación:**

- Ninguna fuente es obligatoria.
- La app funciona sin MCP.
- No se guarda HTML crudo.
- No se llama al sitio real en tests.

**Commit sugerido:**

```text
feat: add multi-source offer ingestion
```

---

## Fase 4 — Matching explicable

- [ ] Cargar `skills.yaml` y resolver alias.
- [ ] Clasificar requisitos must/nice/unknown.
- [ ] Detectar niveles (“básico”, “intermedio”, “avanzado”).
- [ ] Implementar fórmula `overall_score` y `must_have_score`.
- [ ] Implementar decisión `apply` / `apply_with_gaps` / `improve_cv`.
- [ ] Generar explicación con evidencia.
- [ ] Mostrar brechas y recomendaciones.
- [ ] Permitir override manual.
- [ ] Mostrar confianza del análisis.

**E2E del checkpoint:**

- Perfil con SQL 3, Excel 3, Power BI 1, Python 2.
- Oferta que pide SQL 2, Excel 2, Power BI 2 (must) y Python 1 (nice).
- Verificar:
  - score esperado,
  - must_have_score esperado,
  - brecha de Power BI,
  - decisión “Aplicar con brechas”,
  - explicación con evidencia.

**Criterio de aceptación:**

- La fórmula es determinista.
- La explicación coincide con el cálculo.
- El usuario puede corregir y recalcular.
- No hay LLM en el score.

**Commit sugerido:**

```text
feat: add explainable matching
```

---

## Fase 5 — Postulaciones y recordatorios

- [ ] Kanban con cinco estados.
- [ ] Crear postulación desde una oferta.
- [ ] Mover tarjetas con drag-and-drop y con teclado.
- [ ] Notas y próxima acción.
- [ ] Historial de eventos.
- [ ] Recordatorios por fecha.
- [ ] Exportación `.ics`.
- [ ] Filtros por estado, match y vencimiento.

**E2E del checkpoint:**

- Crear 3 postulaciones.
- Mover una a “Entrevista”.
- Agregar nota y próxima acción.
- Crear recordatorio para una fecha.
- Exportar `.ics` y verificar el evento.

**Criterio de aceptación:**

- El estado persiste.
- El Kanban es accesible por teclado.
- El `.ics` abre en Google Calendar/Outlook.
- No se pierden cambios si falla una petición.

**Commit sugerido:**

```text
feat: add application tracking and reminders
```

---

## Fase 6 — Exportaciones y UI bilingüe

- [ ] Exportación Excel con hojas:
  - `Postulaciones`,
  - `Ofertas`,
  - `Matches`,
  - `Brechas`,
  - `Timeline`.
- [ ] Exportación CSV.
- [ ] i18n ES/EN en toda la UI.
- [ ] Toggle de idioma persistente.
- [ ] Revisión de accesibilidad:
  - labels,
  - foco,
  - teclado,
  - contraste.
- [ ] Estados `loading`, `empty`, `error`, `success` en todas las pantallas.
- [ ] Modo demo con datos sintéticos.

**E2E del checkpoint:**

- Cambiar idioma a inglés y verificar textos clave.
- Exportar Excel y verificar las 5 hojas.
- Verificar que el modo demo no usa PII.
- Navegar el Kanban solo con teclado.

**Criterio de aceptación:**

- No hay strings hardcodeados.
- El Excel abre sin reparaciones.
- La UI es usable en ambos idiomas.
- El modo demo es reproducible.

**Commit sugerido:**

```text
feat: add exports and bilingual UI
```

---

## Fase 7 — E2E final, demo y release

- [ ] E2E medio-difícil completo:
  - 1 perfil,
  - 2 CVs,
  - 5 ofertas,
  - duplicado,
  - fecha vencida,
  - must-have faltante.
- [ ] Artefactos con checksums.
- [ ] README con capturas y métricas reales.
- [ ] README.en.md.
- [ ] Video demo de 2–3 minutos.
- [ ] Dogfooding:
  - usar PractiCV en 3–5 ofertas reales,
  - registrar tiempos y brechas,
  - documentar aprendizajes.
- [ ] Tag `v0.1.0`.
- [ ] Release con artefactos.

**E2E del checkpoint:**

- Ejecutar desde cero en una base limpia.
- Verificar todos los flujos.
- Confirmar que no hay llamadas a sitios reales.
- Verificar checksums.

**Criterio de aceptación:**

- Todos los checkpoints anteriores marcados.
- E2E verde y reproducible.
- README y README.en.md completos.
- Demo funciona sin Practilizate ni MCP.
- No hay PII ni secretos.
- Tag y release creados.

**Commits sugeridos:**

```text
test: add medium-hard e2e scenario
docs: finalize v0.1.0
chore: release v0.1.0
```

---

## Definición de terminado

Un checkpoint está terminado cuando:

- [ ] El E2E del checkpoint pasa.
- [ ] El artefacto correspondiente existe.
- [ ] El checkbox está marcado.
- [ ] `README.md` está actualizado si cambió algo visible.
- [ ] `ruff format` y `ruff check` pasan.
- [ ] `pnpm lint` y `pnpm typecheck` pasan.
- [ ] No hay PII, secretos ni datos crudos.
- [ ] El commit está hecho.

El proyecto está terminado cuando:

- [ ] Todos los checkpoints están marcados.
- [ ] El E2E medio-difícil pasa desde cero.
- [ ] La demo funciona con datos sintéticos.
- [ ] README y README.en.md están completos.
- [ ] La UI funciona en español e inglés.
- [ ] No hay dependencia de Practilizate ni del MCP para arrancar.
- [ ] La licencia y los créditos están claros.

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
