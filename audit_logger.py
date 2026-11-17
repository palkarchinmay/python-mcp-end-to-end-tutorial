import json
import logging
import sys
from datetime import datetime, timezone
import time
import functools
from request_context import role_var

from request_context import correlation_id_var


logger = logging.getLogger("mcp.audit")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

def audit_tool(tool_name: str):
    """Decorator for auditing asynchronous MCP tool execution."""

    def decorator(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            start_time = time.perf_counter()
            correlation_id = correlation_id_var.get()
            role = role_var.get()

            try:
                result = await func(*args, **kwargs)

                duration_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                audit_event(
                        event="mcp_tool_execution",
                        correlation_id=correlation_id,
                        role=role,
                        tool=tool_name,
                        status="success",
                        duration_ms=round(duration_ms, 2),
                    )

                return result

            except Exception as exc:

                duration_ms = (
                    time.perf_counter() - start_time
                ) * 1000

                audit_event(
                        event="mcp_tool_execution",
                        correlation_id=correlation_id,
                        role=role,
                        tool=tool_name,
                        status="failed",
                        duration_ms=round(duration_ms, 2),
                        error_type=type(exc).__name__,
                    )

                raise

        return wrapper

    return decorator    


def audit_event(
    event: str,
    correlation_id: str | None,
    role: str | None = None,
    tool: str | None = None,
    status: str | None = None,
    duration_ms: float | None = None,
    error_type: str | None = None,
):
    """Emit a structured audit event without sensitive payloads."""

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "correlation_id": correlation_id,
        "role": role,
        "tool": tool,
        "status": status,
        "duration_ms": duration_ms,
        "error_type": error_type,
    }

    logger.info(json.dumps(record))

