# CODESTYLE.md — PractiCV

> **Regla base:** documentación en español; código, esquema, logs y commits en inglés; UI en español e inglés.

---

## 1. Principios

- **Correctness first:** primero que funcione y sea entendible; después, que sea elegante.
- **Simplicidad:** la abstracción se gana cuando elimina duplicación real, no cuando “se ve profesional”.
- **Explícito sobre implícito:** nombres claros, errores claros, contratos claros.
- **Sin magia:** nada de metaprogramación innecesaria, imports dinámicos o `**kwargs` opacos.
- **Sin código muerto:** si no se usa, se borra.
- **Sin comentarios narrativos:** el código debe explicarse solo; los comentarios son para decisiones no obvias.
- **Profesionalismo:** no se commitea código roto; no se ocultan fallos; no se adivina un requisito.

---

## 2. Idioma

| Elemento | Idioma |
|---|---|
| Documentación (`SPECS`, `ROADMAP`, `CODESTYLE`, `AGENTS`, `README`) | Español |
| `README.en.md` | Inglés |
| UI visible | Español e inglés (i18n) |
| Código, variables, funciones, clases | Inglés |
| Tablas, columnas, migraciones | Inglés |
| Logs y errores técnicos | Inglés |
| Commits | Inglés |
| Comentarios técnicos | Inglés, solo si son necesarios |
| Mensajes de error al usuario | Español e inglés |

No hardcodear strings de UI. Todo texto visible pasa por el sistema de i18n.

---

## 3. Backend

### Stack

- Python 3.13.
- FastAPI.
- SQLAlchemy 2.
- Pydantic v2.
- Alembic.
- SQLite para v0.1; PostgreSQL opcional para v0.2.
- `ruff` para formato y lint.
- `pytest` + Playwright para E2E.

### Estructura

```text
backend/
├─ practicv/
│  ├─ domain/
│  │  ├─ profile/
│  │  ├─ offers/
│  │  ├─ matching/
│  │  ├─ applications/
│  │  └─ shared/
│  ├─ application/
│  │  ├─ use_cases/
│  │  └─ ports/
│  ├─ adapters/
│  │  ├─ db/
│  │  └─ sources/
│  ├─ api/
│  │  ├─ routes/
│  │  └─ schemas/
│  ├─ config.py
│  └─ main.py
├─ migrations/
└─ pyproject.toml
```

### Reglas

- Type hints en todo el código público.
- `from __future__ import annotations` solo si aporta claridad.
- Funciones pequeñas; una responsabilidad por función.
- Nada de `print()`. Usar `logging` estructurado.
- Nada de `except Exception: pass`.
- Los errores de dominio se modelan como excepciones explícitas y se mapean a HTTP en la capa API.
- La configuración se lee con `pydantic-settings`; nunca se hardcodean credenciales.
- El dominio no importa FastAPI, SQLAlchemy ni clientes HTTP.
- Los repositorios se inyectan; no se instancian dentro del dominio.
- Las consultas SQL viven en adaptadores de persistencia, no en rutas ni en componentes.
- Evitar N+1: usar `selectinload`/`joinedload` cuando corresponda.
- Paginación obligatoria en listados.
- Fechas en UTC; la UI las muestra en zona local.
- IDs UUID o ULID; no autos incrementales expuestos en URLs si se puede evitar.

### Manejo de errores

Formato de error de API:

```json
{
  "error": {
    "code": "offer_not_found",
    "message": "Offer not found",
    "details": {}
  }
}
```

- `code` estable y en inglés.
- `message` técnico en inglés.
- La traducción al usuario se hace en la UI.
- No devolver stack traces en producción.

### Logging

- JSON estructurado.
- Campos: `timestamp`, `level`, `request_id`, `event`, `context`.
- Sin PII: no loggear CVs, correos ni teléfonos.
- No loggear tokens ni secretos.

---

## 4. Frontend

### Stack

- Next.js + TypeScript estricto.
- Tailwind CSS.
- `dnd-kit` para el Kanban.
- `next-intl` o equivalente para i18n ES/EN.
- ESLint + Prettier.

### Reglas

- `strict: true` en TypeScript.
- Nada de `any` salvo justificación explícita.
- Componentes pequeños y con una responsabilidad.
- Server Components por defecto; Client Components solo cuando haya estado, eventos o APIs del navegador.
- Los tipos de API se comparten o se generan; no duplicar contratos a mano.
- Estados obligatorios en cada pantalla: `loading`, `empty`, `error`, `success`.
- Nada de `alert()` ni `confirm()` nativos; usar componentes accesibles.
- No hardcodear URLs de API; usar variables de entorno.
- No hardcodear textos visibles; usar i18n.

### Accesibilidad

- Todos los inputs con `label`.
- Navegación completa por teclado.
- Foco visible.
- Contraste mínimo WCAG AA.
- `aria-*` solo cuando sea necesario y correcto.
- No usar color como único indicador.
- Respetar `prefers-reduced-motion`.

### Kanban

