from __future__ import annotations

import os
from typing import Any
from uuid import UUID

import logfire

from harness.mcp_server import mcp


logfire.configure(
    service_name="procdork-harness",
    environment=os.environ.get("VERCEL_ENV", "local"),
    send_to_logfire="if-token-present",
    console=False,
)


def e2e_trace(app: Any) -> Any:
    async def traced(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        run_id = valid_run_id(scope)
        if run_id is None:
            await app(scope, receive, send)
            return

        async def send_with_run_id(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-e2e-run-id", run_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        with logfire.span("e2e.mcp_request", **{"e2e.run_id": run_id}):
            await app(scope, receive, send_with_run_id)

    return traced


def valid_run_id(scope: dict[str, Any]) -> str | None:
    for name, value in scope.get("headers", []):
        if name.lower() != b"x-e2e-run-id":
            continue
        try:
            return str(UUID(value.decode("ascii")))
        except (UnicodeDecodeError, ValueError):
            return None
    return None


app = logfire.instrument_asgi(e2e_trace(mcp.streamable_http_app()))
