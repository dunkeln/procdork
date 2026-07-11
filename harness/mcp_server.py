from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

import jwt
from duckdb import StatementType
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.types import Icon, ToolAnnotations
from jwt import PyJWKClient
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from olap import connect_duckdb, load_dotenv_once


OKF_ROOT = Path(__file__).parent / "okf"
MAX_QUERY_ROWS = int(os.getenv("MCP_MAX_QUERY_ROWS", "500"))
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


class WorkOSTokenVerifier:
    def __init__(self, issuer: str, audience: str) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks = PyJWKClient(f"{self.issuer}/oauth2/jwks")

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.PyJWTError:
            return None

        scopes = claims.get("scope") or ""
        return AccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("azp") or "",
            scopes=scopes.split() if isinstance(scopes, str) else scopes,
            expires_at=claims.get("exp"),
            resource=self.audience,
            subject=claims.get("sub"),
            claims=claims,
        )


def workos_auth() -> dict[str, object]:
    load_dotenv_once()
    issuer = os.getenv("WORKOS_AUTHKIT_DOMAIN")
    resource = os.getenv("MCP_RESOURCE_URL")
    if not issuer and not resource:
        return {}
    if not issuer or not resource:
        raise RuntimeError("WORKOS_AUTHKIT_DOMAIN and MCP_RESOURCE_URL must be configured together")
    return {
        "token_verifier": WorkOSTokenVerifier(issuer, resource),
        "auth": AuthSettings(issuer_url=issuer, resource_server_url=resource),
    }

mcp = FastMCP(
    "procdork",
    instructions="Use OKF resources for durable context. Analytics tools are read-only and results are bounded.",
    icons=[Icon(src="https://procdork.vercel.app/procdork-logo.png", mimeType="image/png", sizes=["640x640"])],
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
    **workos_auth(),
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


@mcp.tool(
    title="Query analytics",
    annotations=READ_ONLY,
    structured_output=True,
)
def query(sql: str) -> dict[str, object]:
    """Run one read-only DuckDB SQL statement and return a bounded result."""
    with connect_duckdb() as connection:
        statements = connection.extract_statements(sql)
        if len(statements) != 1 or statements[0].type not in {StatementType.SELECT, StatementType.EXPLAIN}:
            raise ValueError("Exactly one SELECT, DESCRIBE, SHOW, or EXPLAIN statement is allowed")

        connection.execute("set enable_external_access = false")
        result = connection.execute(sql)
        columns = [column[0] for column in result.description or []]
        rows = result.fetchmany(MAX_QUERY_ROWS + 1)

    return {
        "columns": columns,
        "rows": [[str(value) if value is not None else None for value in row] for row in rows[:MAX_QUERY_ROWS]],
        "truncated": len(rows) > MAX_QUERY_ROWS,
    }


@mcp.tool(
    title="List available marts",
    annotations=READ_ONLY,
    structured_output=True,
)
def list_marts() -> dict[str, object]:
    """List stable analytics marts that are ready to query."""
    return query(
        """
        select table_catalog, table_schema, table_name, table_type
        from information_schema.tables
        where table_name like 'mart_%'
        order by table_catalog, table_schema, table_name
        """
    )


@mcp.tool(
    title="Describe an analytics mart",
    annotations=READ_ONLY,
    structured_output=True,
)
def describe_mart(mart_name: str) -> dict[str, object]:
    """List the columns and types for one mart returned by list_marts."""
    with connect_duckdb() as connection:
        connection.execute("set enable_external_access = false")
        rows = connection.execute(
            """
            select table_catalog, table_schema, table_name, column_name, data_type, is_nullable
            from information_schema.columns
            where table_name = ? and table_name like 'mart_%'
            order by table_catalog, table_schema, ordinal_position
            """,
            [mart_name],
        ).fetchall()

    if not rows:
        raise ValueError(f"Unknown mart: {mart_name}")

    return {
        "columns": ["table_catalog", "table_schema", "table_name", "column_name", "data_type", "is_nullable"],
        "rows": [[str(value) if value is not None else None for value in row] for row in rows],
        "truncated": False,
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def serve() -> None:
    mcp.run(transport="streamable-http")
