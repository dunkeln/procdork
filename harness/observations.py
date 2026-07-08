from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
import json
import re
from secrets import token_hex
from pathlib import Path

import duckdb

from extraction import HarnessModel
from olap import connect_duckdb


class SqlObservation(HarnessModel):
    session_id: str | None = None
    step_number: int | None = None
    pattern_id: str
    canonical_sql: str
    original_sql: str
    source_relations: list[str]
    output_columns: list[str]
    operation: str
    grain: list[str]
    observed_at: datetime
    actor: str


class WorkflowSummary(HarnessModel):
    workflow_pattern_id: str
    workflow_pattern: list[str]
    workflow_count: int


class ObservationRecord(HarnessModel):
    observation: SqlObservation
    pattern_count: int
    workflow: WorkflowSummary | None = None


def observe_sql(
    sql: str,
    actor: str = "unknown",
    session_id: str | None = None,
    step_number: int | None = None,
) -> SqlObservation:
    canonical_sql = canonicalize_sql(sql)
    return SqlObservation(
        session_id=session_id,
        step_number=step_number,
        pattern_id=f"sql_{sha256(canonical_sql.encode()).hexdigest()[:12]}",
        canonical_sql=canonical_sql,
        original_sql=sql,
        source_relations=source_relations(canonical_sql),
        output_columns=output_columns(canonical_sql),
        operation=operation(canonical_sql),
        grain=grain(canonical_sql),
        observed_at=datetime.now(UTC),
        actor=actor,
    )


def record_sql_observation(
    observation: SqlObservation,
    db_path: Path | str | None = None,
) -> ObservationRecord:
    with connect_duckdb(db_path) as con:
        ensure_sql_observations(con)
        con.execute(
            """
            insert into sql_observations (
                session_id,
                step_number,
                pattern_id,
                canonical_sql,
                original_sql,
                source_relations,
                output_columns,
                operation,
                grain,
                observed_at,
                actor
            )
            values (?, ?, ?, ?, ?, ?::json, ?::json, ?, ?::json, ?, ?)
            """,
            [
                observation.session_id,
                observation.step_number,
                observation.pattern_id,
                observation.canonical_sql,
                observation.original_sql,
                json.dumps(observation.source_relations),
                json.dumps(observation.output_columns),
                observation.operation,
                json.dumps(observation.grain),
                observation.observed_at,
                observation.actor,
            ],
        )
        pattern_count = con.execute(
            "select count(*) from sql_observations where pattern_id = ?",
            [observation.pattern_id],
        ).fetchone()[0]
        workflow = workflow_summary(con, observation.session_id) if observation.session_id else None
        return ObservationRecord(observation=observation, pattern_count=pattern_count, workflow=workflow)


def ensure_sql_observations(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        create table if not exists sql_observations (
            session_id varchar,
            step_number integer,
            pattern_id varchar,
            canonical_sql varchar,
            original_sql varchar,
            source_relations json,
            output_columns json,
            operation varchar,
            grain json,
            observed_at timestamptz,
            actor varchar
        )
        """
    )
    con.execute("alter table sql_observations add column if not exists session_id varchar")
    con.execute("alter table sql_observations add column if not exists step_number integer")


def workflow_summary(con: duckdb.DuckDBPyConnection, session_id: str) -> WorkflowSummary:
    workflow_pattern = [
        row[0]
        for row in con.execute(
            """
            select pattern_id
            from sql_observations
            where session_id = ?
            order by coalesce(step_number, 2147483647), observed_at, pattern_id
            """,
            [session_id],
        ).fetchall()
    ]
    workflow_pattern_id = workflow_id(workflow_pattern)
    workflow_count = sum(
        1
        for pattern in workflow_patterns(con).values()
        if pattern == workflow_pattern
    )
    return WorkflowSummary(
        workflow_pattern_id=workflow_pattern_id,
        workflow_pattern=workflow_pattern,
        workflow_count=workflow_count,
    )


def workflow_patterns(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    rows = con.execute(
        """
        select session_id, pattern_id
        from sql_observations
        where session_id is not null
        order by session_id, coalesce(step_number, 2147483647), observed_at, pattern_id
        """
    ).fetchall()
    patterns: dict[str, list[str]] = {}
    for session_id, pattern_id in rows:
        patterns.setdefault(session_id, []).append(pattern_id)
    return patterns


def workflow_id(pattern_ids: list[str]) -> str:
    return f"wf_{sha256(' -> '.join(pattern_ids).encode()).hexdigest()[:12]}"


def new_session_id(prefix: str = "sql") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}_{timestamp}_{token_hex(4)}"


def split_sql_statements(sql: str) -> list[str]:
    # ponytail: semicolon splitter; use a parser if procedural SQL dialects need exact string handling.
    return [part.strip() for part in sql.split(";") if part.strip()]


def canonicalize_sql(sql: str) -> str:
    # ponytail: regex canonicalizer; swap for a SQL parser when dialect coverage matters.
    text = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    text = re.sub(r"--.*?$", " ", text, flags=re.MULTILINE)
    text = re.sub(r"'(?:''|[^'])*'", "?", text)
    text = re.sub(r'"(?:""|[^"])*"', "?", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "?", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "?", text)
    return re.sub(r"\s+", " ", text).strip().lower().rstrip(";")


def source_relations(canonical_sql: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:from|join)\s+([a-z_][\w.]*)(?!\s*\()", canonical_sql)))


def output_columns(canonical_sql: str) -> list[str]:
    match = re.search(r"\bselect\s+(.*?)\s+\bfrom\b", canonical_sql)
    if not match:
        return []
    return [clean_column(part) for part in split_csv(match.group(1))]


def grain(canonical_sql: str) -> list[str]:
    match = re.search(r"\bgroup\s+by\s+(.*?)(?:\border\s+by\b|\blimit\b|$)", canonical_sql)
    if not match:
        return []
    return [part.strip() for part in split_csv(match.group(1))]


def operation(canonical_sql: str) -> str:
    if re.search(r"\bgroup\s+by\b|\b(count|sum|avg|min|max)\s*\(", canonical_sql):
        return "aggregate"
    if re.search(r"\bjoin\b", canonical_sql):
        return "join"
    return "select"


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def clean_column(value: str) -> str:
    value = re.sub(r"\s+as\s+[a-z_][\w]*$", "", value.strip())
    return value.split(".")[-1]
