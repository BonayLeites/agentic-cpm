from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentResult,
    BaseAgent,
    StepMetrics,
    parse_findings_json,
)
from app.llm.gateway import get_gateway
from app.llm.prompts.performance import VARIANCE_ANALYSIS_SYSTEM

_REVENUE_ACCOUNT = "4000"
_COGS_ACCOUNT = "5000"


class VarianceAnalyzerAgent(BaseAgent):
    """Analyze budget vs. actuals variances and decompose eroded margins."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Budget vs. actuals variance analysis and margin decomposition"
        self.model = "gpt-4o"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        llm_calls: list[dict[str, Any]] = []

        # DataLoaderAgent already loaded this data into memory
        tb_current = await context.memory.get("trial_balances_current", {})
        tb_previous = await context.memory.get("trial_balances_previous", {})
        budgets = await context.memory.get("budgets", {})

        variance_results = _compute_variances(tb_current, budgets)
        margin_analysis = _compute_margin_analysis(tb_current, tb_previous, budgets)

        user_content = _build_user_message(
            variance_results, margin_analysis, context.config,
        )

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": VARIANCE_ANALYSIS_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            model="gpt-4o",
        )
        llm_calls.append({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
        })

        findings = parse_findings_json(
            response.content,
            default_severity="high",
            default_category="margin",
            default_confidence=0.85,
        )

        variance_findings = [
            {"title": f.title, "severity": f.severity, "description": f.description}
            for f in findings
        ]

        return AgentResult(
            status="completed",
            findings=findings,
            data={
                "variance_results": variance_results,
                "margin_analysis": margin_analysis,
                "variance_findings": variance_findings,
            },
            metrics=StepMetrics(
                llm_calls=llm_calls,
                cost=response.cost,
            ),
        )


def _compute_variances(
    tb_current: dict[str, Any],
    budgets: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Calculate variance per entity/account: actual - budget."""
    budget_map: dict[tuple[str, str], float] = {}
    for row in budgets.get("rows", []):
        key = (row["entity_code"], row["account_code"])
        budget_map[key] = float(row["amount"])

    actual_map: dict[tuple[str, str], dict[str, Any]] = {}
    for row in tb_current.get("rows", []):
        key = (row["entity_code"], row["account_code"])
        # Revenue (4000) uses credit; expenses use debit
        if row["account_code"] == _REVENUE_ACCOUNT:
            actual = float(row.get("credit", 0) or 0)
        else:
            actual = float(row.get("debit", 0) or 0)
        actual_map[key] = {
            "account_name": row["account_name"],
            "account_code": row["account_code"],
            "entity_code": row["entity_code"],
            "actual": actual,
        }

    variances: dict[str, list[dict[str, Any]]] = {}
    for (entity, account), budget_amt in budget_map.items():
        actual_info = actual_map.get((entity, account))
        if not actual_info:
            continue
        actual_amt = actual_info["actual"]
        variance = actual_amt - budget_amt
        variance_pct = (variance / budget_amt * 100) if budget_amt else 0.0

        if entity not in variances:
            variances[entity] = []
        variances[entity].append({
            "account_code": account,
            "account_name": actual_info["account_name"],
            "budget": budget_amt,
            "actual": actual_amt,
            "variance": variance,
            "variance_pct": round(variance_pct, 2),
        })

    return variances


