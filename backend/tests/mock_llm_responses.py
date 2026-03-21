"""Realistic mock LLM responses for integration tests.

Each function returns a JSON string that the corresponding agent parses
via parse_findings_json() or parse_review(). Responses follow the exact
format each agent expects.
"""

import json


# ---------------------------------------------------------------------------
# Case 1: Consolidation
# ---------------------------------------------------------------------------

def ic_check_response() -> str:
    """ICCheckAgent response: 1 finding about IC mismatch."""
    return json.dumps({
        "findings": [
            {
                "title": "IC Cut-Off Mismatch NKG-JP vs NKG-SG",
                "severity": "high",
                "category": "intercompany",
                "entity_code": "NKG-JP, NKG-SG",
                "description": "Intercompany service invoice recorded Jan 28 by NKG-JP but Feb 2 by NKG-SG, creating 5-day timing gap.",
                "impact_amount": 3300000,
                "impact_currency": "JPY",
                "rule_triggered": "ic_mismatch_tolerance",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Timing gap",
                        "value": "5 days (Jan 28 vs Feb 2)",
                        "source": "IC Matching Tool",
                    },
                    {
                        "type": "data_point",
                        "label": "Amount difference",
                        "value": "JPY 3,300,000",
                        "source": "IC Matching Tool",
                    },
                ],
                "suggested_questions": ["Was the cut-off timing intentional?"],
                "suggested_actions": ["Align recording dates between entities"],
                "confidence": 0.90,
            }
        ]
    })


def anomaly_detect_response() -> str:
    """AnomalyDetectorAgent response: 1 finding about consulting fee spike."""
    return json.dumps({
        "findings": [
            {
                "title": "OPEX Anomaly: Consulting Fees Spike in NKG-US",
                "severity": "medium",
                "category": "opex",
                "entity_code": "NKG-US",
                "description": "Consulting fees increased 47% MoM from USD 195K to USD 287K, exceeding the 15% threshold.",
                "impact_amount": 92000,
                "impact_currency": "USD",
                "rule_triggered": "anomaly_detection_threshold",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "MoM change",
                        "value": "+47.2% (USD 195K → USD 287K)",
                        "source": "Anomaly Detection Tool",
                    },
                ],
                "suggested_questions": ["What drove the consulting spend increase?"],
                "suggested_actions": ["Review consulting contracts for Q1"],
                "confidence": 0.82,
            }
        ]
    })


def analysis_consolidation_response() -> str:
    """AnalysisAgent (consolidation) response: 3 findings."""
    return json.dumps({
        "findings": [
            {
                "title": "IC Cut-Off Timing Mismatch",
                "severity": "high",
                "category": "intercompany",
                "entity_code": "NKG-JP, NKG-SG",
                "description": "5-day timing gap on IC service invoice between NKG-JP and NKG-SG.",
                "impact_amount": 3300000,
                "impact_currency": "JPY",
                "rule_triggered": "ic_mismatch_tolerance",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Timing gap",
                        "value": "5 days",
                        "source": "IC Matching Tool",
                    },
                ],
                "suggested_questions": ["Has the cut-off been corrected?"],
                "suggested_actions": ["Request NKG-SG to backdate or accrue"],
                "confidence": 0.88,
            },
            {
                "title": "Consulting Fee Spike NKG-US",
                "severity": "medium",
                "category": "opex",
                "entity_code": "NKG-US",
                "description": "47% MoM increase in consulting fees exceeds the 15% anomaly threshold.",
                "impact_amount": 92000,
                "impact_currency": "USD",
                "rule_triggered": "anomaly_detection_threshold",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "MoM change",
                        "value": "+47.2%",
                        "source": "Anomaly Detection Tool",
                    },
                ],
                "suggested_questions": ["Is this a one-time project?"],
                "suggested_actions": ["Obtain supporting contracts"],
                "confidence": 0.80,
            },
            {
                "title": "Goodwill Adjustment Review",
                "severity": "medium",
                "category": "consolidation_adjustment",
                "entity_code": "NKG-JP",
                "description": "Manual journal entry JE-2026-0287 for goodwill adjustment of JPY 12.8M with brief description.",
                "impact_amount": 12800000,
                "impact_currency": "JPY",
                "rule_triggered": "manual_adjustment_threshold",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Journal entry",
                        "value": "JE-2026-0287, JPY 12.8M",
                        "source": "Journal Entries Tool",
                    },
                ],
                "suggested_questions": ["Was the goodwill assessment documented?"],
                "suggested_actions": ["Request impairment test documentation"],
                "confidence": 0.78,
            },
        ]
    })


# ---------------------------------------------------------------------------
# Case 2: Performance
# ---------------------------------------------------------------------------

