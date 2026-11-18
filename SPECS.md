# SPECS.md — PractiCV

> **Producto:** PractiCV — Copiloto de postulaciones para estudiantes.
> **Versión:** 0.1 (MVP).
> **Fecha:** 17 de noviembre de 2026.
> **Estado:** especificación cerrada; implementación pendiente.
> **Documentación:** español. **Código y commits:** inglés. **UI:** español e inglés.

---

## 1. Resumen

PractiCV es una aplicación **local-first** que ayuda a un estudiante a decidir a qué prácticas postular y a no perder el seguimiento.

El flujo es:

1. El estudiante crea su perfil y sube su CV.
2. Captura ofertas desde texto, CSV, URL o el MCP `practicas-pe`.
3. PractiCV extrae requisitos y habilidades.
4. Calcula un **match explicable** entre el CV y la oferta.
5. Muestra brechas concretas: “te falta SQL”, “tu Power BI está en nivel 1 y piden 2”.
6. Organiza la postulación en un Kanban con fechas y recordatorios.
7. Exporta Excel, CSV y calendario.

PractiCV **no depende de Practilizate**. Practilizate es un observatorio de datos agregados; PractiCV es un copiloto personal. La única integración posible es un adaptador opcional de benchmarks o de CSV local.

---

## 2. Problema

Los estudiantes pierden oportunidades por cuatro razones:

1. **Filtran mal:** revisan muchas ofertas sin criterio.
2. **No adaptan el CV:** postulan con el mismo CV a todo.
3. **No hacen seguimiento:** olvidan fechas, entrevistas y respuestas.
4. **No saben qué les falta:** no tienen una explicación concreta de sus brechas.

Las bolsas de trabajo resuelven la publicación, no la decisión personal. PractiCV se enfoca en la decisión y el seguimiento.

---

## 3. Usuarios

### Usuario principal

- Estudiante de 6.º a 10.º ciclo de una carrera universitaria o técnica.
- Busca prácticas preprofesionales o profesionales.
- Tiene un CV en PDF o DOCX.
- Usa principalmente español; puede leer inglés.

### Usuario secundario

- Recién egresado en búsqueda de su primer empleo.
- Centro de empleabilidad que quiera recomendar la herramienta.
- Autor del proyecto, como caso de portafolio.

### Fuera de alcance

- Reclutadores.
- Empresas que publican ofertas.
- Usuarios que buscan empleos senior.

---

## 4. Principios de producto

1. **Trae tu propia oferta (BYOO):** funciona con cualquier oferta que el usuario encuentre.
2. **Local-first:** el CV y las postulaciones viven en la máquina del usuario.
3. **Explicable:** el match muestra fórmula, evidencia y brechas; no es una caja negra.
4. **Honesto:** no inventa experiencia ni promete empleo.
5. **Sin dependencias:** si el MCP o Practilizate no están, la app sigue funcionando.
6. **Sin auto-postulación:** el usuario decide y envía.
7. **Privacidad por defecto:** sin telemetría, sin CVs en la nube, sin PII en el repo.

---

## 5. Alcance del MVP (v0.1)

### Incluido

- Un solo usuario, local-first, PostgreSQL 17 local (Docker).
- Perfil del estudiante.
- Un CV activo (PDF/DOCX) con parseo mixto:
  - reglas locales primero,
  - LLM opcional solo para campos que no se pudieron extraer,
  - confirmación y edición manual.
- Captura de ofertas:
  - MCP `practicas-pe` (opcional),
  - texto pegado,
  - CSV/Excel,
  - URL con JSON-LD/OpenGraph (best effort).
- Taxonomía de habilidades propia.
- Matching explicable por reglas.
- Kanban con cinco estados.
- Recordatorios en app y exportación `.ics`.
- Exportación a Excel y CSV.
- UI español/inglés.
- Modo demo con datos sintéticos.
- E2E medio-difícil con artefactos.

### Fuera del MVP

- Auto-postulación.
- Scraping masivo o de LinkedIn.
- Multiusuario o SaaS.
- App móvil nativa.
- Bookmarklet y correos de alerta (v0.2).
- Integración con Jira como dependencia del producto.
- LLM obligatorio para el matching.
- Firma de documentos o trámites legales.
- Promesas de empleo o probabilidades de contratación.
- Dashboard Power BI (v0.2 opcional).

