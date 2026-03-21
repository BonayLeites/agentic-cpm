# CPM Agent Accelerator — Product Spec

> Version: 3.0 (final — ready to build)
> Author: Bonay (EDISA)
> Date: 2026-03-20
> Purpose: Spec-driven development contract for demo implementation
> Changes from v1: Fixed IC anomaly (now cut-off timing, not FX), adjusted margins to tech-realistic, added NCI note, DAG orchestration with retries, parameterized queries, keyword search over RAG, concrete confidence scoring, renamed Trace to Audit Trail, collapsed Data Config into side panel, pre-baked workflow runs in demo script, added testing strategy, revised NFR to 90s.

---

## 0. Context & Goal

### What is this
A demo application for a Money Forward AI Solutions Engineer interview. It demonstrates a **configurable agentic AI accelerator** for Corporate Performance Management (CPM) workflows.

### What it must prove
1. I understand CPM domain deeply (consolidation, close, budgets, governance)
2. I can design reusable AI agent architectures, not one-shot scripts
3. I think in product terms, not just technology
4. I design software with production-minded concerns: observability, deployment reproducibility, CI/CD, and governance
5. My ERP and enterprise software background gives me relevant domain leverage for CPM-oriented AI workflows

### Core message
> "This is not a single AI agent. It is a configurable accelerator that adapts to different CPM workflows through configuration — not code changes."

### Why AI, not only rules
Rules detect threshold breaches and deterministic mismatches. AI adds:
- **Prioritization**: ranking findings by business impact, not just amount
- **Explanation**: decomposing a margin drop into price/mix and cost effects
- **Synthesis**: combining structured data with unstructured documents (controller notes, policies)
- **Audience adaptation**: translating the same findings into controller language vs executive language
- **Suggested actions**: proposing next steps based on context, not just flagging

By case: Consolidation (Case 1) uses AI for explanation + prioritization + doc grounding. Performance (Case 2) uses AI for hypothesis generation + KPI synthesis + executive narrative.

### Money Forward alignment
The demo aligns with Money Forward's CPM product areas:
- **Manageboard** → Performance review, budget/actual, KPI workflows (Case 2)
- **MF Cloud Consolidated Accounting** → Multi-entity close and IC review (Case 1)
- **Governance-oriented workflows** → Board prep, risk flags, decision support (Case 2)

---

## 1. Design Criteria

### 1.1 Product principles

| Principle | Meaning | How it manifests |
|---|---|---|
| **Accelerator, not framework** | It is a product that accelerates CPM workflows, not a developer toolkit | Home screen shows use-case selection, not code |
| **Configuration over code** | Different CPM workflows are enabled by swapping config, not rewriting | Rules, tools, knowledge packs are configurable per tenant |
| **Governed AI** | The AI operates with explicit rules, grounding, and audit trail | Every finding has evidence, every step is traced |
| **Audience-aware** | Outputs adapt to the consumer (controller vs executive) | Executive Summary has audience toggle |
| **Workflow-driven** | The user clicks "Run", agents execute a defined workflow, results appear | Guided multi-step workflow, not open-ended chat |
| **Observable** | Every agent step is traceable: inputs, outputs, tools, cost, confidence | Audit Trail with full telemetry |

### 1.2 Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | User can select between 2 workflow types from Home | Must |
| FR-02 | User can peek at data sources, rules, and knowledge packs via side panel | Must |
| FR-03 | User can trigger a workflow run and see real-time execution progress | Should |
| FR-04 | System executes a DAG-based multi-step agent workflow | Must |
| FR-05 | Each workflow produces prioritized findings with evidence | Must |
| FR-06 | System generates an executive summary from findings | Must |
| FR-07 | Executive summary supports 2 audience modes (controller/executive) | Must |
| FR-08 | User can view full audit trail of any workflow run | Must |
| FR-09 | System uses keyword search over knowledge packs for document grounding | Must |
| FR-10 | System applies business rules (materiality thresholds, tolerances) | Must |
| FR-11 | Findings include suggested questions and actions | Should |
| FR-12 | Workflow steps can escalate to human review on low confidence | Should |
| FR-13 | System tracks and displays estimated cost per run | Nice |
| FR-14 | Steps that fail are retried with backoff; partial results are preserved | Should |

### 1.3 Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Full workflow run completes in under 90 seconds |
| NFR-02 | Frontend streams execution progress via SSE with heartbeat |
| NFR-03 | Backend is stateless (all state in PostgreSQL) |
| NFR-04 | Deployable to Azure via Terraform |
| NFR-05 | CI/CD via GitHub Actions (lint, test, build, deploy) |
| NFR-06 | Docker Compose for local development |
| NFR-07 | Python 3.12+, Node 20+, PostgreSQL 16+ |

### 1.4 Tech stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | TailwindCSS for styling, Recharts for charts |
| Backend | FastAPI + Python 3.12 | SQLAlchemy ORM, Pydantic models |
| Database | PostgreSQL 16 | Financial data + agent state. Faster dev, better JSON support, strong enterprise credibility |
| LLM | Azure AI Foundry (OpenAI GPT-4o + GPT-4o-mini) | Via openai SDK pointing to Azure endpoint |
| Document search | Keyword-based (TF-IDF) | In-memory over knowledge packs. Upgradeable to Chroma if needed |
| IaC | Terraform | Azure Container Apps + PostgreSQL Flexible Server |
| CI/CD | GitHub Actions | PR checks + deploy pipelines |
| Containers | Docker + Docker Compose | Local dev and prod deployment |

### 1.5 Model selection per agent step (initial routing for demo)

| Step | Model | Rationale |
|---|---|---|
| Data loading & validation | gpt-4o-mini | Simple validation, low complexity |
| IC check | gpt-4o | Domain-specific financial reasoning |
| Anomaly detection | gpt-4o-mini | Statistical, less language nuance needed |
| Document retrieval | No LLM | Pure keyword search tool |
| Analysis (finding synthesis) | gpt-4o | Critical reasoning, JSON structured output |
| Narrative generation | gpt-4o | Quality of language matters |
| Quality gate | gpt-4o-mini | Simple pass/fail evaluation |

Estimated cost per run with this split: ~$0.08-0.15 (vs ~$0.40 with gpt-4o everywhere).
Estimated latency: ~45-60s (with steps 2-3 parallel).

### 1.6 Mock company: NikkoGroup

| Entity | Code | Country | Currency | Role | Ownership |
|---|---|---|---|---|---|
| NikkoGroup Japan | NKG-JP | Japan | JPY | Parent / HQ | — |
| NikkoGroup US | NKG-US | United States | USD | Subsidiary (Americas) | 100% |
| NikkoGroup Singapore | NKG-SG | Singapore | SGD | Subsidiary (APAC) | 80% |

NKG-SG is 80% owned — this enables minority interest (NCI) calculation in consolidation, showing the demo handles real group accounting, not just simple aggregation.

Industry: Technology services group (consulting + SaaS + cloud infrastructure).

**Domain simplifications acknowledged** (mention if asked):
- Unified chart of accounts for demo. In production, local COAs would map to a group COA via GL bridge tables.
- Materiality set as fixed JPY amount. In production, calculated dynamically as % of revenue or equity per entity.
- No tax consolidation or transfer pricing. Noted as future agent scope.

---

## 2. Frontend Spec — Screens, UX, UI

### 2.1 Design system

