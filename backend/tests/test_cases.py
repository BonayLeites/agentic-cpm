"""End-to-end tests for both workflows with real agents and mocked LLM.

These tests run the full workflows (real DataLoader against DB,
LLM-based agents with mock responses). They verify that findings
are correctly persisted to DB.
"""

import asyncio

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")
from unittest.mock import AsyncMock

from sqlalchemy import select

from app.core.orchestrator import WorkflowOrchestrator
from app.db.models import Finding, WorkflowRun

from tests.conftest import make_llm_response
from tests.mock_llm_responses import (
    analysis_consolidation_response,
    analysis_performance_response,
    anomaly_detect_response,
    ic_check_response,
    kpi_analysis_response,
    narrative_response,
    quality_gate_response,
    variance_analyzer_response,
)


# ---------------------------------------------------------------------------
# LLM side_effect dispatchers
# ---------------------------------------------------------------------------

def _consolidation_side_effect(messages, **kwargs):
    """Dispatch mock response based on the agent's system prompt."""
    system = messages[0]["content"].lower() if messages else ""

    if kwargs.get("response_format"):
        # AnalysisAgent usa response_format=json_object
        content = analysis_consolidation_response()
    elif "anomaly" in system or "statistical" in system:
        content = anomaly_detect_response()
    elif "intercompany" in system:
        content = ic_check_response()
    elif ("quality" in system) or ("coherence" in system) or ("review" in system and "finding" in system):
        content = quality_gate_response()
    else:
        content = narrative_response()

    return make_llm_response(content)


def _performance_side_effect(messages, **kwargs):
    """Dispatch mock response for the performance workflow."""
    system = messages[0]["content"].lower() if messages else ""

    if kwargs.get("response_format"):
        content = analysis_performance_response()
    elif "variance" in system or "budget vs actual" in system:
        content = variance_analyzer_response()
    elif "kpi" in system:
        content = kpi_analysis_response()
    elif "quality" in system or "coherence" in system or "review" in system and "finding" in system:
        content = quality_gate_response()
    else:
        content = narrative_response()

    return make_llm_response(content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _run_workflow(
    test_session_factory,
    monkeypatch,
    workflow_type: str,
    side_effect,
) -> int:
    """Create a run, patch LLM and session, execute the workflow."""
    mock_gateway = AsyncMock()
    mock_gateway.complete = AsyncMock(side_effect=side_effect)
    monkeypatch.setattr("app.llm.gateway._gateway", mock_gateway)
    monkeypatch.setattr("app.core.orchestrator.async_session", test_session_factory)

    async with test_session_factory() as session:
        run = WorkflowRun(workflow_type=workflow_type, status="pending")
        session.add(run)
        await session.commit()
        run_id = run.id

    queue: asyncio.Queue[str | None] = asyncio.Queue()
    orchestrator = WorkflowOrchestrator()
    await orchestrator.run(workflow_type, run_id, queue)

    return run_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_case1_produces_3_findings(test_session_factory, seeded_db, monkeypatch):
    """Case 1 (consolidation) produces at least 3 findings."""
    run_id = await _run_workflow(
        test_session_factory, monkeypatch, "consolidation", _consolidation_side_effect,
    )

    async with test_session_factory() as session:
        run = await session.get(WorkflowRun, run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.total_findings >= 3


async def test_case2_produces_4_findings(test_session_factory, seeded_db, monkeypatch):
    """Case 2 (performance) produces at least 4 findings."""
    run_id = await _run_workflow(
        test_session_factory, monkeypatch, "performance", _performance_side_effect,
    )

    async with test_session_factory() as session:
        run = await session.get(WorkflowRun, run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.total_findings >= 4


async def test_findings_have_evidence(test_session_factory, seeded_db, monkeypatch):
    """All findings have at least 1 evidence item."""
    run_id = await _run_workflow(
        test_session_factory, monkeypatch, "consolidation", _consolidation_side_effect,
    )

    async with test_session_factory() as session:
        findings = (
            await session.execute(select(Finding).where(Finding.run_id == run_id))
        ).scalars().all()

        assert len(findings) >= 1
        for finding in findings:
            assert finding.evidence is not None
            assert len(finding.evidence) >= 1
            # Each evidence item has at least type, label, value
            for ev in finding.evidence:
                assert "type" in ev
                assert "label" in ev
                assert "value" in ev
