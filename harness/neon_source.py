from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from extraction import HarnessModel
from olap import connect_duckdb, load_dotenv_once


CHAT_TABLES = ["sessions", "messages", "message_events", "sources", "message_sources"]


class NeonSyncResult(HarnessModel):
    source: str = "neon_chat"
    tables: dict[str, int]


def sync_neon_chat(db_path: str | None = None, database_url: str | None = None) -> NeonSyncResult:
    load_dotenv_once()
    url = postgres_scanner_url(database_url or os.environ.get("DATABASE_URL", ""))
    if not url:
        raise ValueError("DATABASE_URL is not configured")

    tables: dict[str, int] = {}
    with connect_duckdb(db_path) as con:
        con.execute("install postgres")
        con.execute("load postgres")
        con.execute(f"attach {sql_literal(url)} as neon_src (type postgres, read_only)")
        try:
            for table in CHAT_TABLES:
                target = f"app_{table}"
                con.execute(f"create or replace table {target} as select * from neon_src.public.{table}")
                tables[target] = con.execute(f"select count(*) from {target}").fetchone()[0]
        finally:
            con.execute("detach neon_src")
    return NeonSyncResult(tables=tables)


def postgres_scanner_url(url: str) -> str:
    parts = urlsplit(url)
    query = urlencode(
        [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "channel_binding"]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
