import asyncio
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal

from app.api.sse import format_sse_event
from app.core.agent_base import AgentContext, AgentResult, StepMetrics
from app.core.agent_registry import get_workflow_steps, StepDefinition
from app.core.confidence import ConfidenceScorer
from app.core.dag import SimpleDAG
from app.core.event_bus import remove_queue
from app.core.memory import WorkflowMemory
from app.core.rules_engine import get_rules
from app.db.models import Finding, WorkflowRun, WorkflowStep
from app.db.session import async_session

logger = logging.getLogger(__name__)

# Global set to keep references to background tasks (prevents premature GC)
_background_tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]


def _utcnow() -> datetime:
    """UTC datetime without timezone (compatible with timezone-naive DateTime columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _to_decimal(value: float, places: int = 2) -> Decimal:
    """Convert float to Decimal with controlled precision."""
    return Decimal(str(round(value, places)))


def launch_workflow(
    workflow_type: str,
    run_id: int,
    queue: asyncio.Queue[str | None],
    language: str = "en",
) -> None:
    """Launch the orchestrator as a background task with a safe reference."""
    orchestrator = WorkflowOrchestrator()
    task = asyncio.create_task(orchestrator.run(workflow_type, run_id, queue, language))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


class WorkflowOrchestrator:
    """Execute a full workflow: DAG loop, retries, SSE streaming, persistence."""

    def __init__(self) -> None:
        self.scorer = ConfidenceScorer()

    async def run(
        self,
        workflow_type: str,
        run_id: int,
        event_queue: asyncio.Queue[str | None],
        language: str = "en",
    ) -> None:
        """Run the workflow as a background task."""
        run_start = time.monotonic()

        try:
            await self._execute_workflow(workflow_type, run_id, event_queue, run_start, language)
        except Exception:
            logger.exception("Error fatal en workflow run_id=%d", run_id)
            try:
                async with async_session() as session:
                    run_record = await session.get(WorkflowRun, run_id)
                    if run_record:
                        run_record.status = "failed"
                        run_record.completed_at = _utcnow()
                        await session.commit()
            except Exception:
                logger.exception("No se pudo marcar run %d como failed", run_id)

            await event_queue.put(
                format_sse_event("run_completed", {
                    "run_id": run_id,
                    "status": "failed",
                    "total_duration_ms": int((time.monotonic() - run_start) * 1000),
                    "total_findings": 0,
                    "overall_confidence": 0,
                })
            )
        finally:
            await event_queue.put(None)

    async def _execute_workflow(
        self,
        workflow_type: str,
        run_id: int,
        event_queue: asyncio.Queue[str | None],
        run_start: float,
        language: str = "en",
    ) -> None:
        # Prepare steps, DAG, and rules
        step_defs = get_workflow_steps(workflow_type)
        graph = {s.step_name: set(s.dependencies) for s in step_defs}
        dag = SimpleDAG(graph)
        rules = get_rules(workflow_type)

        step_id_map: dict[str, int] = {}

        async with async_session() as session:
            run_record = await session.get(WorkflowRun, run_id)
            if not run_record:
                raise ValueError(f"WorkflowRun {run_id} no encontrado")

            run_record.status = "running"
            run_record.started_at = _utcnow()
            run_record.config_snapshot = rules

            for sd in step_defs:
                ws = WorkflowStep(
                    run_id=run_id,
                    step_order=sd.step_order,
                    agent_name=sd.step_name,
                    status="queued",
                )
                session.add(ws)

            await session.flush()
            await session.refresh(run_record, ["steps"])
            for ws in run_record.steps:
                step_id_map[ws.agent_name] = ws.id
            await session.commit()

        # Build agent context
        memory = WorkflowMemory()
        context = AgentContext(
            run_id=run_id,
            workflow_type=workflow_type,
            config=rules,
            session_factory=async_session,
            memory=memory,
            language=language,
        )

        # DAG execution loop
        completed: set[str] = set()
        step_scores: list[float] = [0.0] * len(step_defs)
        total_findings = 0
        total_cost = 0.0
        step_def_map = {sd.step_name: sd for sd in step_defs}

        while len(completed) < len(graph):
            ready_names = dag.get_ready_steps(completed)

            tasks = [
                self._run_step_with_retry(
                    step_def=step_def_map[name],
                    step_id=step_id_map[name],
                    context=context,
                    event_queue=event_queue,
                )
                for name in ready_names
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for name, result in zip(ready_names, results):
                sd = step_def_map[name]
                if isinstance(result, Exception):
                    logger.error("Step %s failed: %s", name, result)
                    step_scores[sd.step_order - 1] = 0.0
                else:
                    step_scores[sd.step_order - 1] = result.metrics.confidence_score
                    total_findings += result.metrics.finding_count
                    total_cost += result.metrics.cost
                    await memory.update(result.data)

                completed.add(name)

        # Compute final metrics and update run record
        overall_confidence = self.scorer.score_run(step_scores)
        total_duration_ms = int((time.monotonic() - run_start) * 1000)

        async with async_session() as session:
            run_record = await session.get(WorkflowRun, run_id)
            if run_record:
                run_record.status = "completed"
                run_record.completed_at = _utcnow()
                run_record.total_duration_ms = total_duration_ms
                run_record.total_findings = total_findings
                run_record.total_cost = _to_decimal(total_cost, 4)
                run_record.overall_confidence = _to_decimal(overall_confidence * 100, 2)
                await session.commit()

        await event_queue.put(
            format_sse_event("run_completed", {
                "run_id": run_id,
                "status": "completed",
                "total_duration_ms": total_duration_ms,
                "total_findings": total_findings,
                "overall_confidence": round(overall_confidence * 100, 2),
            })
        )

    async def _run_step_with_retry(
        self,
        step_def: StepDefinition,
        step_id: int,
        context: AgentContext,
        event_queue: asyncio.Queue[str | None],
        max_retries: int = 2,
        timeout_seconds: float = 120.0,
    ) -> AgentResult:
        """Execute a step with retries and exponential backoff. Each step uses its own session."""
        agent = step_def.agent_class(
            name=step_def.step_name,
            step_order=step_def.step_order,
        )

        for attempt in range(max_retries + 1):
            step_start = time.monotonic()

            try:
                # Mark step as running
                async with async_session() as session:
                    step_record = await session.get(WorkflowStep, step_id)
                    if step_record:
                        step_record.status = "running"
                        step_record.started_at = _utcnow()
                        await session.commit()

                await event_queue.put(
                    format_sse_event("step_started", {
                        "step_name": step_def.step_name,
                        "step_order": step_def.step_order,
                        "run_id": context.run_id,
                    })
                )

                # Execute agent with timeout
                result = await asyncio.wait_for(
                    agent.execute(context),
                    timeout=timeout_seconds,
                )

                duration_ms = int((time.monotonic() - step_start) * 1000)
                result.metrics.duration_ms = duration_ms

                # Confidence scoring
                step_data = await context.memory.snapshot()
                for finding in result.findings:
                    finding.confidence = self.scorer.score_finding(finding, step_data)

                step_confidence = self.scorer.score_step(result.findings)
                result.metrics.confidence_score = step_confidence
                result.metrics.finding_count = len(result.findings)

                # Persist findings and update step record
                async with async_session() as session:
                    for af in result.findings:
                        orm_finding = Finding(
                            run_id=context.run_id,
                            step_id=step_id,
                            title=af.title,
                            severity=af.severity,
                            category=af.category,
                            entity_code=af.entity_code,
                            description=af.description,
                            impact_amount=_to_decimal(af.impact_amount) if af.impact_amount is not None else None,
                            impact_currency=af.impact_currency,
                            rule_triggered=af.rule_triggered,
                            evidence=[e.model_dump() for e in af.evidence],
                            suggested_questions=af.suggested_questions,
                            suggested_actions=af.suggested_actions,
                            confidence=_to_decimal(af.confidence * 100, 2),
                            escalation_needed=af.escalation_needed,
                            escalation_reason=af.escalation_reason,
                        )
                        session.add(orm_finding)

                    step_status = "escalated" if step_confidence < 0.5 else "completed"
                    step_record = await session.get(WorkflowStep, step_id)
                    if step_record:
                        step_record.status = step_status
                        step_record.completed_at = _utcnow()
                        step_record.duration_ms = duration_ms
                        step_record.finding_count = len(result.findings)
                        step_record.confidence_score = _to_decimal(step_confidence * 100, 2)
                        step_record.cost = _to_decimal(result.metrics.cost, 4)
                        step_record.tools_used = result.metrics.tools_used
                        step_record.llm_calls = result.metrics.llm_calls
                        step_record.output_data = result.data
                        step_record.retry_count = attempt

                    await session.commit()

                await self._emit_step_result(
                    event_queue, step_def, context.run_id, step_status,
                    duration_ms, len(result.findings), step_confidence,
                )
                return result

            except (TimeoutError, asyncio.TimeoutError) as e:
                logger.warning(
                    "Step %s timeout intento %d/%d: %s",
                    step_def.step_name, attempt + 1, max_retries + 1, e,
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue

                return await self._fail_step(
                    step_id, step_def, context.run_id, event_queue, step_start, attempt, e,
                )

            except Exception as e:
                # Non-recoverable errors (bugs, programming errors) are not retried
                logger.error(
                    "Step %s error no recuperable: %s", step_def.step_name, e,
                )
                return await self._fail_step(
                    step_id, step_def, context.run_id, event_queue, step_start, attempt, e,
                )

        return AgentResult(status="failed", metrics=StepMetrics())  # pragma: no cover

    async def _emit_step_result(
        self,
        event_queue: asyncio.Queue[str | None],
        step_def: StepDefinition,
        run_id: int,
        status: str,
        duration_ms: int,
        finding_count: int,
        confidence: float,
    ) -> None:
        """Emit SSE event for step result (completed or escalated)."""
        if status == "escalated":
            await event_queue.put(
                format_sse_event("step_escalated", {
                    "step_name": step_def.step_name,
                    "step_order": step_def.step_order,
                    "run_id": run_id,
                    "reason": "Step confidence below 0.5",
                })
            )
        else:
            await event_queue.put(
                format_sse_event("step_completed", {
                    "step_name": step_def.step_name,
                    "step_order": step_def.step_order,
                    "run_id": run_id,
                    "duration_ms": duration_ms,
                    "finding_count": finding_count,
                    "confidence_score": round(confidence * 100, 2),
                })
            )

    async def _fail_step(
        self,
        step_id: int,
        step_def: StepDefinition,
        run_id: int,
        event_queue: asyncio.Queue[str | None],
        step_start: float,
        attempt: int,
        error: Exception,
    ) -> AgentResult:
        """Mark a step as failed and emit an SSE event."""
        duration_ms = int((time.monotonic() - step_start) * 1000)
        async with async_session() as session:
            step_record = await session.get(WorkflowStep, step_id)
            if step_record:
                step_record.status = "failed"
                step_record.completed_at = _utcnow()
                step_record.duration_ms = duration_ms
                step_record.error_message = str(error)
                step_record.retry_count = attempt
                await session.commit()

        await event_queue.put(
            format_sse_event("step_failed", {
                "step_name": step_def.step_name,
                "step_order": step_def.step_order,
                "run_id": run_id,
                "error": str(error),
            })
        )
        return AgentResult(status="failed", findings=[], data={}, metrics=StepMetrics(duration_ms=duration_ms))