---

## 6. Fuentes de datos

### 6.1 Matriz general

| Dato | Fuente | Cómo se obtiene | ¿MVP? | Dependencia |
|---|---|---|---|---|
| Perfil | Usuario | Formulario | Sí | Ninguna |
| CV | Usuario | PDF/DOCX + parser local | Sí | Ninguna |
| Ofertas de practicas.pe | MCP `practicas-pe` | `buscar_practicas` + `obtener_practica` | Sí, opcional | MCP (opcional) |
| Oferta individual | Usuario | Pegar texto | Sí | Ninguna |
| Ofertas en lote | Usuario | Importar CSV/Excel | Sí | Ninguna |
| Oferta desde URL | Página pública | Fetch + JSON-LD/OpenGraph | Sí, best effort | Ninguna |
| Oferta desde navegador | Página actual | Bookmarklet | v0.2 | Ninguna |
| Oferta desde correo | Gmail/Outlook | OAuth + parser | v0.2 | Ninguna |
| Oferta desde Practilizate | CSV/PostgreSQL local | Adaptador opcional | v0.2 | Practilizate (opcional) |
| Taxonomía de habilidades | Propia | `skills.yaml` + alias | Sí | Ninguna |
| Benchmarks | Practilizate/público | CSV agregado | Opcional | Opcional |
| Recordatorios | App | Scheduler + ICS | Sí | Ninguna |
| Correo/WhatsApp | Power Automate | Flujo externo | v0.2 | Ninguna |

### 6.2 MCP `practicas-pe`

El servidor existente está en:

`C:\Users\sebas\Desktop\practicas\mcp\practicas_pe_server.py`

Expone:

- `listar_filtros`: carreras, departamentos, modalidades y órdenes.
- `buscar_practicas`: búsqueda por texto, carrera, departamento, modalidad, orden, página y límite.
- `obtener_practica`: detalle completo por URL.

**Flujo:**

1. El usuario abre “Buscar en practicas.pe”.
2. Elige carrera, departamento, modalidad y palabra clave.
3. PractiCV llama a `buscar_practicas`.
4. El usuario selecciona resultados.
5. PractiCV llama a `obtener_practica` para cada uno.
6. Normaliza y guarda la oferta con procedencia.

**Mapeo:**

| MCP `practicas-pe` | PractiCV |
|---|---|
| `titulo` | `offers.title` |
| `empresa` | `offers.company` |
| `ubicacion` | `offers.location` |
| `subvencion_monto` | `offers.salary_amount` |
| `moneda` | `offers.salary_currency` |
| `modalidad` | `offers.modality` |
| `requisitos`, `conocimientos`, `formacion_academica`, `funciones` | `offers.requirements_text` |
| `descripcion` | `offers.description` |
| `publicado` | `offers.published_at` |
| `vence` o `plazo_postular` | `offers.deadline_at` |
| `url` | `offers.source_url` |
| `id_oferta` | `offers.external_id` |
| `enlaces_postulacion` | `offer_links` |

**Implementación:**

- Adaptador aislado en `backend/practicv/adapters/sources/practicas_pe_mcp.py`.
- Cliente MCP por stdio o HTTP.
- Recomendación MVP: lanzar el servidor como subproceso persistente y usar el SDK de MCP por stdio.
- Timeout, reintentos y caché local.
- Si falla, error claro y fallback a texto/CSV/URL.
- **No imports de Practilizate.**

**Legal:** el MCP usa caché y límites básicos, pero no verifica `robots.txt`. Antes de distribuir PractiCV, revisar términos y agregar verificación. Solo búsquedas iniciadas por el usuario; no crawlers.

### 6.3 Texto pegado

Fuente principal y más confiable. El usuario pega la descripción y completa o confirma:

- título, empresa, ubicación, modalidad,
- URL, sueldo, fecha límite,
- descripción y requisitos.

Funciona con cualquier portal y no depende de scraping.

### 6.4 CSV/Excel

Plantilla:

```text
url,titulo,empresa,ubicacion,modalidad,sueldo,descripcion,requisitos,fecha_limite
```

La app valida, previsualiza y permite corregir antes de importar.

### 6.5 URL + JSON-LD

