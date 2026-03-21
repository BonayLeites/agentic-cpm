from dataclasses import dataclass, field

from app.agents.analysis import AnalysisAgent
from app.agents.anomaly_detector import AnomalyDetectorAgent
from app.agents.data_loader import DataLoaderAgent
from app.agents.doc_search import DocSearchAgent
from app.agents.ic_checker import ICCheckAgent
from app.agents.kpi_analyzer import KPIAnalysisAgent
from app.agents.narrative import NarrativeAgent
from app.agents.quality_gate import QualityGateAgent
from app.agents.variance_analyzer import VarianceAnalyzerAgent
from app.core.agent_base import BaseAgent
from app.core.dag import SimpleDAG


@dataclass
class StepDefinition:
    """Definition of a step within a workflow."""

    step_order: int
    step_name: str
    agent_class: type[BaseAgent]
    dependencies: set[str] = field(default_factory=set)


# --- Workflow registries ---

CONSOLIDATION_STEPS: list[StepDefinition] = [
    StepDefinition(1, "load_data", DataLoaderAgent),
    StepDefinition(2, "ic_check", ICCheckAgent, {"load_data"}),
    StepDefinition(3, "anomaly_detect", AnomalyDetectorAgent, {"load_data"}),
    StepDefinition(4, "doc_search", DocSearchAgent, {"ic_check", "anomaly_detect"}),
    StepDefinition(5, "analysis", AnalysisAgent, {"doc_search"}),
    StepDefinition(6, "narrative", NarrativeAgent, {"analysis"}),
    StepDefinition(7, "quality_gate", QualityGateAgent, {"narrative"}),
]

PERFORMANCE_STEPS: list[StepDefinition] = [
    StepDefinition(1, "load_data", DataLoaderAgent),
    StepDefinition(2, "variance_analysis", VarianceAnalyzerAgent, {"load_data"}),
    StepDefinition(3, "kpi_analysis", KPIAnalysisAgent, {"load_data"}),
    StepDefinition(4, "doc_search", DocSearchAgent, {"variance_analysis", "kpi_analysis"}),
    StepDefinition(5, "analysis", AnalysisAgent, {"doc_search"}),
    StepDefinition(6, "narrative", NarrativeAgent, {"analysis"}),
    StepDefinition(7, "quality_gate", QualityGateAgent, {"narrative"}),
]

_REGISTRY: dict[str, list[StepDefinition]] = {
    "consolidation": CONSOLIDATION_STEPS,
    "performance": PERFORMANCE_STEPS,
}


def get_workflow_steps(workflow_type: str) -> list[StepDefinition]:
    """Return step definitions for a given workflow type."""
    steps = _REGISTRY.get(workflow_type)
    if steps is None:
        raise ValueError(f"Unknown workflow type: {workflow_type}")
    return steps


def get_workflow_dag(workflow_type: str) -> SimpleDAG:
    """Build a DAG from step definitions."""
    steps = get_workflow_steps(workflow_type)
    graph = {s.step_name: set(s.dependencies) for s in steps}
    return SimpleDAG(graph)
