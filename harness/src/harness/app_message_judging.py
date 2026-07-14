from __future__ import annotations

from datetime import UTC, datetime
import os

import duckdb

from .connectors.anthropic import judge_json
from .connectors.procdork import chat_dataset_version, load_app_message_cases
from .evaluations import ensure_evaluation_table, record_evaluation
from .evaluators.app_message_judge import (
    NAME,
    PROMPT_VERSION,
    RUBRIC_VERSION,
    evaluation_from_judge,
    judge_payload,
    judge_schema,
)


def judge_app_messages(
    connection: duckdb.DuckDBPyConnection,
    *,
    system_version: str,
    judge_model: str | None = None,
    judge_version: str = "1",
    rubric_version: str = RUBRIC_VERSION,
    case_id: str | None = None,
    limit: int = 5,
    batch_id: str | None = None,
) -> dict[str, object]:
    model = judge_model or os.environ.get("ANTHROPIC_JUDGE_MODEL") or os.environ.get("ANTHROPIC_MODEL")
    if not model:
        raise ValueError("Set --judge-model or ANTHROPIC_JUDGE_MODEL")

    batch = batch_id or datetime.now(UTC).strftime("appmsg-%Y%m%dT%H%M%SZ")
    ensure_evaluation_table(connection)
    cases = load_app_message_cases(connection, case_id=case_id, limit=limit)
    if not cases:
        raise ValueError("No completed app messages matched")

    dataset_version = chat_dataset_version(connection)
    results = []
    for case in cases:
        payload, usage = judge_json(
            model=model,
            system=APP_MESSAGE_JUDGE_SYSTEM,
            payload=judge_payload(case, rubric_version=rubric_version),
            tool_name="score_app_message",
            tool_description="Return anchored message-quality scores and a short rationale.",
            input_schema=judge_schema(),
        )
        scores = payload.get("scores")
        if not isinstance(scores, dict):
            raise ValueError(f"Judge returned no scores for {case['case_id']}")
        evaluation = evaluation_from_judge(
            run_id=safe_run_id(batch, NAME, judge_version, rubric_version, str(case["case_id"])),
            case=case,
            scores={key: int(value) for key, value in scores.items()},
            rationale=str(payload.get("rationale") or ""),
            judge_model=model,
            judge_version=judge_version,
            rubric_version=rubric_version,
            judge_usage=usage,
            dataset_version=dataset_version,
            system_version=system_version,
        )
        record_evaluation(connection, evaluation)
        results.append(
            {
                "case_id": evaluation.case_id,
                "score": evaluation.score,
                "result": evaluation.result,
                "evidence_uri": evaluation.evidence_uri,
            }
        )

    return {
        "batch_id": batch,
        "dataset_version": dataset_version,
        "system_version": system_version,
        "judge_model": model,
        "judge_version": judge_version,
        "rubric_version": rubric_version,
        "prompt_version": PROMPT_VERSION,
        "cases": results,
    }


APP_MESSAGE_JUDGE_SYSTEM = (
    "Score one stored application answer. Use only the user question, answer text, "
    "and attached source metadata. Do not reward confidence when evidence is thin. "
    "Use anchored integers: 1 is unusable or misleading, 3 is adequate with clear "
    "limitations, and 5 is grounded, complete, consistent, composable, and clear. "
    "Return one concise rationale."
)


def safe_run_id(*parts: str) -> str:
    return ":".join(
        "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in part)
        for part in parts
    )