- **Framework**: TailwindCSS utility classes
- **Color palette**: Neutral grays for chrome. Blue (#2563EB) primary actions. Red for high severity. Amber for medium / warnings. Gray-400 for low severity. Green for completed states.
- **Typography**: Inter (or system sans-serif). 14px base, 12px secondary.
- **Layout**: Fixed left sidebar (nav) + main content area. Max-width 1280px centered.
- **Cards**: White bg, border-gray-200, rounded-lg, shadow-sm. Collapsed by default where noted.
- **Tables**: Compact, zebra-striped, sticky headers. Horizontally scrollable if >5 columns.
- **Status badges**: Colored pills — green (completed), blue (running), gray (queued), amber (escalated), red (failed).
- **States**: Every screen must handle: loading (skeleton), empty (no data), error, and populated states.

### 2.2 Navigation (Left sidebar)

```
[Logo: CPM Accelerator]

  Home
  Workflow Run
  Findings
  Executive Summary
  Audit Trail

[Footer: NikkoGroup | v1.0]
```

Note: Data & Config is NOT a separate page. It is a slide-out panel accessible from Workflow Run via a "View Config" button.

---

### 2.3 Screen 1: Home

**Route**: `/`

**Purpose**: Select a workflow. This is the product screen.

**Layout**:
```
+------------------------------------------------------------------+
| CPM Agent Accelerator                                [NikkoGroup] |
+------------------------------------------------------------------+
|                                                                    |
|  Select a workflow                                                 |
|                                                                    |
|  +----------------------------+  +----------------------------+   |
|  | CASE 1                     |  | CASE 2                     |   |
|  | Pre-Close &                |  | Executive Performance      |   |
|  | Consolidation Review       |  | Review                     |   |
|  |                            |  |                            |   |
|  | Automates pre-close review:|  | Transforms performance     |   |
|  | IC reconciliation, anomaly |  | data into decision support:|   |
|  | detection, exception       |  | variance analysis, KPI     |   |
|  | prioritization.            |  | synthesis, risk flags,     |   |
|  |                            |  | board-ready materials.     |   |
|  | Audience: Controller       |  | Audience: CFO / ExCo       |   |
|  |                            |  |                            |   |
|  |  [Select ->]               |  |  [Select ->]               |   |
|  +----------------------------+  +----------------------------+   |
|                                                                    |
|  3 entities | 6 months data | 4 knowledge docs                   |
|                                                                    |
+------------------------------------------------------------------+
```

**Behavior**: "Select" navigates to `/workflow-run?workflow=consolidation` or `performance`.

**Components**: `WorkflowCard`, `SourcesSummary`

---

### 2.4 Screen 2: Workflow Run

**Route**: `/workflow-run?workflow={type}`

**Purpose**: Execute the agent workflow and show progress. The "magic" screen.

**Layout**:

```
+------------------------------------------------------------------+
| Workflow Run                           [View Config]  [History v] |
+------------------------------------------------------------------+
|                                                                    |
|  +--------------------------------------------------------------+ |
|  |            >> RUN AI REVIEW <<                                | |
|  |   (full-width primary button, prominent)                      | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  Status: Completed (7/7)                          Total: 47.2s   |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  | WORKFLOW TIMELINE                                             | |
|  |                                                               | |
|  |  [ok] 1. Data validation              12.3s                   | |
|  |  [ok] 2. Intercompany review            8.7s   ┐ parallel    | |
|  |  [ok] 3. Anomaly scan                   9.1s   ┘              | |
|  |  [ok] 4. Document grounding             3.2s                   | |
|  |  [ok] 5. Findings synthesis             6.4s                   | |
|  |  [ok] 6. Summary generation             5.8s                   | |
|  |  [ok] 7. Quality gate                   1.7s                   | |
|  |                                                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|  +--------------------------------------------------------------+ |
|  | ACTIVITY LOG (scrollable)                                     | |
|  |                                                               | |
|  | 14:32:15  IC review: Matched 22/24 IC transactions             | |
|  | 14:32:16  IC review: MISMATCH — NKG-JP <> NKG-SG              | |
|  |           Cut-off timing: invoice dates differ by 5 days       | |
|  | 14:32:18  IC review: Tool: intercompany_check (2.1s)           | |
|  | 14:32:20  IC review: Step completed. 1 finding.                | |
|  | 14:32:21  Anomaly scan: Starting...                            | |
|  | 14:32:22  Anomaly scan: Tool: get_trial_balance                | |
|  |           Query: NKG-US, period=2026-02, account=consulting    | |
|  |                                                               | |
|  +--------------------------------------------------------------+ |
|                                                                    |
|               [View Findings ->]  [View Summary ->]               |
+------------------------------------------------------------------+
```

**"View Config" side panel** (slides from right, 400px wide):
Shows 4 sections: Connected Data (entity tree, dataset counts), Knowledge Packs (doc titles), Business Rules (key-value list), Enabled Tools (tool name + description). Read-only.

**Workflow DAG** (not linear):
Steps 2 and 3 run in parallel (both depend only on step 1). Step 4 depends on steps 2 AND 3. Rest is sequential.

```
Step 1 (Load) ──> Step 2 (IC Check) ──┐
                                        ├──> Step 4 (Docs) -> Step 5 (Analysis) -> Step 6 (Narrative) -> Step 7 (QA)
                 ──> Step 3 (Anomaly) ──┘
```

**SSE events**: `step_started`, `step_completed`, `step_escalated`, `step_failed`, `run_completed`, `heartbeat` (every 20s).

```json
{
  "event": "step_completed",
  "data": {
    "step_id": 2,
    "agent_name": "ic_checker",
    "status": "completed",
    "message": "Matched 22/24 IC transactions. 1 mismatch found.",
    "duration_ms": 8700,
    "finding_count": 1,
    "confidence": 0.91
  }
}
```

**Error/escalation states on timeline**:
- Failed step: red badge + error message. Workflow continues with degraded data if possible.
- Escalated step: amber badge + "Manual review needed" + reason.

**Demo note**: For live demo, pre-bake one completed run per case. Show completed timeline immediately, then navigate to Findings. Avoids 50s wait during presentation.

**Components**: `RunButton` (full-width), `WorkflowTimeline`, `ActivityLog`, `ConfigSidePanel`

---

### 2.5 Screen 3: Findings

**Route**: `/findings?run={id}`

**Purpose**: Show what the AI found, with evidence and actions. The "value" screen.

**Layout**:
```
+------------------------------------------------------------------+
| Findings                                  Run #12 | Consolidation |
+------------------------------------------------------------------+
|                                                                    |
| [All (3)] [* High (1)] [* Medium (1)] [* Low (1)]   Filter chips |
|                                                                    |
| +--------------------------------------------------------------+ |
| | [HIGH] IC timing mismatch: NKG-JP <> NKG-SG           [Open] | |
| | JPY 3.3M | 91% confidence | Evidence: 4 | Action: Confirm dates| |
| | [Expand v]                                                     | |
| +--------------------------------------------------------------+ |
|                                                                    |
| +--------------------------------------------------------------+ |
| | [MED] Unusual OPEX: NKG-US consulting fees +47%       [Open] | |
| | USD 92K | 85% confidence | Evidence: 3 | Action: Document spend | |
| | [Expand v]                                                     | |
| +--------------------------------------------------------------+ |
|                                                                    |
| +--------------------------------------------------------------+ |
| | [LOW] Manual adjustment above threshold: JPY 12.8M    [Open] | |
| | JPY 12.8M | 82% confidence | Evidence: 2 | Action: Enhance doc | |
| | [Expand v]                                                     | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

**Collapsed state** (default): Title + severity badge + one-line summary + impact + evidence count + primary action. Fits 3-4 findings on screen without scrolling.

**Expanded state** (on click): Full description, evidence list, suggested questions, suggested actions.

```
+--------------------------------------------------------------+
| [HIGH] IC timing mismatch: NKG-JP <> NKG-SG        [Collapse] |
|                                                                |
| NKG-JP recorded an intercompany receivable of JPY 45.2M on    |
| Jan 28 (invoice NKG-2026-0412). NKG-SG recorded the           |
| corresponding payable of SGD 395K on Feb 2, after their        |
| local month-end close. At Feb closing rate (SGD/JPY 115.3),    |
| the SGD amount = JPY 45.5M. The core mismatch of JPY 3.3M     |
| is driven by cut-off timing (5-day gap), not FX.               |
|                                                                |
| This exceeds the 2% IC tolerance threshold and must be         |
| resolved before consolidated close sign-off.                   |
|                                                                |
| Entity: NKG-SG              Impact: JPY 3.3M                  |
| Rule triggered: IC mismatch tolerance > 2%                     |
|                                                                |
| EVIDENCE                                                       |
|  [data] NKG-JP AR: JPY 45.2M (invoice Jan 28)                 |
|  [data] NKG-SG AP: SGD 395K (recorded Feb 2)                  |
|  [doc]  consolidation_policy.md S4.2: "IC differences > 2%     |
|         require reconciliation before close sign-off"          |
|  [doc]  close_notes_feb_2026.md: "Singapore team delayed       |
|         in submitting final AR confirmation"                    |
|                                                                |
| SUGGESTED QUESTIONS                                            |
|  - Was the SGD 395K payable accrued in January or February?    |
|  - Has NKG-SG confirmed the correct invoice date?              |
|                                                                |
| SUGGESTED ACTIONS                                              |
|  1. Request NKG-SG to re-date the payable to January           |
|  2. If timing confirmed, post consolidation adjustment          |
|  3. Document cut-off procedure for future months               |
|                                                                |
| CONFIDENCE: 91%  |  ESCALATION: none                           |
+--------------------------------------------------------------+
```

**Finding data model**:
```typescript
interface Finding {
  id: number;
  severity: "high" | "medium" | "low";
  status: "open" | "needs_review" | "in_progress" | "resolved";  // actionable workflow state
  title: string;
  description: string;
  entity_code: string | null;
  impact_amount: number | null;
  impact_currency: string;
  rule_triggered: string | null;
  evidence: Evidence[];
  suggested_questions: string[];
  suggested_actions: string[];
  confidence: number;
  escalation_reason: string | null;  // e.g. "Low evidence coverage", "Missing entity data"
}

interface Evidence {
  type: "data_point" | "document_excerpt" | "rule_reference";
  label: string;
  value: string;
  source: string;
  relevance_score?: number;       // used by confidence scorer for document_excerpt type
}
```

**Components**: `FindingCard` (collapsible), `SeverityBadge`, `SeverityFilter`, `EvidenceItem`

---

### 2.6 Screen 4: Executive Summary

**Route**: `/summary?run={id}`

**Purpose**: AI-generated narrative adapted to audience. The "decision support" screen.

**Layout**:
```
+------------------------------------------------------------------+
| Executive Summary                                                  |
+------------------------------------------------------------------+
|                                                                    |
| Audience: [Controller (blue)]  [Executive (green)]  Run #12      |
|           Operational review    Decision support                  |
|                                                                    |
| +--------------------------------------------------------------+ |
| |                                                               | |
| | CONSOLIDATION REVIEW — FEBRUARY 2026                          | |
| |                                                               | |
| | >> WHAT CHANGED                                               | |
| | Two consolidation issues require attention before close       | |
| | sign-off. An intercompany timing difference between Japan     | |
| | and Singapore is the highest priority. US operating expenses  | |
| | show an unusual increase in consulting fees.                  | |
| |                                                               | |
| | !! WHY IT MATTERS                                             | |
| | The IC mismatch of JPY 3.3M exceeds policy threshold and     | |
| | would create a material error in consolidated statements if   | |
| | not resolved. The OPEX movement lacks supporting docs, which  | |
| | is a compliance gap for the US entity close.                  | |
| |                                                               | |
| | /!\ RISKS                                                     | |
| | - Close delay if Singapore does not confirm payable date by   | |
| |   March 3                                                     | |
| | - NCI impact: 20% minority share in NKG-SG affected          | |
| | - Audit finding on undocumented US consulting spend           | |
| |                                                               | |
| | ? QUESTIONS TO ASK                                            | |
| | - Has NKG-SG confirmed the invoice receipt date?              | |
| | - What is the nature of the USD 92K consulting engagement?    | |
| | - Is the goodwill adjustment recurring or one-time?           | |
| |                                                               | |
| | -> RECOMMENDED ACTIONS                                        | |
| | 1. Request NKG-SG payable date confirmation (deadline Mar 3)  | |
| | 2. Request NKG-US controller to document consulting fees      | |
| | 3. Approve goodwill adjustment with enhanced supporting note  | |
| |                                                               | |
| +--------------------------------------------------------------+ |
|                                                                    |
| +--------------------------------------------------------------+ |
| | Generated by CPM Agent Accelerator                            | |
| | Confidence: 87% | 7 steps | 14 tool calls | ~$0.12           | |
| | [View Audit Trail]                                            | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

**Audience toggle behavior**:

**Controller mode** (blue accent):
- Accounting terminology used freely (accounts, journal entries, reconciliation)
- References specific entries, thresholds, and compliance steps
- More operational detail: what to fix, where, and how
- Mentions NCI impact, audit trail references

**Executive mode** (green accent):
- Business impact first, always
- No journal entry or account code references unless material
- Fewer details, more decision framing
- Language: "revenue pressure" not "variance in account 4100"

Both versions are pre-generated by the NarrativeAgent (2 LLM calls). Frontend fetches via `GET /api/summary?run_id={id}&audience={mode}`. No on-demand LLM calls on toggle.

**Summary structure** (same for both cases):
1. What changed
2. Why it matters
3. Risks
4. Questions to ask
5. Recommended actions

**Components**: `AudienceToggle`, `SummaryDocument` (section-based with visual icons), `ConfidenceFooter`

---

### 2.7 Screen 5: Audit Trail

**Route**: `/audit?run={id}`

**Purpose**: Full observability. Communicates enterprise readiness and governance. Framed as audit/governance, not developer debugging.

**Layout**:
```
+------------------------------------------------------------------+
| Audit Trail                              Run #12 | 47.2s total   |
+------------------------------------------------------------------+
|                                                                    |
| +--------------------------------------------------------------+ |
| | EXECUTION OVERVIEW                                            | |
| |                                                               | |
| | Duration: 47.2s  |  Steps: 7  |  Tool calls: 14              | |
| | Findings: 3      |  Avg confidence: 87%  |  Cost: ~$0.12     | |
| | All evidence from auditable sources. No ungrounded claims.    | |
| +--------------------------------------------------------------+ |
|                                                                    |
| +--------------------------------------------------------------+ |
| | STEP DETAILS (click to expand)                                | |
| |                                                               | |
| | Step | Stage                | Duration | Confidence | Status    | |
| |------|----------------------|----------|------------|-----------|  |
| |  1   | Data validation      |   12.3s  |    95%     | completed | |
| |  2   | Intercompany review  |    8.7s  |    91%     | completed | |
| |  3   | Anomaly scan         |    9.1s  |    82%     | completed | |
| |  4   | Document grounding   |    3.2s  |    89%     | completed | |
| |  5   | Findings synthesis   |    6.4s  |    85%     | completed | |
| |  6   | Summary generation   |    5.8s  |    88%     | completed | |
| |  7   | Quality gate         |    1.7s  |    87%     | completed | |
| +--------------------------------------------------------------+ |
|                                                                    |
| +--------------------------------------------------------------+ |
| | STEP 2 DETAIL (expanded)                                      | |
| |                                                               | |
| | Stage: Intercompany review                                    | |
| |                                                               | |
| | Tools executed:                                               | |
| |   1. get_ic_transactions (1.8s)                               | |
| |      Query: period=2026-02                                    | |
| |      Result: 24 transactions loaded                           | |
| |      Source: intercompany_transactions table                  | |
| |                                                               | |
| |   2. match_ic_pairs (3.4s)                                    | |
| |      Input: Match AR/AP pairs across 3 entities               | |
| |      Result: 22/24 matched, 1 mismatch (NKG-JP<>NKG-SG),    | |
| |              1 partial (below tolerance)                      | |
| |      Evidence: invoice dates, amounts, rates                  | |
| |                                                               | |
| |   3. search_documents (1.8s)                                  | |
| |      Query: "intercompany elimination policy threshold"       | |
| |      Result: consolidation_policy.md S4.2 (score: 0.94)      | |
| |                                                               | |
| | LLM calls:                                                    | |
| |   1. Analyze IC results (gpt-4o, 2.1K tokens, 1.9s)         | |
| |   2. Generate finding (gpt-4o, 2.4K tokens, 2.3s)           | |
| |                                                               | |
| | Decision: 1 finding (HIGH severity)                           | |
| | Confidence: 91%                                               | |
| |   Why: IC amounts explicit, policy threshold documented,      | |
| |   cut-off timing gap confirmed in controller notes            | |
| |                                                               | |
| | Possible escalation reasons (shown when confidence < 0.7):   | |
| |   - Low evidence coverage                                     | |
| |   - Missing entity data                                       | |
| |   - Conflicting document context                              | |
| |   - Weak rule match                                           | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

**Key design choices**:
- Framed as "Audit Trail" not "Trace" — governance language, not debugging.
- Main table shows only 5 columns (Step, Agent, Duration, Confidence, Status). Token counts and cost moved to expanded detail.
- Expanded detail emphasizes **data lineage** (source tables, document references) and **decision rationale** (why this confidence score).
- "All evidence from auditable sources" statement at top.

**Components**: `TraceOverview`, `StepTable` (expandable rows), `StepDetail`, `ConfidenceExplanation`

---

## 3. Backend Spec

### 3.1 API Endpoints

```
POST   /api/workflows/run
       Body: { workflow_type: "consolidation" | "performance" }
       Response: { run_id: number, status: "started" }

GET    /api/workflows/{run_id}/stream
       SSE stream. Events: step_started, step_completed, step_escalated,
       step_failed, run_completed, heartbeat (every 20s)
       Headers: Cache-Control: no-cache, X-Accel-Buffering: no

GET    /api/workflows/{run_id}
       Response: Full workflow run with steps summary

GET    /api/workflows/latest?workflow_type={type}
       Response: Most recent completed run (for pre-baked demo)

GET    /api/findings?run_id={id}
       Response: Array of findings sorted by severity

GET    /api/summary?run_id={id}&audience={controller|executive}
       Response: Pre-generated executive summary for given audience

GET    /api/audit?run_id={id}
       Response: Full audit trail (steps, tool calls, LLM calls, metrics)

GET    /api/config/{workflow_type}
       Response: Data sources, rules, knowledge packs, tools

GET    /api/health
       Response: { status: "ok", version: "1.0.0" }
```

### 3.2 Agent Architecture

**Base classes**:
```python
class BaseAgent(ABC):
    name: str
    description: str
    model: str                          # "gpt-4o" or "gpt-4o-mini"

    async def execute(self, context: AgentContext) -> AgentResult:
        pass

class AgentContext:
    run_id: int
    workflow_type: str
    config: WorkflowConfig              # rules, thresholds
    db: AsyncSession
    llm: LLMGateway
    doc_search: DocumentSearch           # keyword search
    memory: dict                         # shared key-value for inter-agent data
    tracer: Tracer

class AgentResult:
    status: Literal["completed", "escalated", "failed"]
    findings: list[Finding]
    data: dict                           # data for subsequent agents
    metrics: StepMetrics
```

### 3.3 Workflow Orchestrator — DAG-based with retries

```python
class WorkflowOrchestrator:
    async def run(self, workflow_type: str) -> int:
        config = load_workflow_config(workflow_type)
        dag = load_workflow_dag(workflow_type)
        context = AgentContext(...)
        run = create_run(workflow_type)

        completed = set()

        while dag.has_pending_steps(completed):
            # Get all steps whose dependencies are satisfied
            ready = dag.get_ready_steps(completed)

            # Run ready steps in parallel
            tasks = [
                self._run_step_with_retry(step, context)
                for step in ready
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, result in zip(ready, results):
                if isinstance(result, Exception):
                    emit_sse("step_failed", step, str(result))
                    # Mark as failed but continue with degraded data
                    completed.add(step.name)
                else:
                    context.memory.update(result.data)
                    save_findings(result.findings)
                    completed.add(step.name)

        # NarrativeAgent generates both audience modes
        # QualityGate checks all findings

        emit_sse("run_completed", run)
        return run.id

    async def _run_step_with_retry(self, step, context, max_retries=2):
        for attempt in range(max_retries + 1):
            try:
                emit_sse("step_started", step)
                result = await asyncio.wait_for(
                    step.agent.execute(context),
                    timeout=30  # per-step timeout
                )
                emit_sse("step_completed", step, result.metrics)
                return result
            except (TimeoutError, LLMError) as e:
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                    continue
                raise
```

**Workflow DAGs**:

**Case 1 — Consolidation Review**:
```
load_data ──> ic_checker ──────┐
           ──> anomaly_detect ──┤──> doc_search -> analysis -> narrative -> quality_gate
```

**Case 2 — Performance Review**:
```
load_data ──> variance_analyzer ──┐
           ──> kpi_analyzer ──────┤──> doc_search -> analysis -> narrative -> quality_gate
```

### 3.4 Agent Definitions

**Case 1 — Consolidation Review**:

| Step | Agent | What it does | Tools | Model |
|---|---|---|---|---|
| 1 | `DataLoaderAgent` | Load trial balances, JEs, IC txns for period. Validate completeness. | `get_trial_balances`, `get_ic_transactions` | gpt-4o-mini |
| 2 | `ICCheckAgent` | Match IC transactions across entities. Flag mismatches above tolerance. | `get_ic_transactions`, `match_ic_pairs`, `search_documents` | gpt-4o |
| 3 | `AnomalyDetectorAgent` | Statistical scan: MoM changes, unusual balances, threshold breaches. | `get_trial_balances`, `detect_anomalies` | gpt-4o-mini |
| 4 | `DocSearchAgent` | For each issue found in steps 2-3, search knowledge packs for context. | `search_documents` | No LLM |
| 5 | `AnalysisAgent` | Synthesize data + anomalies + docs into structured findings (JSON). | LLM only | gpt-4o |
| 6 | `NarrativeAgent` | Generate executive summary in both audience modes. | LLM only | gpt-4o |
| 7 | `QualityGateAgent` | Check confidence scores. Flag findings <0.6 for review. | LLM only | gpt-4o-mini |

**Case 2 — Performance Review**:

| Step | Agent | What it does | Tools | Model |
|---|---|---|---|---|
| 1 | `DataLoaderAgent` | Load actuals, budgets, KPIs for period. | `get_trial_balances`, `get_budgets`, `get_kpis` | gpt-4o-mini |
| 2 | `VarianceAnalyzerAgent` | Calculate actual vs budget variances. Decompose into volume, price/mix, and cost drivers. | `get_trial_balances`, `get_budgets`, `detect_anomalies` | gpt-4o |
| 3 | `KPIAnalysisAgent` | Analyze KPI trends, targets, anomalies. Cross-reference with financials. | `get_kpis`, `detect_anomalies` | gpt-4o-mini |
| 4 | `DocSearchAgent` | Search FP&A commentary, board agenda, mgmt notes. | `search_documents` | No LLM |
| 5 | `AnalysisAgent` | Synthesize into structured findings. | LLM only | gpt-4o |
| 6 | `NarrativeAgent` | Generate summary with discussion points, risk assessment, actions. | LLM only | gpt-4o |
| 7 | `QualityGateAgent` | Confidence check. | LLM only | gpt-4o-mini |

### 3.5 Tools Spec

Tools are callable functions with typed input/output. Two types:

**Type A — Parameterized queries (deterministic, no LLM)**:
```python
PARAMETERIZED_QUERIES = {
    "get_trial_balances": {
        "sql": "SELECT * FROM trial_balances WHERE entity_id IN ({entity_ids}) AND period = {period}",
        "params": ["entity_ids: list[int]", "period: str"]
    },
    "get_ic_transactions": {
        "sql": "SELECT * FROM intercompany_transactions WHERE period = {period}",
        "params": ["period: str"]
    },
    "get_budgets": {
        "sql": "SELECT * FROM budgets WHERE entity_id IN ({entity_ids}) AND period = {period}",
        "params": ["entity_ids: list[int]", "period: str"]
    },
    "get_kpis": {
        "sql": "SELECT * FROM kpis WHERE entity_id IN ({entity_ids}) AND period = {period}",
        "params": ["entity_ids: list[int]", "period: str"]
    },
    "get_exchange_rates": {
        "sql": "SELECT * FROM exchange_rates WHERE rate_date BETWEEN {start} AND {end}",
        "params": ["start: date", "end: date"]
    }
}
```

**Type B — Logic tools (deterministic computation)**:
```python
# match_ic_pairs: Match AR/AP across entities, apply FX conversion, calculate mismatch
# Input: { period: str }
# Output: { matched: int, mismatched: list[{from_entity, to_entity, amount_diff, pct_diff}], total: int }

# detect_anomalies: Statistical MoM comparison + threshold check
# Input: { entity_code: str, period: str, comparison_period: str }
# Output: { anomalies: list[{account, current, previous, change_pct, z_score, threshold_breached: bool}] }
```

**Type C — Document search (keyword-based, no LLM)**:
```python
# search_documents: TF-IDF keyword search over knowledge pack documents
# Input: { query: str, top_k: int = 3 }
# Output: { documents: list[{title, excerpt (2-3 sentences), relevance_score}] }
#
# Implementation: Load docs on startup, compute TF-IDF index.
# Extract relevant excerpt: find paragraph with highest keyword overlap.
# Upgradeable to Chroma vector store later if needed.
```

**No NL2SQL tool.** All data queries are parameterized templates. The LLM decides WHICH template to call (via function calling), not WHAT SQL to write. This eliminates hallucination risk on queries.

### 3.6 LLM Gateway

```python
class LLMGateway:
    async def complete(
        self,
        messages: list,
        tools: list = None,         # function calling schemas
        model: str = "gpt-4o",
        response_format: dict = None,  # {"type": "json_object"} for structured output
        temperature: float = 0.3,     # low temp for financial accuracy
    ) -> LLMResponse:
        # Uses openai SDK configured for Azure AI Foundry
        pass

    # No embed method — using keyword search, not vector embeddings
```

**Structured output for AnalysisAgent**: The AnalysisAgent uses `response_format={"type": "json_object"}` to produce findings as JSON. This ensures consistent structure and eliminates parsing errors.

**Template-guided narrative for NarrativeAgent**: The NarrativeAgent receives a template with section headers (WHAT CHANGED, WHY IT MATTERS, etc.) and fills in content. Lower hallucination risk than free-form generation.

Configuration via env vars:
```
AZURE_AI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_AI_API_KEY=<key>
AZURE_AI_DEPLOYMENT_GPT4O=gpt-4o
AZURE_AI_DEPLOYMENT_MINI=gpt-4o-mini
```

### 3.7 Confidence Scoring (heuristic for demo)

Practical scoring approach for the demo. In production, this would be calibrated using historical review outcomes and evaluator datasets.

```python
class ConfidenceScorer:
    def score_finding(self, finding: Finding, step_data: dict) -> float:
        score = 1.0

        # Evidence chain penalties
        if len(finding.evidence) == 0:
            score -= 0.4                    # No evidence at all
        else:
            has_data = any(e.type == "data_point" for e in finding.evidence)
            has_doc = any(e.type == "document_excerpt" for e in finding.evidence)
            has_rule = any(e.type == "rule_reference" for e in finding.evidence)

            if not has_data:
                score -= 0.2                # No hard data backing
            if not has_doc:
                score -= 0.1                # No document grounding
            if not has_rule:
                score -= 0.05               # No rule explicitly triggered

        # Document relevance penalty
        doc_scores = [e.relevance_score for e in finding.evidence
                      if e.type == "document_excerpt" and hasattr(e, "relevance_score")]
        if doc_scores and min(doc_scores) < 0.5:
            score -= 0.15                   # Weak document match

        # Data quality penalty
        if step_data.get("missing_entities"):
            score -= 0.1                    # Not all entities reported

        return max(0.0, min(1.0, round(score, 2)))

    def score_step(self, findings: list[Finding]) -> float:
        if not findings:
            return 0.95                     # No findings = high confidence in "nothing found"
        return round(sum(f.confidence for f in findings) / len(findings), 2)

    def score_run(self, steps: list) -> float:
        # Weighted average: later steps (analysis, narrative) weighted higher
        weights = [0.5, 1.0, 1.0, 0.5, 1.5, 1.5, 0.5]  # per step
        total = sum(s.confidence * w for s, w in zip(steps, weights))
        return round(total / sum(weights), 2)
```

**Quality gate thresholds**:
- Finding confidence <0.6 → flagged as `review_required: true`
- Step confidence <0.5 → step marked as `escalated`
- Run confidence <0.7 → run marked with warning

### 3.8 Testing Strategy

**Must-have tests** (implement before demo):

```python
# tests/test_orchestrator.py
test_workflow_run_happy_path()           # All 7 steps complete, findings generated
test_parallel_steps_execute()            # Steps 2+3 run concurrently
test_step_retry_on_transient_error()     # Step fails once, succeeds on retry

# tests/test_tools.py
test_parameterized_query_returns_data()  # get_trial_balances returns correct rows
test_ic_matching_finds_mismatch()        # match_ic_pairs detects planted mismatch
test_anomaly_detector_flags_outlier()    # detect_anomalies finds consulting fee spike

# tests/test_cases.py
test_case1_produces_3_findings()         # IC mismatch, OPEX, adjustment
test_case2_produces_4_findings()         # Margin, cash, churn, KPI disconnect
test_findings_have_evidence()            # All findings have >=1 evidence item
test_confidence_scores_in_range()        # All scores between 0.0 and 1.0
```

**Nice-to-have tests** (if time allows):

```python
# tests/test_orchestrator.py
test_step_timeout()                      # Step exceeds 30s timeout, fails gracefully
test_partial_failure_continues()         # Step 3 fails, steps 4-7 still run

# tests/test_tools.py
test_document_search_relevance()         # "IC policy threshold" returns correct doc

# tests/test_api.py
test_post_workflow_run()                 # POST returns run_id
test_sse_stream_events()                 # SSE delivers events in order
test_get_findings_sorted()               # Findings sorted by severity
test_get_summary_both_audiences()        # Controller vs executive versions differ
test_get_audit_trail()                   # Full trace data returned
```

Run via: `pytest tests/ -v` in CI on every PR.

---

## 4. Demo Cases — Data & Expected Outputs

### 4.1 Case 1: Pre-Close & Consolidation Review

**Period**: February 2026 | **Comparison**: vs January 2026 and vs budget

#### Trial balances (simplified P&L per entity, Feb 2026)

| Account | NKG-JP (JPY M) | NKG-US (USD K) | NKG-SG (SGD K) |
|---|---|---|---|
| Revenue | 850 | 2,400 | 1,200 |
| COGS | -425 | -1,200 | -660 |
| **Gross Margin** | **425 (50.0%)** | **1,200 (50.0%)** | **540 (45.0%)** |
| SGA | -180 | -620 | -280 |
| Consulting fees | -25 | -287 | -45 |
| Other OPEX | -35 | -48 | -22 |
| **Operating Income** | **185** | **245** | **193** |

**January 2026** key differences:
- NKG-US consulting fees were USD 195K (now 287K = +47%)
- NKG-SG gross margin was 48.2% (now 45.0% = -3.2pts)

Note on margins: 45-50% gross margin is realistic for a tech services group. NKG-SG is lower because it is the newest entity (market entry phase with competitive pricing). This is documented in the knowledge pack.

#### Intercompany transactions (Feb 2026)

| From | To | Type | Invoice date | From books | To books | To books (JPY equiv) | Match? |
|---|---|---|---|---|---|---|---|
| NKG-JP | NKG-US | Services | Jan 25 | AR: JPY 15M | AP: USD 102K (Jan 25) | JPY 15.1M | Yes |
| NKG-JP | NKG-SG | Services | Jan 28 | AR: JPY 45.2M | AP: SGD 395K (Feb 2) | JPY 45.5M | **NO — cut-off** |
| NKG-US | NKG-JP | Royalties | Feb 5 | AR: USD 50K | AP: JPY 7.35M (Feb 5) | JPY 7.35M | Yes |

**The planted IC anomaly**: NKG-JP recorded the invoice on **Jan 28** but NKG-SG recorded receipt on **Feb 2** (after their local month-end). This is a genuine **cut-off timing issue**, not an FX problem. The amount in JPY terms is close (JPY 45.2M vs 45.5M — the small difference is FX translation, normal). But the cut-off means NKG-SG has this in February while NKG-JP has it in January. For IC elimination purposes, the amounts don't match in the same period. Impact: JPY 3.3M unreconciled (the difference between recording in Jan vs Feb affects the elimination).

This is what a real controller investigates. It is NOT an FX error — it's a process issue (Singapore's AP team was slow to record).

#### Exchange rates (Feb 2026)

| Pair | Average rate | Closing rate |
|---|---|---|
| USD/JPY | 147.0 | 148.5 |
| SGD/JPY | 112.8 | 115.3 |

These rates are also used for Case 2 currency conversions.

#### Journal entries of note
- JE-2026-0287: Consolidation adjustment, JPY 12.8M debit Goodwill / credit Equity. Note: "Year-end goodwill adjustment". Posted by: System. This is part of the annual impairment test for the NKG-SG acquisition goodwill. The note is too brief for an adjustment above the JPY 10M review threshold.

#### Knowledge pack documents
1. `consolidation_policy.md` — IC elimination rules, materiality thresholds, review requirements. Section 4.2: "IC differences > 2% require reconciliation before close sign-off."
2. `close_notes_feb_2026.md` — Controller notes: "Singapore team delayed in submitting final AR confirmation. US consulting engagement approved by VP Operations in January for a 3-month strategic project with external advisory firm."
3. `ic_elimination_rules.md` — Detailed IC matching procedure: match by invoice number first, then by amount within tolerance band, then by entity pair and period.

#### Expected findings

**Finding 1 (HIGH)**: Intercompany cut-off mismatch: NKG-JP <> NKG-SG
- Root cause: Invoice recorded Jan 28 by NKG-JP, Feb 2 by NKG-SG (5-day gap)
- Impact: JPY 3.3M unreconciled in Feb period
- Evidence: invoice dates, AR/AP amounts, policy doc §4.2, controller notes
- Questions: Was the SGD payable accrued in January or February? Has NKG-SG confirmed?
- Actions: Request NKG-SG to re-date or post adjustment. Document cut-off procedure.
- Confidence: 0.91

**Finding 2 (MEDIUM)**: Unusual OPEX increase — NKG-US consulting fees
- Root cause: 3-month strategic project (found in controller notes)
- Impact: USD 92K above prior month (+47%)
- Evidence: MoM comparison, controller note excerpt, no budget line
- Questions: Is this in the revised forecast? Will it recur?
- Actions: Request formal documentation, update forecast.
- Confidence: 0.85

**Finding 3 (LOW)**: Manual consolidation adjustment above threshold
- Root cause: Goodwill impairment adjustment with insufficient documentation
- Impact: JPY 12.8M (above JPY 10M review threshold)
- Evidence: JE details, policy requirement, goodwill relates to NKG-SG acquisition
- Questions: Is this part of the annual impairment test? What triggered the write-down amount?
- Actions: Enhance documentation. Reference impairment test workpaper.
- Confidence: 0.82

#### Expected executive summary (Controller mode)

"Two consolidation issues require resolution before close sign-off. The highest priority is an intercompany cut-off timing difference between Japan HQ and Singapore — NKG-JP recorded the receivable in January while NKG-SG recorded the payable in February, creating a JPY 3.3M unreconciled difference. This is a process issue, not an amount discrepancy. Additionally, NKG-US consulting fees increased 47% MoM; controller notes indicate a 3-month strategic advisory engagement, but no budget line exists and formal documentation is pending. A goodwill adjustment of JPY 12.8M has been posted with minimal supporting notes. Close sign-off depends on Singapore payable date confirmation by March 3."

#### Expected executive summary (Executive mode)

"Two items need attention before consolidated close. First, a timing difference between Japan and Singapore offices means one intercompany transaction is recorded in different months — this needs to be aligned before the numbers are final. Second, the US entity has a new consulting engagement that isn't in the budget yet. Both are manageable but require action this week."

---

### 4.2 Case 2: Executive Performance Review

**Period**: Q1 2026 (Jan-Feb actual + March forecast) | **Comparison**: vs FY2026 budget

#### Actuals vs Budget (Q1 2026, annualized run-rate)

| Metric | NKG-JP | NKG-US | NKG-SG | Group* |
|---|---|---|---|---|
| Revenue (actual) | JPY 2,520M | USD 7,100K | SGD 3,480K | JPY 4,180M |
| Revenue (budget) | JPY 2,400M | USD 7,200K | SGD 3,600K | JPY 4,200M |
| Revenue variance | +5.0% | -1.4% | -3.3% | -0.5% |
| Gross margin (actual) | 51.2% | 49.1% | 41.8% | 48.1% |
| Gross margin (budget) | 50.0% | 50.0% | 46.0% | 49.5% |
| Margin variance | +1.2pts | -0.9pts | **-4.2pts** | -1.4pts |
| Op. income variance | +12% | -8% | **-22%** | -5% |

*Group in JPY equivalent at average rates (USD/JPY 147.0, SGD/JPY 112.8).

**Variance decomposition for NKG-SG margin erosion**:
- Price/mix effect: -2.1pts (aggressive discounting on 2 new enterprise deals)
- Cost effect: -2.1pts (delivery costs up 15% due to contractor rate increases)
- Volume effect: +0.0pts (revenue roughly on plan)

This decomposition is what the VarianceAnalyzerAgent should produce.

#### KPIs

| KPI | NKG-JP | NKG-US | NKG-SG | Target |
|---|---|---|---|---|
| MRR (SaaS) | JPY 85M | USD 580K | SGD 290K | +5% QoQ |
| Churn rate | 1.2% | **4.8%** | 2.1% | <2.5% |
| NPS | 72 | 68 | 61 | >65 |
| Consulting utilization | 78% | 82% | 71% | >75% |
| DSO (days) | 45 | **58** | 52 | <50 |
| Headcount | 320 | 185 | 95 | per plan |

#### Knowledge pack documents
1. `fpa_commentary_q1_2026.md` — FP&A notes: mentions Singapore pricing pressure, US client loss, cash collection delays
2. `board_agenda_template.md` — Standard quarterly review structure
3. `market_benchmarks_2026.md` — SaaS benchmarks: median churn 2-3%, median gross margin 70-80% (pure SaaS), 50-60% (tech services blended)
4. `management_commentary_q4_2025.md` — Prior quarter for trend comparison

#### Expected findings

**Finding 1 (HIGH)**: Margin erosion in NKG-SG despite near-flat revenue
- Decomposition: Price/mix -2.1pts + Cost -2.1pts = -4.2pts total
- Evidence: deal-level discounting data, contractor rate invoices, FP&A commentary
- Actions: Review pricing discipline vs growth mandate. Request delivery cost forecast.
- Confidence: 0.88

**Finding 2 (HIGH)**: Cash conversion deteriorating at group level
- DSO up 8 days (from 50 to 58) at NKG-US, driven by receivables aging
- Evidence: DSO trend, AR aging buckets, target benchmark
- Note: 58 days DSO is within normal tech industry range, but the deterioration trend is the signal
- Actions: Group-wide cash collection initiative. Focus on NKG-US AR >60 days.
- Confidence: 0.84

**Finding 3 (MEDIUM)**: SaaS churn spike in NKG-US
- Lost 1 enterprise client, MRR impact -USD 340K/month
- Churn at 4.8% vs 2.5% target
- Not reflected in revised forecast
- Evidence: churn rate trend, client loss data, pipeline vs actuals
- Actions: Update forecast. Review client retention strategy.
- Confidence: 0.86

**Finding 4 (LOW)**: KPI-financial disconnect in NKG-US
- Pipeline +35%, NPS OK, utilization high — but operating income -8% and contribution margin flat
- Root cause: sales mix shift toward lower-margin, smaller deals
- Evidence: average deal size trend, margin by deal tier
- Actions: Review pricing tiers. Align sales incentives with margin targets.
- Confidence: 0.78

#### Expected executive summary (Executive mode)

"The most significant management issue is margin deterioration in Singapore: -4.2 points despite stable revenue. The driver is two-fold — aggressive deal pricing (-2.1pts) and rising contractor costs (-2.1pts). Neither is in the current forecast. At the group level, working capital is under pressure — DSO increased 8 days, primarily in the US. The committee should discuss: (1) Singapore pricing discipline vs growth mandate, (2) a group-wide cash collection initiative focused on US receivables, and (3) US client retention following a material enterprise churn event (USD 340K MRR lost, not yet reflected in forecast)."

---

## 5. Demo Speech

### 5.1 Revised script (10 minutes, pre-baked runs)

**Opening (1 min)** — Home screen
> "I built a configurable AI accelerator for Corporate Performance Management. The same governed agent framework adapts to different financial workflows through configuration — not code changes. I'll show two cases: consolidation close review for controllers, and executive performance review for CFOs."

**Case 1 (2.5 min)** — Consolidation
- Click "Select" → Workflow Run page with pre-baked completed run
- "This ran 7 agent steps in 47 seconds. Steps 2 and 3 ran in parallel."
- Quick scan of timeline (5 sec)
- Click "View Findings"
- Walk through HIGH finding (IC cut-off mismatch):
  - "The AI matched 24 intercompany transactions. It found one where Japan and Singapore recorded the same invoice in different months. It cross-referenced the consolidation policy, found controller notes about Singapore delays, and flagged it with specific evidence."
  - Point to evidence section: "Every finding is grounded in data and policy, not guesses."
- Click "View Summary"
- Controller mode (10 sec): "This is what the group controller gets"
- Toggle to Executive mode (10 sec): "Same findings, reframed for the CFO. No account codes, no jargon — just what matters and what to do."

**Case 2 (2.5 min)** — Performance Review
- Back to Home, select Case 2
- Workflow Run → pre-baked → jump to Findings
- "Same orchestrator, different agents. This case analyzes budget variances, KPIs, and prepares board materials."
- Walk through HIGH finding (margin erosion NKG-SG):
  - "The agent didn't just flag 'margin is down'. It decomposed the variance: pricing effect minus 2.1 points, cost effect minus 2.1 points. That's the kind of analysis a CFO needs."
- Executive Summary:
  - "Notice the difference: now we're discussing pricing strategy and cash collection, not reconciliation."

**Architecture (2.5 min)** — Audit Trail
- Show Audit Trail: "Enterprise AI needs to be auditable."
- Expand one step: "Every tool call logged. Every document reference traceable. Every confidence score explainable."
- "This isn't a black box. If an auditor asks 'why did the AI flag this?', we can show the exact data, rules, and documents it used."
- Quick mention: "Behind this: FastAPI backend, React frontend, PostgreSQL for financial data, Azure AI Foundry for LLM calls, Terraform for infrastructure, GitHub Actions for CI/CD. Built to be deployed, not just demoed."

**Closing (1 min)**
> "Three concepts make this work: Governed AI — rules, evidence, and grounding. Configuration over code — the second case reused the same framework with different agents. And Observable Workflows — every decision is auditable."
>
> "What I wanted to demonstrate is not just agent orchestration, but how to turn financial workflows into governed AI systems: reusable, configurable, evidence-based, and observable. That is the layer I believe can add real value on top of products like Manageboard and consolidated accounting workflows."
>
> "My background building AI solutions for ERP at EDISA means I understand the financial data these agents consume — and that understanding is where the real integration work happens."

### 5.2 Key phrases
- "Governed AI" — not just "AI"
- "Accelerator" — not "chatbot"
- "Configuration, not code" — reusability
- "Evidence-based findings" — grounded
- "Audience-aware" — controller vs executive
- "Observable and auditable" — enterprise requirement
- "Cut-off timing, not FX error" — shows real domain knowledge

### 5.3 Anticipated questions

**Q: Why Azure AI Foundry?**
A: The LLM Gateway abstracts the provider. Azure was chosen for tracing integration. Same code works with Bedrock or Vertex by changing gateway config.

**Q: How do you handle hallucination?**
A: Three layers: (1) All data queries are parameterized templates, not LLM-generated SQL. (2) Document search grounds claims in actual policy docs. (3) Confidence scoring flags findings with weak evidence for human review.

**Q: How would this scale to 50+ entities?**
A: The DAG architecture parallelizes entity-level checks. IC matching scales O(n²) on entity pairs but can be batched. Main bottleneck is LLM latency — addressed by async workflows, model selection (gpt-4o-mini for simple steps), and pagination on the findings UI.

**Q: What's the difference between this and a chatbot over financial data?**
A: A chatbot is reactive — it answers what you ask. This is proactive — it runs a defined workflow, applies business rules, and produces structured findings without the user knowing what to look for. The workflow guarantees coverage.

**Q: Did you consider the IC reconciliation vs elimination distinction?**
A: Yes. The IC Check Agent handles reconciliation (do amounts match?). The Consolidation Agent (not shown in this demo scope) would handle elimination (remove matched IC items from consolidated statements). This demo focuses on the pre-close review — the step before elimination.

**Q: How long to build?**
A: About 10 days solo. The reusable framework (orchestrator, tools, gateway, audit trail) took 4 days. Each case took 3 days. The second case was faster because the framework existed. That's the accelerator pattern.

---

## 6. Repository Structure

```
cpm-agent-accelerator/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI app, CORS, lifespan
│   │   ├── config.py                       # Settings (env vars, defaults)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── workflows.py            # POST /run, GET /{id}, GET /stream, GET /latest
│   │   │   │   ├── findings.py             # GET /findings
│   │   │   │   ├── summary.py              # GET /summary
│   │   │   │   ├── audit.py                # GET /audit
│   │   │   │   ├── config_routes.py        # GET /config
│   │   │   │   └── health.py               # GET /health
│   │   │   └── sse.py                      # SSE helper with heartbeat
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py             # DAG-based WorkflowOrchestrator
│   │   │   ├── dag.py                      # DAG definition and execution
│   │   │   ├── agent_base.py              # BaseAgent, AgentContext, AgentResult
│   │   │   ├── agent_registry.py          # Register agents by workflow type
│   │   │   ├── rules_engine.py            # Business rules evaluation
│   │   │   ├── confidence.py              # ConfidenceScorer
│   │   │   └── memory.py                  # Shared run memory
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── data_loader.py             # Shared: load & validate
│   │   │   ├── doc_search.py              # Shared: keyword document search
│   │   │   ├── analysis.py               # Shared: synthesize findings (JSON output)
│   │   │   ├── narrative.py              # Shared: generate summary (template-guided)
│   │   │   ├── quality_gate.py           # Shared: confidence check
│   │   │   ├── ic_checker.py             # Case 1: intercompany reconciliation
│   │   │   ├── anomaly_detector.py       # Case 1: statistical anomaly scan
│   │   │   ├── variance_analyzer.py      # Case 2: budget vs actual + decomposition
│   │   │   └── kpi_analyzer.py           # Case 2: KPI trend analysis
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # BaseTool interface
│   │   │   ├── parameterized_queries.py   # Type A: all SQL templates
│   │   │   ├── ic_matching.py             # Type B: IC pair matching logic
│   │   │   ├── anomaly_detection.py       # Type B: statistical analysis
│   │   │   └── document_search.py         # Type C: TF-IDF keyword search
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── gateway.py                 # LLMGateway (Azure AI Foundry)
│   │   │   └── prompts/
│   │   │       ├── consolidation.py       # System prompts for Case 1 agents
│   │   │       ├── performance.py         # System prompts for Case 2 agents
│   │   │       └── narrative.py           # Summary templates per audience
│   │   │
│   │   ├── observability/
│   │   │   ├── __init__.py
│   │   │   ├── tracer.py                  # Step/tool/LLM call tracing
│   │   │   ├── metrics.py                # Aggregation helpers
│   │   │   └── cost_tracker.py           # Token-based cost estimation
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── models.py                  # SQLAlchemy models
│   │       ├── session.py                # DB session factory
│   │       └── seed/
│   │           ├── seed_all.py           # Master seeder
│   │           ├── entities.py           # Entity + CoA data
│   │           ├── case1_data.py         # Trial balances, IC, JEs, FX
│   │           ├── case2_data.py         # Budget, KPIs, actuals
│   │           └── knowledge_packs/
│   │               ├── consolidation_policy.md
│   │               ├── close_notes_feb_2026.md
│   │               ├── ic_elimination_rules.md
│   │               ├── fpa_commentary_q1_2026.md
│   │               ├── board_agenda_template.md
│   │               ├── market_benchmarks_2026.md
│   │               └── management_commentary_q4_2025.md
│   │
│   ├── tests/
│   │   ├── conftest.py                   # Fixtures (test DB, mock LLM)
│   │   ├── test_orchestrator.py
│   │   ├── test_tools.py
│   │   ├── test_api.py
│   │   └── test_cases.py
│   │
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── WorkflowRun.tsx
│   │   │   ├── Findings.tsx
│   │   │   ├── ExecutiveSummary.tsx
│   │   │   └── AuditTrail.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── WorkflowCard.tsx
│   │   │   ├── ConfigSidePanel.tsx
│   │   │   ├── WorkflowTimeline.tsx
│   │   │   ├── ActivityLog.tsx
│   │   │   ├── RunButton.tsx
│   │   │   ├── FindingCard.tsx
│   │   │   ├── EvidenceItem.tsx
│   │   │   ├── SeverityBadge.tsx
│   │   │   ├── SeverityFilter.tsx
│   │   │   ├── AudienceToggle.tsx
│   │   │   ├── SummaryDocument.tsx
│   │   │   ├── ConfidenceFooter.tsx
│   │   │   ├── TraceOverview.tsx
│   │   │   ├── StepTable.tsx
│   │   │   ├── StepDetail.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── ErrorState.tsx
│   │   │   └── LoadingSkeleton.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useSSE.ts
│   │   │   └── useWorkflow.ts
│   │   │
│   │   ├── api/
│   │   │   └── client.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   ├── index.html
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── infra/
│   ├── modules/
│   │   ├── network/main.tf
│   │   ├── database/main.tf
│   │   ├── compute/main.tf
│   │   └── ai/main.tf
│   ├── environments/
│   │   ├── staging/terraform.tfvars
│   │   └── production/terraform.tfvars
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── .github/
│   └── workflows/
│       ├── pr.yml
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## 7. Implementation Priority

### Phase 1: Skeleton
1. `docker-compose.yml` (PostgreSQL + backend + frontend)
2. DB schema (`db/models.py`) + seed script with ALL mock data for both cases
3. FastAPI app with health endpoint + CORS
4. React app with router, sidebar, all 5 pages as shells
5. API client + TypeScript types

### Phase 2: Core framework
1. `BaseAgent`, `AgentContext`, `AgentResult`
2. DAG definition and execution (`dag.py`, `orchestrator.py`)
3. `LLMGateway` (Azure AI Foundry via openai SDK)
4. `ConfidenceScorer`
5. SSE streaming with heartbeat (`sse.py`)
6. Parameterized query tools
7. Keyword document search tool

### Phase 3: Case 1 agents
1. `DataLoaderAgent`
2. `ICCheckAgent` + `ic_matching` tool
3. `AnomalyDetectorAgent` + `anomaly_detection` tool
4. `DocSearchAgent`
5. `AnalysisAgent` (JSON structured output)
6. `NarrativeAgent` (template-guided, both audiences)
7. `QualityGateAgent`
8. Seed knowledge pack documents

### Phase 4: Frontend (all screens)
1. Home with workflow cards
2. Workflow Run with timeline + activity log + config side panel
3. Findings with collapsible cards + severity filter
4. Executive Summary with audience toggle
5. Audit Trail with expandable step table
6. Empty, error, loading states

### Phase 5: Case 2 agents
1. `VarianceAnalyzerAgent` (with decomposition)
2. `KPIAnalysisAgent`
3. Case 2 seed data + knowledge packs
4. Verify frontend works with Case 2 data

### Phase 6: Tests + CI/CD
1. All tests from section 3.8
2. GitHub Actions PR pipeline (lint + test)
3. Docker build pipeline
4. Terraform modules (stretch goal)

### Phase 7: Polish
1. Pre-bake one completed run per case for demo
2. Visual polish (loading animations, transitions)
3. Edge cases and error handling
4. README
5. Demo rehearsal

---

*End of spec v2. This document is the single source of truth for implementation.*
