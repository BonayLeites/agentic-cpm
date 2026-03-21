import logging
from typing import Any

from app.core.agent_base import (
    AgentContext,
    AgentResult,
    BaseAgent,
    StepMetrics,
    parse_findings_json,
)
from app.llm.gateway import get_gateway
from app.llm.prompts.consolidation import ANALYSIS_SYSTEM
from app.llm.prompts.performance import PERFORMANCE_ANALYSIS_SYSTEM

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """Synthesize all workflow data into structured findings (JSON mode)."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = "Finding synthesis with LLM in JSON mode"
        self.model = "gpt-4o"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        llm_calls: list[dict[str, Any]] = []

        memory_snapshot = await context.memory.snapshot()

        rules_text = "\n".join(f"- {k}: {v}" for k, v in context.config.items())
        period = memory_snapshot.get("period", "2026-02")

        if context.workflow_type == "performance":
            system_prompt = PERFORMANCE_ANALYSIS_SYSTEM.format(
                period=period, rules=rules_text,
            )
            user_content = _build_performance_user_message(memory_snapshot)
        else:
            system_prompt = ANALYSIS_SYSTEM.format(
                period=period, rules=rules_text,
            )
            user_content = _build_user_message(memory_snapshot)

        llm = get_gateway()
        response = await llm.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model="gpt-4o",
            response_format={"type": "json_object"},
        )
        llm_calls.append({
            "model": response.model,
            "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens,
            "cost": response.cost,
        })

        findings = parse_findings_json(response.content, default_confidence=0.85)

        # Serialize for downstream agents
        analysis_findings = []
        for f in findings:
            analysis_findings.append({
                "title": f.title,
                "severity": f.severity,
                "category": f.category,
                "entity_code": f.entity_code,
                "description": f.description,
                "impact_amount": f.impact_amount,
                "impact_currency": f.impact_currency,
                "rule_triggered": f.rule_triggered,
                "evidence": [e.model_dump() for e in f.evidence],
                "suggested_questions": f.suggested_questions,
                "suggested_actions": f.suggested_actions,
                "confidence": f.confidence,
            })

        return AgentResult(
            status="completed",
            findings=findings,
            data={"analysis_findings": analysis_findings},
            metrics=StepMetrics(
                llm_calls=llm_calls,
                cost=response.cost,
            ),
        )


def _build_user_message(memory: dict[str, Any]) -> str:
    """Build the user message with all workflow data."""
    parts: list[str] = []

    period = memory.get("period", "2026-02")
    comparison = memory.get("comparison_period", "2026-01")
    parts.append(f"# Consolidation Review Data — {period} vs {comparison}\n")

    # Current trial balances
    tb_current = memory.get("trial_balances_current", {})
    if tb_current.get("rows"):
        parts.append("## Trial Balances (Current Period)")
        for row in tb_current["rows"]:
            parts.append(
                f"- {row['entity_code']} | {row['account_name']} ({row['account_code']}): "
                f"D={row['debit']:,.2f} C={row['credit']:,.2f}"
            )

    tb_prev = memory.get("trial_balances_previous", {})
    if tb_prev.get("rows"):
        parts.append("\n## Trial Balances (Previous Period)")
        for row in tb_prev["rows"]:
            parts.append(
                f"- {row['entity_code']} | {row['account_name']} ({row['account_code']}): "
                f"D={row['debit']:,.2f} C={row['credit']:,.2f}"
            )

    ic_result = memory.get("ic_match_result", {})
    if ic_result:
        parts.append(f"\n## IC Matching: {ic_result.get('matched', 0)} matched, "
                     f"{len(ic_result.get('mismatched', []))} mismatched")
        for m in ic_result.get("mismatched", []):
            parts.append(
                f"- {m['from_entity']} → {m['to_entity']}: "
                f"diff={m['amount_diff']:,.0f}, pct={m['pct_diff']}%, "
                f"timing_gap={m['timing_gap_days']}d "
                f"(invoice: {m['invoice_date']}, recorded: {m['recorded_date']})"
            )

    anomalies = memory.get("anomalies", {})
    if anomalies:
        parts.append("\n## Anomalies Detected")
        for entity, anoms in anomalies.items():
            for a in anoms:
                parts.append(
                    f"- {entity} | {a['account_name']} ({a['account_code']}): "
                    f"{a['change_pct']:+.2f}% (current={a['current']:,.2f}, prev={a['previous']:,.2f})"
                )

    je_data = memory.get("journal_entries", {})
    if je_data.get("rows"):
        parts.append("\n## Journal Entries")
        for row in je_data["rows"]:
            parts.append(
                f"- {row['entry_number']} | {row['entity_code']} | "
                f"{row['account_name']}: D={row['debit']:,.2f} C={row['credit']:,.2f} | "
                f"Posted by: {row['posted_by']} | {row['entry_description']}"
            )

    doc_results = memory.get("doc_search_results", {})
    if doc_results:
        parts.append("\n## Relevant Documents")
        for key, docs in doc_results.items():
            parts.append(f"\n### Search: {key}")
            for doc in docs:
                parts.append(f"- **{doc['title']}** (score: {doc['relevance_score']})")
                parts.append(f"  {doc['excerpt']}")

    fx = memory.get("exchange_rates", {})
    if fx.get("rows"):
        parts.append("\n## Exchange Rates")
        for row in fx["rows"]:
            parts.append(
                f"- {row['from_currency']}/{row['to_currency']} "
                f"({row['rate_type']}): {row['rate']} @ {row['effective_date']}"
            )

    return "\n".join(parts)


def _build_performance_user_message(memory: dict[str, Any]) -> str:
    """Build the user message with performance review data."""
    parts: list[str] = []

    period = memory.get("period", "2026-02")
    comparison = memory.get("comparison_period", "2026-01")
    parts.append(f"# Performance Review Data — {period} vs {comparison}\n")

    tb_current = memory.get("trial_balances_current", {})
    if tb_current.get("rows"):
        parts.append("## Trial Balances (Current Period)")
        for row in tb_current["rows"]:
            parts.append(
                f"- {row['entity_code']} | {row['account_name']} ({row['account_code']}): "
                f"D={row['debit']:,.2f} C={row['credit']:,.2f}"
            )

    tb_prev = memory.get("trial_balances_previous", {})
    if tb_prev.get("rows"):
        parts.append("\n## Trial Balances (Previous Period)")
        for row in tb_prev["rows"]:
            parts.append(
                f"- {row['entity_code']} | {row['account_name']} ({row['account_code']}): "
                f"D={row['debit']:,.2f} C={row['credit']:,.2f}"
            )

    variance_results = memory.get("variance_results", {})
    if variance_results:
        parts.append("\n## Budget vs Actual Variances")
        for entity, vars_list in variance_results.items():
            parts.append(f"\n### {entity}")
            for v in vars_list:
                flag = " ⚠️" if abs(v.get("variance_pct", 0)) > 10 else ""
                parts.append(
                    f"- {v['account_name']} ({v['account_code']}): "
                    f"Budget={v['budget']:,.0f}, Actual={v['actual']:,.0f}, "
                    f"Variance={v['variance']:+,.0f} ({v['variance_pct']:+.1f}%){flag}"
                )

    margin_analysis = memory.get("margin_analysis", [])
    if margin_analysis:
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

    kpi_breaches = memory.get("kpi_breaches", [])
    kpi_trends = memory.get("kpi_trends", [])
    if kpi_breaches:
        parts.append("\n## KPI Breaches")
        for b in kpi_breaches:
            parts.append(
                f"- ⚠️ {b['entity_code']} | {b['kpi_name']}: "
                f"value={b['value']}, target={b['target']}, "
                f"breach={b['breach_pct']:+.1f}% (rule: {b['rule']})"
            )

    if kpi_trends:
        parts.append("\n## KPI Trends")
        for t in kpi_trends:
            if t.get("direction") != "stable":
                parts.append(
                    f"- {t['entity_code']} | {t['kpi_name']}: "
                    f"{t['previous']} → {t['current']} ({t['change']:+.2f}) [{t['direction']}]"
                )

    doc_results = memory.get("doc_search_results", {})
    if doc_results:
        parts.append("\n## Relevant Documents")
        for key, docs in doc_results.items():
            parts.append(f"\n### Search: {key}")
            for doc in docs:
                parts.append(f"- **{doc['title']}** (score: {doc['relevance_score']})")
                parts.append(f"  {doc['excerpt']}")

    fx = memory.get("exchange_rates", {})
    if fx.get("rows"):
        parts.append("\n## Exchange Rates")
        for row in fx["rows"]:
            parts.append(
                f"- {row['from_currency']}/{row['to_currency']} "
                f"({row['rate_type']}): {row['rate']} @ {row['effective_date']}"
            )

    return "\n".join(parts)
