import logging
from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentResult,
    BaseAgent,
    StepMetrics,
    parse_findings_json,
)
from app.core.tools.anomaly_detection import AnomalyDetectionTool
from app.llm.gateway import get_gateway
from app.llm.prompts import localize_prompt
from app.llm.prompts.consolidation import ANOMALY_DETECT_SYSTEM

logger = logging.getLogger(__name__)


class AnomalyDetectorAgent(BaseAgent):
    """Detect MoM anomalies per entity and evaluate severity with LLM."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Statistical anomaly detection on trial balances"
        self.model = "gpt-4o-mini"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        entities: list[str] = await context.memory.get("entities", ["NKG-JP", "NKG-US", "NKG-SG"])
        period = await context.memory.get("period", "2026-02")
        comparison_period = await context.memory.get("comparison_period", "2026-01")

        tools_used: list[str] = []
        llm_calls: list[dict[str, Any]] = []
        total_cost = 0.0

        # 1. Ejecutar detección de anomalías por entidad
        anomaly_tool = AnomalyDetectionTool()
        all_anomalies: dict[str, list[dict[str, Any]]] = {}

        async with context.session_factory() as session:
            for entity_code in entities:
                result = await anomaly_tool.execute(
                    {
                        "entity_code": entity_code,
                        "period": period,
                        "comparison_period": comparison_period,
                    },
                    session,
                )
                if result["anomalies"]:
                    all_anomalies[entity_code] = result["anomalies"]

        tools_used.append("detect_anomalies")

        if not all_anomalies:
            return AgentResult(
                status="completed",
                data={"anomalies": {}, "anomaly_findings": []},
                metrics=StepMetrics(tools_used=tools_used),
            )

        # 2. Evaluar severidad con LLM
        user_content = _build_user_message(all_anomalies, context.config)

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": localize_prompt(ANOMALY_DETECT_SYSTEM, context.language, json_mode=True)},
                {"role": "user", "content": user_content},
            ],
            model="gpt-4o-mini",
        )
        total_cost += response.cost
        llm_calls.append({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
        })

        findings = parse_findings_json(
            response.content,
            default_severity="medium",
            default_category="opex",
            default_currency="USD",
            default_confidence=0.80,
        )

        findings_data = [
            {"title": f.title, "severity": f.severity, "description": f.description}
            for f in findings
        ]

        return AgentResult(
            status="completed",
            findings=findings,
            data={
                "anomalies": all_anomalies,
                "anomaly_findings": findings_data,
            },
            metrics=StepMetrics(
                tools_used=tools_used,
                llm_calls=llm_calls,
                cost=total_cost,
            ),
        )


def _build_user_message(
    anomalies: dict[str, list[dict[str, Any]]],
    rules: dict[str, str],
) -> str:
    """Build the user message with anomalies and business rules."""
    parts: list[str] = []

    parts.append("## Detected Anomalies (MoM comparison)")

    for entity_code, entity_anomalies in anomalies.items():
        parts.append(f"\n### Entity: {entity_code}")
        for a in entity_anomalies:
            parts.append(f"- {a['account_name']} ({a['account_code']})")
            parts.append(f"  Current: {a['current']:,.2f}, Previous: {a['previous']:,.2f}")
            parts.append(f"  Change: {a['change_pct']:+.2f}%")

    parts.append("\n## Business Rules")
    for key, value in rules.items():
        parts.append(f"- {key}: {value}")

    return "\n".join(parts)
