import re
from typing import Any

from app.core.agent_base import AgentContext, AgentResult, BaseAgent, StepMetrics
from app.core.tools.document_search import DocumentSearchTool


class DocSearchAgent(BaseAgent):
    """Search for relevant documents for each detected issue. No LLM."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Knowledge pack search for detected issues"
        self.model = ""
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        tools_used: list[str] = []

        queries: dict[str, str] = {}

        if context.workflow_type == "performance":
            queries = await self._build_performance_queries(context)
        else:
            queries = await self._build_consolidation_queries(context)

        if not queries:
            return AgentResult(
                status="completed",
                data={"doc_search_results": {}},
                metrics=StepMetrics(tools_used=tools_used),
            )

        # Execute searches
        doc_tool = DocumentSearchTool()
        async with context.session_factory() as session:
            await doc_tool.initialize(session)

            doc_search_results: dict[str, list[dict[str, Any]]] = {}
            for key, query in queries.items():
                result = await doc_tool.execute({"query": query, "top_k": 3}, session)
                doc_search_results[key] = result.get("documents", [])

        tools_used.append("search_documents")

        return AgentResult(
            status="completed",
            findings=[],
            data={"doc_search_results": doc_search_results},
            metrics=StepMetrics(tools_used=tools_used),
        )


    async def _build_consolidation_queries(self, context: AgentContext) -> dict[str, str]:
        ic_findings = await context.memory.get("ic_findings", [])
        anomaly_findings = await context.memory.get("anomaly_findings", [])
        journal_entries = await context.memory.get("journal_entries", {})

        queries: dict[str, str] = {}

        if ic_findings:
            queries["ic_mismatch"] = "intercompany elimination cut-off timing mismatch period"

        if anomaly_findings:
            queries["anomaly_opex"] = "consulting fees increase strategic project budget variance"

        threshold = _parse_threshold(context.config.get("manual_adjustment_threshold", "JPY 10,000,000"))
        je_rows = journal_entries.get("rows", []) if isinstance(journal_entries, dict) else []
        for row in je_rows:
            debit = row.get("debit", 0) or 0
            if debit >= threshold:
                queries["journal_adjustment"] = "goodwill impairment adjustment consolidation manual review threshold"
                break

        return queries

    async def _build_performance_queries(self, context: AgentContext) -> dict[str, str]:
        variance_findings = await context.memory.get("variance_findings", [])
        kpi_findings = await context.memory.get("kpi_findings", [])

        queries: dict[str, str] = {}

        if variance_findings:
            queries["margin_variance"] = "margin erosion pricing cost contractor budget variance"

        if kpi_findings:
            queries["kpi_breach"] = "churn rate client retention DSO cash collection SaaS metrics"

        queries["benchmarks"] = "market benchmarks SaaS metrics industry comparison"

        return queries


def _parse_threshold(value: str) -> float:
    """Extract the numeric value from a threshold string like 'JPY 10,000,000'."""
    digits = re.sub(r"[^\d.]", "", value)
    try:
        return float(digits)
    except ValueError:
        return 10_000_000.0
