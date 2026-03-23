import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Literal, get_args

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.memory import WorkflowMemory

EvidenceType = Literal["data_point", "document_excerpt", "rule_reference"]
_VALID_EVIDENCE_TYPES = set(get_args(EvidenceType))

logger = logging.getLogger(__name__)


# --- Data types for agent results ---


class Evidence(BaseModel):
    """Evidence supporting a finding."""

    type: EvidenceType
    label: str
    value: str
    source: str
    relevance_score: float | None = None


class AgentFinding(BaseModel):
    """Finding produced by an agent. Converted to ORM Finding when persisted."""

    title: str
    severity: str  # "high", "medium", "low"
    category: str | None = None
    entity_code: str | None = None
    description: str | None = None
    impact_amount: float | None = None
    impact_currency: str = "JPY"
    rule_triggered: str | None = None
    evidence: list[Evidence] = []
    suggested_questions: list[str] = []
    suggested_actions: list[str] = []
    confidence: float = 0.0  # 0-1 internal scale
    escalation_needed: bool = False
    escalation_reason: str | None = None


class StepMetrics(BaseModel):
    """Execution metrics for a step."""

    duration_ms: int = 0
    finding_count: int = 0
    confidence_score: float = 0.0  # 0-1 internal scale
    tools_used: list[str] = []
    llm_calls: list[dict[str, Any]] = []
    cost: float = 0.0


class AgentResult(BaseModel):
    """Result of an agent's execution."""

    status: Literal["completed", "escalated", "failed"]
    findings: list[AgentFinding] = []
    data: dict[str, Any] = {}  # data for downstream agents via memory
    metrics: StepMetrics = StepMetrics()


# --- Agent context and base class ---


class AgentContext:
    """Shared context passed to each agent during execution."""

    def __init__(
        self,
        run_id: int,
        workflow_type: str,
        config: dict[str, str],
        session_factory: async_sessionmaker,
        memory: WorkflowMemory,
        language: str = "en",
    ) -> None:
        self.run_id = run_id
        self.workflow_type = workflow_type
        self.config = config
        self.session_factory = session_factory
        self.memory = memory
        self.language = language


class BaseAgent(ABC):
    """Abstract base class for all workflow agents."""

    name: str
    description: str
    model: str  # "gpt-4o", "gpt-4o-mini", or "" if no LLM

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        ...


# --- Helpers for parsing LLM responses ---


def parse_evidence_list(raw: list[dict[str, Any]]) -> list[Evidence]:
    """Convert a list of raw dicts to Evidence objects, sanitizing the type field."""
    evidence: list[Evidence] = []
    for e in raw:
        etype = e.get("type", "data_point")
        if etype not in _VALID_EVIDENCE_TYPES:
            etype = "data_point"
        evidence.append(Evidence(
            type=etype,
            label=e.get("label", ""),
            value=e.get("value", ""),
            source=e.get("source", ""),
            relevance_score=e.get("relevance_score"),
        ))
    return evidence


def parse_findings_json(
    llm_response: str,
    *,
    default_severity: str = "medium",
    default_category: str | None = None,
    default_currency: str = "JPY",
    default_confidence: float = 0.80,
) -> list[AgentFinding]:
    """Parse an LLM JSON response into a list of AgentFindings."""
    try:
        data = json.loads(llm_response)
    except json.JSONDecodeError:
        logger.error("LLM response is not valid JSON: %s", llm_response[:200])
        return []

    findings: list[AgentFinding] = []
    for f in data.get("findings", []):
        evidence = parse_evidence_list(f.get("evidence", []))
        findings.append(AgentFinding(
            title=f.get("title", "Finding"),
            severity=f.get("severity", default_severity),
            category=f.get("category", default_category),
            entity_code=f.get("entity_code"),
            description=f.get("description"),
            impact_amount=f.get("impact_amount"),
            impact_currency=f.get("impact_currency", default_currency),
            rule_triggered=f.get("rule_triggered"),
            evidence=evidence,
            suggested_questions=f.get("suggested_questions", []),
            suggested_actions=f.get("suggested_actions", []),
            confidence=f.get("confidence", default_confidence),
        ))
    return findings


def enrich_doc_evidence(
    findings: list[AgentFinding],
    doc_excerpts: list[dict[str, Any]],
) -> None:
    """Attach the top document excerpt as evidence to findings that lack a document_excerpt."""
    if not doc_excerpts:
        return
    top_doc = doc_excerpts[0]
    for finding in findings:
        has_doc = any(e.type == "document_excerpt" for e in finding.evidence)
        if not has_doc:
            finding.evidence.append(Evidence(
                type="document_excerpt",
                label=top_doc["title"],
                value=top_doc["excerpt"],
                source=top_doc["title"],
                relevance_score=top_doc.get("relevance_score"),
            ))
