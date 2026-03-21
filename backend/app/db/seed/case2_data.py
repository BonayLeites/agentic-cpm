from decimal import Decimal

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Budget, KPI, TrialBalance


async def seed_case2_data(
    session: AsyncSession,
    entity_ids: dict[str, int],
    account_ids: dict[str, int],
) -> None:
    """Seed data for Case 2: Executive Performance Review (Q1 2026)."""
    await _seed_budgets(session, entity_ids, account_ids)
    await _seed_q1_actuals(session, entity_ids, account_ids)
    await _seed_kpis(session, entity_ids)
    await session.flush()


async def _seed_budgets(
    session: AsyncSession,
    entities: dict[str, int],
    accounts: dict[str, int],
) -> None:
    """FY2026 Q1 budgets (3 months x 3 entities x 5 P&L accounts)."""
    jp = entities["NKG-JP"]
    us = entities["NKG-US"]
    sg = entities["NKG-SG"]

    rev = accounts["4000"]
    cogs = accounts["5000"]
    sga = accounts["6100"]
    consulting = accounts["6200"]
    other = accounts["6300"]

    # Monthly budget per entity
    budget_data = {
        jp: [
            (rev, Decimal("800000000")),
            (cogs, Decimal("400000000")),
            (sga, Decimal("175000000")),
            (consulting, Decimal("22000000")),
            (other, Decimal("33000000")),
        ],
        us: [
            (rev, Decimal("2400000")),
            (cogs, Decimal("1200000")),
            (sga, Decimal("600000")),
            (consulting, Decimal("200000")),
            (other, Decimal("45000")),
        ],
        sg: [
            (rev, Decimal("1200000")),
            (cogs, Decimal("648000")),
            (sga, Decimal("270000")),
            (consulting, Decimal("40000")),
            (other, Decimal("20000")),
        ],
    }

    rows = []
    for entity_id, account_amounts in budget_data.items():
        for period in ["2026-01", "2026-02", "2026-03"]:
            for account_id, amount in account_amounts:
                rows.append({
                    "entity_id": entity_id,
                    "account_id": account_id,
                    "period": period,
                    "amount": amount,
                })

    await session.execute(insert(Budget), rows)


async def _seed_q1_actuals(
    session: AsyncSession,
    entities: dict[str, int],
    accounts: dict[str, int],
) -> None:
    """Actual trial balances for Mar 2026 (Jan and Feb are already in case1_data)."""
    jp = entities["NKG-JP"]
    us = entities["NKG-US"]
    sg = entities["NKG-SG"]

    rev = accounts["4000"]
    cogs = accounts["5000"]
    sga = accounts["6100"]
    consulting = accounts["6200"]
    other = accounts["6300"]

    # Mar 2026 — continues trend from spec
    # NKG-JP: revenue +5% vs budget (840M vs 800M budget)
    # NKG-US: revenue -1.4% vs budget (slight underperform)
    # NKG-SG: revenue -3.3% vs budget, margin erosion continues
    rows = [
        # NKG-JP (JPY) — Mar 2026, strong
        {"entity_id": jp, "account_id": rev, "period": "2026-03", "debit": 0, "credit": Decimal("840000000")},
        {"entity_id": jp, "account_id": cogs, "period": "2026-03", "debit": Decimal("411600000"), "credit": 0},  # 51% GM
        {"entity_id": jp, "account_id": sga, "period": "2026-03", "debit": Decimal("178000000"), "credit": 0},
        {"entity_id": jp, "account_id": consulting, "period": "2026-03", "debit": Decimal("24000000"), "credit": 0},
        {"entity_id": jp, "account_id": other, "period": "2026-03", "debit": Decimal("34000000"), "credit": 0},

        # NKG-US (USD) — Mar 2026, under pressure
        {"entity_id": us, "account_id": rev, "period": "2026-03", "debit": 0, "credit": Decimal("2350000")},
        {"entity_id": us, "account_id": cogs, "period": "2026-03", "debit": Decimal("1198500"), "credit": 0},  # 49.0% GM
        {"entity_id": us, "account_id": sga, "period": "2026-03", "debit": Decimal("615000"), "credit": 0},
        {"entity_id": us, "account_id": consulting, "period": "2026-03", "debit": Decimal("280000"), "credit": 0},
        {"entity_id": us, "account_id": other, "period": "2026-03", "debit": Decimal("47000"), "credit": 0},

        # NKG-SG (SGD) — Mar 2026, margin erosion continues
        {"entity_id": sg, "account_id": rev, "period": "2026-03", "debit": 0, "credit": Decimal("1100000")},
        {"entity_id": sg, "account_id": cogs, "period": "2026-03", "debit": Decimal("643500"), "credit": 0},  # 41.5% GM
        {"entity_id": sg, "account_id": sga, "period": "2026-03", "debit": Decimal("275000"), "credit": 0},
        {"entity_id": sg, "account_id": consulting, "period": "2026-03", "debit": Decimal("44000"), "credit": 0},
        {"entity_id": sg, "account_id": other, "period": "2026-03", "debit": Decimal("22000"), "credit": 0},
    ]

    await session.execute(insert(TrialBalance), rows)


