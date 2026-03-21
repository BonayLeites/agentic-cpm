from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tools.base import BaseTool
from app.db.models import Entity, IntercompanyTransaction


class ICMatchingTool(BaseTool):
    """Match IC transactions, convert to JPY, and calculate mismatches."""

    name = "match_ic_pairs"
    description = "Match intercompany transaction pairs and detect mismatches"

    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        period: str = params["period"]

        from_entity = Entity.__table__.alias("from_entity")
        to_entity = Entity.__table__.alias("to_entity")

        stmt = (
            select(
                from_entity.c.code.label("from_entity"),
                to_entity.c.code.label("to_entity"),
                IntercompanyTransaction.transaction_type,
                IntercompanyTransaction.from_amount,
                IntercompanyTransaction.to_amount,
                IntercompanyTransaction.to_amount_jpy,
                IntercompanyTransaction.mismatch_amount,
                IntercompanyTransaction.invoice_date,
                IntercompanyTransaction.recorded_date,
                IntercompanyTransaction.currency,
            )
            .join(from_entity, IntercompanyTransaction.from_entity_id == from_entity.c.id)
            .join(to_entity, IntercompanyTransaction.to_entity_id == to_entity.c.id)
            .where(IntercompanyTransaction.period == period)
            .order_by(IntercompanyTransaction.id)
        )

        result = await session.execute(stmt)

        matched_count = 0
        total = 0
        mismatched: list[dict[str, Any]] = []

        for row in result:
            total += 1
            from_amount = float(row.from_amount) if row.from_amount else 0.0
            mismatch = float(row.mismatch_amount) if row.mismatch_amount else 0.0

            pct_diff = (abs(mismatch) / from_amount * 100) if from_amount > 0 else 0.0
            pct_diff = round(pct_diff, 2)

            timing_gap_days = 0
            if row.invoice_date and row.recorded_date:
                timing_gap_days = abs((row.recorded_date - row.invoice_date).days)

            if mismatch != 0.0 or timing_gap_days > 0:
                mismatched.append({
                    "from_entity": row.from_entity,
                    "to_entity": row.to_entity,
                    "transaction_type": row.transaction_type,
                    "from_amount": from_amount,
                    "to_amount_jpy": float(row.to_amount_jpy) if row.to_amount_jpy else 0.0,
                    "amount_diff": mismatch,
                    "pct_diff": pct_diff,
                    "timing_gap_days": timing_gap_days,
                    "invoice_date": row.invoice_date.isoformat() if row.invoice_date else None,
                    "recorded_date": row.recorded_date.isoformat() if row.recorded_date else None,
                })
            else:
                matched_count += 1

        return {
            "matched": matched_count,
            "mismatched": mismatched,
            "total": total,
        }
