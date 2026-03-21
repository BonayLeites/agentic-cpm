# CPM Agent Accelerator — Implementation Playbook

> This file guides Claude Code through implementation phase by phase.
> Each phase is a self-contained unit with: goal, tasks, and verification criteria.
> Do NOT skip phases. Complete verification before moving to next phase.
> Reference SPEC.md for details (read only the section you need, not the whole file).

---

## Phase 1: Project Skeleton

### Goal
Working dev environment: Docker Compose starts, backend serves health endpoint, frontend renders a blank page, database accepts connections.

### Tasks
1. Create repo structure:
   ```
   cpm-agent-accelerator/
     backend/
       app/__init__.py, main.py, config.py
       app/db/__init__.py, models.py, session.py
       app/api/__init__.py
       requirements.txt
       Dockerfile
     frontend/
       src/App.tsx, main.tsx
       index.html, package.json, vite.config.ts, tsconfig.json, tailwind.config.js
       Dockerfile
     docker-compose.yml
     .env.example
     Makefile
   ```
2. `docker-compose.yml`: PostgreSQL 16 + backend (FastAPI, port 8000) + frontend (Vite dev server, port 3000).
3. Backend `main.py`: FastAPI app with CORS (allow localhost:3000), single `GET /api/health` returning `{"status": "ok"}`.
4. Backend `config.py`: pydantic-settings loading from `.env` (DATABASE_URL, AZURE_AI_ENDPOINT, AZURE_AI_API_KEY, etc.).
5. Backend `models.py`: All SQLAlchemy models from SPEC.md Section 3 (entities, chart_of_accounts, trial_balances, journal_entries, journal_entry_lines, intercompany_transactions, exchange_rates, budgets, kpis, documents, workflow_runs, workflow_steps, findings). Use async engine.
6. Backend `session.py`: Async session factory. On startup, create all tables.
7. Frontend: Vite + React + TypeScript. TailwindCSS configured. Single `<App />` rendering "CPM Agent Accelerator" text.
8. `Makefile` with: `make up` (docker compose up), `make down`, `make seed`, `make logs`.

### Verification
Run these checks. ALL must pass before moving to Phase 2:
```bash
# 1. Containers start without errors
docker compose up -d && docker compose ps
# Expected: 3 containers running (db, backend, frontend)

# 2. Backend health endpoint responds
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}

# 3. Frontend loads
curl -s http://localhost:3000 | grep "CPM Agent Accelerator"
# Expected: match found

# 4. Database tables created
docker compose exec db psql -U postgres -d cpm -c "\dt"
# Expected: all tables listed (entities, trial_balances, etc.)
```

---

## Phase 2: Seed Data

### Goal
Database populated with all mock data for both cases. Verifiable by querying specific expected values.

### Tasks
1. Create `backend/app/db/seed/entities.py`: 3 entities (NKG-JP, NKG-US, NKG-SG) + chart of accounts (~18 accounts covering revenue, COGS, SGA, consulting fees, other OPEX, operating income, plus BS accounts for AR, AP, goodwill, equity).
2. Create `backend/app/db/seed/case1_data.py`: Read SPEC.md Section 4.1 for exact numbers.
   - Trial balances for 3 entities x 2 months (Jan + Feb 2026).
   - IC transactions (3 pairs, one with planted mismatch: NKG-JP invoice Jan 28, NKG-SG recorded Feb 2).
   - Exchange rates (USD/JPY, SGD/JPY, average + closing for Jan + Feb).
   - Journal entry JE-2026-0287 (goodwill adjustment JPY 12.8M).
3. Create `backend/app/db/seed/case2_data.py`: Read SPEC.md Section 4.2 for exact numbers.
   - Budgets for FY2026 by entity and account.
   - Actuals (trial balances) for Q1 2026.
   - KPIs: MRR, churn, NPS, utilization, DSO, headcount per entity.
