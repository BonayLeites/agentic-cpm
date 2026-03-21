import logging
from typing import Any

from app.core.agent_base import AgentContext, AgentResult, BaseAgent, StepMetrics
from app.core.tools.parameterized_queries import (
    GetBudgetsTool,
    GetExchangeRatesTool,
    GetICTransactionsTool,
    GetJournalEntriesTool,
    GetKPIsTool,
    GetTrialBalancesTool,
)

logger = logging.getLogger(__name__)

_ENTITIES = ["NKG-JP", "NKG-US", "NKG-SG"]
_PERIOD = "2026-02"
_COMPARISON_PERIOD = "2026-01"


class DataLoaderAgent(BaseAgent):
    """Load and validate financial data for the analysis period."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Load financial data based on workflow type"
        self.model = ""
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        if context.workflow_type == "performance":
            return await self._load_performance(context)
        return await self._load_consolidation(context)

    async def _load_consolidation(self, context: AgentContext) -> AgentResult:
        tools_used: list[str] = []

        tb_tool = GetTrialBalancesTool()
        ic_tool = GetICTransactionsTool()
        fx_tool = GetExchangeRatesTool()
        je_tool = GetJournalEntriesTool()

        async with context.session_factory() as session:
            tb_current = await tb_tool.execute(
                {"entity_codes": _ENTITIES, "period": _PERIOD}, session,
            )
            tools_used.append("get_trial_balances")

            tb_previous = await tb_tool.execute(
                {"entity_codes": _ENTITIES, "period": _COMPARISON_PERIOD}, session,
            )

            ic_txns = await ic_tool.execute({"period": _PERIOD}, session)
            tools_used.append("get_ic_transactions")

            fx_rates = await fx_tool.execute(
                {"start_date": "2026-01-01", "end_date": "2026-02-28"}, session,
            )
            tools_used.append("get_exchange_rates")

            je_data = await je_tool.execute(
                {"entity_codes": _ENTITIES, "period": _PERIOD}, session,
            )
            tools_used.append("get_journal_entries")

        entities_with_data = {
            row["entity_code"] for row in tb_current.get("rows", [])
        }
        missing = [e for e in _ENTITIES if e not in entities_with_data]
        if missing:
            logger.warning("Entities with no trial balance data: %s", missing)

        data: dict[str, Any] = {
            "entities": _ENTITIES,
            "period": _PERIOD,
            "comparison_period": _COMPARISON_PERIOD,
            "trial_balances_current": tb_current,
            "trial_balances_previous": tb_previous,
            "ic_transactions": ic_txns,
            "exchange_rates": fx_rates,
            "journal_entries": je_data,
            "missing_entities": missing,
        }

        return AgentResult(
            status="completed",
            findings=[],
            data=data,
            metrics=StepMetrics(
                tools_used=tools_used,
                finding_count=0,
                confidence_score=0.95,
            ),
        )

    async def _load_performance(self, context: AgentContext) -> AgentResult:
        tools_used: list[str] = []

        tb_tool = GetTrialBalancesTool()
        budget_tool = GetBudgetsTool()
        kpi_tool = GetKPIsTool()
        fx_tool = GetExchangeRatesTool()

        async with context.session_factory() as session:
            tb_current = await tb_tool.execute(
                {"entity_codes": _ENTITIES, "period": _PERIOD}, session,
            )
            tb_previous = await tb_tool.execute(
                {"entity_codes": _ENTITIES, "period": _COMPARISON_PERIOD}, session,
            )
            tools_used.append("get_trial_balances")

            budgets = await budget_tool.execute(
                {"entity_codes": _ENTITIES, "period": _PERIOD}, session,
            )
            tools_used.append("get_budgets")

            kpis_current = await kpi_tool.execute(
                {"entity_codes": _ENTITIES, "period": _PERIOD}, session,
            )
            kpis_previous = await kpi_tool.execute(
                {"entity_codes": _ENTITIES, "period": _COMPARISON_PERIOD}, session,
            )
            tools_used.append("get_kpis")

            fx_rates = await fx_tool.execute(
                {"start_date": "2026-01-01", "end_date": "2026-02-28"}, session,
            )
            tools_used.append("get_exchange_rates")

        entities_with_data = {
            row["entity_code"] for row in tb_current.get("rows", [])
        }
        missing = [e for e in _ENTITIES if e not in entities_with_data]
        if missing:
            logger.warning("Entities with no trial balance data: %s", missing)

        data: dict[str, Any] = {
            "entities": _ENTITIES,
            "period": _PERIOD,
            "comparison_period": _COMPARISON_PERIOD,
            "trial_balances_current": tb_current,
            "trial_balances_previous": tb_previous,
            "budgets": budgets,
            "kpis_current": kpis_current,
            "kpis_previous": kpis_previous,
            "exchange_rates": fx_rates,
            "missing_entities": missing,
        }

        return AgentResult(
            status="completed",
            findings=[],
            data=data,
            metrics=StepMetrics(
                tools_used=tools_used,
                finding_count=0,
                confidence_score=0.95,
            ),
        )
