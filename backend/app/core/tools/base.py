from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class BaseTool(ABC):
    """Base interface for all workflow tools."""

    name: str
    description: str

    @abstractmethod
    async def execute(self, params: dict[str, Any], session: AsyncSession) -> dict[str, Any]:
        """Execute the tool with the given parameters and return results."""
        ...
