from __future__ import annotations

import re
from uuid import uuid4

from ..evaluations import EvaluationResult


NAME = "inline_citations"
VERSION = "1"


def evaluate(
    *,
    case_id: str,
    request: str,
    response: str,
    citations: list[dict[str, object]],
    dataset_version: str,
    system_version: str,
    evidence_uri: str,
) -> EvaluationResult:
    markers = {int(value) for value in re.findall(r"\[(\d+)]", response)}
    valid_markers = {value for value in markers if 1 <= value <= len(citations)}
    checks = [
        bool(response.strip()),
        bool(citations),
        bool(valid_markers),
        markers == valid_markers,
    ]
    score = sum(checks) / len(checks)
    return EvaluationResult(
        run_id=str(uuid4()),
        case_id=case_id,
        dataset_version=dataset_version,
        system_version=system_version,
        evaluator_name=NAME,
        evaluator_version=VERSION,
        score=score,
        result="pass" if score == 1 else "fail",
        evidence_uri=evidence_uri,
        metadata={
            "request": request,
            "response": response,
            "citations": citations,
            "citation_count": len(citations),
            "inline_markers": sorted(markers),
        },
    )
