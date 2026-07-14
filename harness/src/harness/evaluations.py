from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Literal

import duckdb
from .extraction import HarnessModel
from pydantic import Field


class EvaluationResult(HarnessModel):
    run_id: str
    case_id: str
    dataset_version: str
    system_version: str
    evaluator_name: str
    evaluator_version: str
    score: float | None = None
    result: str
    evidence_uri: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def ensure_evaluation_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        create table if not exists raw_evaluation_results (
            run_id varchar,
            case_id varchar,
            dataset_version varchar,
            system_version varchar,
            evaluator_name varchar,
            evaluator_version varchar,
            score double,
            result varchar,
            evidence_uri varchar,
            metadata json,
            evaluated_at timestamptz
        )
        """
    )


def record_evaluation(
    con: duckdb.DuckDBPyConnection, evaluation: EvaluationResult
) -> None:
    """Persist one provider-neutral evaluation result for dbt to transform."""
    ensure_evaluation_table(con)
    con.execute("begin")
    try:
        con.execute(
            """
            delete from raw_evaluation_results
            where run_id = ? and evaluator_name = ?
            """,
            [
                evaluation.run_id,
                evaluation.evaluator_name,
            ],
        )
        con.execute(
            """
            insert into raw_evaluation_results values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?::json, ?)
            """,
            [
                evaluation.run_id,
                evaluation.case_id,
                evaluation.dataset_version,
                evaluation.system_version,
                evaluation.evaluator_name,
                evaluation.evaluator_version,
                evaluation.score,
                evaluation.result,
                evaluation.evidence_uri,
                json.dumps(evaluation.metadata, sort_keys=True),
                evaluation.evaluated_at,
            ],
        )
        con.execute("commit")
    except Exception:
        con.execute("rollback")
        raise


def latest_result(
    con: duckdb.DuckDBPyConnection, case_id: str, evaluator_name: str
) -> tuple[Literal["pass", "fail"], float | None, str] | None:
    row = con.execute(
        """
        select result, score, system_version
        from raw_evaluation_results
        where case_id = ? and evaluator_name = ?
        order by evaluated_at desc
        limit 1
        """,
        [case_id, evaluator_name],
    ).fetchone()
    return row if row else None
