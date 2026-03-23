from __future__ import annotations

from time import perf_counter
from typing import Any, Callable


def build_tool_response(
    tool_name: str,
    tool_input: dict[str, Any],
    executor: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    started_at = perf_counter()
    try:
        payload = executor() or {}
        success = payload.get("found", True)
        error = None if success else payload.get("message", "Tool execution returned no result.")
        latency_ms = int((perf_counter() - started_at) * 1000)
        return {
            "success": success,
            "tool_name": tool_name,
            "input": tool_input,
            "output": payload,
            "latency_ms": latency_ms,
            "error": error,
            **payload,
        }
    except Exception as exc:
        latency_ms = int((perf_counter() - started_at) * 1000)
        return {
            "success": False,
            "tool_name": tool_name,
            "input": tool_input,
            "output": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }

