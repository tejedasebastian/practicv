# PractiCV

**Copiloto de postulaciones para estudiantes.**

PractiCV convierte cualquier oferta de prácticas en una decisión: captura la oferta, la compara con tu CV, te explica qué te falta y organiza tu postulación en un Kanban con recordatorios.

> **Estado:** Fase 0 completada (scaffold, health check, UI base, Docker y CI). El producto v0.1.0 sigue en desarrollo. Este README describe el producto terminado; las capturas y métricas se completan al cerrar el roadmap.
>
> **English:** [README.en.md](README.en.md)

---

## ¿Por qué PractiCV?

Los estudiantes postulan a ciegas: revisan muchas ofertas sin criterio, usan el mismo CV para todo y olvidan fechas límite. Las bolsas de trabajo resuelven la publicación, no la decisión personal.

PractiCV responde:

- ¿Qué requisitos pide realmente esta oferta?
- ¿Cuáles cumplo y cuáles no?
- ¿Qué evidencia de mi CV respalda cada requisito?
- ¿Vale la pena postular o me conviene prepararme primero?
- ¿A qué postulé y qué sigue?

---

## Qué hace

1. **Perfil y CV:** crea tu perfil y sube tu CV en PDF o DOCX.
2. **Captura:** agrega ofertas desde texto, CSV, URL o el MCP de practicas.pe.
3. **Extracción:** detecta requisitos, habilidades y niveles.
4. **Match explicable:** calcula coincidencia y muestra brechas con evidencia.
5. **Kanban:** guarda, postula, agenda entrevista, registra rechazo u oferta.
6. **Recordatorios:** fechas límite y próximas acciones, con exportación `.ics`.
7. **Exportación:** Excel, CSV y calendario.

No es un job board, no postula automáticamente y no promete empleo.

---

## Demo

> Capturas pendientes de la implementación.

![Match CV–oferta](docs/assets/match.png)

![Kanban de postulaciones](docs/assets/kanban.png)

![Vista bilingüe](docs/assets/bilingual.png)

---

## Arquitectura

PractiCV es un **monolito modular local-first**: boundaries y contratos de microservicios, pero un solo deployable.

```text
Next.js (UI ES/EN)
        │
        ▼
FastAPI (API + casos de uso)
        │
   ┌────┼────────────┬──────────────┐
   ▼    ▼            ▼              ▼
Profile Offers     Matching     Applications
CV      Ingestion  Reglas       Kanban
        │                           │
        ▼                           ▼
Sources: MCP, texto, CSV, URL   Exports: Excel, CSV, ICS
```

**Contextos:**

- `profile`: perfil, CV, habilidades.
- `offers`: captura, normalización, deduplicación, procedencia.
- `matching`: requisitos, score y explicación.
- `applications`: Kanban, eventos y recordatorios.
- `exports`: Excel, CSV, ICS.

**Principios:**

- El dominio no depende de FastAPI ni SQLAlchemy.
- Los contextos se comunican por contratos, no por tablas.
- La ingesta es idempotente.
- Si una fuente falla, el resto sigue funcionando.
- Sin colas, brokers ni microservicios reales en el MVP.

---

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic |
| Base de datos | SQLite (PostgreSQL opcional) |
| Frontend | Next.js, TypeScript, Tailwind CSS, dnd-kit |
| Parseo | pdfplumber/pypdf, python-docx, BeautifulSoup, extruct |
| Matching | Reglas deterministas en Python |
| Exportación | openpyxl, pandas, ics |
| Testing | pytest + Playwright, E2E-first |
| Infra | Docker Compose, GitHub Actions |

---

## Inicio rápido

> Comandos objetivo; se ajustan cuando exista el scaffold.

```powershell
git clone <repository-url>
cd practicv

# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn practicv.main:app --reload

# Frontend
cd ..\frontend
pnpm install
pnpm dev
```

Abrir `http://localhost:3000`.

### Docker Compose

```powershell
docker compose up --build
```

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8001`
- Health: `http://localhost:8001/health`

Los puertos de Docker se mueven a 3001/8001 para no chocar con otros proyectos locales.

### Modo demo

```powershell
python -m practicv seed --demo
```

Carga un perfil sintético, ofertas de ejemplo y matches. No usa datos personales.

---

## Cómo se usa

### 1. Crear perfil

Completa carrera, ciclo, ubicación, roles objetivo y expectativa de sueldo.

### 2. Subir CV

