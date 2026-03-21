from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChartOfAccounts, Entity


async def seed_entities(session: AsyncSession) -> dict[str, int]:
    """Create the 3 NikkoGroup entities. Returns a code -> id mapping."""
    # NKG-JP first (parent)
    jp = Entity(
        code="NKG-JP",
        name="NikkoGroup Japan",
        country="Japan",
        currency="JPY",
        parent_id=None,
        ownership_pct=None,
    )
    session.add(jp)
    await session.flush()

    # Subsidiaries
    us = Entity(
        code="NKG-US",
        name="NikkoGroup US",
        country="United States",
        currency="USD",
        parent_id=jp.id,
        ownership_pct=Decimal("100.00"),
    )
    sg = Entity(
        code="NKG-SG",
        name="NikkoGroup Singapore",
        country="Singapore",
        currency="SGD",
        parent_id=jp.id,
        ownership_pct=Decimal("80.00"),
    )
    session.add_all([us, sg])
    await session.flush()

    return {"NKG-JP": jp.id, "NKG-US": us.id, "NKG-SG": sg.id}


async def seed_chart_of_accounts(session: AsyncSession) -> dict[str, int]:
    """Create the unified chart of accounts (~18 accounts). Returns a code -> id mapping."""
    accounts = [
        # P&L
        {"account_code": "4000", "account_name": "Revenue", "account_type": "revenue"},
        {"account_code": "5000", "account_name": "Cost of Goods Sold", "account_type": "expense"},
        {"account_code": "6100", "account_name": "Selling, General & Administrative", "account_type": "expense"},
        {"account_code": "6200", "account_name": "Consulting Fees", "account_type": "expense"},
        {"account_code": "6300", "account_name": "Other Operating Expenses", "account_type": "expense"},
        # Assets
        {"account_code": "1100", "account_name": "Cash & Equivalents", "account_type": "asset"},
        {"account_code": "1200", "account_name": "Accounts Receivable", "account_type": "asset"},
        {"account_code": "1300", "account_name": "Intercompany Receivable", "account_type": "asset"},
        {"account_code": "1400", "account_name": "Fixed Assets", "account_type": "asset"},
        {"account_code": "1500", "account_name": "Goodwill", "account_type": "asset"},
        {"account_code": "1600", "account_name": "Accumulated Depreciation", "account_type": "asset"},
        # Liabilities
        {"account_code": "2100", "account_name": "Accounts Payable", "account_type": "liability"},
        {"account_code": "2200", "account_name": "Intercompany Payable", "account_type": "liability"},
        {"account_code": "2300", "account_name": "Accrued Expenses", "account_type": "liability"},
        {"account_code": "2400", "account_name": "Deferred Revenue", "account_type": "liability"},
        # Equity
        {"account_code": "3100", "account_name": "Share Capital", "account_type": "equity"},
        {"account_code": "3200", "account_name": "Retained Earnings", "account_type": "equity"},
        {"account_code": "3300", "account_name": "Non-controlling Interest", "account_type": "equity"},
    ]

    await session.execute(insert(ChartOfAccounts), accounts)
    await session.flush()

    # Return code -> id mapping
    result = await session.execute(
        select(ChartOfAccounts.account_code, ChartOfAccounts.id)
    )
    return {row.account_code: row.id for row in result}
