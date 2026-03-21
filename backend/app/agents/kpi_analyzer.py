import re
from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentResult,
    BaseAgent,
    StepMetrics,
    parse_findings_json,
)
from app.llm.gateway import get_gateway
from app.llm.prompts.performance import KPI_ANALYSIS_SYSTEM

# KPIs where an increase is negative (for trend direction)
_BAD_IF_UP = ("churn_rate", "dso")


class KPIAnalysisAgent(BaseAgent):
    """Analyze KPIs vs. targets and detect breaches and deteriorating trends."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "KPI vs. target analysis and breach detection"
        self.model = "gpt-4o-mini"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        llm_calls: list[dict[str, Any]] = []

        # DataLoaderAgent already loaded this data into memory
        kpi_current = await context.memory.get("kpis_current", {})
        kpi_previous = await context.memory.get("kpis_previous", {})

        churn_ceiling = _parse_numeric(context.config.get("churn_rate_ceiling", "2.5% monthly"))
        dso_warning = _parse_numeric(context.config.get("dso_warning_threshold", "50 days"))
        breach_pct = _parse_numeric(context.config.get("kpi_breach_threshold", "Target ± 20%")) / 100

        breaches = _compute_breaches(kpi_current, churn_ceiling, dso_warning, breach_pct)
        trends = _compute_trends(kpi_current, kpi_previous)

        user_content = _build_user_message(
            kpi_current, kpi_previous, breaches, trends, context.config,
        )

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": KPI_ANALYSIS_SYSTEM},
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

        findings = parse_findings_json(
            response.content,
            default_severity="medium",
            default_category="kpi",
            default_confidence=0.82,
        )

        kpi_findings = [
            {"title": f.title, "severity": f.severity, "description": f.description}
            for f in findings
        ]

        return AgentResult(
            status="completed",
            findings=findings,
            data={
                "kpi_breaches": breaches,
                "kpi_trends": trends,
                "kpi_findings": kpi_findings,
            },
            metrics=StepMetrics(
                llm_calls=llm_calls,
                cost=response.cost,
            ),
        )


def _parse_numeric(value: str) -> float:
    """Extract the first number from a rule string like '2.5% monthly' or '50 days'."""
    match = re.search(r"[\d.]+", value)
    return float(match.group()) if match else 0.0


def _compute_breaches(
    kpi_data: dict[str, Any],
    churn_ceiling: float,
    dso_warning: float,
    breach_pct: float,
) -> list[dict[str, Any]]:
    """Detect KPI breaches vs. targets and specific business rules."""
    breaches: list[dict[str, Any]] = []

    for row in kpi_data.get("rows", []):
        value = float(row["kpi_value"])
        target = float(row["kpi_target"]) if row.get("kpi_target") is not None else None
        name = row["kpi_name"]
        entity = row["entity_code"]

        if name == "churn_rate" and value > churn_ceiling:
            breaches.append({
                "entity_code": entity,
                "kpi_name": name,
                "value": value,
                "target": churn_ceiling,
                "rule": "churn_rate_ceiling",
                "breach_pct": round((value - churn_ceiling) / churn_ceiling * 100, 1),
            })
        elif name == "dso" and value > dso_warning:
            breaches.append({
                "entity_code": entity,
                "kpi_name": name,
                "value": value,
                "target": dso_warning,
                "rule": "dso_warning_threshold",
                "breach_pct": round((value - dso_warning) / dso_warning * 100, 1),
            })
        elif target is not None and target > 0:
            deviation = abs(value - target) / target
            if deviation > breach_pct:
                breaches.append({
                    "entity_code": entity,
                    "kpi_name": name,
                    "value": value,
                    "target": target,
                    "rule": "kpi_breach_threshold",
                    "breach_pct": round(deviation * 100, 1),
                })

    return breaches


def _compute_trends(
    kpi_current: dict[str, Any],
    kpi_previous: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate MoM trend for each KPI per entity."""
    prev_map: dict[tuple[str, str], float] = {}
    for row in kpi_previous.get("rows", []):
        key = (row["entity_code"], row["kpi_name"])
        prev_map[key] = float(row["kpi_value"])

    trends: list[dict[str, Any]] = []
    for row in kpi_current.get("rows", []):
        entity = row["entity_code"]
        name = row["kpi_name"]
        current_val = float(row["kpi_value"])
        prev_val = prev_map.get((entity, name))

        if prev_val is not None:
            change = current_val - prev_val
            change_pct = (change / prev_val * 100) if prev_val else 0.0
            if abs(change_pct) < 2:
                direction = "stable"
            elif (change > 0 and name in _BAD_IF_UP) or (change < 0 and name not in _BAD_IF_UP):
                direction = "deteriorating"
            else:
                direction = "improving"

            trends.append({
                "entity_code": entity,
                "kpi_name": name,
                "current": current_val,
                "previous": prev_val,
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "direction": direction,
            })

    return trends


def _build_user_message(
    kpi_current: dict[str, Any],
    kpi_previous: dict[str, Any],
    breaches: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    rules: dict[str, str],
) -> str:
    """Build the user message with KPIs, breaches, trends, and business rules."""
    parts: list[str] = []

    parts.append("## Current Period KPIs")
    for row in kpi_current.get("rows", []):
        target_str = f" (target: {row['kpi_target']})" if row.get("kpi_target") is not None else ""
        parts.append(
            f"- {row['entity_code']} | {row['kpi_name']}: "
            f"{row['kpi_value']} {row['unit']}{target_str}"
        )

    parts.append("\n## Previous Period KPIs")
    for row in kpi_previous.get("rows", []):
        parts.append(
            f"- {row['entity_code']} | {row['kpi_name']}: "
            f"{row['kpi_value']} {row['unit']}"
        )

    if breaches:
        parts.append("\n## KPI Breaches Detected")
        for b in breaches:
            parts.append(
                f"- {b['entity_code']} | {b['kpi_name']}: "
                f"value={b['value']}, target={b['target']}, "
                f"breach={b['breach_pct']:+.1f}% (rule: {b['rule']})"
            )

    if trends:
        parts.append("\n## Month-over-Month Trends")
        for t in trends:
            parts.append(
                f"- {t['entity_code']} | {t['kpi_name']}: "
                f"{t['previous']} -> {t['current']} ({t['change']:+.2f}, {t['change_pct']:+.1f}%) "
                f"[{t['direction']}]"
            )

    parts.append("\n## Business Rules")
    for key, value in rules.items():
        parts.append(f"- {key}: {value}")

    return "\n".join(parts)
