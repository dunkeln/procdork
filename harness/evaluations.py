from __future__ import annotations

from datetime import UTC, datetime
import json

from extraction import HarnessModel
from olap import connect_duckdb
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


def record_evaluation(evaluation: EvaluationResult, db_path: str | None = None) -> None:
    """Persist one provider-neutral evaluation result for dbt to transform."""
    with connect_duckdb(db_path) as con:
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
        con.execute("begin")
        try:
            con.execute(
                """
                delete from raw_evaluation_results
                where case_id = ? and dataset_version = ? and system_version = ?
                  and evaluator_name = ? and evaluator_version = ?
                """,
                [
                    evaluation.case_id,
                    evaluation.dataset_version,
                    evaluation.system_version,
                    evaluation.evaluator_name,
                    evaluation.evaluator_version,
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
