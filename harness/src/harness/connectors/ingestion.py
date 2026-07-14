from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import dlt
import duckdb
from pydantic import ConfigDict

from ..extraction import HarnessModel


class IngestionEvent(HarnessModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_type: str
    schema_version: str
    emitted_at: datetime
    job_id: str
    session_id: str | None = None
    turn_id: str | None = None
    status: str
    duration_ms: int
    sources: list[dict[str, object]]
    observed_suppliers: list[dict[str, object]]
    canonical_suppliers: list[dict[str, object]]
    source_claims: list[dict[str, object]]
    conflicts: list[dict[str, object]]
    artifacts: list[dict[str, object]]


class IngestionEventSyncResult(HarnessModel):
    source: str
    events_read: int
    events_inserted: int
    duplicate_events: int


EVENT_COLUMNS = {
    "event_id": {"data_type": "text"},
    "event_type": {"data_type": "text"},
    "schema_version": {"data_type": "text"},
    "emitted_at": {"data_type": "timestamp", "timezone": True},
    "job_id": {"data_type": "text"},
    "session_id": {"data_type": "text", "nullable": True},
    "turn_id": {"data_type": "text", "nullable": True},
    "status": {"data_type": "text"},
    "duration_ms": {"data_type": "bigint"},
    "payload": {"data_type": "json"},
}


@dlt.resource(
    table_name="raw_ingestion_events",
    write_disposition="merge",
    primary_key="event_id",
    columns=EVENT_COLUMNS,
    max_table_nesting=0,
)
def raw_ingestion_event_rows(events: list[IngestionEvent]):
    for event in events:
        yield event_row(event)


def sync_ingestion_events(
    connection: duckdb.DuckDBPyConnection,
    event_jsonl: Path | str,
) -> IngestionEventSyncResult:
    path = Path(event_jsonl)
    if not path.is_file():
        raise ValueError(f"Ingestion event file does not exist: {path}")

    events = read_ingestion_events(path)
    if use_dlt_loader(connection):
        return sync_ingestion_events_dlt(connection, path, events)
    return sync_ingestion_events_sql(connection, path, events)


def sync_ingestion_events_dlt(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    events: list[IngestionEvent],
) -> IngestionEventSyncResult:
    before = raw_ingestion_event_count(connection)
    dlt.pipeline(
        pipeline_name="procdork_ingestion_events",
        destination=dlt.destinations.duckdb(connection),
        dataset_name="main",
        dev_mode=False,
    ).run(raw_ingestion_event_rows(events))
    inserted = raw_ingestion_event_count(connection) - before
    return IngestionEventSyncResult(
        source=str(path),
        events_read=len(events),
        events_inserted=inserted,
        duplicate_events=len(events) - inserted,
    )


def sync_ingestion_events_sql(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    events: list[IngestionEvent],
) -> IngestionEventSyncResult:
    ensure_raw_ingestion_events(connection)
    existing_ids = {
        str(row[0]) for row in connection.execute("select event_id from raw_ingestion_events").fetchall()
    }
    inserted = 0
    duplicates = 0
    for event in events:
        if event.event_id in existing_ids:
            duplicates += 1
            continue
        connection.execute(
            """
            insert into raw_ingestion_events values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::json)
            """,
            [
                event.event_id,
                event.event_type,
                event.schema_version,
                event.emitted_at,
                event.job_id,
                event.session_id,
                event.turn_id,
                event.status,
                event.duration_ms,
                json.dumps(event.model_dump(mode="json"), sort_keys=True),
            ],
        )
        inserted += 1
        existing_ids.add(event.event_id)
    return IngestionEventSyncResult(
        source=str(path),
        events_read=len(events),
        events_inserted=inserted,
        duplicate_events=duplicates,
    )


def use_dlt_loader(connection: duckdb.DuckDBPyConnection) -> bool:
    if not table_exists(connection, "raw_ingestion_events"):
        return True
    columns = {
        str(row[0])
        for row in connection.execute(
            """
            select column_name
            from information_schema.columns
            where table_schema = 'main' and table_name = 'raw_ingestion_events'
            """
        ).fetchall()
    }
    return "_dlt_load_id" in columns and "_dlt_id" in columns


def table_exists(connection: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    return bool(
        connection.execute(
            """
            select 1
            from information_schema.tables
            where table_schema = 'main' and table_name = ?
            """,
            [table_name],
        ).fetchone()
    )


def raw_ingestion_event_count(connection: duckdb.DuckDBPyConnection) -> int:
    if not table_exists(connection, "raw_ingestion_events"):
        return 0
    return int(connection.execute("select count(*) from raw_ingestion_events").fetchone()[0])


def ensure_raw_ingestion_events(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        create table if not exists raw_ingestion_events (
            event_id varchar,
            event_type varchar,
            schema_version varchar,
            emitted_at timestamptz,
            job_id varchar,
            session_id varchar,
            turn_id varchar,
            status varchar,
            duration_ms ubigint,
            payload json
        )
        """
    )


def event_row(event: IngestionEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "schema_version": event.schema_version,
        "emitted_at": event.emitted_at,
        "job_id": event.job_id,
        "session_id": event.session_id,
        "turn_id": event.turn_id,
        "status": event.status,
        "duration_ms": event.duration_ms,
        "payload": event.model_dump(mode="json"),
    }


def read_ingestion_events(path: Path) -> list[IngestionEvent]:
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(IngestionEvent.model_validate_json(line))
        except ValueError as exc:
            raise ValueError(f"Invalid ingestion event at {path}:{line_number}: {exc}") from exc
    return events
