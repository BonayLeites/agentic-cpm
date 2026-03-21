import logging
import time
from typing import Any

from openai import AsyncAzureOpenAI
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# Approximate prices per 1K tokens (Azure GPT-4o / GPT-4o-mini)
_COST_PER_1K = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


class LLMResponse(BaseModel):
    """Result of a single LLM call."""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    model: str = ""
    duration_ms: int = 0


class LLMGateway:
    """Thin wrapper over the openai SDK configured for Azure AI Foundry."""

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_ai_endpoint,
            api_key=settings.azure_ai_api_key,
            api_version="2024-08-01-preview",
        )
        self._deployments = {
            "gpt-4o": settings.azure_ai_deployment_gpt4o,
            "gpt-4o-mini": settings.azure_ai_deployment_mini,
        }

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        response_format: dict[str, str] | None = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Execute a chat completion call with usage and cost tracking."""
        deployment = self._deployments.get(model, model)

        kwargs: dict[str, Any] = {
            "model": deployment,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        start = time.monotonic()
        response = await self._client.chat.completions.create(**kwargs)
        duration_ms = int((time.monotonic() - start) * 1000)

        choice = response.choices[0]
        usage = response.usage

        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        rates = _COST_PER_1K.get(model, _COST_PER_1K["gpt-4o"])
        cost = (prompt_tokens / 1000 * rates["input"]) + (
            completion_tokens / 1000 * rates["output"]
        )

        return LLMResponse(
            content=choice.message.content or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=round(cost, 6),
            model=model,
            duration_ms=duration_ms,
        )


_gateway: LLMGateway | None = None


def get_gateway() -> LLMGateway:
    """Return the LLMGateway singleton (reuses the connection pool)."""
    global _gateway  # noqa: PLW0603
    if _gateway is None:
        _gateway = LLMGateway()
    return _gateway
