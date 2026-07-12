from __future__ import annotations

from functools import partial
import json
import os
from pathlib import Path

import click

from connectors.neon import sync_neon_chat
from connectors.procdork import chat_dataset_version, load_chat_cases, replay_chat
from connectors.sources import read_url_or_file
from connectors.storage import append_jsonl, write_local_blob
from evaluations import ensure_evaluation_table, latest_result, record_evaluation
from evaluators.inline_citations import NAME as EVALUATOR_NAME
from evaluators.inline_citations import evaluate
from extraction import extract_source
from load import load_manifest_duckdb, load_raw
from olap import connect_duckdb, load_dotenv_once


@click.group()
def main() -> None:
    """Run the procdork harness."""


@main.command()
@click.argument("source")
@click.option("--source-type", default="unknown", show_default=True)
@click.option("--storage-root", default="data/lake", show_default=True)
@click.option(
    "--duckdb-path",
    default=None,
    help="DuckDB/MotherDuck path. Defaults to DUCKDB_PATH or local data/harness.duckdb.",
)
@click.option("--manifest-jsonl", default=None, help="Optional JSONL backup path.")
def extract(
    source: str,
    source_type: str,
    storage_root: str,
    duckdb_path: str | None,
    manifest_jsonl: str | None,
) -> None:
    """Extract a URL or local file, then load raw bytes into the harness lake."""
    try:
        artifact = load_raw(
            extract_source(source, read_url_or_file, source_type),
            partial(write_local_blob, storage_root=Path(storage_root)),
        )
        load_manifest_duckdb(artifact, duckdb_path)
        if manifest_jsonl:
            append_jsonl(artifact, Path(manifest_jsonl))
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(artifact.model_dump_json(indent=2))


@main.command("sync-neon-chat")
@click.option(
    "--duckdb-path",
    default=None,
    help="DuckDB/MotherDuck path. Defaults to DUCKDB_PATH or local data/harness.duckdb.",
)
def sync_neon_chat_command(duckdb_path: str | None) -> None:
    """Copy demo chat tables from Neon into the harness OLAP database."""
    try:
        load_dotenv_once()
        with connect_duckdb(duckdb_path) as connection:
            result = sync_neon_chat(connection, os.environ.get("DATABASE_URL", ""))
    except (OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(result.model_dump_json(indent=2))


@main.command("eval-replay")
@click.option(
    "--system-version",
    required=True,
    help="Candidate release or commit being evaluated.",
)
@click.option("--target-url", default="https://procdork.vercel.app", show_default=True)
@click.option(
    "--case-id", default=None, help="Replay one historical assistant message ID."
)
@click.option(
    "--previous-result",
    type=click.Choice(["all", "pass", "fail"]),
    default="all",
    show_default=True,
    help="Replay all eligible cases or only previous successes/failures.",
)
@click.option("--limit", default=1, show_default=True, type=click.IntRange(1, 100))
@click.option("--duckdb-path", default=None, help="DuckDB/MotherDuck path.")
def eval_replay(
    system_version: str,
    target_url: str,
    case_id: str | None,
    previous_result: str,
    limit: int,
    duckdb_path: str | None,
) -> None:
    """Replay historical source-backed answers and compare them with their latest evaluation."""
    with connect_duckdb(duckdb_path) as connection:
        ensure_evaluation_table(connection)
        cases = load_chat_cases(
            connection,
            case_id=case_id,
            previous_result=previous_result,
            limit=limit,
        )
        if not cases:
            raise click.ClickException("No eligible chat cases matched")
        dataset_version = chat_dataset_version(connection)
        results = []
        for case in cases:
            baseline = latest_result(connection, str(case["case_id"]), EVALUATOR_NAME)
            try:
                replay = replay_chat(target_url, case["replay_requests"])
            except (OSError, RuntimeError, ValueError) as exc:
                raise click.ClickException(
                    f"Replay failed for case {case['case_id']}: {exc}"
                ) from exc
            evaluation = evaluate(
                case_id=str(case["case_id"]),
                request=str(case["original_request"]),
                response=str(replay["response"]),
                citations=replay["citations"],
                dataset_version=dataset_version,
                system_version=system_version,
                evidence_uri=str(replay["evidence_uri"]),
            )
            evaluation = evaluation.model_copy(
                update={
                    "metadata": {
                        **evaluation.metadata,
                        "replay_requests": case["replay_requests"],
                    }
                }
            )
            record_evaluation(connection, evaluation)
            results.append(
                {
                    "case_id": evaluation.case_id,
                    "baseline": None
                    if baseline is None
                    else {
                        "result": baseline[0],
                        "score": baseline[1],
                        "system_version": baseline[2],
                    },
                    "candidate": {
                        "result": evaluation.result,
                        "score": evaluation.score,
                        "system_version": evaluation.system_version,
                    },
                    "evidence_uri": evaluation.evidence_uri,
                }
            )
    click.echo(
        json.dumps({"dataset_version": dataset_version, "cases": results}, indent=2)
    )


@main.command("serve-mcp")
def serve_mcp_command() -> None:
    """Serve procdork's read-only analytics and OKF MCP surface."""
    from mcp_server import serve

    serve()


if __name__ == "__main__":
    main()
