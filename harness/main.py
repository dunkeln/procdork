from __future__ import annotations

from pathlib import Path

import click

from extraction import extract_source
from load import append_manifest, load_manifest_duckdb, load_raw


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


if __name__ == "__main__":
    main()
