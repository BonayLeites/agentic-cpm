// Types that mirror backend/app/api/schemas.py exactly

export type WorkflowType = "consolidation" | "performance";
export type Severity = "high" | "medium" | "low";
export type AudienceType = "controller" | "executive";
export type WorkflowStatus = "pending" | "running" | "completed" | "failed";
export type StepStatus = "queued" | "running" | "completed" | "failed" | "escalated";

// === Entidades ===

export interface EntityResponse {
  id: number;
  code: string;
  name: string;
  country: string | null;
  currency: string;
  parent_id: number | null;
  ownership_pct: number | null;
}

// === Data Explorer ===

export interface TrialBalanceRow {
  entity_code: string;
  account_code: string;
  account_name: string;
  account_type: string;
  debit: number;
  credit: number;
  period: string;
}

export interface ICTransactionRow {
  from_entity: string;
  to_entity: string;
  transaction_type: string;
  amount: number;
  currency: string;
  invoice_date: string | null;
  recorded_date: string | null;
  mismatch: number;
}

export interface KPIRow {
  entity_code: string;
  kpi_name: string;
  value: number;
  target: number | null;
  unit: string | null;
  period: string;
}

// === Data Stats ===

export interface StatsResponse {
  entities: number;
  trial_balances: number;
  intercompany_transactions: number;
  exchange_rates: number;
  journal_entries: number;
  budgets: number;
  kpis: number;
  documents: number;
}

// === Config ===

export interface KnowledgePackInfo {
  title: string;
  doc_type: string | null;
}

export interface ToolInfo {
  name: string;
  description: string;
}

export interface ConfigResponse {
  workflow_type: string;
  entities: EntityResponse[];
  dataset_counts: StatsResponse;
  business_rules: Record<string, string>;
  knowledge_packs: KnowledgePackInfo[];
  tools: ToolInfo[];
}

// === Workflows ===

export interface WorkflowRunResponse {
  run_id: number;
  status: string;
}

export interface WorkflowStepResponse {
  id: number;
  step_order: number;
  agent_name: string;
  status: StepStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  finding_count: number;
  confidence_score: number | null;
  cost: number | null;
  error_message: string | null;
}

export interface WorkflowRunDetailResponse {
  id: number;
  workflow_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  total_duration_ms: number | null;
  total_findings: number;
  total_cost: number | null;
  overall_confidence: number | null;
  created_at: string | null;
  steps: WorkflowStepResponse[];
}

// === Findings ===

export interface Evidence {
  type: "data_point" | "document_excerpt" | "rule_reference";
  label: string;
  value: string;
  source: string;
  relevance_score?: number;
}

export interface FindingResponse {
  id: number;
  run_id: number;
  step_id: number | null;
  title: string;
  severity: Severity;
  status: string;
  category: string | null;
  entity_code: string | null;
  description: string | null;
  impact_amount: number | null;
  impact_currency: string | null;
  rule_triggered: string | null;
  evidence: Evidence[] | null;
  suggested_questions: string[] | null;
  suggested_actions: string[] | null;
  confidence: number | null;
  escalation_needed: boolean;
  escalation_reason: string | null;
  created_at: string | null;
}

// === Summary ===

export interface SummaryResponse {
  id: number;
  run_id: number;
  audience: string;
  summary: string;
  created_at: string | null;
}

// === Audit ===

export interface AuditStepResponse {
  id: number;
  step_order: number;
  agent_name: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  input_data: unknown;
  output_data: unknown;
  tools_used: unknown;
  llm_calls: unknown;
  finding_count: number;
  confidence_score: number | null;
  cost: number | null;
  error_message: string | null;
  retry_count: number;
}

export interface AuditResponse {
  run_id: number;
  workflow_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  total_duration_ms: number | null;
  total_findings: number;
  total_cost: number | null;
  overall_confidence: number | null;
  steps: AuditStepResponse[];
}

// === SSE Events ===

export type SSEEventType =
  | "step_started"
  | "step_completed"
  | "step_failed"
  | "step_escalated"
  | "run_completed";

export interface SSEStepStarted {
  step_name: string;
  step_order: number;
  run_id: number;
}

export interface SSEStepCompleted {
  step_name: string;
  step_order: number;
  run_id: number;
  duration_ms: number;
  finding_count: number;
  confidence_score: number;
}

export interface SSEStepFailed {
  step_name: string;
  step_order: number;
  run_id: number;
  error: string;
}

export interface SSEStepEscalated {
  step_name: string;
  step_order: number;
  run_id: number;
  reason: string;
}

export interface SSERunCompleted {
  run_id: number;
  status: string;
  total_duration_ms: number;
  total_findings: number;
  overall_confidence: number;
  total_cost: number;
}

export interface ActivityEvent {
  id: number;
  timestamp: Date;
  type: SSEEventType;
  step_name?: string;
  step_order?: number;
  data: Record<string, unknown>;
}

export interface LiveStep {
  step_order: number;
  step_name: string;
  status: StepStatus;
  duration_ms: number | null;
  finding_count: number;
  confidence_score: number | null;
}
