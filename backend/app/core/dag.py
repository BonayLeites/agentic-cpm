class SimpleDAG:
    """Directed acyclic graph for ordering step execution."""

    def __init__(self, graph: dict[str, set[str]]) -> None:
        self._graph = graph

    def get_ready_steps(self, completed: set[str]) -> list[str]:
        """Return steps whose dependencies are satisfied and have not yet completed."""
        ready = [
            step
            for step, deps in self._graph.items()
            if step not in completed and deps.issubset(completed)
        ]
        return sorted(ready)  # sorted for deterministic test ordering

    def has_pending(self, completed: set[str]) -> bool:
        """True if there are still pending steps."""
        return len(completed) < len(self._graph)
