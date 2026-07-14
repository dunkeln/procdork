from __future__ import annotations

from duckdb import StatementType
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from harness.olap import connect_duckdb


mcp = FastMCP("raw-analytics")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False)


@mcp.tool(annotations=READ_ONLY, structured_output=True)
def query_raw(sql: str) -> dict[str, object]:
    """Run one bounded read-only SQL statement against physical analytics tables."""
    with connect_duckdb() as connection:
        statements = connection.extract_statements(sql)
        if len(statements) != 1 or statements[0].type not in {
            StatementType.SELECT,
            StatementType.EXPLAIN,
        }:
            raise ValueError("Only one SELECT or EXPLAIN statement is allowed")
        connection.execute("set enable_external_access = false")
        result = connection.execute(sql)
        columns = [column[0] for column in result.description or []]
        rows = result.fetchmany(101)
    return {
        "columns": columns,
        "rows": [list(row) for row in rows[:100]],
        "truncated": len(rows) > 100,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