4. Create `backend/app/db/seed/knowledge_packs/` with 7 markdown docs. Content should be realistic 1-2 paragraphs each. Read SPEC.md Sections 4.1 and 4.2 for titles and key content that agents need to find.
5. Create `backend/app/db/seed/seed_all.py`: Master seeder that drops and recreates all data. Called via `make seed`.
6. Add seed command to Makefile: `make seed` runs `docker compose exec backend python -m app.db.seed.seed_all`.

### Verification
```bash
# 1. Seed runs without errors
make seed

# 2. Entities exist
docker compose exec db psql -U postgres -d cpm -c "SELECT code, name, currency FROM entities;"
# Expected: NKG-JP (JPY), NKG-US (USD), NKG-SG (SGD)

# 3. IC mismatch is planted
docker compose exec db psql -U postgres -d cpm -c "
  SELECT from_entity_id, to_entity_id, amount, currency
  FROM intercompany_transactions
  WHERE period = '2026-02' AND mismatch_amount > 0;"
# Expected: 1 row (NKG-JP <> NKG-SG mismatch)

# 4. Case 2 KPIs exist
docker compose exec db psql -U postgres -d cpm -c "
  SELECT entity_id, kpi_name, kpi_value
  FROM kpis WHERE kpi_name = 'churn_rate' AND period = '2026-02';"
# Expected: NKG-US churn = 4.8

# 5. Knowledge pack documents loaded
docker compose exec db psql -U postgres -d cpm -c "SELECT title, doc_type FROM documents;"
# Expected: 7 documents
```

---

## Phase 3: API Endpoints (data-only, no agents yet)

### Goal
All read endpoints working. Frontend can fetch config, entities, and workflow history. No agent execution yet — just the data layer.

### Tasks
1. Create `backend/app/api/routes/health.py`: Already done in Phase 1.
2. Create `backend/app/api/routes/config_routes.py`:
   - `GET /api/config/{workflow_type}` — returns entities, dataset counts, business rules (hardcoded dict), knowledge pack titles, tool names. Read SPEC.md Section 2.4 for what each panel needs.
3. Create `backend/app/api/routes/data.py`:
   - `GET /api/data/entities` — entity tree.
   - `GET /api/data/stats` — dataset counts.
4. Create `backend/app/api/routes/workflows.py`:
   - `GET /api/workflows/latest?workflow_type={type}` — most recent completed run (returns null if none).
   - `GET /api/workflows/{run_id}` — full run with steps.
   - `POST /api/workflows/run` — placeholder that creates a run record and returns run_id (no actual agent execution yet).
5. Create `backend/app/api/routes/findings.py`:
   - `GET /api/findings?run_id={id}` — findings sorted by severity.
6. Create `backend/app/api/routes/summary.py`:
   - `GET /api/summary?run_id={id}&audience={mode}` — returns pre-stored summary text.
7. Create `backend/app/api/routes/audit.py`:
   - `GET /api/audit?run_id={id}` — full trace data.
8. Register all routers in `main.py`.
9. Create Pydantic response models for all endpoints in `backend/app/api/schemas.py`.

### Verification
```bash
# 1. Config endpoint returns data
curl http://localhost:8000/api/config/consolidation | python -m json.tool
# Expected: JSON with entities, rules, knowledge_packs, tools keys

# 2. Entity tree
curl http://localhost:8000/api/data/entities | python -m json.tool
# Expected: 3 entities with parent_id relationships

# 3. Workflow run creation
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "consolidation"}'
# Expected: {"run_id": 1, "status": "started"}

# 4. Findings endpoint (empty for now)
curl http://localhost:8000/api/findings?run_id=1
# Expected: [] (empty array, no agent has run yet)
```

---

## Phase 4: Frontend Shell (all 5 screens)

### Goal
All 5 pages render with layout, routing, and real data from the API. No agent execution yet — screens show structure with whatever data exists.

