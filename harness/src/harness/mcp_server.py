from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path
from typing import Callable, Literal

from duckdb import DuckDBPyConnection, StatementType
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    Annotations,
    CallToolResult,
    Icon,
    TextContent,
    ToolAnnotations,
)
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from .chart_payload import (
    build_chart,
    render_markdown_table,
)
from .connectors.workos import workos_auth
from .olap import connect_duckdb, load_dotenv_once


KNOWLEDGE_ROOT = Path(__file__).parent / "knowledge"
CHART_APP = files("harness").joinpath("chartui", "mcp-app.html")
CHART_APP_URI = "ui://charts/result/v3"
MAX_QUERY_ROWS = int(os.getenv("MCP_MAX_QUERY_ROWS", "500"))
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


load_dotenv_once()
mcp = FastMCP(
    "procdork",
    instructions=(
        "Begin every analytical workflow by reading the knowledge index. Use okf://bundle/index when resources "
        "are available; otherwise call read_knowledge with path='index'. Follow only the relevant knowledge links "
        "before table discovery or querying. "
        "Analytics tools are read-only. "
        "Prefer chartable summaries: find categorical dimensions, numeric measures, and *_bucket time labels before "
        "falling back to plain table output. Do not preflight charts with row-count queries; use knowledge and "
        "describe_table for planning, then issue one chart-ready query. If that query returns no rows, report the "
        "empty result and the table surface it came from instead of retrying row counts. "
        "Query results return a Markdown table or an MCP App chart plus deterministic key facts. "
        "Answer from key_facts; do not recompute values from charts. Include the returned table or chart when useful."
    ),
    icons=[
        Icon(
            src="https://procdork.vercel.app/procdork-logo.png",
            mimeType="image/png",
            sizes=["640x640"],
        )
    ],
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
    **workos_auth(
        os.getenv("WORKOS_AUTHKIT_DOMAIN"),
        os.getenv("MCP_RESOURCE_URL"),
    ),
)


def reader(path: Path) -> Callable[[], str]:
    def read() -> str:
        return path.read_text(encoding="utf-8")

    return read


for knowledge_path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
    concept_id = knowledge_path.relative_to(KNOWLEDGE_ROOT).with_suffix("").as_posix()
    mcp.resource(
        f"okf://bundle/{concept_id}",
        name=concept_id,
        title=concept_id.replace("/", " / ").replace("_", " ").title(),
        description=f"Git-authored OKF document: {concept_id}",
        mime_type="text/markdown",
        annotations=Annotations(audience=["assistant"], priority=1.0)
        if concept_id == "index"
        else None,
    )(reader(knowledge_path))


mcp.resource(
    CHART_APP_URI,
    name="chart_result",
    title="Analytics chart",
    description="Displays the chart returned by the analytics query tool.",
    mime_type="text/html;profile=mcp-app",
    meta={"ui": {"prefersBorder": False}},
)(reader(CHART_APP))


@mcp.tool(
    title="Read knowledge first",
    annotations=READ_ONLY,
)
def read_knowledge(path: str = "index") -> str:
    """Read reviewed knowledge. Call with path='index' before any analytics tool."""
    root = KNOWLEDGE_ROOT.resolve()
    requested = path.strip().removesuffix(".md").strip("/") or "index"
    document = (root / requested).resolve()
    if document.is_dir():
        document /= "index.md"
    else:
        document = document.with_suffix(".md")
    if not document.is_relative_to(root) or not document.is_file():
        raise ValueError(f"Unknown knowledge path: {path}")
    return document.read_text(encoding="utf-8")


