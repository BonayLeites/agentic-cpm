from app.core.agent_base import AgentFinding


class ConfidenceScorer:
    """Heuristic confidence scorer (SPEC §3.7). Operates on a 0-1 scale."""

    def score_finding(self, finding: AgentFinding, step_data: dict) -> float:
        """Calculate confidence score for an individual finding."""
        score = 1.0

        # Penalty for evidence chain
        if len(finding.evidence) == 0:
            score -= 0.4
        else:
            has_data = any(e.type == "data_point" for e in finding.evidence)
            has_doc = any(e.type == "document_excerpt" for e in finding.evidence)
            has_rule = any(e.type == "rule_reference" for e in finding.evidence)

            if not has_data:
                score -= 0.2
            if not has_doc:
                score -= 0.1
            if not has_rule:
                score -= 0.05

        # Penalty for low document relevance
        doc_scores = [
            e.relevance_score
            for e in finding.evidence
            if e.type == "document_excerpt" and e.relevance_score is not None
        ]
        if doc_scores and min(doc_scores) < 0.5:
            score -= 0.15

        # Penalty for incomplete data
        if step_data.get("missing_entities"):
            score -= 0.1

        return max(0.0, min(1.0, round(score, 2)))

    def score_step(self, findings: list[AgentFinding]) -> float:
        """Average confidence for a step. No findings → high confidence."""
        if not findings:
            return 0.95
        return round(sum(f.confidence for f in findings) / len(findings), 2)

    def score_run(self, step_scores: list[float]) -> float:
        """Weighted average of step scores."""
        weights = [0.5, 1.0, 1.0, 0.5, 1.5, 1.5, 0.5]
        if len(step_scores) != len(weights):
            weights = [1.0] * len(step_scores)
        total = sum(s * w for s, w in zip(step_scores, weights))
        return round(total / sum(weights), 2)
