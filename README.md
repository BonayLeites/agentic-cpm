# CPM Agent Accelerator

> A proof-of-concept multi-agent orchestration platform for Corporate Performance Management workflows.

---

## The Problem

Finance teams at mid-size to large companies spend days each month on manual close and performance reviews: loading trial balances from multiple entities, reconciling intercompany transactions, comparing actuals against budgets, and assembling narratives for different audiences. The work is repetitive, error-prone, and slow — even when the data is already in the system.

## What This Does

This PoC shows what CPM review workflows look like when orchestrated by a team of specialized AI agents. Two workflows are included:

| Workflow | What it reviews |
|---|---|
| **Consolidation Review** | Pre-close intercompany matching, anomaly detection, goodwill adjustments, multi-entity trial balances |
| **Performance Review** | Budget vs. actuals variance, gross margin decomposition, KPI breach detection, trend analysis |

Both workflows share the same orchestrator framework and produce structured findings, audit trails, and executive summaries — surfaced in a real-time frontend.

---

## Key Capabilities

### ⚡ Speed
Parallel agent execution surfaces findings in minutes. Steps 2 and 3 (IC matching + anomaly detection) run concurrently; subsequent agents build on their output. What took days of manual triage becomes a reviewable report at the end of a coffee break.

### 🔌 Extensibility
New workflows plug into the same orchestrator via a DAG configuration. New agents inherit `BaseAgent` and implement a single `execute()` method. The registry maps workflow types to ordered steps — add a step, change the order, or swap an agent without touching the orchestrator.

### 🔍 Traceability
Every tool call, LLM invocation, finding, and confidence score is persisted to the database. The Audit Trail screen exposes every step's inputs, outputs, duration, cost, and evidence chain. Nothing is a black box.

### ⚙️ Configurability
The orchestrator is model-agnostic. Business rules (materiality thresholds, breach percentages, DSO ceilings) live in a single source of truth and are passed to agents as configuration. Models can be swapped per agent independently.

---

## How It Works

```
POST /api/workflows/run
        │
   ┌────▼────┐
   │ Step 1  │  DataLoader          (loads all data into shared memory)
   └────┬────┘
        │
   ┌────▼────┬────────────┐
   │ Step 2  │  Step 3    │         (parallel)
   │ICChecker│AnomalyDet. │
   └────┬────┴──────┬─────┘
        └─────┬─────┘
         ┌────▼────┐
         │ Step 4  │  DocSearch     (reads step 2+3 findings, searches knowledge packs)
         └────┬────┘
         ┌────▼────┐
         │ Step 5  │  Analysis      (synthesizes all data into structured findings)
         └────┬────┘
         ┌────▼────┐
         │ Step 6  │  Narrative     (generates controller + executive summaries in parallel)
         └────┬────┘
         ┌────▼────┐
         │ Step 7  │  QualityGate   (reviews coherence, flags low-confidence items)
         └─────────┘
         SSE stream → frontend (real-time step events + heartbeat)
```

Agents downstream of Step 1 read all data from `AgentContext.memory` — the DataLoader is the single point of database access.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy async, Pydantic v2 |
| LLM | Azure AI Foundry — `gpt-4o` (reasoning), `gpt-4o-mini` (classification) |
| Document search | scikit-learn TF-IDF (no vector embeddings) |
| Database | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Recharts |
| Streaming | Server-Sent Events (SSE) with 20 s heartbeat |
| Infrastructure | Docker Compose (dev), Terraform modules for Azure (prod) |
| Tests | pytest + pytest-asyncio, 9 integration tests |
| CI/CD | GitHub Actions |

---

## The 5 Screens

1. **Home** — workflow selector (Consolidation Review / Performance Review)
2. **Workflow Run** — live timeline, activity log, and config side panel
3. **Findings** — collapsible cards with severity filter and confidence bars
4. **Executive Summary** — audience toggle (Controller / Executive)
5. **Audit Trail** — step table with expandable inputs, outputs, duration, and cost

The UI is fully internationalized (EN / ES / JA).

---

## Quick Start

**Prerequisites:** Docker, Docker Compose, Azure OpenAI credentials.

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — fill in AZURE_AI_ENDPOINT and AZURE_AI_API_KEY

# 2. Start all containers (backend, frontend, PostgreSQL)
make up

# 3. Seed the database with NikkoGroup demo data
make seed

# 4. Open the app
#    Frontend: http://localhost:3000
#    API docs:  http://localhost:8000/docs
```

---

## Environment Variables

Place in `backend/.env` (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:$POSTGRES_PASSWORD@db:5432/cpm` | PostgreSQL connection string |
| `AZURE_AI_ENDPOINT` | _(required)_ | Azure AI Foundry endpoint URL |
| `AZURE_AI_API_KEY` | _(required)_ | Azure AI API key |
| `AZURE_AI_DEPLOYMENT_GPT4O` | `gpt-4o` | GPT-4o deployment name |
| `AZURE_AI_DEPLOYMENT_MINI` | `gpt-4o-mini` | GPT-4o-mini deployment name |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins (JSON list) |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # 7+ agent implementations (data_loader, ic_checker, …)
│   │   ├── api/             # FastAPI routes + SSE + schemas
│   │   ├── core/            # Orchestrator, DAG, memory, event bus, tools
│   │   ├── db/              # SQLAlchemy models, session, seed data
│   │   └── llm/             # LLM gateway + system prompts
│   └── tests/               # Integration tests (pytest-asyncio)
├── frontend/
│   └── src/
│       ├── components/      # Shared UI components
│       ├── hooks/           # useSSE, useWorkflow
│       ├── pages/           # 5 screens
│       └── i18n/            # EN / ES / JA translations
├── infra/                   # Terraform modules (Azure network, DB, compute, AI)
├── docs/                    # SPEC.md, PLAYBOOK.md
├── Makefile
└── docker-compose.yml
```

---

## Running Tests & Linting

```bash
# Run all 9 integration tests (requires make up + local Python)
make test

# Lint + format check (ruff + mypy)
make lint

# TypeScript type check
cd frontend && npx tsc --noEmit
```

---

## Deployment

### Option 1: Docker Compose on a VPS (recommended)

Production-ready Docker Compose with nginx reverse proxy, gunicorn workers, and multi-stage frontend build:

```bash
cp .env.example .env
# Edit .env with real Azure AI credentials and a secure POSTGRES_PASSWORD

docker compose -f docker-compose.prod.yml up -d
# App available at http://your-server:80
```

Three services: PostgreSQL, backend (gunicorn + uvicorn workers), frontend (nginx serving static files + API reverse proxy). Everything runs under a single domain — no CORS needed.

### Option 2: Azure Cloud (Terraform)

Terraform modules under `infra/` provision enterprise-grade Azure infrastructure: VNet with private subnets, Azure Database for PostgreSQL Flexible Server, Container Apps for backend and frontend, and Azure AI Foundry with model deployments. See `infra/README.md` for usage.

---

## Demo Data

The seed script populates a fictional group company, **NikkoGroup**:

- **NKG-JP** — Japan parent entity (JPY)
- **NKG-US** — US subsidiary, 100% owned (USD)
- **NKG-SG** — Singapore subsidiary, 80% owned (SGD)

Seeded data includes trial balances, intercompany transactions (with one intentional cut-off mismatch), exchange rates, journal entries, budgets, KPIs, and 7 knowledge pack documents.
