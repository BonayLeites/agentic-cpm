from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ConfigResponse, KnowledgePackInfo, StatsResponse, ToolInfo
from app.db.models import (
    Budget,
    Document,
    Entity,
    ExchangeRate,
    IntercompanyTransaction,
    JournalEntry,
    KPI,
    TrialBalance,
)
from app.core.rules_engine import BUSINESS_RULES
from app.db.session import get_session

router = APIRouter(tags=["config"])

# Tools enabled per workflow_type
WORKFLOW_TOOLS = {
    "consolidation": [
        ToolInfo(name="get_trial_balances", description="Fetch trial balance data by entity and period"),
        ToolInfo(name="get_ic_transactions", description="Fetch intercompany transactions by period"),
        ToolInfo(name="get_exchange_rates", description="Fetch exchange rates by currency pair and date"),
        ToolInfo(name="match_ic_pairs", description="Match intercompany transaction pairs and detect mismatches"),
        ToolInfo(name="detect_anomalies", description="Statistical anomaly detection on financial data"),
        ToolInfo(name="search_documents", description="TF-IDF keyword search over knowledge pack documents"),
    ],
    "performance": [
        ToolInfo(name="get_trial_balances", description="Fetch trial balance data by entity and period"),
        ToolInfo(name="get_budgets", description="Fetch budget data by entity, account, and period"),
        ToolInfo(name="get_kpis", description="Fetch KPI values and targets by entity and period"),
        ToolInfo(name="get_exchange_rates", description="Fetch exchange rates by currency pair and date"),
        ToolInfo(name="detect_anomalies", description="Statistical anomaly detection on financial data"),
        ToolInfo(name="search_documents", description="TF-IDF keyword search over knowledge pack documents"),
    ],
}

# Knowledge packs filtered by workflow_type
WORKFLOW_DOC_TYPES = {
    "consolidation": {"policy", "notes", "rules"},
    "performance": {"commentary", "template", "benchmarks"},
}


@router.get("/api/config/{workflow_type}", response_model=ConfigResponse)
async def get_config(
    workflow_type: str,
    session: AsyncSession = Depends(get_session),
):
    if workflow_type not in BUSINESS_RULES:
        raise HTTPException(status_code=400, detail=f"Invalid workflow_type: {workflow_type}")

    # Entities
    result = await session.execute(select(Entity).order_by(Entity.id))
    entities = result.scalars().all()

    # Dataset counts
    counts = StatsResponse(
        entities=(await session.execute(select(func.count(Entity.id)))).scalar_one(),
        trial_balances=(await session.execute(select(func.count(TrialBalance.id)))).scalar_one(),
        intercompany_transactions=(await session.execute(select(func.count(IntercompanyTransaction.id)))).scalar_one(),
        exchange_rates=(await session.execute(select(func.count(ExchangeRate.id)))).scalar_one(),
        journal_entries=(await session.execute(select(func.count(JournalEntry.id)))).scalar_one(),
        budgets=(await session.execute(select(func.count(Budget.id)))).scalar_one(),
        kpis=(await session.execute(select(func.count(KPI.id)))).scalar_one(),
        documents=(await session.execute(select(func.count(Document.id)))).scalar_one(),
    )

    # Knowledge packs filtered by workflow type
    doc_types = WORKFLOW_DOC_TYPES[workflow_type]
    docs_result = await session.execute(
        select(Document.title, Document.doc_type)
        .where(Document.doc_type.in_(doc_types))
        .order_by(Document.id)
    )
    knowledge_packs = [
        KnowledgePackInfo(title=row.title, doc_type=row.doc_type)
        for row in docs_result
    ]

    return ConfigResponse(
        workflow_type=workflow_type,
        entities=entities,
        dataset_counts=counts,
        business_rules=BUSINESS_RULES[workflow_type],
        knowledge_packs=knowledge_packs,
        tools=WORKFLOW_TOOLS[workflow_type],
    )
