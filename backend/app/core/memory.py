import asyncio
from typing import Any


class WorkflowMemory:
    """Thread-safe dict wrapper for sharing data between agents."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value

    async def update(self, data: dict[str, Any]) -> None:
        async with self._lock:
            self._data.update(data)

    async def snapshot(self) -> dict[str, Any]:
        """Return a copy of the current state (for logging/audit)."""
        async with self._lock:
            return dict(self._data)