### Tasks
1. Create `frontend/src/types/index.ts`: All TypeScript interfaces from SPEC.md (Finding, Evidence, WorkflowRun, WorkflowStep, etc.).
2. Create `frontend/src/api/client.ts`: Fetch wrapper with base URL from env.
3. Create `frontend/src/components/Layout.tsx`: Sidebar + main content area.
4. Create `frontend/src/components/Sidebar.tsx`: Navigation links to all 5 pages. Active state highlighting.
5. Create all 5 pages as shells with real API calls:
   - `Home.tsx`: 2 WorkflowCard components. Link to Workflow Run. Source summary from `/api/data/stats`.
   - `WorkflowRun.tsx`: RunButton (disabled for now), WorkflowTimeline (empty), ActivityLog (empty). "View Config" button opens ConfigSidePanel. Read SPEC.md Section 2.4 for panel content.
   - `Findings.tsx`: SeverityFilter chips + FindingCard list from `/api/findings?run_id=X`. Shows EmptyState when no data.
   - `ExecutiveSummary.tsx`: AudienceToggle (controller/executive) + SummaryDocument from `/api/summary`. Shows EmptyState.
   - `AuditTrail.tsx`: TraceOverview + StepTable from `/api/audit`. Shows EmptyState.
6. Create shared components: `EmptyState.tsx`, `LoadingSkeleton.tsx`, `SeverityBadge.tsx`.
7. React Router: `/`, `/workflow-run`, `/findings`, `/summary`, `/audit`. Query params for `workflow` and `run`.

### Verification
Open browser at http://localhost:3000 and verify:
```
1. Home page shows 2 workflow cards with descriptions
2. Clicking "Select" navigates to /workflow-run?workflow=consolidation
3. Workflow Run page shows layout with empty timeline and "View Config" button
4. Config side panel opens and shows entities, rules, knowledge packs, tools
5. Findings page shows empty state message
6. Executive Summary page shows empty state message
7. Audit Trail page shows empty state message
8. Sidebar navigation works between all 5 pages
9. No console errors
```

---

## Phase 5: Core Agent Framework

### Goal
The orchestrator can execute a workflow: load agents from config, run them in DAG order (with parallel steps), stream SSE events, and store results. Tested with a minimal "echo" agent before wiring real logic.

### Tasks
1. Create `backend/app/core/agent_base.py`: BaseAgent, AgentContext, AgentResult, StepMetrics, Finding, Evidence classes. Read SPEC.md Section 3.2.
2. Create `backend/app/core/dag.py`: Simple DAG class. Takes a dict of step_name -> dependencies. Method `get_ready_steps(completed)` returns steps whose deps are satisfied. Method `has_pending(completed)` checks if work remains.
3. Create `backend/app/core/orchestrator.py`: WorkflowOrchestrator. Read SPEC.md Section 3.3 for the DAG execution loop with parallel steps, retries, and SSE emission.
4. Create `backend/app/core/agent_registry.py`: Maps workflow_type -> ordered list of (step_name, AgentClass, dependencies). Two registrations: "consolidation" and "performance".
5. Create `backend/app/core/rules_engine.py`: Load business rules from YAML/dict config. Method `check_threshold(value, rule_name) -> bool`.
6. Create `backend/app/core/confidence.py`: ConfidenceScorer from SPEC.md Section 3.7.
7. Create `backend/app/core/memory.py`: Simple dict wrapper for shared inter-agent data.
8. Create `backend/app/api/sse.py`: SSE event helper. Format events as `event: {type}\ndata: {json}\n\n`. Include heartbeat.
9. Wire `POST /api/workflows/run` to actually call the orchestrator (async background task).
10. Wire `GET /api/workflows/{run_id}/stream` to SSE endpoint.
11. Create a test echo agent that just sleeps 1s and returns an empty result. Register it as all 7 steps temporarily.
12. Test: trigger a workflow run and verify 7 SSE events arrive.