Sube un PDF o DOCX. PractiCV extrae texto y habilidades con reglas locales. Revisa, corrige y confirma.

Si una sección no se pudo leer, puedes activar “analizar con IA”. Antes de enviar, se redactan correo y teléfono.

### 3. Agregar ofertas

- **MCP practicas.pe:** busca por carrera, departamento y modalidad.
- **Texto:** pega la descripción desde cualquier portal.
- **CSV/Excel:** importa varias ofertas.
- **URL:** captura JSON-LD/OpenGraph cuando esté disponible.

### 4. Revisar el match

Ves:

- score general,
- score de requisitos must-have,
- brechas concretas,
- evidencia del CV,
- recomendación.

### 5. Organizar la postulación

Mueve la oferta a Guardada, Postulada, Entrevista, Rechazada u Oferta. Agrega notas y próxima acción.

### 6. Recordatorios y exportación

Exporta `.ics` para tu calendario y Excel/CSV para tu registro.

---

## Fuentes de datos

| Fuente | Uso | ¿Obligatoria? |
|---|---|---|
| MCP `practicas-pe` | Buscar ofertas de practicas.pe | No |
| Texto pegado | Cualquier portal | No |
| CSV/Excel | Carga masiva | No |
| URL + JSON-LD | Captura individual | No |
| Practilizate | Benchmarks históricos | No |

**PractiCV no depende de Practilizate ni del MCP.** Si no están disponibles, la app funciona con texto, CSV y URL.

---

## Matching explicable

Para cada requisito:

- `w`: peso (must-have = 3, nice-to-have = 1, unknown = 1.5).
- `r`: nivel requerido (1–3).
- `u`: nivel del usuario (0–3).
- `coverage = min(u, r) / r`.

```text
overall_score = 100 * Σ(w * coverage) / Σ(w)
must_have_score = 100 * Σ(w * coverage must) / Σ(w must)
```

Decisión:

- `must_have_score >= 85` y `overall >= 80`: **Aplicar**.
- `must_have_score >= 60`: **Aplicar con brechas**.
- Si no: **Preparar CV**.

El usuario puede corregir habilidades, niveles y decisión. El score es una **coincidencia estimada**, no una probabilidad de contratación.

---

## Privacidad

- Local-first: tu CV y tus postulaciones viven en tu máquina.
- Sin telemetría por defecto.
- Sin PII en el repositorio.
- Sin secretos en Git.
- Sin scraping masivo.
- Sin auto-postulación.
- LLM opcional y con consentimiento.
- Puedes exportar y borrar tus datos.

---

## Testing

- E2E-first.
- E2E como mecanismo principal.
- Sin unit tests después del código.
- Escenario medio-difícil.
- Artefactos repetibles en `artifacts/e2e/`.

```powershell
pytest tests/e2e
```

Artefactos:

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

## Métricas

> Se completan con el E2E y el dogfooding. No se inventan.

| Métrica | Valor |
|---|---|
| Ofertas evaluadas en dogfooding | `[pendiente]` |
| Tiempo mediano para evaluar una oferta | `[pendiente]` |
| Postulaciones registradas | `[pendiente]` |
| Brechas descubiertas | `[pendiente]` |
| Tiempo de ejecución del E2E | `[pendiente]` |
| Cobertura de flujos críticos | `[pendiente]` |

---

## Limitaciones

- v0.1 es local-first y de un solo usuario.
- El parseo de CV puede fallar en formatos complejos; el usuario corrige.
- La captura por URL es best effort; algunos portales bloquean.
- El MCP puede no estar disponible; hay fallback manual.
- El match es una guía, no una garantía.
- No incluye auto-postulación.
- No incluye app móvil.
- No incluye multiusuario.

---

## Roadmap

- v0.1: perfil, CV, captura, match, Kanban, recordatorios y export.
- v0.2: bookmarklet, correos de alerta, adaptador Practilizate, Power Automate, Power BI.
- v0.3: múltiples versiones de CV y deploy público de la demo.

Ver [ROADMAP.md](ROADMAP.md).

---

## Licencia

MIT para el código. Los datos de terceros mantienen sus propios términos.

---

## Créditos

- Fuente de ofertas: [practicas.pe](https://www.practicas.pe/). PractiCV no está afiliado.
- Inspiración de producto: Practilizate, el observatorio de prácticas del Perú.
- Construido como proyecto de portafolio para roles de data/BI y software.
