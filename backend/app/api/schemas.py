from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


# === Entities ===

class EntityResponse(BaseModel):
    id: int
    code: str
    name: str
    country: str | None
    currency: str
    parent_id: int | None
    ownership_pct: Decimal | None

    model_config = {"from_attributes": True}


# === Data Stats ===

class StatsResponse(BaseModel):
    entities: int
    trial_balances: int
    intercompany_transactions: int
    exchange_rates: int
    journal_entries: int
    budgets: int
    kpis: int
    documents: int


# === Data Explorer ===

class TrialBalanceRow(BaseModel):
    entity_code: str
    account_code: str
    account_name: str
    account_type: str
    debit: float
    credit: float
    period: str


class ICTransactionRow(BaseModel):
    from_entity: str
    to_entity: str
    transaction_type: str
    amount: float
    currency: str
    invoice_date: str | None
    recorded_date: str | None
    mismatch: float


class KPIRow(BaseModel):
    entity_code: str
    kpi_name: str
    value: float
    target: float | None
    unit: str | None
    period: str


# === Config ===

class KnowledgePackInfo(BaseModel):
    title: str
    doc_type: str | None

    model_config = {"from_attributes": True}


class ToolInfo(BaseModel):
    name: str
    description: str


class ConfigResponse(BaseModel):
    workflow_type: str
    entities: list[EntityResponse]
    dataset_counts: StatsResponse
    business_rules: dict[str, str]
    knowledge_packs: list[KnowledgePackInfo]
    tools: list[ToolInfo]


# === Workflows ===

class WorkflowRunCreate(BaseModel):
    workflow_type: str
    language: str = "en"


class WorkflowRunResponse(BaseModel):
    run_id: int
    status: str


class WorkflowStepResponse(BaseModel):
    id: int
    step_order: int
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    finding_count: int
    confidence_score: Decimal | None
    cost: Decimal | None
    error_message: str | None

    model_config = {"from_attributes": True}


class WorkflowRunDetailResponse(BaseModel):
    id: int
    workflow_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_duration_ms: int | None
    total_findings: int
    total_cost: Decimal | None
    overall_confidence: Decimal | None
    created_at: datetime | None
    steps: list[WorkflowStepResponse]

    model_config = {"from_attributes": True}


# === Findings ===

class FindingResponse(BaseModel):
    id: int
    run_id: int
    step_id: int | None
    title: str
    severity: str
    status: str
    category: str | None
    entity_code: str | None
    description: str | None
    impact_amount: Decimal | None
    impact_currency: str | None
    rule_triggered: str | None
    evidence: Any | None
    suggested_questions: Any | None
    suggested_actions: Any | None
    confidence: Decimal | None
    escalation_needed: bool
    escalation_reason: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}


# === Summary ===

class SummaryResponse(BaseModel):
    id: int
    run_id: int
    audience: str
    summary: str
    created_at: datetime | None

    model_config = {"from_attributes": True}


# === Audit ===

class AuditStepResponse(BaseModel):
    id: int
    step_order: int
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    input_data: Any | None
    output_data: Any | None
    tools_used: Any | None
    llm_calls: Any | None
    finding_count: int
    confidence_score: Decimal | None
    cost: Decimal | None
    error_message: str | None
    retry_count: int

    model_config = {"from_attributes": True}


class AuditResponse(BaseModel):
    run_id: int
    workflow_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    total_duration_ms: int | None
    total_findings: int
    total_cost: Decimal | None
    overall_confidence: Decimal | None
    steps: list[AuditStepResponse]