### Verification
```bash
# 1. Trigger a workflow run
RUN_ID=$(curl -s -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "consolidation"}' | python -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

# 2. Check SSE stream delivers events (wait for completion)
curl -N http://localhost:8000/api/workflows/${RUN_ID}/stream 2>&1 | head -50
# Expected: multiple "event: step_started" and "event: step_completed" events, ending with "event: run_completed"

# 3. Workflow run stored in DB
curl http://localhost:8000/api/workflows/${RUN_ID} | python -m json.tool
# Expected: run with status "completed", 7 steps listed

# 4. Steps 2 and 3 ran in parallel (check start times are within 1s of each other)
curl http://localhost:8000/api/audit?run_id=${RUN_ID} | python -m json.tool
# Expected: steps 2 and 3 have overlapping start times
```

---

## Phase 6: Tools

### Goal
All tools work independently and return correct data from the seeded database.

### Tasks
1. Create `backend/app/tools/base.py`: BaseTool interface.
2. Create `backend/app/tools/parameterized_queries.py`: All Type A tools (get_trial_balances, get_ic_transactions, get_budgets, get_kpis, get_exchange_rates). Each takes typed params, builds SQL from template, executes, returns rows. Read SPEC.md Section 3.5.
3. Create `backend/app/tools/ic_matching.py`: match_ic_pairs tool. Loads IC transactions for period, groups by entity pair, converts to common currency using exchange rates, calculates mismatch amounts and percentages.
4. Create `backend/app/tools/anomaly_detection.py`: detect_anomalies tool. Compares current period vs previous period for an entity. Calculates change %, flags items exceeding threshold. Simple statistical approach (MoM change > X%).
5. Create `backend/app/tools/document_search.py`: TF-IDF keyword search. On init, loads all documents from DB, builds TF-IDF index (scikit-learn TfidfVectorizer). Search returns top_k docs with relevance score and excerpt.

### Verification
```bash
# 1. IC matching finds the planted mismatch
docker compose exec backend python -c "
import asyncio
from app.tools.ic_matching import ICMatchingTool
from app.db.session import get_session
async def test():
    async with get_session() as db:
        tool = ICMatchingTool()
        result = await tool.execute({'period': '2026-02'}, db)
        print(f'Matched: {result[\"matched\"]}, Mismatched: {len(result[\"mismatched\"])}')
        for m in result['mismatched']:
            print(f'  {m[\"from_entity\"]} <> {m[\"to_entity\"]}: {m[\"amount_diff\"]}')
asyncio.run(test())
"
# Expected: Matched: 2 (or 22 if using 6-month data), Mismatched: 1 (NKG-JP <> NKG-SG)

# 2. Anomaly detection finds consulting fee spike
docker compose exec backend python -c "
import asyncio
from app.tools.anomaly_detection import AnomalyDetectionTool
from app.db.session import get_session
async def test():
    async with get_session() as db:
        tool = AnomalyDetectionTool()
        result = await tool.execute({
            'entity_code': 'NKG-US',
            'period': '2026-02',
            'comparison_period': '2026-01'
        }, db)
        for a in result['anomalies']:
            print(f'  {a[\"account\"]}: {a[\"change_pct\"]}%')
asyncio.run(test())
"
# Expected: consulting_fees shows +47% change

# 3. Document search finds IC policy
docker compose exec backend python -c "
import asyncio
from app.tools.document_search import DocumentSearchTool
from app.db.session import get_session
async def test():
    async with get_session() as db:
        tool = DocumentSearchTool()
        await tool.initialize(db)
        result = await tool.execute({'query': 'intercompany elimination policy threshold', 'top_k': 3})
        for d in result['documents']:
            print(f'  {d[\"title\"]} (score: {d[\"relevance_score\"]:.2f})')
asyncio.run(test())
"
# Expected: consolidation_policy.md ranked first with high score
```

---

## Phase 7: Case 1 Agents (Consolidation Review)

### Goal
Running workflow type "consolidation" produces 3 findings matching SPEC.md Section 4.1 expected outputs.