1. Verifica `robots.txt` y términos.
2. Hace una petición con User-Agent identificable.
3. Busca JSON-LD `JobPosting`.
4. Extrae campos.
5. Si falla, intenta OpenGraph.
6. Si no hay mínimo viable, pide pegar texto.

No guarda HTML crudo.

### 6.6 Bookmarklet (v0.2)

Bookmarklet que envía título, URL, JSON-LD y texto visible a `http://localhost:8000/api/offers/capture`. El usuario confirma. Evita anti-bot y mantiene el contenido local.

### 6.7 Correos de alerta (v0.2)

Gmail/Outlook con permisos de solo lectura. Se buscan alertas de empleo y el usuario elige cuáles importar. No se autentica en LinkedIn ni en portales. Tokens en el llavero del sistema.

### 6.8 Practilizate (opcional, v0.2)

Lee:

- `data/processed/dashboard_dataset.csv` si el usuario corrió Practilizate localmente, o
- una vista PostgreSQL de Practilizate.

Mapea columnas. Desactivado por defecto. **No imports de código.**

### 6.9 Taxonomía de habilidades

Archivo `skills.yaml`:

```yaml
- id: sql
  name: SQL
  category: data
  aliases: [sql, mysql, postgresql, postgres, pl/sql, t-sql]
- id: power_bi
  name: Power BI
  category: bi
  aliases: [power bi, powerbi, pbi]
- id: excel
  name: Excel
  category: office
  aliases: [excel, hojas de cálculo, spreadsheets]
```

Se puede sembrar con ESCO/O*NET y términos del mercado peruano. Es editable. No se importa desde Practilizate.

### 6.10 Qué fuente usar

| Situación | Fuente |
|---|---|
| “Quiero ver ofertas de practicas.pe ahora” | MCP |
| “Encontré una oferta en Bumeran/Computrabajo/LinkedIn” | Texto o URL |
| “Tengo una hoja de Excel” | CSV/Excel |
| “Quiero capturar la oferta del navegador” | Bookmarklet (v0.2) |
| “Quiero importar alertas del correo” | Correos (v0.2) |
| “Quiero datos históricos” | Practilizate (opcional) |
| “No tengo internet o el portal bloquea” | Texto |

La UI muestra siempre la procedencia y la fecha de captura.

---

## 7. Flujo de usuario

1. Crear perfil.
2. Subir CV.
3. Confirmar habilidades y niveles.
4. Agregar oferta (MCP/texto/CSV/URL).
5. Revisar requisitos extraídos.
6. Ver match y explicación.
7. Decidir: guardar, postular o descartar.
8. Mover en Kanban y poner fecha límite.
9. Recibir recordatorio / exportar ICS.
10. Exportar Excel y métricas.

### Pantallas

- `/` — resumen: postulaciones activas, vencimientos, próximas acciones.
- `/perfil` — datos del estudiante.
- `/cv` — carga, parseo y confirmación.
- `/ofertas` — lista y filtros.
- `/ofertas/nueva` — pestañas: MCP, texto, CSV, URL.
- `/ofertas/[id]` — detalle, requisitos, match y explicación.
- `/postulaciones` — Kanban.
- `/postulaciones/[id]` — historial, notas, recordatorios.
- `/ajustes` — fuentes, exportación, privacidad, idioma.

---

## 8. Arquitectura

### 8.1 Monolito modular

Un solo deployable local, con boundaries y contratos de microservicios.

```text
┌─────────────────────────────┐
│ Next.js (UI)                │
│ ES/EN, Kanban, perfil, CV   │
└──────────────┬──────────────┘
               │ HTTP
┌──────────────▼──────────────┐
│ FastAPI                     │
│ API + casos de uso          │
└──────────────┬──────────────┘
               │
   ┌───────────┼────────────┬──────────────┐
   ▼           ▼            ▼              ▼
┌────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐
│Profile │ │ Offers   │ │ Matching  │ │Applications│
│CV      │ │Ingestion │ │ Reglas    │ │Kanban      │
└────────┘ └────┬─────┘ └───────────┘ └─────┬──────┘
                │                           │
                ▼                           ▼
        ┌──────────────┐            ┌──────────────┐
        │ Sources      │            │ Exports      │
        │ MCP/CSV/URL  │            │ Excel/CSV/ICS│
        │ Manual       │            │              │
        └──────────────┘            └──────────────┘
```

### 8.2 Contextos