def variance_analyzer_response() -> str:
    """VarianceAnalyzerAgent response: 1 finding about margin erosion."""
    return json.dumps({
        "findings": [
            {
                "title": "Gross Margin Erosion in NKG-SG",
                "severity": "high",
                "category": "margin",
                "entity_code": "NKG-SG",
                "description": "Gross margin dropped from 48.2% to 45.0%, a 3.2 pp decline exceeding the 3 pp alert threshold.",
                "impact_amount": 38400,
                "impact_currency": "SGD",
                "rule_triggered": "margin_erosion_alert",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Margin change",
                        "value": "48.2% → 45.0% (-3.2 pp)",
                        "source": "Variance Analysis",
                    },
                ],
                "suggested_questions": ["What caused the cost increase?"],
                "suggested_actions": ["Review contractor rates"],
                "confidence": 0.85,
            }
        ]
    })


def kpi_analysis_response() -> str:
    """KPIAnalysisAgent response: 2 findings about KPI breaches."""
    return json.dumps({
        "findings": [
            {
                "title": "Churn Rate Breach NKG-US",
                "severity": "high",
                "category": "kpi",
                "entity_code": "NKG-US",
                "description": "Monthly churn rate at 3.1% exceeds the 2.5% ceiling.",
                "rule_triggered": "churn_rate_ceiling",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Churn rate",
                        "value": "3.1% vs 2.5% ceiling",
                        "source": "KPI Data",
                    },
                ],
                "suggested_questions": ["Which clients churned?"],
                "suggested_actions": ["Conduct churn root cause analysis"],
                "confidence": 0.87,
            },
            {
                "title": "DSO Warning NKG-SG",
                "severity": "medium",
                "category": "kpi",
                "entity_code": "NKG-SG",
                "description": "Days Sales Outstanding at 52 days exceeds the 50-day warning threshold.",
                "rule_triggered": "dso_warning_threshold",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "DSO",
                        "value": "52 days vs 50 day threshold",
                        "source": "KPI Data",
                    },
                ],
                "suggested_questions": ["Are there overdue invoices?"],
                "suggested_actions": ["Review AR aging report"],
                "confidence": 0.80,
            },
        ]
    })


def analysis_performance_response() -> str:
    """AnalysisAgent (performance) response: 4 findings."""
    return json.dumps({
        "findings": [
            {
                "title": "Gross Margin Erosion NKG-SG",
                "severity": "high",
                "category": "margin",
                "entity_code": "NKG-SG",
                "description": "Gross margin dropped 3.2 percentage points, driven by higher contractor costs.",
                "impact_amount": 38400,
                "impact_currency": "SGD",
                "rule_triggered": "margin_erosion_alert",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Margin drop",
                        "value": "-3.2 pp (48.2% → 45.0%)",
                        "source": "Variance Analysis",
                    },
                ],
                "confidence": 0.87,
            },
            {
                "title": "Cash Collection Deterioration",
                "severity": "medium",
                "category": "cash_flow",
                "entity_code": "NKG-SG",
                "description": "DSO increased to 52 days, above the 50-day warning threshold.",
                "rule_triggered": "dso_warning_threshold",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "DSO trend",
                        "value": "52 days (prev: 48 days)",
                        "source": "KPI Trends",
                    },
                ],
                "confidence": 0.80,
            },
            {
                "title": "Customer Churn Spike NKG-US",
                "severity": "high",
                "category": "kpi",
                "entity_code": "NKG-US",
                "description": "Monthly churn at 3.1% breaches the 2.5% ceiling, indicating retention issues.",
                "rule_triggered": "churn_rate_ceiling",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "Churn rate",
                        "value": "3.1% vs 2.5% ceiling",
                        "source": "KPI Breaches",
                    },
                ],
                "confidence": 0.85,
            },
            {
                "title": "KPI-Financial Disconnect NKG-SG",
                "severity": "medium",
                "category": "kpi",
                "entity_code": "NKG-SG",
                "description": "MRR growth positive but gross margin declining, suggesting unprofitable growth.",
                "evidence": [
                    {
                        "type": "data_point",
                        "label": "MRR vs margin",
                        "value": "MRR up, margin down 3.2 pp",
                        "source": "Cross-analysis",
                    },
                ],
                "confidence": 0.75,
            },
        ]
    })


# ---------------------------------------------------------------------------
# Shared agents (narrative, quality gate)
# ---------------------------------------------------------------------------

def narrative_response() -> str:
    """NarrativeAgent response: markdown text."""
    return (
        "## Executive Summary\n\n"
        "The review identified several items requiring attention. "
        "Key findings include intercompany timing differences and "
        "cost anomalies that should be addressed before close.\n\n"
        "### Key Points\n"
        "- IC mismatch between NKG-JP and NKG-SG requires alignment\n"
        "- Consulting fee spike in NKG-US needs documentation\n"
        "- Manual journal entry for goodwill should be reviewed\n"
    )


def quality_gate_response() -> str:
    """QualityGateAgent response: JSON review with no escalation."""
    return json.dumps({
        "review": [
            {
                "finding_title": "IC Cut-Off",
                "passed": True,
                "issues": [],
            },
            {
                "finding_title": "Consulting Fee",
                "passed": True,
                "issues": [],
            },
            {
                "finding_title": "Goodwill Adjustment",
                "passed": True,
                "issues": [],
            },
        ],
        "overall_coherent": True,
        "escalation_flags": [],
    })