### Tasks
1. Create `backend/app/llm/gateway.py`: LLMGateway wrapping openai SDK for Azure AI Foundry. Methods: `complete(messages, tools, model, response_format, temperature)`. Read SPEC.md Section 3.6.
2. Create `backend/app/llm/prompts/consolidation.py`: System prompts for each Case 1 agent. These should instruct the LLM on its role, available data, and expected output format.
3. Create Case 1 agents in `backend/app/agents/`:
   - `data_loader.py`: Load trial balances + IC transactions + JEs for Feb 2026. Validate all 3 entities have data. Store in context.memory.
   - `ic_checker.py`: Call match_ic_pairs tool. Call search_documents for IC policy. Use LLM (gpt-4o) to analyze mismatch and generate finding.
   - `anomaly_detector.py`: Call detect_anomalies for each entity. Use LLM (gpt-4o-mini) to evaluate which anomalies exceed rules. Generate findings.
   - `doc_search.py`: For each issue found in steps 2-3, search knowledge packs. No LLM — pure tool call. Store excerpts in context.memory.
   - `analysis.py`: Receive all data from memory. Use LLM (gpt-4o, JSON mode) to synthesize into structured findings with evidence, questions, actions.
   - `narrative.py`: Use LLM (gpt-4o) to generate executive summary in both controller and executive mode. Store both in DB.
   - `quality_gate.py`: Use ConfidenceScorer on all findings. Flag any below 0.6. Use LLM (gpt-4o-mini) for final sanity check.
4. Register Case 1 agents in agent_registry.
5. Wire findings storage: orchestrator saves findings to DB after each agent step.
6. Wire summary storage: narrative agent saves summaries to DB.

### Verification
```bash
# 1. Run Case 1 workflow
RUN_ID=$(curl -s -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "consolidation"}' | python -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

# 2. Wait for completion (check status)
sleep 60 && curl http://localhost:8000/api/workflows/${RUN_ID} | python -c "
import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"]}, Steps: {len(d[\"steps\"])}')"
# Expected: Status: completed, Steps: 7

# 3. Check findings
curl http://localhost:8000/api/findings?run_id=${RUN_ID} | python -c "
import sys,json
findings = json.load(sys.stdin)
print(f'Total findings: {len(findings)}')
for f in findings:
    print(f'  [{f[\"severity\"].upper()}] {f[\"title\"]} (confidence: {f[\"confidence\"]})')
    print(f'    Evidence items: {len(f[\"evidence\"])}')
"
# Expected: 3 findings (1 high, 1 medium, 1 low), each with >=1 evidence item

# 4. Check summaries exist for both audiences
curl "http://localhost:8000/api/summary?run_id=${RUN_ID}&audience=controller" | python -c "
import sys,json; d=json.load(sys.stdin); print(f'Controller summary length: {len(d[\"summary\"])} chars')"
curl "http://localhost:8000/api/summary?run_id=${RUN_ID}&audience=executive" | python -c "
import sys,json; d=json.load(sys.stdin); print(f'Executive summary length: {len(d[\"summary\"])} chars')"
# Expected: Both >200 characters, different content

# 5. Audit trail has tool calls logged
curl http://localhost:8000/api/audit?run_id=${RUN_ID} | python -c "
import sys,json; d=json.load(sys.stdin)
for s in d['steps']:
    print(f'  Step {s[\"step_order\"]}: {s[\"agent_name\"]} | tools: {len(s.get(\"tools_used\", []))} | confidence: {s.get(\"confidence_score\", \"n/a\")}')"
# Expected: Each step has tools_used and confidence_score logged
```

---

## Phase 8: Frontend Wired to Real Data

### Goal
All 5 screens show real data from Case 1 runs. User can trigger a run, see timeline progress, browse findings, read summaries, and explore the audit trail.

