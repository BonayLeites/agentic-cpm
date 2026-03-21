import json
from typing import Any


def format_sse_event(event_type: str, data: Any) -> str:
    """Format an SSE event according to the protocol.

    Format: event: {type}\\ndata: {json}\\n\\n
    """
    json_data = json.dumps(data, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n"
