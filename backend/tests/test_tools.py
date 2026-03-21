"""Tests for framework tools (no LLM required).

These tests run tools directly against the seeded DB.
"""

import pytest

from app.core.tools.anomaly_detection import AnomalyDetectionTool
from app.core.tools.ic_matching import ICMatchingTool
from app.core.tools.parameterized_queries import GetTrialBalancesTool

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_parameterized_query_returns_data(db_session):
    """GetTrialBalancesTool returns rows for NKG-JP in 2026-02."""
    tool = GetTrialBalancesTool()
    result = await tool.execute(
        {"entity_codes": ["NKG-JP"], "period": "2026-02"},
        db_session,
    )
    rows = result["rows"]
    assert len(rows) >= 5
    assert all(r["entity_code"] == "NKG-JP" for r in rows)
    # Verify values were serialized correctly (float, not Decimal)
    assert isinstance(rows[0]["debit"], (int, float))


async def test_ic_matching_finds_mismatch(db_session):
    """ICMatchingTool detects the planted mismatch NKG-JP → NKG-SG."""
    tool = ICMatchingTool()
    result = await tool.execute({"period": "2026-02"}, db_session)

    assert result["total"] == 3
    assert result["matched"] >= 1
    mismatched = result["mismatched"]
    assert len(mismatched) >= 1

    # Planted mismatch: NKG-JP → NKG-SG, 5-day timing gap, JPY 3.3M mismatch
    sg_mismatch = [m for m in mismatched if m["to_entity"] == "NKG-SG"]
    assert len(sg_mismatch) >= 1
    assert sg_mismatch[0]["timing_gap_days"] == 5
    assert sg_mismatch[0]["amount_diff"] == 3_300_000.0


async def test_anomaly_detector_flags_outlier(db_session):
    """AnomalyDetectionTool detects the consulting fee spike in NKG-US."""
    tool = AnomalyDetectionTool()
    result = await tool.execute(
        {
            "entity_code": "NKG-US",
            "period": "2026-02",
            "comparison_period": "2026-01",
            "threshold_pct": 15.0,
        },
        db_session,
    )

    anomalies = result["anomalies"]
    assert len(anomalies) >= 1

    # Consulting fees (account 6200): Jan 195K → Feb 287K = +47.2%  (planted anomaly)
    consulting = [a for a in anomalies if a["account_code"] == "6200"]
    assert len(consulting) == 1
    assert consulting[0]["change_pct"] > 40
    assert consulting[0]["threshold_breached"] is True
