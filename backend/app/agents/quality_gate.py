import json
import logging
from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentFinding,
    AgentResult,
    BaseAgent,
    StepMetrics,
    parse_evidence_list,
)
from app.llm.gateway import get_gateway
from app.llm.prompts import localize_prompt
from app.llm.prompts.consolidation import QUALITY_GATE_SYSTEM

logger = logging.getLogger(__name__)

_ESCALATION_THRESHOLD = 0.6


class QualityGateAgent(BaseAgent):
    """Review finding coherence and flag items that need escalation."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Quality control and finding coherence check"
        self.model = "gpt-4o-mini"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        llm_calls: list[dict[str, Any]] = []

        analysis_findings: list[dict[str, Any]] = await context.memory.get("analysis_findings", [])

        if not analysis_findings:
            return AgentResult(
                status="completed",
                data={"quality_gate_passed": True},
                metrics=StepMetrics(confidence_score=0.95),
            )

        user_content = _build_user_message(analysis_findings)

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": localize_prompt(QUALITY_GATE_SYSTEM, context.language, json_mode=True)},
                {"role": "user", "content": user_content},
            ],
            model="gpt-4o-mini",
        )
        llm_calls.append({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
        })

        review = _parse_review(response.content)

        # Re-emit findings with escalation flags if needed
        findings: list[AgentFinding] = []
        for f_data in analysis_findings:
            confidence = f_data.get("confidence", 0.80)
            needs_escalation = confidence < _ESCALATION_THRESHOLD

            review_item = _find_review_for(f_data.get("title", ""), review)
            escalation_reason = None
            if review_item and not review_item.get("passed", True):
                needs_escalation = True
                issues = review_item.get("issues", [])
                escalation_reason = "; ".join(issues) if issues else "Quality gate flag"

            if needs_escalation:
                evidence = parse_evidence_list(f_data.get("evidence", []))
                findings.append(AgentFinding(
                    title=f_data.get("title", "Finding"),
                    severity=f_data.get("severity", "medium"),
                    category=f_data.get("category"),
                    entity_code=f_data.get("entity_code"),
                    description=f_data.get("description"),
                    impact_amount=f_data.get("impact_amount"),
                    impact_currency=f_data.get("impact_currency", "JPY"),
                    rule_triggered=f_data.get("rule_triggered"),
                    evidence=evidence,
                    suggested_questions=f_data.get("suggested_questions", []),
                    suggested_actions=f_data.get("suggested_actions", []),
                    confidence=confidence,
                    escalation_needed=True,
                    escalation_reason=escalation_reason or f"Confidence {confidence:.2f} < {_ESCALATION_THRESHOLD}",
                ))

        return AgentResult(
            status="completed",
            findings=findings,
            data={
                "quality_gate_passed": len(findings) == 0,
                "quality_review": review,
            },
            metrics=StepMetrics(
                llm_calls=llm_calls,
                cost=response.cost,
            ),
        )


def _build_user_message(findings: list[dict[str, Any]]) -> str:
    """Build the user message with findings for review."""
    parts: list[str] = ["# Findings to Review\n"]

    for i, f in enumerate(findings, 1):
        parts.append(f"## Finding {i}: {f.get('title', 'Untitled')}")
        parts.append(f"Severity: {f.get('severity', 'unknown')}")
        parts.append(f"Confidence: {f.get('confidence', 0):.2f}")
        parts.append(f"Entity: {f.get('entity_code', 'N/A')}")

        if f.get("description"):
            parts.append(f"Description: {f['description']}")

        if f.get("impact_amount"):
            parts.append(f"Impact: {f.get('impact_currency', 'JPY')} {f['impact_amount']:,.0f}")

        if f.get("evidence"):
            parts.append(f"Evidence count: {len(f['evidence'])}")
            for e in f["evidence"]:
                parts.append(f"  - [{e.get('type', '')}] {e.get('label', '')}")

        parts.append("")

    return "\n".join(parts)


def _parse_review(llm_response: str) -> dict[str, Any]:
    """Parse the quality gate JSON response."""
    try:
        return json.loads(llm_response)
    except json.JSONDecodeError:
        logger.error("QualityGate: response is not valid JSON: %s", llm_response[:200])
        return {"review": [], "overall_coherent": True, "escalation_flags": []}


def _find_review_for(title: str, review: dict[str, Any]) -> dict[str, Any] | None:
    """Find the review item matching a finding by title."""
    for item in review.get("review", []):
        review_title = item.get("finding_title", "")
        if review_title.lower() in title.lower() or title.lower() in review_title.lower():
            return item
    return None
