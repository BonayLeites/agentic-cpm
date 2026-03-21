from datetime import date
from decimal import Decimal

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ExchangeRate,
    IntercompanyTransaction,
    JournalEntry,
    JournalEntryLine,
    TrialBalance,
)


async def seed_case1_data(
    session: AsyncSession,
    entity_ids: dict[str, int],
    account_ids: dict[str, int],
) -> None:
    """Seed data for Case 1: Pre-Close & Consolidation Review (Feb 2026)."""
    await _seed_trial_balances(session, entity_ids, account_ids)
    await _seed_exchange_rates(session)
    await _seed_ic_transactions(session, entity_ids)
    await _seed_journal_entries(session, entity_ids, account_ids)
    await session.flush()


async def _seed_trial_balances(
    session: AsyncSession,
    entities: dict[str, int],
    accounts: dict[str, int],
) -> None:
    """Trial balances for Jan and Feb 2026 (3 entities x 5 P&L accounts x 2 months)."""
    jp = entities["NKG-JP"]
    us = entities["NKG-US"]
    sg = entities["NKG-SG"]

    rev = accounts["4000"]
    cogs = accounts["5000"]
    sga = accounts["6100"]
    consulting = accounts["6200"]
    other = accounts["6300"]

    rows = [
        # === Feb 2026 ===
        # NKG-JP (JPY) — GM 50.0%
        {"entity_id": jp, "account_id": rev, "period": "2026-02", "debit": 0, "credit": Decimal("850000000")},
        {"entity_id": jp, "account_id": cogs, "period": "2026-02", "debit": Decimal("425000000"), "credit": 0},
        {"entity_id": jp, "account_id": sga, "period": "2026-02", "debit": Decimal("180000000"), "credit": 0},
        {"entity_id": jp, "account_id": consulting, "period": "2026-02", "debit": Decimal("25000000"), "credit": 0},
        {"entity_id": jp, "account_id": other, "period": "2026-02", "debit": Decimal("35000000"), "credit": 0},
        # NKG-US (USD) — GM 50.0%
        {"entity_id": us, "account_id": rev, "period": "2026-02", "debit": 0, "credit": Decimal("2400000")},
        {"entity_id": us, "account_id": cogs, "period": "2026-02", "debit": Decimal("1200000"), "credit": 0},
        {"entity_id": us, "account_id": sga, "period": "2026-02", "debit": Decimal("620000"), "credit": 0},
        {"entity_id": us, "account_id": consulting, "period": "2026-02", "debit": Decimal("287000"), "credit": 0},
        {"entity_id": us, "account_id": other, "period": "2026-02", "debit": Decimal("48000"), "credit": 0},
        # NKG-SG (SGD) — GM 45.0%
        {"entity_id": sg, "account_id": rev, "period": "2026-02", "debit": 0, "credit": Decimal("1200000")},
        {"entity_id": sg, "account_id": cogs, "period": "2026-02", "debit": Decimal("660000"), "credit": 0},
        {"entity_id": sg, "account_id": sga, "period": "2026-02", "debit": Decimal("280000"), "credit": 0},
        {"entity_id": sg, "account_id": consulting, "period": "2026-02", "debit": Decimal("45000"), "credit": 0},
        {"entity_id": sg, "account_id": other, "period": "2026-02", "debit": Decimal("22000"), "credit": 0},

        # === Jan 2026 ===
        # NKG-JP (JPY) — similar to Feb
        {"entity_id": jp, "account_id": rev, "period": "2026-01", "debit": 0, "credit": Decimal("830000000")},
        {"entity_id": jp, "account_id": cogs, "period": "2026-01", "debit": Decimal("415000000"), "credit": 0},
        {"entity_id": jp, "account_id": sga, "period": "2026-01", "debit": Decimal("176000000"), "credit": 0},
        {"entity_id": jp, "account_id": consulting, "period": "2026-01", "debit": Decimal("24000000"), "credit": 0},
        {"entity_id": jp, "account_id": other, "period": "2026-01", "debit": Decimal("33000000"), "credit": 0},
        # NKG-US (USD) — consulting 195K (vs 287K in Feb = +47%)
        {"entity_id": us, "account_id": rev, "period": "2026-01", "debit": 0, "credit": Decimal("2350000")},
        {"entity_id": us, "account_id": cogs, "period": "2026-01", "debit": Decimal("1175000"), "credit": 0},
        {"entity_id": us, "account_id": sga, "period": "2026-01", "debit": Decimal("610000"), "credit": 0},
        {"entity_id": us, "account_id": consulting, "period": "2026-01", "debit": Decimal("195000"), "credit": 0},
        {"entity_id": us, "account_id": other, "period": "2026-01", "debit": Decimal("45000"), "credit": 0},
        # NKG-SG (SGD) — GM 48.2% => rev 1,180K, COGS 611K
        {"entity_id": sg, "account_id": rev, "period": "2026-01", "debit": 0, "credit": Decimal("1180000")},
        {"entity_id": sg, "account_id": cogs, "period": "2026-01", "debit": Decimal("611240"), "credit": 0},
        {"entity_id": sg, "account_id": sga, "period": "2026-01", "debit": Decimal("272000"), "credit": 0},
        {"entity_id": sg, "account_id": consulting, "period": "2026-01", "debit": Decimal("42000"), "credit": 0},
        {"entity_id": sg, "account_id": other, "period": "2026-01", "debit": Decimal("21000"), "credit": 0},
    ]

    await session.execute(insert(TrialBalance), rows)


