from __future__ import annotations

from datetime import UTC, datetime
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel

from harness.charts import build_chart, render_svg
from e2e.benchmarks.connectors.anthropic import JUDGE_PROMPT_VERSION, judge_response
from e2e.benchmarks.evaluator import deterministic_evaluation, semantic_evaluation
from harness.evaluations import record_evaluation
from harness.olap import connect_duckdb


class BenchmarkCase(BaseModel):
    id: str
    family: str
    question: str
    glossary_terms: list[str]
    tables: list[str]
    knowledge: list[str]
    expected_behavior: str
    required_caveats: list[str]
    reference_sql: str | None


def load_cases(path: Path) -> list[BenchmarkCase]:
    cases = [
        BenchmarkCase.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]
    if len(cases) != 20 or len({case.id for case in cases}) != 20:
        raise ValueError("The benchmark corpus must contain 20 unique cases")
    families = Counter(case.family for case in cases)
    if families != {
        "exact_retrieval": 4,
        "comparison": 4,
        "freshness": 3,
        "evidence_quality": 3,
        "knowledge_application": 3,
        "abstention": 3,
    }:
        raise ValueError(
            "The benchmark corpus does not contain the required case families"
        )
    return cases


def run_benchmark(
    *,
    database_path: str,
    cases: list[BenchmarkCase],
    attempts: int,
    model: str,
    judge_model: str,
    dataset_version: str,
    system_version: str,
    mcp_url: str,
    output_root: Path,
    pricing: dict[str, object],
) -> Path:
    suite = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suite.mkdir(parents=True)
    manifest = {
        "dataset_version": dataset_version,
        "system_version": system_version,
        "agent_model": model,
        "judge_model": judge_model,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "attempts": attempts,
        "raw_database": database_path.split("?", 1)[0],
        "harness_mcp_url": mcp_url,
        "pricing": pricing,
        "started_at": datetime.now(UTC).isoformat(),
    }
    (suite / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    (suite / "cases.jsonl").write_text(
        "\n".join(case.model_dump_json() for case in cases) + "\n",
        encoding="utf-8",
    )
    for case_index, case in enumerate(cases):
        with connect_duckdb(database_path) as connection:
            reference_evidence = reference_query(connection, case.reference_sql)
        case_dir = suite / case.id
        case_dir.mkdir()
        (case_dir / "reference.json").write_text(
            json.dumps(reference_evidence, indent=2, sort_keys=True, default=str)
            + "\n",
            encoding="utf-8",
        )
        case_payload = {**case.model_dump(), "reference_evidence": reference_evidence}
        for attempt in range(1, attempts + 1):
            treatments = ["harness", "raw_sql"]
            if (case_index + attempt) % 2:
                treatments.reverse()
            for treatment in treatments:
                run_id = str(uuid4())
                run_dir = suite / case.id / f"attempt-{attempt}" / treatment
                response, events, elapsed_ms = run_agent(
                    case=case,
                    treatment=treatment,
                    model=model,
                    mcp_url=mcp_url,
                    run_dir=run_dir,
                    database_path=database_path,
                )
                evidence_uri = str(run_dir / "events.jsonl")
                deterministic = deterministic_evaluation(
                    run_id=run_id,
                    attempt=attempt,
                    agent_model=model,
                    case=case_payload,
                    treatment=treatment,
                    response=response,
                    events=events,
                    elapsed_ms=elapsed_ms,
                    dataset_version=dataset_version,
                    system_version=system_version,
                    evidence_uri=evidence_uri,
                    pricing=pricing,
                )
                scores, rationale, judge_usage = judge_response(
                    case_payload, response, judge_model
                )
                semantic = semantic_evaluation(
                    run_id=run_id,
                    case=case_payload,
                    response=response,
                    scores=scores,
                    rationale=rationale,
                    judge_model=judge_model,
                    judge_usage=judge_usage,
                    dataset_version=dataset_version,
                    system_version=system_version,
                    evidence_uri=evidence_uri,
                )
                with connect_duckdb(database_path) as connection:
                    record_evaluation(connection, deterministic)
                    record_evaluation(connection, semantic)
    return suite


def reference_query(connection, sql: str | None) -> dict[str, object] | None:
    if sql is None:
        return None
    result = connection.execute(sql)
    rows = result.fetchmany(101)
    return {
        "columns": [column[0] for column in result.description or []],
        "rows": [list(row) for row in rows[:100]],
        "truncated": len(rows) > 100,
    }


def write_charts(connection, output: Path) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    queries = {
        "pass-rate.svg": (
            "Deterministic pass rate by treatment",
            "select treatment, avg(deterministic_pass_rate) from mart_benchmark_summary group by 1 order by 1",
        ),
        "elapsed-time.svg": (
            "Median workflow time by treatment",
            "select treatment, avg(median_elapsed_ms) from mart_benchmark_summary group by 1 order by 1",
        ),
        "semantic-score.svg": (
            "Semantic score by treatment",
            "select treatment, avg(average_semantic_score) from mart_benchmark_summary where average_semantic_score is not null group by 1 order by 1",
        ),
    }
    written = []
    for filename, (title, sql) in queries.items():
        result = connection.execute(sql)
        columns = [column[0] for column in result.description or []]
        payload = build_chart(columns, result.fetchall(), title, "bar")
        path = output / filename
        path.write_text(render_svg(payload), encoding="utf-8")
        written.append(path)
    return written


def run_agent(
    *,
    case: BenchmarkCase,
    treatment: str,
    model: str,
    mcp_url: str,
    run_dir: Path,
    database_path: str,
) -> tuple[str, list[dict[str, object]], int]:
    run_dir.mkdir(parents=True)
    final_path = run_dir / "final.md"
    events_path = run_dir / "events.jsonl"
    harness_root = Path(__file__).resolve().parents[2]
    if treatment == "harness":
        config = ["-c", f'mcp_servers.procdork.url="{mcp_url}"']
        prompt = (
            "Use only the procdork MCP. Read the relevant knowledge resources "
            f"{case.knowledge}, inspect the permitted tables {case.tables}, and answer: {case.question} "
            "Preserve exact values and state evidence limits."
        )
    else:
        config = [
            "-c",
            'mcp_servers.raw.command="uv"',
            "-c",
            f'mcp_servers.raw.args=["--directory","{harness_root}","run","python","-m","e2e.benchmarks.raw_sql_server"]',
        ]
        prompt = (
            "Use only the raw-analytics MCP. Discover physical analytics tables through information_schema "
            f"and answer from read-only SQL: {case.question} Preserve exact values and state evidence limits."
        )
    command = [
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--ignore-user-config",
        "--model",
        model,
        *config,
        "--json",
        "-o",
        str(final_path),
        prompt,
    ]
    started = perf_counter()
    events: list[dict[str, object]] = []
    with (
        events_path.open("w", encoding="utf-8") as output,
        (run_dir / "stderr.log").open("w") as errors,
    ):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=errors,
            text=True,
            env={**os.environ, "DUCKDB_PATH": database_path},
        )
        assert process.stdout is not None
        for line in process.stdout:
            event = json.loads(line)
            event["observed_at"] = datetime.now(UTC).isoformat()
            events.append(event)
            output.write(json.dumps(event, sort_keys=True) + "\n")
        return_code = process.wait()
    elapsed_ms = round((perf_counter() - started) * 1000)
    if return_code:
        failure = {
            "type": "error",
            "message": f"codex exec exited {return_code}",
            "observed_at": datetime.now(UTC).isoformat(),
        }
        events.append(failure)
        with events_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(failure, sort_keys=True) + "\n")
    response = final_path.read_text(encoding="utf-8") if final_path.exists() else ""
    return response, events, elapsed_ms
