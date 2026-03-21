import asyncio

from app.core.agent_base import AgentContext, AgentResult, BaseAgent, StepMetrics


class EchoAgent(BaseAgent):
    """Test agent used in Phase 5. Sleeps 1s and returns an empty result."""

    def __init__(self, name: str, step_order: int) -> None:
        self.name = name
        self.description = f"Echo agent for step {name}"
        self.model = "gpt-4o-mini"
        self._step_order = step_order

    async def execute(self, context: AgentContext) -> AgentResult:
        await asyncio.sleep(1)
        return AgentResult(
            status="completed",
            findings=[],
            data={f"{self.name}_done": True},
            metrics=StepMetrics(
                duration_ms=1000,
                finding_count=0,
                confidence_score=0.95,
                tools_used=[],
                llm_calls=[],
                cost=0.0,
            ),
        )
