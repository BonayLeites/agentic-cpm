from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tools.base import BaseTool
from app.db.models import (
    Budget,
    ChartOfAccounts,
    Entity,
    ExchangeRate,
    IntercompanyTransaction,
    JournalEntry,
    JournalEntryLine,
    KPI,
    TrialBalance,
)


def _serialize(value: Any) -> Any:
    """Convert Decimal/date to float/str for JSON serialization."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


def _serialize_rows(result: Any) -> dict[str, Any]:
    """Serialize SQLAlchemy result rows to a JSON-compatible dict."""
    rows = [
        {k: _serialize(v) for k, v in row._mapping.items()}
        for row in result
    ]
    return {"rows": rows}


class GetTrialBalancesTool(BaseTool):
    """Query trial balances by entity and period."""

    name = "get_trial_balances"
    description = "Fetch trial balance data by entity and period"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        entity_codes: list[str] = params["entity_codes"]
        period: str = params["period"]

        stmt = (
            select(
                Entity.code.label("entity_code"),
                Entity.name.label("entity_name"),
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                ChartOfAccounts.account_type,
                TrialBalance.debit,
                TrialBalance.credit,
                TrialBalance.period,
            )
            .join(Entity, TrialBalance.entity_id == Entity.id)
            .join(ChartOfAccounts, TrialBalance.account_id == ChartOfAccounts.id)
            .where(Entity.code.in_(entity_codes), TrialBalance.period == period)
            .order_by(Entity.code, ChartOfAccounts.account_code)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)


class GetICTransactionsTool(BaseTool):
    """Query intercompany transactions by period."""

    name = "get_ic_transactions"
    description = "Fetch intercompany transactions by period"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        period: str = params["period"]

        from_entity = Entity.__table__.alias("from_entity")
        to_entity = Entity.__table__.alias("to_entity")

        stmt = (
            select(
                from_entity.c.code.label("from_entity"),
                to_entity.c.code.label("to_entity"),
                IntercompanyTransaction.transaction_type,
                IntercompanyTransaction.amount,
                IntercompanyTransaction.currency,
                IntercompanyTransaction.from_amount,
                IntercompanyTransaction.to_amount,
                IntercompanyTransaction.to_amount_jpy,
                IntercompanyTransaction.mismatch_amount,
                IntercompanyTransaction.invoice_date,
                IntercompanyTransaction.recorded_date,
                IntercompanyTransaction.period,
            )
            .join(from_entity, IntercompanyTransaction.from_entity_id == from_entity.c.id)
            .join(to_entity, IntercompanyTransaction.to_entity_id == to_entity.c.id)
            .where(IntercompanyTransaction.period == period)
            .order_by(IntercompanyTransaction.id)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)


class GetBudgetsTool(BaseTool):
    """Query budgets by entity and period."""

    name = "get_budgets"
    description = "Fetch budget data by entity, account, and period"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        entity_codes: list[str] = params["entity_codes"]
        period: str = params["period"]

        stmt = (
            select(
                Entity.code.label("entity_code"),
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                Budget.period,
                Budget.amount,
            )
            .join(Entity, Budget.entity_id == Entity.id)
            .join(ChartOfAccounts, Budget.account_id == ChartOfAccounts.id)
            .where(Entity.code.in_(entity_codes), Budget.period == period)
            .order_by(Entity.code, ChartOfAccounts.account_code)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)


class GetKPIsTool(BaseTool):
    """Query KPIs by entity and period."""

    name = "get_kpis"
    description = "Fetch KPI values and targets by entity and period"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        entity_codes: list[str] = params["entity_codes"]
        period: str = params["period"]

        stmt = (
            select(
                Entity.code.label("entity_code"),
                KPI.kpi_name,
                KPI.kpi_value,
                KPI.kpi_target,
                KPI.period,
                KPI.unit,
            )
            .join(Entity, KPI.entity_id == Entity.id)
            .where(Entity.code.in_(entity_codes), KPI.period == period)
            .order_by(Entity.code, KPI.kpi_name)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)


class GetExchangeRatesTool(BaseTool):
    """Query exchange rates by date range."""

    name = "get_exchange_rates"
    description = "Fetch exchange rates by currency pair and date range"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        start = date.fromisoformat(params["start_date"])
        end = date.fromisoformat(params["end_date"])

        stmt = (
            select(
                ExchangeRate.from_currency,
                ExchangeRate.to_currency,
                ExchangeRate.rate_type,
                ExchangeRate.rate,
                ExchangeRate.effective_date,
            )
            .where(ExchangeRate.effective_date.between(start, end))
            .order_by(ExchangeRate.effective_date, ExchangeRate.from_currency)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)


class GetJournalEntriesTool(BaseTool):
    """Query journal entries with line items by entity and period."""

    name = "get_journal_entries"
    description = "Fetch journal entries with line items by entity and period"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        entity_codes: list[str] = params["entity_codes"]
        period: str = params["period"]

        stmt = (
            select(
                Entity.code.label("entity_code"),
                JournalEntry.entry_number,
                JournalEntry.entry_date,
                JournalEntry.description.label("entry_description"),
                JournalEntry.posted_by,
                ChartOfAccounts.account_code,
                ChartOfAccounts.account_name,
                JournalEntryLine.debit,
                JournalEntryLine.credit,
                JournalEntryLine.description.label("line_description"),
            )
            .join(Entity, JournalEntry.entity_id == Entity.id)
            .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id)
            .where(Entity.code.in_(entity_codes), JournalEntry.period == period)
            .order_by(JournalEntry.entry_number, JournalEntryLine.id)
        )

        result = await session.execute(stmt)
        return _serialize_rows(result)
