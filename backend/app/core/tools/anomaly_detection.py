from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tools.base import BaseTool
from app.db.models import ChartOfAccounts, Entity, TrialBalance


class AnomalyDetectionTool(BaseTool):
    """MoM comparison of trial balances. Flags changes that exceed the threshold."""

    name = "detect_anomalies"
    description = "Statistical anomaly detection on financial data"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        entity_code: str = params["entity_code"]
        period: str = params["period"]
        comparison_period: str = params["comparison_period"]
        threshold_pct: float = params.get("threshold_pct", 15.0)

        # Single query for both periods
        balances_by_period = await self._load_balances_both(
            session, entity_code, period, comparison_period,
        )
        current_data = balances_by_period.get(period, {})
        previous_data = balances_by_period.get(comparison_period, {})

        anomalies: list[dict[str, Any]] = []

        for account_code, current_info in current_data.items():
            previous_info = previous_data.get(account_code)
            if previous_info is None:
                continue

            current_net = current_info["net"]
            previous_net = previous_info["net"]

            if previous_net == 0.0:
                continue

            change_pct = round((current_net - previous_net) / abs(previous_net) * 100, 2)

            if abs(change_pct) > threshold_pct:
                anomalies.append({
                    "account_code": account_code,
                    "account_name": current_info["account_name"],
                    "current": current_net,
                    "previous": previous_net,
                    "change_pct": change_pct,
                    "threshold_breached": True,
                })

        return {
            "entity_code": entity_code,
            "period": period,
            "comparison_period": comparison_period,
            "threshold_pct": threshold_pct,
            "anomalies": anomalies,
        }

    async def _load_balances_both(
        self,
        session: AsyncSession,
        entity_code: str,
        period: str,
        comparison_period: str,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Load trial balances for both periods in a single query."""
        stmt = (
            select(
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                ChartOfAccounts.account_type,
                TrialBalance.debit,
                TrialBalance.credit,
                TrialBalance.period,
            )
            .join(Entity, TrialBalance.entity_id == Entity.id)
            .join(ChartOfAccounts, TrialBalance.account_id == ChartOfAccounts.id)
            .where(
                Entity.code == entity_code,
                TrialBalance.period.in_([period, comparison_period]),
            )
        )

        result = await session.execute(stmt)
        data: dict[str, dict[str, dict[str, Any]]] = {}

        for row in result:
            debit = float(row.debit) if row.debit else 0.0
            credit = float(row.credit) if row.credit else 0.0

            # Expense/asset: net = debit - credit (positive = expense/asset)
            # Revenue/liability/equity: net = credit - debit (positive = income/liability)
            if row.account_type in ("expense", "asset"):
                net = debit - credit
            else:
                net = credit - debit

            data.setdefault(row.period, {})[row.account_code] = {
                "account_name": row.account_name,
                "account_type": row.account_type,
                "net": net,
            }

        return data