### Tasks
1. Create `frontend/src/hooks/useSSE.ts`: Hook that connects to SSE endpoint, parses events, returns step updates. Auto-reconnect on disconnect.
2. Create `frontend/src/hooks/useWorkflow.ts`: State management for current workflow run. Fetches latest run on mount.
3. Wire `Home.tsx`: Stats from API. Clicking "Select" navigates with workflow type.
4. Wire `WorkflowRun.tsx`:
   - RunButton triggers POST /api/workflows/run, then connects SSE.
   - WorkflowTimeline renders steps with status badges (green/blue/gray/amber). Updates via SSE.
   - ActivityLog shows SSE messages as they arrive. Auto-scroll.
   - ConfigSidePanel fetches from /api/config.
   - On completion, show "View Findings" and "View Summary" buttons.
5. Wire `Findings.tsx`:
   - Fetch findings from API.
   - SeverityFilter: clickable chips that filter the list.
   - FindingCard: collapsed by default showing title + severity + impact + confidence. Expandable to full detail with evidence, questions, actions, confidence, escalation.
6. Wire `ExecutiveSummary.tsx`:
   - AudienceToggle switches between controller/executive.
   - Fetch summary from API with audience param.
   - Render summary with section headers (WHAT CHANGED, WHY IT MATTERS, RISKS, QUESTIONS, ACTIONS).
   - ConfidenceFooter with stats.
7. Wire `AuditTrail.tsx`:
   - TraceOverview cards (duration, steps, tool calls, confidence, cost).
   - StepTable with Stage names (Data validation, Intercompany review, etc.).
   - Expandable rows showing tool calls, LLM calls, inputs/outputs.

### Verification
Open browser at http://localhost:3000:
```
1. Home: 2 cards visible, stats show "3 entities | X months data | 7 knowledge docs"
2. Select Case 1 -> Workflow Run page
3. Click "Run AI Review" -> timeline starts updating (or load pre-baked run)
4. After completion, click "View Findings"
5. Findings: 3 cards visible. HIGH finding shows red badge. Click to expand -> evidence, questions, actions visible
6. Severity filter: clicking "High" shows only 1 finding
7. Navigate to Executive Summary: controller text visible
8. Toggle to Executive: text changes, blue accent -> green accent
9. Navigate to Audit Trail: overview cards show stats, step table has 7 rows
10. Click step 2 row: expanded detail shows tool calls with inputs/outputs
11. No console errors throughout
```

---

## Phase 9: Case 2 Agents (Performance Review)

### Goal
Running workflow type "performance" produces 4 findings matching SPEC.md Section 4.2.

### Tasks
1. Create `backend/app/llm/prompts/performance.py`: System prompts for Case 2 agents.
2. Create Case 2 specific agents:
   - `variance_analyzer.py`: Load actuals + budgets. Calculate variances. Decompose NKG-SG margin drop into price/mix (-2.1pts) and cost (-2.1pts) effects.
   - `kpi_analyzer.py`: Load KPIs. Compare to targets. Flag breaches (churn 4.8% > 2.5% target, DSO 58 > 50 target).
3. Reuse shared agents: data_loader, doc_search, analysis, narrative, quality_gate.
4. Register Case 2 agents in agent_registry with correct DAG (variance + kpi in parallel).
5. Verify all 4 findings produced with correct content.

### Verification
```bash
# 1. Run Case 2 workflow
RUN_ID=$(curl -s -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "performance"}' | python -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

# 2. Wait and check
sleep 60 && curl http://localhost:8000/api/findings?run_id=${RUN_ID} | python -c "
import sys,json
findings = json.load(sys.stdin)
print(f'Total findings: {len(findings)}')
for f in findings:
    print(f'  [{f[\"severity\"].upper()}] {f[\"title\"]}')"
# Expected: 4 findings (2 high, 1 medium, 1 low)

# 3. Check variance decomposition in findings
curl http://localhost:8000/api/findings?run_id=${RUN_ID} | python -c "
import sys,json
findings = json.load(sys.stdin)
margin_finding = [f for f in findings if 'margin' in f['title'].lower()][0]
print(margin_finding['description'][:300])"
# Expected: mentions price/mix effect and cost effect
```

