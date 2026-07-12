from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import duckdb

from extraction import HarnessModel


CHAT_TABLES = ["sessions", "messages", "message_events", "sources", "message_sources"]


class NeonSyncResult(HarnessModel):
    source: str = "neon_chat"
    tables: dict[str, int]


def sync_neon_chat(
    connection: duckdb.DuckDBPyConnection, database_url: str
) -> NeonSyncResult:
    url = postgres_scanner_url(database_url)
    if not url:
        raise ValueError("DATABASE_URL is not configured")

    tables: dict[str, int] = {}
    connection.execute("install postgres")
    connection.execute("load postgres")
    connection.execute(f"attach {sql_literal(url)} as neon_src (type postgres, read_only)")
    try:
        for table in CHAT_TABLES:
            target = f"app_{table}"
            connection.execute(
                f"create or replace table {target} as select * from neon_src.public.{table}"
            )
            tables[target] = connection.execute(f"select count(*) from {target}").fetchone()[0]
    finally:
        connection.execute("detach neon_src")
    return NeonSyncResult(tables=tables)


def postgres_scanner_url(url: str) -> str:
    parts = urlsplit(url)
    query = urlencode(
        [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "channel_binding"]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
