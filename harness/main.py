from __future__ import annotations

from pathlib import Path

import click

from extraction import extract_source
from load import append_manifest, load_manifest_duckdb, load_raw
from neon_source import sync_neon_chat


@click.group()
def main() -> None:
    """Run the procdork harness."""


@main.command()
@click.argument("source")
@click.option("--source-type", default="unknown", show_default=True)
@click.option("--storage-root", default="data/lake", show_default=True)
@click.option("--duckdb-path", default=None, help="DuckDB/MotherDuck path. Defaults to DUCKDB_PATH or local data/harness.duckdb.")
@click.option("--manifest-jsonl", default=None, help="Optional JSONL backup path.")
def extract(source: str, source_type: str, storage_root: str, duckdb_path: str | None, manifest_jsonl: str | None) -> None:
    """Extract a URL or local file, then load raw bytes into the harness lake."""
    try:
        artifact = load_raw(extract_source(source, source_type), Path(storage_root))
        load_manifest_duckdb(artifact, duckdb_path)
        if manifest_jsonl:
            append_manifest(artifact, Path(manifest_jsonl))
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(artifact.model_dump_json(indent=2))


@main.command("sync-neon-chat")
@click.option("--duckdb-path", default=None, help="DuckDB/MotherDuck path. Defaults to DUCKDB_PATH or local data/harness.duckdb.")
def sync_neon_chat_command(duckdb_path: str | None) -> None:
    """Copy demo chat tables from Neon into the harness OLAP database."""
    try:
        result = sync_neon_chat(duckdb_path)
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(result.model_dump_json(indent=2))


@main.command("serve-mcp")
def serve_mcp_command() -> None:
    """Serve the Git-authored OKF bundle as read-only MCP resources."""
    from mcp_server import serve

    serve()


if __name__ == "__main__":
    main()