Then verify in browser:
```
1. Home -> Select Case 2 -> Workflow Run -> run or load pre-baked
2. Findings: 4 cards. 2 HIGH (margin, cash), 1 MEDIUM (churn), 1 LOW (KPI disconnect)
3. Executive Summary: executive mode mentions pricing discipline and cash collection
4. Audit Trail: 7 steps, steps 2-3 parallel
```

---

## Phase 10: Pre-bake + Polish

### Goal
Two pre-baked runs ready for demo. Visual polish. Error states working. Demo rehearsal passes.

### Tasks
1. Run both workflows and note the run IDs. Update frontend to load latest completed run by default on each workflow page.
2. Add `GET /api/workflows/latest?workflow_type={type}` endpoint if not done.
3. Visual polish:
   - Loading skeletons on all data fetches.
   - Smooth transitions on finding card expand/collapse.
   - RunButton disabled state while running.
   - ActivityLog auto-scroll.
   - Proper color coding: red HIGH, amber MEDIUM, gray LOW.
   - Audience toggle visual difference (blue/green accent).
4. Error states:
   - API errors show friendly message, not stack trace.
   - SSE disconnect shows reconnecting indicator.
5. Run demo script from SPEC.md Section 5.1 end to end. Time it. Should be under 10 minutes.

### Verification
```
1. Open http://localhost:3000 fresh (no prior state)
2. Home shows 2 cards -> Select Case 1
3. Workflow Run loads pre-baked run immediately (no wait)
4. Navigate through: Findings -> Summary -> Audit Trail
5. Back to Home -> Select Case 2
6. Same flow with Case 2 data
7. Total time: under 10 minutes following the SPEC demo script
8. No console errors, no broken layouts, no empty screens
```

---

## Phase 11: Tests + CI (stretch)

### Goal
Must-have tests pass. GitHub Actions PR pipeline configured.

### Tasks
1. Create `backend/tests/conftest.py`: Test database fixture, mock LLM gateway.
2. Implement must-have tests from SPEC.md Section 3.8.
3. Create `.github/workflows/pr.yml`: ruff + mypy + pytest on backend, eslint + tsc on frontend.
4. Create Dockerfiles optimized for CI (multi-stage builds).

### Verification
```bash
# 1. Tests pass
cd backend && pytest tests/ -v
# Expected: all tests pass

# 2. Lint passes
cd backend && ruff check app/
cd frontend && npx eslint src/
# Expected: no errors
```

---

## Phase 12: Infrastructure (stretch)

### Goal
Terraform modules exist and are syntactically valid. Full deployment is a stretch goal.

### Tasks
1. Create `infra/modules/` with: network, database, compute, ai.
2. Create `infra/environments/staging/terraform.tfvars`.
3. Validate: `terraform init && terraform validate`.

### Verification
```bash
cd infra && terraform init && terraform validate
# Expected: "Success! The configuration is valid."
```

---

## Execution order summary

| Phase | What | Days | Critical? |
|---|---|---|---|
| 1 | Project skeleton | 0.5 | Yes |
| 2 | Seed data | 0.5 | Yes |
| 3 | API endpoints | 0.5 | Yes |
| 4 | Frontend shell | 1 | Yes |
| 5 | Core agent framework | 1 | Yes |
| 6 | Tools | 1 | Yes |
| 7 | Case 1 agents | 1.5 | Yes |
| 8 | Frontend wired | 1 | Yes |
| 9 | Case 2 agents | 1 | Yes |
| 10 | Pre-bake + polish | 1 | Yes |
| 11 | Tests + CI | 0.5 | Stretch |
| 12 | Infrastructure | 0.5 | Stretch |
| **Total** | | **~10 days** | |