| Contexto | Responsabilidad |
|---|---|
| `profile` | Perfil, CV, habilidades, niveles |
| `offers` | Captura, normalización, dedupe, procedencia |
| `matching` | Requisitos, score, explicación, brechas |
| `applications` | Kanban, eventos, recordatorios |
| `exports` | Excel, CSV, ICS |
| `shared` | Contratos, configuración, logging, errores |

### 8.3 Reglas de boundaries

- Cada contexto tiene `domain`, `application`, `adapters`.
- Solo se comunican por interfaces públicas y contratos.
- El dominio no importa FastAPI, SQLAlchemy ni clientes HTTP.
- No se comparten modelos ORM entre contextos.
- Los adaptadores externos viven en `adapters/sources/`.
- La ingesta es idempotente: `dedupe_hash` único.
- Los errores se mapean explícitamente a HTTP.
- Logs estructurados, sin PII.

### 8.4 Principios de microservicios aplicados

- **Single responsibility:** cada contexto hace una cosa.
- **Contratos explícitos:** Pydantic/TypeScript en los bordes.
- **Aislamiento de fallos:** si el MCP falla, el resto sigue.
- **Idempotencia:** reintentar una importación no duplica.
- **Observabilidad:** `request_id`, logs, `run_manifest`.
- **Configuración externa:** `.env`, no hardcodeo.
- **Sin infraestructura distribuida:** no colas, brokers ni servicios separados en el MVP.

---

## 9. Modelo de datos

Base: **PostgreSQL 17**. `SQLAlchemy 2` + `Alembic` + `psycopg 3`. Fechas UTC.

### `profiles`

- `id` (UUID, PK)
- `full_name`
- `email`
- `phone`
- `university`
- `career`
- `cycle`
- `location`
- `target_roles` (JSON)
- `preferred_modality`
- `salary_expectation`
- `availability`
- `locale` (`es`/`en`)
- `created_at`
- `updated_at`

### `cv_documents`

- `id` (UUID, PK)
- `profile_id` (FK)
- `filename`
- `mime_type`
- `raw_text`
- `parsed_json`
- `is_active`
- `uploaded_at`

### `skills`

- `id` (PK)
- `canonical_name`
- `category`
- `aliases` (JSON)

### `profile_skills`

- `profile_id` (FK)
- `skill_id` (FK)
- `level` (0–3)
- `evidence`
- `source` (`cv`, `manual`, `course`)
- `confirmed` (bool)

### `offers`

- `id` (UUID, PK)
- `source_type` (`manual`, `csv`, `url`, `bookmarklet`, `email`, `mcp_practicas_pe`, `practilizate`, `ats`)
- `external_id`
- `source_url`
- `captured_at`
- `title`
- `company`
- `location`
- `modality`
- `salary_text`
- `salary_amount`
- `salary_currency`
- `description`
- `requirements_text`
- `published_at`
- `deadline_at`
- `raw_text`
- `parse_confidence`
- `dedupe_hash` (UNIQUE)

### `offer_skills`

- `offer_id` (FK)
- `skill_id` (FK)
- `requirement_type` (`must`, `nice`, `unknown`)
- `required_level` (1–3)
- `evidence_text`
- `confidence`

### `offer_links`

- `id`
- `offer_id` (FK)
- `kind` (`application`, `bases`, `other`)
- `label`
- `url`

### `matches`

- `id` (UUID, PK)
- `profile_id` (FK)
- `offer_id` (FK)
- `overall_score`
- `must_have_score`
- `decision` (`apply`, `apply_with_gaps`, `improve_cv`)
- `gaps_json`
- `explanation_json`
- `created_at`

### `applications`

- `id` (UUID, PK)
- `profile_id` (FK)
- `offer_id` (FK)
- `status` (`saved`, `applied`, `interview`, `rejected`, `offer`)
- `applied_at`
- `next_action_at`
- `next_action_note`
- `notes`
- `cv_document_id` (FK)
- `created_at`
- `updated_at`

Restricción: `UNIQUE(profile_id, offer_id)`.

### `application_events`

- `id` (UUID, PK)
- `application_id` (FK)
- `event_type`
- `event_at`
- `notes`

### `reminders`

- `id` (UUID, PK)
- `application_id` (FK)
- `due_at`
- `channel` (`in_app`, `ics`)
- `message`
- `status` (`pending`, `done`, `dismissed`)

