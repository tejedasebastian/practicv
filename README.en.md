# PractiCV

**An application copilot for students.**

PractiCV turns any internship posting into a decision: it captures the offer, compares it with your CV, explains your gaps, and organizes your application in a Kanban board with reminders.

> **Status:** Phase 0 complete (scaffold, health check, base UI, Docker, and CI). The v0.1.0 product is still in development. This README describes the finished product; screenshots and metrics will be completed as the roadmap closes.
>
> **Español:** [README.md](README.md)

---

## Why PractiCV?

Students apply blindly: they review many postings without criteria, use the same CV for everything, and forget deadlines. Job boards solve publishing, not personal decision-making.

PractiCV answers:

- What does this posting actually require?
- Which requirements do I meet and which do I miss?
- What CV evidence supports each requirement?
- Should I apply now or prepare first?
- Where did I apply, and what is next?

---

## What it does

1. **Profile and CV:** create a profile and upload a PDF or DOCX CV.
2. **Capture:** add offers from text, CSV, URL, or the practicas.pe MCP.
3. **Extraction:** detect requirements, skills, and levels.
4. **Explainable match:** calculate fit and show gaps with evidence.
5. **Kanban:** saved, applied, interview, rejected, offer.
6. **Reminders:** deadlines and next actions, with `.ics` export.
7. **Export:** Excel, CSV, and calendar.

It is not a job board, it does not auto-apply, and it does not promise employment.

---

## Demo

> Screenshots pending implementation.

![CV–offer match](docs/assets/match.png)

![Application Kanban](docs/assets/kanban.png)

![Bilingual view](docs/assets/bilingual.png)

---

## Architecture

PractiCV is a **local-first modular monolith**: microservice-style boundaries and contracts, but a single deployable.

```text
Next.js (ES/EN UI)
        │
        ▼
FastAPI (API + use cases)
        │
   ┌────┼────────────┬──────────────┐
   ▼    ▼            ▼              ▼
Profile Offers     Matching     Applications
CV      Ingestion  Rules        Kanban
        │                           │
        ▼                           ▼
Sources: MCP, text, CSV, URL    Exports: Excel, CSV, ICS
```

**Contexts:**

- `profile`: profile, CV, skills.
- `offers`: capture, normalization, deduplication, provenance.
- `matching`: requirements, score, explanation.
- `applications`: Kanban, events, reminders.
- `exports`: Excel, CSV, ICS.

**Principles:**

- The domain does not depend on FastAPI or SQLAlchemy.
- Contexts communicate through contracts, not tables.
- Ingestion is idempotent.
- If one source fails, the rest keeps working.
- No queues, brokers, or real microservices in the MVP.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic |
| Database | SQLite (PostgreSQL optional) |
| Frontend | Next.js, TypeScript, Tailwind CSS, dnd-kit |
| Parsing | pdfplumber/pypdf, python-docx, BeautifulSoup, extruct |
| Matching | Deterministic Python rules |
| Export | openpyxl, pandas, ics |
| Testing | pytest + Playwright, E2E-first |
| Infra | Docker Compose, GitHub Actions |

---

## Quick start

> Target commands; they will be adjusted once the scaffold exists.

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

Open `http://localhost:3000`.

### Docker Compose

```powershell
docker compose up --build
```

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8001`
- Health: `http://localhost:8001/health`

Docker ports are 3001/8001 to avoid conflicts with other local projects.

### Demo mode

```powershell
python -m practicv seed --demo
```

Loads a synthetic profile, sample offers, and matches. No personal data is used.

---

## How to use it

### 1. Create a profile

Fill in degree, cycle, location, target roles, and salary expectation.

### 2. Upload a CV

Upload a PDF or DOCX. PractiCV extracts text and skills with local rules. Review, correct, and confirm.

If a section cannot be parsed, you can enable “analyze with AI”. Email and phone are redacted before sending.

### 3. Add offers

- **practicas.pe MCP:** search by degree, department, and modality.
- **Text:** paste the description from any portal.
- **CSV/Excel:** import multiple offers.
- **URL:** capture JSON-LD/OpenGraph when available.

### 4. Review the match

You see:

- overall score,
- must-have score,
- concrete gaps,
- CV evidence,
- recommendation.

### 5. Organize the application

Move the offer to Saved, Applied, Interview, Rejected, or Offer. Add notes and the next action.

### 6. Reminders and export

Export `.ics` to your calendar and Excel/CSV for your records.

---

## Data sources

| Source | Use | Required? |
|---|---|---|
| `practicas-pe` MCP | Search practicas.pe offers | No |
| Pasted text | Any portal | No |
| CSV/Excel | Bulk import | No |
| URL + JSON-LD | Single capture | No |
| Practilizate | Historical benchmarks | No |

**PractiCV does not depend on Practilizate or the MCP.** If they are unavailable, the app works with text, CSV, and URL.

---

## Explainable matching

For each requirement:

- `w`: weight (must-have = 3, nice-to-have = 1, unknown = 1.5).
- `r`: required level (1–3).
- `u`: user level (0–3).
- `coverage = min(u, r) / r`.

```text
overall_score = 100 * Σ(w * coverage) / Σ(w)
must_have_score = 100 * Σ(w * coverage must) / Σ(w must)
```

Decision:

- `must_have_score >= 85` and `overall >= 80`: **Apply**.
- `must_have_score >= 60`: **Apply with gaps**.
- Otherwise: **Prepare CV**.

The user can correct skills, levels, and the decision. The score is an **estimated fit**, not a hiring probability.

---

## Privacy

- Local-first: your CV and applications live on your machine.
- No telemetry by default.
- No PII in the repository.
- No secrets in Git.
- No mass scraping.
- No auto-apply.
- LLM is optional and consent-based.
- You can export and delete your data.

---

## Testing

- E2E-first.
- E2E as the main mechanism.
- No unit tests after writing code.
- Medium-hard scenario.
- Repeatable artifacts in `artifacts/e2e/`.

```powershell
pytest tests/e2e
```

Artifacts:

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

## Metrics

> Completed with E2E and dogfooding. No invented numbers.

| Metric | Value |
|---|---|
| Offers evaluated in dogfooding | `[pending]` |
| Median time to evaluate an offer | `[pending]` |
| Applications tracked | `[pending]` |
| Gaps discovered | `[pending]` |
| E2E runtime | `[pending]` |
| Critical flow coverage | `[pending]` |

---

## Limitations

- v0.1 is local-first and single-user.
- CV parsing may fail on complex formats; the user corrects it.
- URL capture is best effort; some portals block it.
- The MCP may be unavailable; manual fallback exists.
- The match is a guide, not a guarantee.
- No auto-apply.
- No mobile app.
- No multi-user support.

---

## Roadmap

- v0.1: profile, CV, capture, match, Kanban, reminders, and export.
- v0.2: bookmarklet, email alerts, Practilizate adapter, Power Automate, Power BI.
- v0.3: multiple CV versions and a public demo deploy.

See [ROADMAP.md](ROADMAP.md).

---

## License

MIT for the code. Third-party data keeps its own terms.

---

## Credits

- Offer source: [practicas.pe](https://www.practicas.pe/). PractiCV is not affiliated.
- Product inspiration: Practilizate, the Peruvian internship observatory.
- Built as a portfolio project for data/BI and software roles.