@mcp.tool(
    title="Query analytics",
    annotations=READ_ONLY,
    meta={
        "ui": {"resourceUri": CHART_APP_URI},
        "ui/resourceUri": CHART_APP_URI,
    },
)
def query(
    sql: str,
    title: str = "Analytics result",
    chart_kind: Literal[
        "auto", "line", "bar", "heatmap", "scatter", "bubble", "histogram", "box", "table"
    ] = "auto",
) -> CallToolResult:
    """Run one read-only, chart-ready SQL query after reading relevant knowledge. Do not use this for row-count preflights."""
    columns, rows, truncated = execute_readonly(sql, MAX_QUERY_ROWS)
    payload = build_chart(columns, rows, title, chart_kind, truncated)
    structured: dict[str, object] = {
        "title": payload.title,
        "chart_kind": payload.chart_kind,
        "columns": payload.columns,
        "rows": payload.rows,
        "facts": payload.facts.model_dump(mode="json"),
        "key_facts": payload.key_facts,
        "truncated": payload.truncated,
    }
    if payload.chart_kind == "table":
        result = render_markdown_table(payload)
    else:
        result = "The associated MCP App renders this chart."
    markdown = "\n".join(
        [payload.title, "", result, "", *(f"- {fact}" for fact in payload.key_facts)]
    )
    return CallToolResult(
        content=[TextContent(type="text", text=markdown)],
        structuredContent=structured,
    )


def execute_readonly(
    sql: str, row_limit: int = MAX_QUERY_ROWS
) -> tuple[list[str], list[tuple[object, ...]], bool]:
    with connect_duckdb() as connection:
        statements = connection.extract_statements(sql)
        if len(statements) != 1 or statements[0].type not in {
            StatementType.SELECT,
            StatementType.EXPLAIN,
        }:
            raise ValueError(
                "Exactly one SELECT, DESCRIBE, SHOW, or EXPLAIN statement is allowed"
            )

        connection.execute("set enable_external_access = false")
        install_table_aliases(connection)
        result = connection.execute(sql)
        columns = [column[0] for column in result.description or []]
        rows = result.fetchmany(row_limit + 1)
    return columns, rows[:row_limit], len(rows) > row_limit


@mcp.tool(
    title="List available tables",
    annotations=READ_ONLY,
    structured_output=True,
)
def list_tables() -> dict[str, object]:
    """After reading relevant knowledge, list tables that are ready to query."""
    with connect_duckdb() as connection:
        rows = [[public_name] for public_name, *_ in published_tables(connection)]
    return {"columns": ["table_name"], "rows": rows, "truncated": False}


@mcp.tool(
    title="Describe a table",
    annotations=READ_ONLY,
    structured_output=True,
)
def describe_table(table_name: str) -> dict[str, object]:
    """After reading relevant knowledge, describe one table returned by list_tables."""
    with connect_duckdb() as connection:
        connection.execute("set enable_external_access = false")
        matches = [
            table for table in published_tables(connection) if table[0] == table_name
        ]
        if not matches:
            raise ValueError(f"Unknown table: {table_name}")
        _, catalog, schema, physical_name = matches[0]
        rows = connection.execute(
            """
            select column_name, data_type, is_nullable
            from information_schema.columns
            where table_catalog = ? and table_schema = ? and table_name = ?
            order by ordinal_position
            """,
            [catalog, schema, physical_name],
        ).fetchall()

    return {
        "table_name": table_name,
        "columns": ["column_name", "data_type", "is_nullable"],
        "rows": [
            [str(value) if value is not None else None for value in row] for row in rows
        ],
        "truncated": False,
    }


def published_tables(
    connection: DuckDBPyConnection,
) -> list[tuple[str, str, str, str]]:
    rows = connection.execute(
        """
        select table_catalog, table_schema, table_name
        from information_schema.tables
        where table_name like 'mart_%'
        order by table_catalog, table_schema, table_name
        """
    ).fetchall()
    tables = [
        (str(name).removeprefix("mart_"), str(catalog), str(schema), str(name))
        for catalog, schema, name in rows
    ]
    names = [table[0] for table in tables]
    if len(names) != len(set(names)):
        raise RuntimeError("Published table names must be unique")
    return tables


def install_table_aliases(connection: DuckDBPyConnection) -> None:
    for public_name, catalog, schema, physical_name in published_tables(connection):
        connection.execute(
            f"create or replace temp view {quoted(public_name)} as "
            f"select * from {quoted(catalog)}.{quoted(schema)}.{quoted(physical_name)}"
        )


def quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def serve() -> None:
    mcp.run(transport="streamable-http")
