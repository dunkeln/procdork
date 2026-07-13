from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
import json
from statistics import fmean
from uuid import uuid4

from evaluations import EvaluationResult


DETERMINISTIC_NAME = "benchmark_deterministic"
DETERMINISTIC_VERSION = "1"
JUDGE_NAME = "benchmark_semantic_judge"
JUDGE_VERSION = "1"
RUBRIC_VERSION = "1"
DIMENSIONS = (
    "grounding",
    "task_resolution",
    "uncertainty_calibration",
    "decision_usefulness",
    "clarity",
)


def deterministic_evaluation(
    *,
    run_id: str,
    attempt: int,
    agent_model: str,
    case: dict[str, object],
    treatment: str,
    response: str,
    events: list[dict[str, object]],
    elapsed_ms: int,
    dataset_version: str,
    system_version: str,
    evidence_uri: str,
    pricing: dict[str, object],
) -> EvaluationResult:
    tool_calls = [
        event
        for event in events
        if event.get("type") == "item.completed"
        and event_type(event) == "mcp_tool_call"
    ]
    completed_calls = [
        event for event in tool_calls if item(event).get("status") == "completed"
    ]
    errors = [event for event in events if event.get("type") == "error"]
    usage = next(
        (
            event.get("usage", {})
            for event in reversed(events)
            if event.get("type") == "turn.completed"
        ),
        {},
    )
    completed = bool(response.strip()) and not errors
    queried = any(
        item(event).get("tool") in {"query", "query_raw"} for event in completed_calls
    )
    abstention_expected = case["expected_behavior"] == "abstain"
    abstained = contains_any(
        response,
        (
            "not enough evidence",
            "insufficient evidence",
            "does not establish",
            "cannot determine",
            "not available",
        ),
    )
    required_caveats = [str(value) for value in case.get("required_caveats", [])]
    caveats_present = all(
        value.lower() in response.lower() for value in required_caveats
    )
    checks = {
        "completed": completed,
        "query_succeeded": queried,
        "expected_abstention": not abstention_expected or abstained,
        "required_caveats": caveats_present,
        "no_tool_errors": len(tool_calls) == len(completed_calls),
    }
    expected_facts = reference_facts(case.get("reference_evidence"))
    if case["family"] == "exact_retrieval":
        checks["expected_facts"] = all(
            fact.lower() in response.lower() for fact in expected_facts
        )
    score = sum(checks.values()) / len(checks)
    tool_latencies_ms = observed_tool_latencies(events)
    return EvaluationResult(
        run_id=run_id,
        case_id=str(case["id"]),
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name=DETERMINISTIC_NAME,
        evaluator_version=DETERMINISTIC_VERSION,
        score=score,
        result="pass" if all(checks.values()) else "fail",
        evidence_uri=evidence_uri,
        metadata={
            "family": case["family"],
            "treatment": treatment,
            "attempt": attempt,
            "agent_model": agent_model,
            "question": case["question"],
            "glossary_terms": case["glossary_terms"],
            "expected_behavior": case["expected_behavior"],
            "abstained": abstained,
            "expected_facts": expected_facts,
            "checks": checks,
            "response": response,
            "response_sha256": sha256(response.encode()).hexdigest(),
            "elapsed_ms": elapsed_ms,
            "tool_call_count": len(tool_calls),
            "tool_error_count": len(tool_calls) - len(completed_calls),
            "retry_count": retry_count(tool_calls),
            "tool_latencies_ms": tool_latencies_ms,
            "max_tool_latency_ms": max(tool_latencies_ms, default=None),
            "citation_check": "not_applicable",
            "truncated": any(tool_result_truncated(event) for event in tool_calls),
            "usage": usage,
            "cost_proxy_usd": cost_proxy(usage, pricing),
            "pricing": pricing,
        },
    )


def semantic_evaluation(
    *,
    run_id: str,
    case: dict[str, object],
    response: str,
    scores: dict[str, int],
    rationale: str,
    judge_model: str,
    judge_usage: dict[str, int],
    dataset_version: str,
    system_version: str,
    evidence_uri: str,
) -> EvaluationResult:
    validate_scores(scores)
    average = fmean(scores.values())
    return EvaluationResult(
        run_id=run_id,
        case_id=str(case["id"]),
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name=JUDGE_NAME,
        evaluator_version=JUDGE_VERSION,
        score=average / 5,
        result="report",
        evidence_uri=evidence_uri,
        metadata={
            "family": case["family"],
            "question": case["question"],
            "response": response,
            "scores": scores,
            "rationale": rationale,
            "judge_model": judge_model,
            "rubric_version": RUBRIC_VERSION,
            "judge_usage": judge_usage,
            "release_gate": False,
        },
    )