async def _seed_exchange_rates(session: AsyncSession) -> None:
    """Exchange rates for Jan and Feb 2026."""
    rows = [
        # Feb 2026
        {"from_currency": "USD", "to_currency": "JPY", "rate_type": "average", "rate": Decimal("147.000000"), "effective_date": date(2026, 2, 28)},
        {"from_currency": "USD", "to_currency": "JPY", "rate_type": "closing", "rate": Decimal("148.500000"), "effective_date": date(2026, 2, 28)},
        {"from_currency": "SGD", "to_currency": "JPY", "rate_type": "average", "rate": Decimal("112.800000"), "effective_date": date(2026, 2, 28)},
        {"from_currency": "SGD", "to_currency": "JPY", "rate_type": "closing", "rate": Decimal("115.300000"), "effective_date": date(2026, 2, 28)},
        # Jan 2026
        {"from_currency": "USD", "to_currency": "JPY", "rate_type": "average", "rate": Decimal("146.500000"), "effective_date": date(2026, 1, 31)},
        {"from_currency": "USD", "to_currency": "JPY", "rate_type": "closing", "rate": Decimal("147.200000"), "effective_date": date(2026, 1, 31)},
        {"from_currency": "SGD", "to_currency": "JPY", "rate_type": "average", "rate": Decimal("112.200000"), "effective_date": date(2026, 1, 31)},
        {"from_currency": "SGD", "to_currency": "JPY", "rate_type": "closing", "rate": Decimal("113.100000"), "effective_date": date(2026, 1, 31)},
    ]

    await session.execute(insert(ExchangeRate), rows)


async def _seed_ic_transactions(
    session: AsyncSession,
    entities: dict[str, int],
) -> None:
    """3 intercompany transactions for Feb 2026. One has a cut-off timing mismatch."""
    jp = entities["NKG-JP"]
    us = entities["NKG-US"]
    sg = entities["NKG-SG"]

    rows = [
        # NKG-JP → NKG-US: Services, matching OK
        {
            "from_entity_id": jp,
            "to_entity_id": us,
            "transaction_type": "services",
            "amount": Decimal("15000000"),
            "currency": "JPY",
            "period": "2026-02",
            "invoice_date": date(2026, 1, 25),
            "recorded_date": date(2026, 1, 25),
            "from_amount": Decimal("15000000"),
            "to_amount": Decimal("102000"),
            "to_amount_jpy": Decimal("15100000"),
            "mismatch_amount": Decimal("0"),
        },
        # NKG-JP → NKG-SG: Services, MISMATCH — cut-off timing (5 days)
        {
            "from_entity_id": jp,
            "to_entity_id": sg,
            "transaction_type": "services",
            "amount": Decimal("45200000"),
            "currency": "JPY",
            "period": "2026-02",
            "invoice_date": date(2026, 1, 28),
            "recorded_date": date(2026, 2, 2),
            "from_amount": Decimal("45200000"),
            "to_amount": Decimal("395000"),
            "to_amount_jpy": Decimal("45500000"),
            "mismatch_amount": Decimal("3300000"),
        },
        # NKG-US → NKG-JP: Royalties, matching OK
        {
            "from_entity_id": us,
            "to_entity_id": jp,
            "transaction_type": "royalties",
            "amount": Decimal("50000"),
            "currency": "USD",
            "period": "2026-02",
            "invoice_date": date(2026, 2, 5),
            "recorded_date": date(2026, 2, 5),
            "from_amount": Decimal("50000"),
            "to_amount": Decimal("7350000"),
            "to_amount_jpy": Decimal("7350000"),
            "mismatch_amount": Decimal("0"),
        },
    ]

    await session.execute(insert(IntercompanyTransaction), rows)


async def _seed_journal_entries(
    session: AsyncSession,
    entities: dict[str, int],
    accounts: dict[str, int],
) -> None:
    """JE-2026-0287: Goodwill adjustment JPY 12.8M."""
    je = JournalEntry(
        entry_number="JE-2026-0287",
        entity_id=entities["NKG-JP"],
        period="2026-02",
        entry_date=date(2026, 2, 28),
        description="Year-end goodwill adjustment — annual impairment test NKG-SG acquisition",
        posted_by="System",
    )
    session.add(je)
    await session.flush()

    lines = [
        {
            "journal_entry_id": je.id,
            "account_id": accounts["1500"],  # Goodwill
            "debit": Decimal("12800000"),
            "credit": Decimal("0"),
            "description": "Goodwill impairment — NKG-SG acquisition",
        },
        {
            "journal_entry_id": je.id,
            "account_id": accounts["3200"],  # Retained Earnings
            "debit": Decimal("0"),
            "credit": Decimal("12800000"),
            "description": "Equity adjustment for goodwill impairment",
        },
    ]

    await session.execute(insert(JournalEntryLine), lines)
