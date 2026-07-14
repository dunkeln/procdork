from __future__ import annotations

from statistics import fmean

from ..evaluations import EvaluationResult

NAME = "app_message_judge"
VERSION = "1"
RUBRIC_VERSION = "1"
PROMPT_VERSION = "1"
DIMENSIONS = (
    "grounding",
    "task_resolution",
    "uncertainty_calibration",
    "consistency",
    "answer_composability",
    "style_clarity",
)

RUBRIC: dict[str, str] = {
    "grounding": "Answer stays within the prompt and cited/source evidence.",
    "task_resolution": "Answer directly resolves the user's request.",
    "uncertainty_calibration": "Answer admits gaps instead of inventing certainty.",
    "consistency": "Answer does not contradict itself or its available evidence.",
    "answer_composability": "Answer is structured enough for downstream reuse.",
    "style_clarity": "Answer is concise, readable, and operationally useful.",
}


def evaluation_from_judge(
    *,
    run_id: str,
    case: dict[str, object],
    scores: dict[str, int],
    rationale: str,
    judge_model: str,
    judge_version: str,
    rubric_version: str,
    judge_usage: dict[str, int],
    dataset_version: str,
    system_version: str,
) -> EvaluationResult:
    validate_scores(scores)
    return EvaluationResult(
        run_id=run_id,
        case_id=str(case["case_id"]),
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name=NAME,
        evaluator_version=VERSION,
        score=fmean(scores.values()) / 5,
        result="report",
        evidence_uri=str(case.get("evidence_uri") or ""),
        metadata={
            "session_slug": case["session_slug"],
            "session_title": case["session_title"],
            "request": case["request"],
            "response_excerpt": case["response_excerpt"],
            "response_sha256": case["response_sha256"],
            "response_chars": case["response_chars"],
            "message_created_at": case["message_created_at"],
            "message_completed_at": case["message_completed_at"],
            "citation_count": case["citation_count"],
            "sources": case["sources"],
            "scores": scores,
            "rationale": rationale[:800],
            "judge_model": judge_model,
            "judge_version": judge_version,
            "rubric_version": rubric_version,
            "judge_prompt_version": PROMPT_VERSION,
            "judge_usage": judge_usage,
            "release_gate": False,
        },
    )


def validate_scores(scores: dict[str, int]) -> None:
    if set(scores) != set(DIMENSIONS) or any(
        not isinstance(value, int) or not 1 <= value <= 5 for value in scores.values()
    ):
        raise ValueError("Judge scores must contain every dimension with integers from 1 to 5")


def judge_payload(case: dict[str, object], *, rubric_version: str) -> dict[str, object]:
    return {
        "rubric_version": rubric_version,
        "prompt_version": PROMPT_VERSION,
        "rubric": RUBRIC,
        "question": case["request"],
        "answer": case["response_excerpt"],
        "answer_was_truncated_for_judge": case["response_truncated"],
        "sources": case["sources"],
        "citation_count": case["citation_count"],
    }


def judge_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "object",
                "properties": {
                    name: {"type": "integer", "minimum": 1, "maximum": 5}
                    for name in DIMENSIONS
                },
                "required": list(DIMENSIONS),
                "additionalProperties": False,
            },
            "rationale": {"type": "string", "maxLength": 800},
        },
        "required": ["scores", "rationale"],
        "additionalProperties": False,
    }