def human_evaluation(
    *,
    case: dict[str, object],
    dataset_version: str,
    system_version: str,
    elapsed_ms: int,
    accepted: bool,
    interventions: int,
) -> EvaluationResult:
    return EvaluationResult(
        run_id=str(uuid4()),
        case_id=str(case["id"]),
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name="human_baseline",
        evaluator_version="1",
        score=1.0 if accepted else 0.0,
        result="pass" if accepted else "fail",
        metadata={
            "family": case["family"],
            "treatment": "human",
            "attempt": 1,
            "agent_model": "human",
            "question": case["question"],
            "elapsed_ms": elapsed_ms,
            "interventions": interventions,
        },
    )


def operator_evaluation(
    *,
    case: dict[str, object],
    dataset_version: str,
    system_version: str,
    elapsed_ms: int,
    accepted: bool,
    interventions: int,
    response: str,
    evidence_uri: str | None,
) -> EvaluationResult:
    return EvaluationResult(
        run_id=str(uuid4()),
        case_id=str(case["id"]),
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name="operator_agent_baseline",
        evaluator_version="1",
        score=1.0 if accepted else 0.0,
        result="pass" if accepted else "fail",
        evidence_uri=evidence_uri,
        metadata={
            "family": case["family"],
            "treatment": "operator_agent",
            "question": case["question"],
            "response": response,
            "elapsed_ms": elapsed_ms,
            "interventions": interventions,
            "attempt": 1,
            "agent_model": "operator_agent",
        },
    )


def validate_scores(scores: dict[str, int]) -> None:
    if set(scores) != set(DIMENSIONS) or any(
        not 1 <= value <= 5 for value in scores.values()
    ):
        raise ValueError(
            "Judge scores must contain every rubric dimension with values from 1 to 5"
        )


def event_type(event: dict[str, object]) -> object:
    return (
        item(event).get("type")
        if event.get("type") in {"item.started", "item.completed"}
        else event.get("type")
    )


def item(event: dict[str, object]) -> dict[str, object]:
    value = event.get("item")
    return value if isinstance(value, dict) else {}


def contains_any(value: str, needles: Iterable[str]) -> bool:
    lowered = value.lower()
    return any(needle in lowered for needle in needles)


def cost_proxy(usage: object, pricing: dict[str, object]) -> float:
    if not isinstance(usage, dict):
        return 0.0
    input_tokens = max(
        0, int(usage.get("input_tokens", 0)) - int(usage.get("cached_input_tokens", 0))
    )
    cached_tokens = int(usage.get("cached_input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    return round(
        (
            input_tokens * float(pricing["input_usd_per_million"])
            + cached_tokens * float(pricing["cached_input_usd_per_million"])
            + output_tokens * float(pricing["output_usd_per_million"])
        )
        / 1_000_000,
        6,
    )


def tool_result_truncated(event: dict[str, object]) -> bool:
    result = item(event).get("result")
    if not isinstance(result, dict):
        return False
    structured = result.get("structured_content")
    return isinstance(structured, dict) and structured.get("truncated") is True


def reference_facts(evidence: object) -> list[str]:
    if not isinstance(evidence, dict) or not isinstance(evidence.get("rows"), list):
        return []
    return sorted(
        {
            str(value)
            for row in evidence["rows"]
            if isinstance(row, list)
            for value in row
            if value is not None
        }
    )


def observed_tool_latencies(events: list[dict[str, object]]) -> list[int]:
    started: dict[object, datetime] = {}
    latencies = []
    for event in events:
        event_item = item(event)
        if event_type(event) != "mcp_tool_call" or not event.get("observed_at"):
            continue
        observed = datetime.fromisoformat(str(event["observed_at"]))
        if event.get("type") == "item.started":
            started[event_item.get("id")] = observed
        elif event.get("type") == "item.completed" and event_item.get("id") in started:
            latencies.append(
                round((observed - started[event_item.get("id")]).total_seconds() * 1000)
            )
    return latencies


def retry_count(tool_calls: list[dict[str, object]]) -> int:
    failed: set[str] = set()
    retries = 0
    for event in tool_calls:
        event_item = item(event)
        signature = json.dumps(
            [event_item.get("tool"), event_item.get("arguments")], sort_keys=True
        )
        if event_item.get("status") != "completed":
            failed.add(signature)
        elif signature in failed:
            retries += 1
            failed.remove(signature)
    return retries
