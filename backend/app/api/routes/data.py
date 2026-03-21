from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    EntityResponse,
    ICTransactionRow,
    KPIRow,
    StatsResponse,
    TrialBalanceRow,
)
from app.db.models import (
    Budget,
    ChartOfAccounts,
    Document,
    Entity,
    ExchangeRate,
    IntercompanyTransaction,
    JournalEntry,
    KPI,
    TrialBalance,
)
from app.db.session import get_session

router = APIRouter(tags=["data"])


@router.get("/api/data/entities", response_model=list[EntityResponse])
async def get_entities(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Entity).order_by(Entity.id))
    return result.scalars().all()


@router.get("/api/data/trial-balances", response_model=list[TrialBalanceRow])
async def get_trial_balances(
    period: str = Query(default="2026-02"),
    entity_code: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(
            Entity.code.label("entity_code"),
            ChartOfAccounts.account_code,
            ChartOfAccounts.account_name,
            ChartOfAccounts.account_type,
            TrialBalance.debit,
            TrialBalance.credit,
            TrialBalance.period,
        )
        .join(Entity, TrialBalance.entity_id == Entity.id)
        .join(ChartOfAccounts, TrialBalance.account_id == ChartOfAccounts.id)
        .where(TrialBalance.period == period)
        .order_by(Entity.code, ChartOfAccounts.account_code)
    )
    if entity_code:
        stmt = stmt.where(Entity.code == entity_code)
    result = await session.execute(stmt)
    return [
        TrialBalanceRow(
            entity_code=r.entity_code,
            account_code=r.account_code,
            account_name=r.account_name,
            account_type=r.account_type,
            debit=float(r.debit or 0),
            credit=float(r.credit or 0),
            period=r.period,
        )
        for r in result
    ]


@router.get("/api/data/ic-transactions", response_model=list[ICTransactionRow])
async def get_ic_transactions(
    period: str = Query(default="2026-02"),
    session: AsyncSession = Depends(get_session),
):
    from_ent = Entity.__table__.alias("from_ent")
    to_ent = Entity.__table__.alias("to_ent")
    stmt = (
        select(
            from_ent.c.code.label("from_entity"),
            to_ent.c.code.label("to_entity"),
            IntercompanyTransaction.transaction_type,
            IntercompanyTransaction.from_amount,
            IntercompanyTransaction.currency,
            IntercompanyTransaction.invoice_date,
            IntercompanyTransaction.recorded_date,
            IntercompanyTransaction.mismatch_amount,
        )
        .join(from_ent, IntercompanyTransaction.from_entity_id == from_ent.c.id)
        .join(to_ent, IntercompanyTransaction.to_entity_id == to_ent.c.id)
        .where(IntercompanyTransaction.period == period)
        .order_by(IntercompanyTransaction.id)
    )
    result = await session.execute(stmt)
    return [
        ICTransactionRow(
            from_entity=r.from_entity,
            to_entity=r.to_entity,
            transaction_type=r.transaction_type,
            amount=float(r.from_amount or 0),
            currency=r.currency or "",
            invoice_date=r.invoice_date.isoformat() if r.invoice_date else None,
            recorded_date=r.recorded_date.isoformat() if r.recorded_date else None,
            mismatch=float(r.mismatch_amount or 0),
        )
        for r in result
    ]


@router.get("/api/data/kpis", response_model=list[KPIRow])
async def get_kpis(
    period: str = Query(default="2026-02"),
    entity_code: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    stmt = (
        select(
            Entity.code.label("entity_code"),
            KPI.kpi_name,
            KPI.kpi_value,
            KPI.kpi_target,
            KPI.unit,
            KPI.period,
        )
        .join(Entity, KPI.entity_id == Entity.id)
        .where(KPI.period == period)
        .order_by(Entity.code, KPI.kpi_name)
    )
    if entity_code:
        stmt = stmt.where(Entity.code == entity_code)
    result = await session.execute(stmt)
    return [
        KPIRow(
            entity_code=r.entity_code,
            kpi_name=r.kpi_name,
            value=float(r.kpi_value or 0),
            target=float(r.kpi_target) if r.kpi_target else None,
            unit=r.unit,
            period=r.period,
        )
        for r in result
    ]


@router.get("/api/data/stats", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_session)):
    return StatsResponse(
        entities=(await session.execute(select(func.count(Entity.id)))).scalar_one(),
        trial_balances=(await session.execute(select(func.count(TrialBalance.id)))).scalar_one(),
        intercompany_transactions=(await session.execute(select(func.count(IntercompanyTransaction.id)))).scalar_one(),
        exchange_rates=(await session.execute(select(func.count(ExchangeRate.id)))).scalar_one(),
        journal_entries=(await session.execute(select(func.count(JournalEntry.id)))).scalar_one(),
        budgets=(await session.execute(select(func.count(Budget.id)))).scalar_one(),
        kpis=(await session.execute(select(func.count(KPI.id)))).scalar_one(),
        documents=(await session.execute(select(func.count(Document.id)))).scalar_one(),
    )
