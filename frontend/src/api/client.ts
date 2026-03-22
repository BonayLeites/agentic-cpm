import type {
  AuditResponse,
  ConfigResponse,
  EntityResponse,
  FindingResponse,
  ICTransactionRow,
  KPIRow,
  StatsResponse,
  SummaryResponse,
  TrialBalanceRow,
  WorkflowRunDetailResponse,
  WorkflowRunResponse,
} from "../types";

export const API_BASE = import.meta.env.VITE_API_URL ?? "";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("demoToken");
  return token ? { "X-Demo-Token": token } : {};
}

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...authHeaders() },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function apiPost<T, B>(path: string, body: B): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// === Data ===

export function getStats(): Promise<StatsResponse> {
  return apiGet("/api/data/stats");
}

export function getTrialBalances(period: string, entityCode?: string): Promise<TrialBalanceRow[]> {
  const params = new URLSearchParams({ period });
  if (entityCode) params.set("entity_code", entityCode);
  return apiGet(`/api/data/trial-balances?${params}`);
}

export function getICTransactions(period: string): Promise<ICTransactionRow[]> {
  return apiGet(`/api/data/ic-transactions?period=${period}`);
}

export function getKPIs(period: string, entityCode?: string): Promise<KPIRow[]> {
  const params = new URLSearchParams({ period });
  if (entityCode) params.set("entity_code", entityCode);
  return apiGet(`/api/data/kpis?${params}`);
}

// === Config ===

export function getConfig(workflowType: string): Promise<ConfigResponse> {
  return apiGet(`/api/config/${workflowType}`);
}

// === Workflows ===

export function getLatestWorkflow(
  workflowType: string,
): Promise<WorkflowRunDetailResponse | null> {
  return apiGet<WorkflowRunDetailResponse | null>(
    `/api/workflows/latest?workflow_type=${workflowType}`,
  );
}

export function getEntities(): Promise<EntityResponse[]> {
  return apiGet("/api/data/entities");
}

export function getWorkflowRun(
  runId: number,
): Promise<WorkflowRunDetailResponse> {
  return apiGet(`/api/workflows/${runId}`);
}

export function createWorkflowRun(
  workflowType: string,
): Promise<WorkflowRunResponse> {
  return apiPost("/api/workflows/run", { workflow_type: workflowType });
}

// === Findings ===

export function getFindings(runId: number): Promise<FindingResponse[]> {
  return apiGet(`/api/findings?run_id=${runId}`);
}

// === Summary ===

export function getSummary(
  runId: number,
  audience: string,
): Promise<SummaryResponse> {
  return apiGet(`/api/summary?run_id=${runId}&audience=${audience}`);
}

// === Audit ===

export function getAudit(runId: number): Promise<AuditResponse> {
  return apiGet(`/api/audit?run_id=${runId}`);
}
