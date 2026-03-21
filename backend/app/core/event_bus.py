import asyncio

# Global dict: run_id → asyncio.Queue (single process, sufficient for demo)
_run_queues: dict[int, asyncio.Queue[str | None]] = {}


def create_queue(run_id: int) -> asyncio.Queue[str | None]:
    """Create and register an SSE event queue for a run."""
    q: asyncio.Queue[str | None] = asyncio.Queue()
    _run_queues[run_id] = q
    return q


def get_queue(run_id: int) -> asyncio.Queue[str | None] | None:
    """Get the queue for a run, or None if it does not exist."""
    return _run_queues.get(run_id)


def remove_queue(run_id: int) -> None:
    """Remove the queue for a run (cleanup)."""
    _run_queues.pop(run_id, None)
