from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path

import duckdb
from pydantic import ConfigDict

from extraction import HarnessModel


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


def sync_ingestion_events(
    connection: duckdb.DuckDBPyConnection,
    event_jsonl: Path | str,
) -> IngestionEventSyncResult:
    path = Path(event_jsonl)
    if not path.is_file():
        raise ValueError(f"Ingestion event file does not exist: {path}")

    events = read_ingestion_events(path)
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