async def _seed_kpis(
    session: AsyncSession,
    entities: dict[str, int],
) -> None:
    """KPIs for Jan and Feb 2026 (3 entities x 6 KPIs x 2 months)."""
    jp = entities["NKG-JP"]
    us = entities["NKG-US"]
    sg = entities["NKG-SG"]

    rows = [
        # === Feb 2026 ===
        # NKG-JP
        {"entity_id": jp, "kpi_name": "mrr", "kpi_value": Decimal("85000000"), "kpi_target": None, "period": "2026-02", "unit": "JPY"},
        {"entity_id": jp, "kpi_name": "churn_rate", "kpi_value": Decimal("1.2"), "kpi_target": Decimal("2.5"), "period": "2026-02", "unit": "pct"},
        {"entity_id": jp, "kpi_name": "nps", "kpi_value": Decimal("72"), "kpi_target": Decimal("65"), "period": "2026-02", "unit": "score"},
        {"entity_id": jp, "kpi_name": "utilization", "kpi_value": Decimal("78"), "kpi_target": Decimal("75"), "period": "2026-02", "unit": "pct"},
        {"entity_id": jp, "kpi_name": "dso", "kpi_value": Decimal("45"), "kpi_target": Decimal("50"), "period": "2026-02", "unit": "days"},
        {"entity_id": jp, "kpi_name": "headcount", "kpi_value": Decimal("320"), "kpi_target": None, "period": "2026-02", "unit": "count"},

        # NKG-US — churn 4.8% > 2.5% target, DSO 58 > 50 target
        {"entity_id": us, "kpi_name": "mrr", "kpi_value": Decimal("580000"), "kpi_target": None, "period": "2026-02", "unit": "USD"},
        {"entity_id": us, "kpi_name": "churn_rate", "kpi_value": Decimal("4.8"), "kpi_target": Decimal("2.5"), "period": "2026-02", "unit": "pct"},
        {"entity_id": us, "kpi_name": "nps", "kpi_value": Decimal("68"), "kpi_target": Decimal("65"), "period": "2026-02", "unit": "score"},
        {"entity_id": us, "kpi_name": "utilization", "kpi_value": Decimal("82"), "kpi_target": Decimal("75"), "period": "2026-02", "unit": "pct"},
        {"entity_id": us, "kpi_name": "dso", "kpi_value": Decimal("58"), "kpi_target": Decimal("50"), "period": "2026-02", "unit": "days"},
        {"entity_id": us, "kpi_name": "headcount", "kpi_value": Decimal("185"), "kpi_target": None, "period": "2026-02", "unit": "count"},

        # NKG-SG
        {"entity_id": sg, "kpi_name": "mrr", "kpi_value": Decimal("290000"), "kpi_target": None, "period": "2026-02", "unit": "SGD"},
        {"entity_id": sg, "kpi_name": "churn_rate", "kpi_value": Decimal("2.1"), "kpi_target": Decimal("2.5"), "period": "2026-02", "unit": "pct"},
        {"entity_id": sg, "kpi_name": "nps", "kpi_value": Decimal("61"), "kpi_target": Decimal("65"), "period": "2026-02", "unit": "score"},
        {"entity_id": sg, "kpi_name": "utilization", "kpi_value": Decimal("71"), "kpi_target": Decimal("75"), "period": "2026-02", "unit": "pct"},
        {"entity_id": sg, "kpi_name": "dso", "kpi_value": Decimal("52"), "kpi_target": Decimal("50"), "period": "2026-02", "unit": "days"},
        {"entity_id": sg, "kpi_name": "headcount", "kpi_value": Decimal("95"), "kpi_target": None, "period": "2026-02", "unit": "count"},

        # === Jan 2026 (trend: NKG-US churn rising, DSO rising) ===
        # NKG-JP
        {"entity_id": jp, "kpi_name": "mrr", "kpi_value": Decimal("83000000"), "kpi_target": None, "period": "2026-01", "unit": "JPY"},
        {"entity_id": jp, "kpi_name": "churn_rate", "kpi_value": Decimal("1.1"), "kpi_target": Decimal("2.5"), "period": "2026-01", "unit": "pct"},
        {"entity_id": jp, "kpi_name": "nps", "kpi_value": Decimal("73"), "kpi_target": Decimal("65"), "period": "2026-01", "unit": "score"},
        {"entity_id": jp, "kpi_name": "utilization", "kpi_value": Decimal("77"), "kpi_target": Decimal("75"), "period": "2026-01", "unit": "pct"},
        {"entity_id": jp, "kpi_name": "dso", "kpi_value": Decimal("44"), "kpi_target": Decimal("50"), "period": "2026-01", "unit": "days"},
        {"entity_id": jp, "kpi_name": "headcount", "kpi_value": Decimal("318"), "kpi_target": None, "period": "2026-01", "unit": "count"},

        # NKG-US — churn escalating (3.2 → 4.8), DSO rising (53 → 58)
        {"entity_id": us, "kpi_name": "mrr", "kpi_value": Decimal("595000"), "kpi_target": None, "period": "2026-01", "unit": "USD"},
        {"entity_id": us, "kpi_name": "churn_rate", "kpi_value": Decimal("3.2"), "kpi_target": Decimal("2.5"), "period": "2026-01", "unit": "pct"},
        {"entity_id": us, "kpi_name": "nps", "kpi_value": Decimal("70"), "kpi_target": Decimal("65"), "period": "2026-01", "unit": "score"},
        {"entity_id": us, "kpi_name": "utilization", "kpi_value": Decimal("81"), "kpi_target": Decimal("75"), "period": "2026-01", "unit": "pct"},
        {"entity_id": us, "kpi_name": "dso", "kpi_value": Decimal("53"), "kpi_target": Decimal("50"), "period": "2026-01", "unit": "days"},
        {"entity_id": us, "kpi_name": "headcount", "kpi_value": Decimal("183"), "kpi_target": None, "period": "2026-01", "unit": "count"},

        # NKG-SG
        {"entity_id": sg, "kpi_name": "mrr", "kpi_value": Decimal("285000"), "kpi_target": None, "period": "2026-01", "unit": "SGD"},
        {"entity_id": sg, "kpi_name": "churn_rate", "kpi_value": Decimal("1.9"), "kpi_target": Decimal("2.5"), "period": "2026-01", "unit": "pct"},
        {"entity_id": sg, "kpi_name": "nps", "kpi_value": Decimal("63"), "kpi_target": Decimal("65"), "period": "2026-01", "unit": "score"},
        {"entity_id": sg, "kpi_name": "utilization", "kpi_value": Decimal("73"), "kpi_target": Decimal("75"), "period": "2026-01", "unit": "pct"},
        {"entity_id": sg, "kpi_name": "dso", "kpi_value": Decimal("50"), "kpi_target": Decimal("50"), "period": "2026-01", "unit": "days"},
        {"entity_id": sg, "kpi_name": "headcount", "kpi_value": Decimal("93"), "kpi_target": None, "period": "2026-01", "unit": "count"},
    ]

    await session.execute(insert(KPI), rows)