### `source_configs`

- `id`
- `source_type`
- `config_json`
- `enabled`

### Índices y constraints

- `offers.dedupe_hash` UNIQUE.
- `offers.source_url` index.
- `offers.deadline_at` index.
- `applications.status` index.
- `reminders.due_at` index.
- `profile_skills` PK compuesta `(profile_id, skill_id)`.
- `offer_skills` PK compuesta `(offer_id, skill_id)`.

### 9.1 Motor de base de datos y SQL avanzado

**Decisión: PostgreSQL 17 como motor principal.**

SQLAlchemy 2 es el toolkit/ORM, no el motor. SQLite se descarta como motor principal porque no permite demostrar con rigor el nivel **SQL Avanzado** que el CV declara:

- CTEs y window functions de forma nativa.
- `JSONB` para perfiles, explicaciones y configuraciones.
- Vistas y funciones PL/pgSQL.
- Índices parciales, compuestos y `EXPLAIN ANALYZE`.
- Mayor cercanía a los motores usados en analytics y banca.

PostgreSQL se ejecuta localmente con Docker Compose, así que el producto sigue siendo local-first. La app no requiere un servicio cloud.

**Entregables SQL de la Fase 1:**

- Vista `v_offer_ranking`: CTE + `ROW_NUMBER()` para rankear ofertas por perfil.
- Función `fn_top_offers_for_profile(profile_id)`: PL/pgSQL con parámetros y `RETURNS TABLE`.
- Índices:
  - `offers(dedupe_hash)` UNIQUE.
  - `offers(deadline_at)`.
  - `offers(company)`.
  - `applications(profile_id, status)`.
  - `matches(profile_id, overall_score DESC)`.
- `docs/sql-performance.md` con `EXPLAIN ANALYZE` antes/después de un índice.
- Seed de 1,000 ofertas sintéticas para probar volumen.

**CI:** GitHub Actions levanta un servicio PostgreSQL 17 y ejecuta las migraciones y el E2E contra una base limpia.

---

## 10. Matching explicable

### 10.1 Extracción de requisitos

Cada requisito se clasifica:

- **Must-have:** “Requisitos”, “Indispensable”, “Excluyente”, “Obligatorio”.
- **Nice-to-have:** “Deseable”, “Plus”, “Valor agregado”.
- **Unknown:** no se puede determinar; peso medio.

Nivel requerido:

- “Básico” → 1.
- “Intermedio” → 2.
- “Avanzado” → 3.
- Sin mención → 2.

### 10.2 Fórmula

Para cada requisito `i`:

- `w_i`: peso (must = 3, nice = 1, unknown = 1.5).
- `r_i`: nivel requerido (1–3).
- `u_i`: nivel del usuario (0–3).
- `coverage_i = min(u_i, r_i) / r_i`.

```text
overall_score = 100 * Σ(w_i * coverage_i) / Σ(w_i)
must_have_score = 100 * Σ(w_i * coverage_i para must) / Σ(w_i para must)
```

### 10.3 Decisión

```text
si must_have_score >= 85 y overall_score >= 80 -> "Aplicar"
si must_have_score >= 60 -> "Aplicar con brechas"
si no -> "Preparar CV"
```

El usuario puede cambiar la decisión manualmente. El sistema no decide por él.

### 10.4 Explicación

Ejemplo:

> **Match: 85%** — Cumples 3 de 4 requisitos.
> ✅ SQL: nivel 3, cumples el nivel 2.
> ✅ Excel: nivel 3, cumples el nivel 2.
> ⚠️ Power BI: nivel 1, la oferta pide nivel 2. Te falta práctica en DAX.
> ✅ Python: nivel 2, cumples el nivel 1.
>
> **Recomendación:** aplica, pero agrega un proyecto de Power BI con DAX antes de la entrevista.

Cada explicación cita evidencia del CV o del perfil cuando sea posible.

### 10.5 Parseo mixto del CV

1. Las reglas locales extraen texto, secciones, fechas y habilidades del catálogo.
2. Si una sección no se pudo identificar o el texto es ambiguo, se ofrece “analizar con IA”.
3. El usuario ve qué fragmento se enviará y puede cancelar.
4. El LLM devuelve una propuesta estructurada; el usuario confirma o corrige.
5. El LLM **nunca** calcula el score ni inventa experiencia.
6. Sin IA, el flujo sigue funcionando con reglas y edición manual.

