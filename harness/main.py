from __future__ import annotations

import json
from pathlib import Path

import click

from extraction import extract_source
from load import append_manifest, load_manifest_duckdb, load_raw
from observations import new_session_id, observe_sql, record_sql_observation, split_sql_statements


@click.group()
def main() -> None:
    """Run the procdork harness."""


@main.command()
@click.argument("source")
@click.option("--source-type", default="unknown", show_default=True)
@click.option("--storage-root", default="data/lake", show_default=True)
@click.option("--duckdb-path", default="data/harness.duckdb", show_default=True)
@click.option("--manifest-jsonl", default=None, help="Optional JSONL backup path.")
def extract(source: str, source_type: str, storage_root: str, duckdb_path: str, manifest_jsonl: str | None) -> None:
    """Extract a URL or local file, then load raw bytes into the harness lake."""
    try:
        artifact = load_raw(extract_source(source, source_type), Path(storage_root))
        load_manifest_duckdb(artifact, Path(duckdb_path))
        if manifest_jsonl:
            append_manifest(artifact, Path(manifest_jsonl))
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(artifact.model_dump_json(indent=2))


@main.command("observe-sql")
@click.argument("sql", required=False)
@click.option("--sql-file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--duckdb-path", default="data/harness.duckdb", show_default=True)
@click.option("--actor", default="unknown", show_default=True)
@click.option("--session-id", default=None)
@click.option("--step", type=int, default=None)
def observe_sql_command(
    sql: str | None,
    sql_file: Path | None,
    duckdb_path: str,
    actor: str,
    session_id: str | None,
    step: int | None,
) -> None:
    """Fingerprint a SQL query and record its pattern observation."""
    if sql_file:
        sql = sql_file.read_text(encoding="utf-8")
    if not sql:
        raise click.ClickException("provide SQL as an argument or --sql-file")

    session_id = session_id or new_session_id("sql")
    step = step or 1
    record = record_sql_observation(observe_sql(sql, actor, session_id, step), Path(duckdb_path))
    click.echo(json.dumps(record.model_dump(mode="json"), indent=2))


@main.command("observe-sql-session")
@click.argument("sql_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--session-id", default=None)
@click.option("--duckdb-path", default="data/harness.duckdb", show_default=True)
@click.option("--actor", default="unknown", show_default=True)
def observe_sql_session_command(sql_file: Path, session_id: str | None, duckdb_path: str, actor: str) -> None:
    """Fingerprint each statement in a SQL file as one ordered session."""
    statements = split_sql_statements(sql_file.read_text(encoding="utf-8"))
    if not statements:
        raise click.ClickException("sql file did not contain any statements")

    session_id = session_id or new_session_id("sqlsess")
    records = [
        record_sql_observation(observe_sql(statement, actor, session_id, index), Path(duckdb_path))
        for index, statement in enumerate(statements, start=1)
    ]
    click.echo(json.dumps({"records": [record.model_dump(mode="json") for record in records]}, indent=2))


if __name__ == "__main__":
    main()
