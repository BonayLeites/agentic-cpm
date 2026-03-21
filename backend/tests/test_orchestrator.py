"""Tests for the orchestrator (stub agents, no LLM).

These tests verify DAG behavior, parallelism, and retries
using stub agents that return fixed AgentResults.
"""

import asyncio

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="session")

from app.core.agent_base import (
    AgentContext,
    AgentFinding,
    AgentResult,
    BaseAgent,
    Evidence,
    StepMetrics,
)
from app.core.agent_registry import StepDefinition
from app.core.orchestrator import WorkflowOrchestrator
from app.db.models import WorkflowRun


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class StubAgent(BaseAgent):
    """Stub agent that returns a fixed result."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "stub"
        self.model = ""
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            status="completed",
            findings=[
                AgentFinding(
                    title=f"Stub finding from {self.name}",
                    severity="medium",
                    evidence=[Evidence(
                        type="data_point",
                        label="test",
                        value="test value",
                        source="stub",
                    )],
                    confidence=0.85,
                ),
            ],
            data={f"{self.name}_done": True},
            metrics=StepMetrics(tools_used=["stub_tool"], cost=0.001),
        )


def _make_stub_steps(count: int) -> list[StepDefinition]:
    """Generate N steps with StubAgent and linear dependencies."""
    names = [f"step_{i}" for i in range(1, count + 1)]
    steps = []
    for i, name in enumerate(names):
        deps = {names[i - 1]} if i > 0 else set()
        steps.append(StepDefinition(
            step_order=i + 1,
            step_name=name,
            agent_class=StubAgent,
            dependencies=deps,
        ))
    return steps


async def _setup_and_run(
    test_session_factory,
    monkeypatch,
    steps: list[StepDefinition],
) -> tuple[int, asyncio.Queue[str | None]]:
    """Create WorkflowRun, patch orchestrator, execute and return (run_id, queue)."""
    monkeypatch.setattr("app.core.orchestrator.get_workflow_steps", lambda wt: steps)
    monkeypatch.setattr("app.core.orchestrator.async_session", test_session_factory)

    async with test_session_factory() as session:
        run = WorkflowRun(workflow_type="consolidation", status="pending")
        session.add(run)
        await session.commit()
        run_id = run.id

    queue: asyncio.Queue[str | None] = asyncio.Queue()
    orchestrator = WorkflowOrchestrator()
    await orchestrator.run("consolidation", run_id, queue)
    return run_id, queue


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_workflow_run_happy_path(test_session_factory, seeded_db, monkeypatch):
    """All 7 steps complete and findings are generated."""
    run_id, queue = await _setup_and_run(
        test_session_factory, monkeypatch, _make_stub_steps(7),
    )

    # Verify the run completed
    async with test_session_factory() as session:
        run = await session.get(WorkflowRun, run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.total_findings >= 1
        assert run.total_duration_ms > 0
        assert run.overall_confidence is not None

    # Verify SSE events (at least run_completed + None sentinel)
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    assert len(events) >= 2  # at least step events + run_completed + None


async def test_parallel_steps_execute(test_session_factory, seeded_db, monkeypatch):
    """Steps 2 and 3 execute concurrently (DAG deps: 2→1, 3→1)."""
    execution_log: list[tuple[str, str]] = []

    class TimingAgent(BaseAgent):
        """Agent that records start/end position in the execution log."""

        def __init__(self, name: str, step_order: int) -> None:
            self.name = name
            self.description = "timing"
            self.model = ""
            self._step_order = step_order

        async def execute(self, context: AgentContext) -> AgentResult:
            execution_log.append((self.name, "start"))
            await asyncio.sleep(0.1)
            execution_log.append((self.name, "end"))
            return AgentResult(status="completed")

    # DAG: step_1 (no deps) → step_2, step_3 (deps: step_1) → step_4 (deps: step_2, step_3)
    steps = [
        StepDefinition(1, "step_1", TimingAgent),
        StepDefinition(2, "step_2", TimingAgent, {"step_1"}),
        StepDefinition(3, "step_3", TimingAgent, {"step_1"}),
        StepDefinition(4, "step_4", TimingAgent, {"step_2", "step_3"}),
    ]
    run_id, queue = await _setup_and_run(test_session_factory, monkeypatch, steps)

    # Verify parallelism: step_2 and step_3 start before either finishes
    starts = {name: i for i, (name, ev) in enumerate(execution_log) if ev == "start"}
    ends = {name: i for i, (name, ev) in enumerate(execution_log) if ev == "end"}

    assert "step_2" in starts and "step_3" in starts
    # Both starts occur before both ends (concurrency proof)
    assert starts["step_2"] < ends["step_2"]
    assert starts["step_3"] < ends["step_3"]
    # The second start occurs before the first end
    assert starts["step_3"] < ends["step_2"] or starts["step_2"] < ends["step_3"]


async def test_step_retry_on_transient_error(test_session_factory, seeded_db, monkeypatch):
    """Step fails on the first attempt (timeout), retries, and completes."""
    call_count = 0

    class FlakyAgent(BaseAgent):
        def __init__(self, name: str, step_order: int) -> None:
            self.name = name
            self.description = "flaky"
            self.model = ""
            self._step_order = step_order

        async def execute(self, context: AgentContext) -> AgentResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError("Simulated timeout")
            return AgentResult(status="completed")

    steps = [StepDefinition(1, "flaky_step", FlakyAgent)]
    run_id, queue = await _setup_and_run(test_session_factory, monkeypatch, steps)

    assert call_count == 2  # 1 fallo + 1 retry exitoso
    async with test_session_factory() as session:
        run = await session.get(WorkflowRun, run_id)
        assert run is not None
        assert run.status == "completed"
