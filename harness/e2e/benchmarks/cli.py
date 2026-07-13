from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

import click

from e2e.benchmarks.evaluator import DIMENSIONS, human_evaluation, operator_evaluation
from e2e.benchmarks.runner import load_cases, run_benchmark, write_charts
from evaluations import (
    EvaluationResult,
    ensure_evaluation_table,
    record_evaluation,
)
from olap import connect_duckdb, duckdb_path as resolve_duckdb_path


@click.group()
def main() -> None:
    """Run development-only harness benchmarks."""


@main.command("benchmark-run")
@click.option(
    "--cases",
    "cases_path",
    type=click.Path(path_type=Path, dir_okay=False, readable=True),
    default=Path("e2e/benchmarks/cases.jsonl"),
    show_default=True,
)
@click.option("--attempts", type=click.IntRange(1, 10), default=3, show_default=True)
@click.option("--case-id", default=None, help="Run one case for a focused smoke.")
@click.option("--model", required=True, help="Pinned model used for both treatments.")
@click.option("--judge-model", required=True, help="Pinned Anthropic judge model.")
@click.option("--dataset-version", required=True)
@click.option("--system-version", required=True)
@click.option("--mcp-url", default="https://procdork.vercel.app/mcp", show_default=True)
@click.option(
    "--pricing-date", required=True, help="Date for the declared token rates."
)
@click.option("--input-usd-per-million", type=float, required=True)
@click.option("--cached-input-usd-per-million", type=float, required=True)
@click.option("--output-usd-per-million", type=float, required=True)
@click.option("--duckdb-path", default=None)
def benchmark_run(
    cases_path: Path,
    attempts: int,
    case_id: str | None,
    model: str,
    judge_model: str,
    dataset_version: str,
    system_version: str,
    mcp_url: str,
    pricing_date: str,
    input_usd_per_million: float,
    cached_input_usd_per_million: float,
    output_usd_per_million: float,
    duckdb_path: str | None,
) -> None:
    """Run paired harness and raw-SQL benchmark treatments."""
    pricing = {
        "date": pricing_date,
        "input_usd_per_million": input_usd_per_million,
        "cached_input_usd_per_million": cached_input_usd_per_million,
        "output_usd_per_million": output_usd_per_million,
    }
    try:
        database_path = resolve_duckdb_path(duckdb_path)
        with connect_duckdb(database_path) as connection:
            ensure_evaluation_table(connection)
        cases = load_cases(cases_path)
        if case_id:
            cases = [case for case in cases if case.id == case_id]
            if not cases:
                raise ValueError(f"Unknown benchmark case: {case_id}")
        output = run_benchmark(
            database_path=database_path,
            cases=cases,
            attempts=attempts,
            model=model,
            judge_model=judge_model,
            dataset_version=dataset_version,
            system_version=system_version,
            mcp_url=mcp_url,
            output_root=Path("e2e/benchmarks/evidence"),
            pricing=pricing,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(output))


@main.command("benchmark-human")
@click.option(
    "--cases",
    "cases_path",
    type=click.Path(path_type=Path, dir_okay=False, readable=True),
    default=Path("e2e/benchmarks/cases.jsonl"),
    show_default=True,
)
@click.option("--dataset-version", required=True)
@click.option("--system-version", required=True)
@click.option("--duckdb-path", default=None)
def benchmark_human(
    cases_path: Path,
    dataset_version: str,
    system_version: str,
    duckdb_path: str | None,
) -> None:
    """Time one blind manual pass over the benchmark corpus."""
    cases = load_cases(cases_path)
    with connect_duckdb(duckdb_path) as connection:
        ensure_evaluation_table(connection)
        for case in cases:
            click.echo(f"\n[{case.id}] {case.question}")
            click.confirm("Start timer?", abort=True)
            started = perf_counter()
            click.prompt(
                "Press Enter when the answer is complete",
                default="",
                show_default=False,
            )
            elapsed_ms = round((perf_counter() - started) * 1000)
            accepted = click.confirm("Was the answer acceptable?")
            interventions = click.prompt(
                "Operator interventions", type=click.IntRange(0), default=0
            )
            record_evaluation(
                connection,
                human_evaluation(
                    case=case.model_dump(),
                    dataset_version=dataset_version,
                    system_version=system_version,
                    elapsed_ms=elapsed_ms,
                    accepted=accepted,
                    interventions=interventions,
                ),
            )


