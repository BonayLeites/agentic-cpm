import asyncio
import logging
from typing import Any

from app.core.agent_base import AgentContext, AgentResult, BaseAgent, StepMetrics
from app.db.models import ExecutiveSummary
from app.llm.gateway import get_gateway
from app.llm.prompts import localize_prompt
from app.llm.prompts.consolidation import (
    NARRATIVE_CONTROLLER_SYSTEM,
    NARRATIVE_EXECUTIVE_SYSTEM,
)
from app.llm.prompts.performance import (
    PERFORMANCE_NARRATIVE_CONTROLLER_SYSTEM,
    PERFORMANCE_NARRATIVE_EXECUTIVE_SYSTEM,
)

logger = logging.getLogger(__name__)


class NarrativeAgent(BaseAgent):
    """Generate executive summaries for controller and executive audiences, and persist to DB."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Narrative summary generation for two audiences"
        self.model = "gpt-4o"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        llm_calls: list[dict[str, Any]] = []
        total_cost = 0.0

        period = await context.memory.get("period", "2026-02")
        analysis_findings = await context.memory.get("analysis_findings", [])

        findings_text = _format_findings(analysis_findings)
        llm = get_gateway()

        if context.workflow_type == "performance":
            ctrl_system = localize_prompt(
                PERFORMANCE_NARRATIVE_CONTROLLER_SYSTEM.format(period=period),
                context.language,
            )
            exec_system = localize_prompt(
                PERFORMANCE_NARRATIVE_EXECUTIVE_SYSTEM.format(period=period),
                context.language,
            )
        else:
            ctrl_system = localize_prompt(
                NARRATIVE_CONTROLLER_SYSTEM.format(period=period),
                context.language,
            )
            exec_system = localize_prompt(
                NARRATIVE_EXECUTIVE_SYSTEM.format(period=period),
                context.language,
            )

        ctrl_coro = llm.complete(
            messages=[
                {"role": "system", "content": ctrl_system},
                {"role": "user", "content": findings_text},
            ],
            model="gpt-4o",
        )
        exec_coro = llm.complete(
            messages=[
                {"role": "system", "content": exec_system},
                {"role": "user", "content": findings_text},
            ],
            model="gpt-4o",
        )
        ctrl_response, exec_response = await asyncio.gather(ctrl_coro, exec_coro)

        for resp, audience in [(ctrl_response, "controller"), (exec_response, "executive")]:
            total_cost += resp.cost
            llm_calls.append({
                "model": resp.model,
                "prompt_tokens": resp.prompt_tokens,
                "completion_tokens": resp.completion_tokens,
                "cost": resp.cost,
                "audience": audience,
            })

        # Persist summaries to DB
        async with context.session_factory() as session:
            session.add(ExecutiveSummary(
                run_id=context.run_id, audience="controller", summary=ctrl_response.content,
            ))
            session.add(ExecutiveSummary(
                run_id=context.run_id, audience="executive", summary=exec_response.content,
            ))
            await session.commit()

        return AgentResult(
            status="completed",
            findings=[],
            data={"summaries_saved": True},
            metrics=StepMetrics(
                llm_calls=llm_calls,
                cost=total_cost,
            ),
        )


def _format_findings(findings: list[dict[str, Any]]) -> str:
    """Format findings as readable text for the narrative prompt."""
    if not findings:
        return "No findings were identified during the review."

    parts: list[str] = ["# Review Findings\n"]

    for i, f in enumerate(findings, 1):
        parts.append(f"## Finding {i}: {f.get('title', 'Untitled')} [{f.get('severity', 'medium').upper()}]")
        parts.append(f"Entity: {f.get('entity_code', 'N/A')}")
        parts.append(f"Category: {f.get('category', 'N/A')}")

        if f.get("description"):
            parts.append(f"Description: {f['description']}")

        if f.get("impact_amount"):
            parts.append(f"Impact: {f['impact_currency']} {f['impact_amount']:,.0f}")

        if f.get("rule_triggered"):
            parts.append(f"Rule: {f['rule_triggered']}")

        if f.get("evidence"):
            parts.append("Evidence:")
            for e in f["evidence"]:
                parts.append(f"  - [{e.get('type', '')}] {e.get('label', '')}: {e.get('value', '')}")

        if f.get("suggested_questions"):
            parts.append("Questions: " + "; ".join(f["suggested_questions"]))

        if f.get("suggested_actions"):
            parts.append("Actions: " + "; ".join(f["suggested_actions"]))

        parts.append("")

    return "\n".join(parts)