def _compute_margin_analysis(
    tb_current: dict[str, Any],
    tb_previous: dict[str, Any],
    budgets: dict[str, Any],
) -> list[dict[str, Any]]:
    """Calculate actual GM vs budget per entity and decompose if erosion > 3 pts."""
    entities_data: dict[str, dict[str, float]] = {}

    for row in tb_current.get("rows", []):
        entity = row["entity_code"]
        if entity not in entities_data:
            entities_data[entity] = {}
        code = row["account_code"]
        if code == _REVENUE_ACCOUNT:
            entities_data[entity]["actual_rev"] = float(row.get("credit", 0) or 0)
        elif code == _COGS_ACCOUNT:
            entities_data[entity]["actual_cogs"] = float(row.get("debit", 0) or 0)

    for row in tb_previous.get("rows", []):
        entity = row["entity_code"]
        if entity not in entities_data:
            entities_data[entity] = {}
        code = row["account_code"]
        if code == _REVENUE_ACCOUNT:
            entities_data[entity]["prev_rev"] = float(row.get("credit", 0) or 0)
        elif code == _COGS_ACCOUNT:
            entities_data[entity]["prev_cogs"] = float(row.get("debit", 0) or 0)

    budget_map: dict[str, dict[str, float]] = {}
    for row in budgets.get("rows", []):
        entity = row["entity_code"]
        if entity not in budget_map:
            budget_map[entity] = {}
        code = row["account_code"]
        if code == _REVENUE_ACCOUNT:
            budget_map[entity]["budget_rev"] = float(row["amount"])
        elif code == _COGS_ACCOUNT:
            budget_map[entity]["budget_cogs"] = float(row["amount"])

    results: list[dict[str, Any]] = []
    for entity, data in entities_data.items():
        actual_rev = data.get("actual_rev", 0)
        actual_cogs = data.get("actual_cogs", 0)
        prev_rev = data.get("prev_rev", 0)
        prev_cogs = data.get("prev_cogs", 0)
        budget = budget_map.get(entity, {})
        budget_rev = budget.get("budget_rev", 0)
        budget_cogs = budget.get("budget_cogs", 0)

        actual_gm = ((actual_rev - actual_cogs) / actual_rev * 100) if actual_rev else 0
        budget_gm = ((budget_rev - budget_cogs) / budget_rev * 100) if budget_rev else 0
        prev_gm = ((prev_rev - prev_cogs) / prev_rev * 100) if prev_rev else 0
        margin_change = actual_gm - budget_gm

        entry: dict[str, Any] = {
            "entity_code": entity,
            "actual_gm_pct": round(actual_gm, 2),
            "budget_gm_pct": round(budget_gm, 2),
            "prev_gm_pct": round(prev_gm, 2),
            "margin_change_pts": round(margin_change, 2),
        }

        if margin_change < -3 and budget_rev > 0:
            rev_ratio = actual_rev / budget_rev
            price_mix_effect = round((rev_ratio - 1) * budget_gm, 2)
            cost_effect = round(margin_change - price_mix_effect, 2)
            entry["decomposition"] = {
                "price_mix_effect_pts": price_mix_effect,
                "cost_effect_pts": cost_effect,
                # Volume effect not calculated — requires unit-level data not available
                "volume_effect_pts": 0.0,
            }

        results.append(entry)

    return results


def _build_user_message(
    variances: dict[str, list[dict[str, Any]]],
    margin_analysis: list[dict[str, Any]],
    rules: dict[str, str],
) -> str:
    """Build the user message with variances, margins, and business rules."""
    parts: list[str] = []

    parts.append("## Budget vs Actual Variances")
    for entity, entity_vars in variances.items():
        parts.append(f"\n### Entity: {entity}")
        for v in entity_vars:
            flag = " ⚠️" if abs(v["variance_pct"]) > 10 else ""
            parts.append(
                f"- {v['account_name']} ({v['account_code']}): "
                f"Budget={v['budget']:,.0f}, Actual={v['actual']:,.0f}, "
                f"Variance={v['variance']:+,.0f} ({v['variance_pct']:+.1f}%){flag}"
            )

    parts.append("\n## Gross Margin Analysis")
    for m in margin_analysis:
        parts.append(f"\n### {m['entity_code']}")
        parts.append(f"- Actual GM: {m['actual_gm_pct']:.1f}%")
        parts.append(f"- Budget GM: {m['budget_gm_pct']:.1f}%")
        parts.append(f"- Previous GM: {m['prev_gm_pct']:.1f}%")
        parts.append(f"- Change vs budget: {m['margin_change_pts']:+.1f} pts")
        if "decomposition" in m:
            d = m["decomposition"]
            parts.append("- **Decomposition:**")
            parts.append(f"  - Price/mix effect: {d['price_mix_effect_pts']:+.1f} pts")
            parts.append(f"  - Cost effect: {d['cost_effect_pts']:+.1f} pts")
            parts.append(f"  - Volume effect: {d['volume_effect_pts']:+.1f} pts")

    parts.append("\n## Business Rules")
    for key, value in rules.items():
        parts.append(f"- {key}: {value}")

    return "\n".join(parts)