**Privacidad:** redactar correo y teléfono antes de enviar. LLM opcional y desactivable.

### 10.6 Reglas de honestidad

- No usar LLM para el score en v0.1.
- No inventar experiencia.
- Mostrar confianza del análisis si faltan campos.
- Etiquetar como **coincidencia estimada**, no probabilidad de contratación.
- Permitir corregir habilidades y niveles.

---

## 11. API

Base: `/api/v1`.

### Perfil

- `POST /profiles`
- `GET /profiles/{id}`
- `PATCH /profiles/{id}`

### CV

- `POST /profiles/{id}/cv` (multipart)
- `GET /profiles/{id}/cv`
- `PATCH /profiles/{id}/cv/skills` (confirmar/corregir)

### Ofertas

- `POST /offers/manual`
- `POST /offers/import` (CSV)
- `POST /offers/capture-url`
- `GET /offers`
- `GET /offers/{id}`
- `POST /offers/{id}/match`
- `GET /offers/{id}/match`

### MCP

- `GET /sources/mcp/filters`
- `POST /sources/mcp/search`
- `POST /sources/mcp/import` (selección de URLs)

### Postulaciones

- `POST /applications`
- `GET /applications`
- `GET /applications/{id}`
- `PATCH /applications/{id}`
- `POST /applications/{id}/events`
- `POST /applications/{id}/reminders`

### Exportaciones

- `GET /exports/applications.xlsx`
- `GET /exports/applications.csv`
- `GET /exports/calendar.ics`

### Salud

- `GET /health`
- `GET /health/sources` (estado de MCP/Practilizate)

### Formato de error

```json
{
  "error": {
    "code": "offer_not_found",
    "message": "Offer not found",
    "details": {}
  }
}
```

---

## 12. UI

### Idioma

- Español por defecto.
- Inglés con toggle.
- Persistir preferencia en `profiles.locale` o `localStorage`.
- Todas las cadenas visibles en `messages/es.json` y `messages/en.json`.

### Accesibilidad

- Labels en todos los inputs.
- Navegación por teclado.
- Foco visible.
- Contraste WCAG AA.
- No usar color como único indicador.
- Kanban operable sin drag-and-drop.

### Estados

Cada pantalla debe tener:

- `loading`,
- `empty`,
- `error`,
- `success`.

### Kanban

Columnas:

1. Guardada.
2. Postulada.
3. Entrevista.
4. Rechazada.
5. Oferta.

Cada tarjeta:

- empresa,
- título,
- match %,
- fecha límite,
- próxima acción,
- badge de fuente.

---

## 13. Exportaciones

### Excel

Hoja `Postulaciones`:

- empresa, título, estado, match, fecha de postulación, próxima acción, notas.

Hoja `Ofertas`:

- fuente, URL, ubicación, modalidad, sueldo, fecha límite.

Hoja `Matches`:

- score, must-have score, decisión, brechas.

Hoja `Brechas`:

- habilidad, nivel requerido, nivel del usuario, estado.

Hoja `Timeline`:

- eventos por postulación.

### CSV

Mismos datos que `Postulaciones`, UTF-8.

### ICS

Un evento por recordatorio y por fecha límite.

---

## 14. Privacidad, legal y ética

- Local-first; sin telemetría.
- Sin PII en el repositorio.
- Sin secretos; `.env` fuera de Git.
- Sin scraping masivo; una página por acción.
- Sin LinkedIn scraping.
- Sin auto-postulación.
- MCP opcional; fallback.
- Practilizate opcional; no dependencia.
- LLM opcional; avisar qué se envía.
- Borrado y exportación de datos.
- Modo demo sintético.
- Atribución a practicas.pe.
- Disclaimer: match estimado, no promesa de empleo.

---

## 15. Testing

### Estrategia

- **E2E-first.**
- E2E como mecanismo principal.
- Sin unit tests después del código.
- Si se aísla, primero enumerar fallos.
- Sin tests tautológicos ni change-detector.
- Sin regression tests sin brecha real.
- Escenario medio-difícil.
- Artefactos repetibles.

### Herramientas

- `pytest` para flujo de API.
- Playwright para UI.
- Fixtures JSON para MCP, URL y CSV.
- Nunca llamar al sitio real en CI.

