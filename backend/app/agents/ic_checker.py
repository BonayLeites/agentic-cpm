import logging
from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentResult,
    BaseAgent,
    StepMetrics,
    enrich_doc_evidence,
    parse_findings_json,
)
from app.core.tools.document_search import DocumentSearchTool
from app.core.tools.ic_matching import ICMatchingTool
from app.llm.gateway import get_gateway
from app.llm.prompts.consolidation import IC_CHECK_SYSTEM

logger = logging.getLogger(__name__)


class ICCheckAgent(BaseAgent):
    """Match IC transactions and analyze mismatches with LLM."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "IC transaction matching and mismatch analysis"
        self.model = "gpt-4o"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        period = await context.memory.get("period", "2026-02")
        tools_used: list[str] = []
        llm_calls: list[dict[str, Any]] = []
        total_cost = 0.0

        # 1. Ejecutar IC matching
        ic_tool = ICMatchingTool()
        async with context.session_factory() as session:
            ic_result = await ic_tool.execute({"period": period}, session)
        tools_used.append("match_ic_pairs")

        mismatched = ic_result.get("mismatched", [])

        if not mismatched:
            return AgentResult(
                status="completed",
                data={"ic_match_result": ic_result, "ic_findings": []},
                metrics=StepMetrics(tools_used=tools_used),
            )

        # 2. Buscar documentos relevantes
        doc_tool = DocumentSearchTool()
        async with context.session_factory() as session:
            await doc_tool.initialize(session)
            doc_result = await doc_tool.execute(
                {"query": "intercompany elimination cut-off mismatch tolerance", "top_k": 3},
                session,
            )
        tools_used.append("search_documents")
        doc_excerpts = doc_result.get("documents", [])

        # 3. Construir prompt y llamar LLM
        user_content = _build_user_message(ic_result, doc_excerpts, context.config)

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": IC_CHECK_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            model="gpt-4o",
        )
        total_cost += response.cost
        llm_calls.append({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
        })

        # 4. Parsear respuesta y enriquecer con doc evidence
        findings = parse_findings_json(
            response.content,
            default_severity="high",
            default_category="intercompany",
            default_confidence=0.85,
        )
        enrich_doc_evidence(findings, doc_excerpts)

        return AgentResult(
            status="completed",
            findings=findings,
            data={
                "ic_match_result": ic_result,
                "ic_findings": [{"title": f.title, "severity": f.severity, "description": f.description} for f in findings],
            },
            metrics=StepMetrics(
                tools_used=tools_used,
                llm_calls=llm_calls,
                cost=total_cost,
            ),
        )


def _build_user_message(
    ic_result: dict[str, Any],
    doc_excerpts: list[dict[str, Any]],
    rules: dict[str, str],
) -> str:
    """Build the user message with IC data, documents, and business rules."""
    parts: list[str] = []

    parts.append("## IC Matching Results")
    parts.append(f"Total transactions: {ic_result['total']}")
    parts.append(f"Matched: {ic_result['matched']}")
    parts.append(f"Mismatched: {len(ic_result['mismatched'])}")

    for m in ic_result["mismatched"]:
        parts.append(f"\n### Mismatch: {m['from_entity']} → {m['to_entity']}")
        parts.append(f"- Type: {m['transaction_type']}")
        parts.append(f"- From amount: {m['from_amount']:,.0f}")
        parts.append(f"- To amount (JPY): {m['to_amount_jpy']:,.0f}")
        parts.append(f"- Difference: {m['amount_diff']:,.0f}")
        parts.append(f"- Percentage diff: {m['pct_diff']}%")
        parts.append(f"- Invoice date: {m['invoice_date']}")
        parts.append(f"- Recorded date: {m['recorded_date']}")
        parts.append(f"- Timing gap: {m['timing_gap_days']} days")

    if doc_excerpts:
        parts.append("\n## Relevant Documents")
        for doc in doc_excerpts:
            parts.append(f"\n### {doc['title']} (relevance: {doc['relevance_score']})")
            parts.append(doc["excerpt"])

    parts.append("\n## Business Rules")
    for key, value in rules.items():
        parts.append(f"- {key}: {value}")

    return "\n".join(parts)
