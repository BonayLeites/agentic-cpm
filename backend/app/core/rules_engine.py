# Business rules by workflow_type (moved from config_routes.py)
BUSINESS_RULES: dict[str, dict[str, str]] = {
    "consolidation": {
        "ic_mismatch_tolerance": "2% of transaction value",
        "manual_adjustment_threshold": "JPY 10,000,000",
        "anomaly_detection_threshold": "15% MoM change",
        "materiality_income_statement": "JPY 50,000,000",
        "materiality_balance_sheet": "JPY 100,000,000",
    },
    "performance": {
        "budget_variance_threshold": "10% of budget",
        "kpi_breach_threshold": "Target ± 20%",
        "margin_erosion_alert": "3 percentage points decline",
        "dso_warning_threshold": "50 days",
        "churn_rate_ceiling": "2.5% monthly",
    },
}


def get_rules(workflow_type: str) -> dict[str, str]:
    """Return the business rules for a given workflow type."""
    return BUSINESS_RULES.get(workflow_type, {})


def check_threshold(value: float, rule_name: str, workflow_type: str) -> bool:
    """Check whether a value exceeds a rule threshold.

    Stub for Phase 5 — real agents implement this in Phase 7.
    """
    _ = value, rule_name, workflow_type
    return False