@main.command("benchmark-record-operator")
@click.option("--case-id", required=True)
@click.option("--dataset-version", required=True)
@click.option("--system-version", required=True)
@click.option("--elapsed-ms", type=click.IntRange(0), required=True)
@click.option("--accepted/--rejected", default=True)
@click.option("--interventions", type=click.IntRange(0), default=0)
@click.option(
    "--response-file",
    type=click.Path(path_type=Path, dir_okay=False, readable=True),
    required=True,
)
@click.option("--evidence-uri", default=None)
@click.option("--duckdb-path", default=None)
def benchmark_record_operator(
    case_id: str,
    dataset_version: str,
    system_version: str,
    elapsed_ms: int,
    accepted: bool,
    interventions: int,
    response_file: Path,
    evidence_uri: str | None,
    duckdb_path: str | None,
) -> None:
    """Record one browser-operated analytical baseline without calling it human."""
    cases = load_cases(Path("e2e/benchmarks/cases.jsonl"))
    case = next((item for item in cases if item.id == case_id), None)
    if case is None:
        raise click.ClickException(f"Unknown benchmark case: {case_id}")
    with connect_duckdb(duckdb_path) as connection:
        ensure_evaluation_table(connection)
        record_evaluation(
            connection,
            operator_evaluation(
                case=case.model_dump(),
                dataset_version=dataset_version,
                system_version=system_version,
                elapsed_ms=elapsed_ms,
                accepted=accepted,
                interventions=interventions,
                response=response_file.read_text(encoding="utf-8"),
                evidence_uri=evidence_uri,
            ),
        )


@main.command("benchmark-record-review")
@click.option("--run-id", required=True)
@click.option("--grounding", type=click.IntRange(1, 5), required=True)
@click.option("--task-resolution", type=click.IntRange(1, 5), required=True)
@click.option("--uncertainty-calibration", type=click.IntRange(1, 5), required=True)
@click.option("--decision-usefulness", type=click.IntRange(1, 5), required=True)
@click.option("--clarity", type=click.IntRange(1, 5), required=True)
@click.option("--duckdb-path", default=None)
def benchmark_record_review(
    run_id: str,
    grounding: int,
    task_resolution: int,
    uncertainty_calibration: int,
    decision_usefulness: int,
    clarity: int,
    duckdb_path: str | None,
) -> None:
    """Record one blind Codex review as cross-model, not human, calibration."""
    scores = {
        "grounding": grounding,
        "task_resolution": task_resolution,
        "uncertainty_calibration": uncertainty_calibration,
        "decision_usefulness": decision_usefulness,
        "clarity": clarity,
    }
    with connect_duckdb(duckdb_path) as connection:
        row = connection.execute(
            """
            select case_id, dataset_version, system_version
            from raw_evaluation_results
            where run_id = ? and evaluator_name = 'benchmark_deterministic'
            """,
            [run_id],
        ).fetchone()
        if row is None:
            raise click.ClickException(f"Unknown benchmark run: {run_id}")
        record_evaluation(
            connection,
            EvaluationResult(
                run_id=run_id,
                case_id=str(row[0]),
                dataset_version=str(row[1]),
                system_version=str(row[2]),
                evaluator_name="benchmark_operator_judge",
                evaluator_version="1",
                score=sum(scores.values()) / len(scores) / 5,
                result="report",
                metadata={
                    "scores": scores,
                    "blind": True,
                    "reviewer_type": "cross_model",
                },
            ),
        )


@main.command("benchmark-calibrate")
@click.option("--dataset-version", required=True)
@click.option("--system-version", required=True)
@click.option("--duckdb-path", default=None)
def benchmark_calibrate(
    dataset_version: str, system_version: str, duckdb_path: str | None
) -> None:
    """Blind-score 12 balanced outputs for judge calibration."""
    with connect_duckdb(duckdb_path) as connection:
        ensure_evaluation_table(connection)
        rows = connection.execute(
            """
            with candidates as (
                select
                    run_id, case_id, metadata,
                    row_number() over (
                        partition by json_extract_string(metadata, '$.family'),
                                     json_extract_string(metadata, '$.treatment')
                        order by hash(run_id)
                    ) as sample_order
                from raw_evaluation_results
                where evaluator_name = 'benchmark_deterministic'
                  and dataset_version = ? and system_version = ?
            )
            select run_id, case_id, metadata
            from candidates where sample_order = 1
            order by hash(case_id)
            limit 12
            """,
            [dataset_version, system_version],
        ).fetchall()
        if len(rows) != 12:
            raise click.ClickException(
                "Calibration requires 12 balanced benchmark outputs"
            )
        for run_id, case_id, metadata in rows:
            payload = json.loads(metadata) if isinstance(metadata, str) else metadata
            click.echo(
                f"\nQuestion: {payload['question']}\n\nAnswer:\n{payload['response']}"
            )
            scores = {
                name: click.prompt(name.replace("_", " "), type=click.IntRange(1, 5))
                for name in DIMENSIONS
            }
            record_evaluation(
                connection,
                EvaluationResult(
                    run_id=str(run_id),
                    case_id=str(case_id),
                    dataset_version=dataset_version,
                    system_version=system_version,
                    evaluator_name="benchmark_human_judge",
                    evaluator_version="1",
                    score=sum(scores.values()) / len(scores) / 5,
                    result="report",
                    metadata={"scores": scores, "blind": True},
                ),
            )


