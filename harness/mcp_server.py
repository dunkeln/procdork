from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse


OKF_ROOT = Path(__file__).parent / "okf"

mcp = FastMCP(
    "procdork-harness",
    instructions="Read OKF resources for durable context before using live data tools.",
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
)


def reader(path: Path) -> Callable[[], str]:
    def read() -> str:
        return path.read_text(encoding="utf-8")

    return read


for okf_path in sorted(OKF_ROOT.rglob("*.md")):
    concept_id = okf_path.relative_to(OKF_ROOT).with_suffix("").as_posix()
    mcp.resource(
        f"okf://bundle/{concept_id}",
        name=concept_id,
        title=concept_id.replace("/", " / ").replace("_", " ").title(),
        description=f"Git-authored OKF document: {concept_id}",
        mime_type="text/markdown",
    )(reader(okf_path))


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def serve() -> None:
    mcp.run(transport="streamable-http")