- Accesible por teclado: mover tarjetas con botones o menú, no solo drag-and-drop.
- Estados: `saved`, `applied`, `interview`, `rejected`, `offer`.
- Cada tarjeta muestra empresa, título, match, fecha límite y próxima acción.
- No perder cambios si falla una petición; mostrar error y permitir reintentar.

---

## 5. Arquitectura

### Monolito modular

- Un solo deployable local.
- Contextos separados por boundaries.
- Comunicación entre contextos por interfaces públicas, no por tablas.
- Contratos Pydantic/TypeScript en los bordes.
- Adaptadores para fuentes externas.
- Idempotencia en ingesta.
- Observabilidad con logs estructurados y `run_manifest`.

### Contextos

| Contexto | Responsabilidad | No debe hacer |
|---|---|---|
| `profile` | Perfil, CV, habilidades | Leer ofertas o matches |
| `offers` | Captura, normalización, dedupe | Calcular matches |
| `matching` | Requisitos, score, explicación | Escribir en tablas de ofertas |
| `applications` | Kanban, eventos, recordatorios | Scrapear fuentes |
| `exports` | Excel, CSV, ICS | Cambiar estado de negocio |
| `shared` | Contratos, config, logging | Lógica de negocio |

### Prohibido

- Importar modelos ORM entre contextos.
- Compartir tablas como contrato.
- Poner lógica de negocio en rutas o componentes.
- Acoplar el núcleo al MCP o a Practilizate.
- Agregar microservicios reales, colas o brokers en el MVP.

---

## 6. Testing

- **E2E-first:** el escenario se escribe antes de la implementación.
- **E2E es el mecanismo principal.** No unit tests después del código.
- Si necesitas aislar, primero enumera los modos de fallo y luego implementa.
- No tests tautológicos.
- No tests change-detector.
- No regression tests sin brecha real de comportamiento.
- Escenario E2E medio-difícil, no el más simple.
- Artefactos repetibles en `artifacts/e2e/`.
- No modificar fixtures para pasar tests.

### Herramientas

- `pytest` para orquestar E2E de API y flujo completo.
- Playwright para UI.
- Fixtures JSON para MCP, URL y CSV.
- Nunca llamar al sitio real en CI.

### Nombres de tests

```text
test_e2e_profile_cv_matching_flow
test_e2e_offer_ingestion_deduplicates_sources
test_e2e_matching_reports_must_have_gap
test_e2e_kanban_export_calendar
```

---

## 7. Git

### Commits

Conventional commits:

```text
feat: add multi-source offer ingestion
fix: handle missing salary values
docs: add matching explanation
test: add medium-hard e2e scenario
refactor: isolate offer source adapters
chore: configure ruff and eslint
```

Reglas:

- Un commit por checkpoint significativo.
- Mensaje en inglés, imperativo, corto.
- No mezclar refactor grande con feature.
- Formatear y lint antes de commitear.
- No commitear secretos, `.env`, CVs reales ni bases de datos generadas.

### Ramas

- `main` estable.
- `feat/<short-name>` para features.
- `fix/<short-name>` para bugs.
- No trabajar directo en `main` si hay más de una persona.

---

## 8. Formato

### Backend

```powershell
ruff format .
ruff check .
```

Configuración en `pyproject.toml`:

- `line-length = 100`
- `target-version = "py313"`
- Reglas: `E`, `F`, `I`, `UP`, `B`, `SIM`.

### Frontend

```powershell
pnpm format
pnpm lint
pnpm typecheck
```

- Prettier para formato.
- ESLint con reglas de TypeScript y accesibilidad.
- `tsc --noEmit` en CI.

---

## 9. Comentarios

Permitidos:

- Decisiones no obvias (“se deduplica por URL canónica porque el mismo aviso aparece en varias carreras”).
- Workarounds con referencia a un issue.
- Invariantes de negocio.

Prohibidos:

- “Incrementa el contador”.
- “Devuelve la lista”.
- Comentarios que repiten el nombre de la función.
- Código comentado.
- TODOs sin dueño y sin fecha.

---

## 10. Anti-patrones

- Dioses de 1,000 líneas.
- `utils.py` con 50 funciones sin relación.
- Diccionarios mágicos en lugar de contratos.
- `except Exception` silencioso.
- Consultas SQL en componentes React.
- Lógica de matching en la UI.
- Tests que solo verifican que el mock fue llamado.
- Tests que copian la implementación.
- Dependencias circulares.
- Acoplamiento a Practilizate.
- Scraping masivo.
- Métricas inventadas.

---

## 11. Definición de código listo

- Pasa `ruff format`, `ruff check`, `pnpm lint`, `pnpm typecheck`.
- Pasa el E2E del checkpoint.
- Tiene tipos y contratos claros.
- Tiene manejo de errores.
- Tiene logs sin PII.
- Tiene estados de UI.
- Tiene i18n.
- Tiene tests E2E del comportamiento.
- No tiene código muerto.
- No tiene secretos ni PII.