@main.command("benchmark-charts")
@click.option(
    "--output",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("e2e/benchmarks/charts"),
)
@click.option("--duckdb-path", default=None)
def benchmark_charts(output: Path, duckdb_path: str | None) -> None:
    """Render three compact charts from published benchmark evidence."""
    with connect_duckdb(duckdb_path) as connection:
        paths = write_charts(connection, output)
    click.echo("\n".join(str(path) for path in paths))


@main.command("benchmark-verify")
@click.option("--dataset-version", required=True)
@click.option("--system-version", required=True)
@click.option("--attempts", type=click.IntRange(1, 10), default=3, show_default=True)
@click.option("--duckdb-path", default=None)
def benchmark_verify(
    dataset_version: str,
    system_version: str,
    attempts: int,
    duckdb_path: str | None,
) -> None:
    """Verify suite completeness, model parity, and human calibration coverage."""
    with connect_duckdb(duckdb_path) as connection:
        rows = connection.execute(
            """
            select
                json_extract_string(metadata, '$.treatment') as treatment,
                case_id,
                count(distinct run_id) as run_count
            from raw_evaluation_results
            where evaluator_name in ('benchmark_deterministic', 'human_baseline', 'operator_agent_baseline')
              and dataset_version = ? and system_version = ?
            group by 1, 2
            """,
            [dataset_version, system_version],
        ).fetchall()
        expected = {
            "harness": attempts,
            "raw_sql": attempts,
            "human": 1,
            "operator_agent": 1,
        }
        incomplete = [
            row for row in rows if row[0] not in expected or row[2] != expected[row[0]]
        ]
        counts = {
            treatment: sum(1 for row in rows if row[0] == treatment)
            for treatment in expected
        }
        evaluator_counts = connection.execute(
            """
            select evaluator_name, count(*)
            from raw_evaluation_results
            where evaluator_name in ('benchmark_deterministic', 'benchmark_semantic_judge', 'benchmark_human_judge', 'benchmark_operator_judge')
              and dataset_version = ? and system_version = ?
            group by 1
            """,
            [dataset_version, system_version],
        ).fetchall()
        agent_models = connection.execute(
            """
            select count(distinct json_extract_string(metadata, '$.agent_model'))
            from raw_evaluation_results
            where evaluator_name = 'benchmark_deterministic'
              and dataset_version = ? and system_version = ?
            """,
            [dataset_version, system_version],
        ).fetchone()[0]
    evaluator_counts = dict(evaluator_counts)
    automated = 20 * attempts * 2
    automated_counts = {name: counts[name] for name in ("harness", "raw_sql")}
    manual_counts = {name: counts[name] for name in ("human", "operator_agent")}
    if (
        incomplete
        or automated_counts != {"harness": 20, "raw_sql": 20}
        or sorted(manual_counts.values()) != [0, 20]
    ):
        raise click.ClickException(f"Incomplete case attempts: {incomplete or counts}")
    if (
        evaluator_counts.get("benchmark_deterministic") != automated
        or evaluator_counts.get("benchmark_semantic_judge") != automated
    ):
        raise click.ClickException(
            f"Automated evaluator coverage mismatch: {evaluator_counts}"
        )
    reviewer_count = evaluator_counts.get(
        "benchmark_human_judge", 0
    ) + evaluator_counts.get("benchmark_operator_judge", 0)
    if reviewer_count != 12:
        raise click.ClickException(
            "Calibration requires exactly 12 human or cross-model reviews"
        )
    if agent_models != 1:
        raise click.ClickException(
            "Automated treatments did not use one pinned agent model"
        )
    click.echo("Benchmark evidence is complete and version-aligned.")



if __name__ == "__main__":
    main()