### Escenario E2E principal

- 1 perfil.
- 2 CVs: completo y con brechas.
- 5 ofertas:
  - completa,
  - sin sueldo,
  - con must-have faltante,
  - duplicada por URL,
  - con fecha vencida.
- Verificar:
  - deduplicación,
  - clasificación must/nice,
  - score y explicación,
  - Kanban,
  - recordatorio,
  - exportaciones,
  - cambio de idioma.

### Artefactos

```text
artifacts/e2e/
├─ run_manifest.json
├─ matches.json
├─ applications.xlsx
├─ applications.csv
├─ calendar.ics
├─ quality_report.json
└─ checksums.sha256
```

---

## 16. Criterios de aceptación

- La app arranca sin Practilizate ni MCP.
- Se crea perfil y se sube CV PDF/DOCX.
- Se agregan ofertas por texto, CSV y URL.
- El MCP funciona si está disponible; si no, fallback claro.
- El match muestra score, brechas y explicación.
- El Kanban mueve postulaciones y guarda estado.
- Se genera `.ics` y Excel.
- La UI cambia ES/EN sin recargar.
- El E2E medio-difícil pasa y deja artefactos.
- No hay PII ni secretos en el repo.
- README y README.en.md completos.
- `ruff` y `pnpm lint` pasan.

---

## 17. Métricas

### Producto

- Tiempo para agregar una oferta: < 2 min.
- Tiempo para decidir si aplicar: < 5 min.
- % de postulaciones con próxima acción.
- % de fechas límite cumplidas.
- Utilidad del match (1–5) en dogfooding.
- Claridad de brechas (1–5) en dogfooding.

### Técnicas

- Cobertura E2E de los flujos críticos.
- Tiempo de ejecución del E2E.
- Tiempo de parseo de CV.
- Tiempo de matching.
- Errores por fuente.

### Dogfooding

- Ofertas reales evaluadas.
- Postulaciones registradas.
- Brechas descubiertas.
- Tiempo ahorrado vs. proceso manual.

No inventar métricas. Si no se midió, no se reporta.

---

## 18. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| El parseo del CV falla | Confirmación y edición manual; mostrar texto extraído |
| La URL bloquea el fetch | Fallback a pegar texto |
| El MCP no está disponible o cambia | Adaptador opcional con fallback; fixtures en tests |
| La taxonomía no cubre un término | Alias editable y habilidad manual |
| El matching parece caja negra | Fórmula visible, evidencia y explicación |
| El usuario inventa habilidades | Nivel confirmado y evidencia |
| Scope creep | Lista explícita de fuera de alcance |
| Problemas legales por scraping | Solo captura iniciada por el usuario |
| PII en el repo | Modo demo sintético; `.gitignore` |
| Dependencia de Practilizate | Adaptador opcional y desactivado |
| LLM con datos sensibles | Opt-in, redacción y proveedor configurable |

---

## 19. Roadmap

Ver `ROADMAP.md`. Resumen:

1. Base del proyecto.
2. Dominio y persistencia.
3. Perfil y CV.
4. Ofertas.
5. Matching.
6. Postulaciones y recordatorios.
7. Exportaciones y UI bilingüe.
8. E2E final, demo y release.

---

## 20. Decisiones

### Tomadas

- Nombre: PractiCV.
- Repo: `practicv`.
- Carpeta: `projects/practicv`.
- Stack: FastAPI + Next.js + PostgreSQL 17.
- Arquitectura: monolito modular.
- Alcance: MVP completo.
- Piloto: omitido; dogfooding.
- Docs: español.
- UI: español e inglés.
- Código y commits: inglés.
- Practilizate: adaptador opcional, no dependencia.
- MCP: fuente opcional con fallback.

### Pendientes

- Proveedor de LLM para el parseo opcional.
- Deploy de la demo (Vercel + Render o local).
- Licencia final (MIT recomendada).
- Traducción de docs internas al inglés (v0.2).

---

## 21. No objetivos

- No ser un job board.
- No ser un bot de auto-postulación.
- No scrapear LinkedIn.
- No pedir credenciales de portales.
- No inventar experiencia.
- No prometer empleo.
- No ser un clon de Practilizate.
- No depender de Practilizate ni del MCP para funcionar.
