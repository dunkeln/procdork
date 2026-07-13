from __future__ import annotations

import json
import os

from anthropic import Anthropic

from e2e.benchmarks.evaluator import DIMENSIONS, RUBRIC_VERSION


JUDGE_PROMPT_VERSION = "1"


def judge_response(
    case: dict[str, object], response: str, model: str
) -> tuple[dict[str, int], str, dict[str, int]]:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    result = client.messages.create(
        model=model,
        max_tokens=800,
        system=(
            "Score an analytical answer against the supplied question and evidence contract. "
            "Do not reward glossary wording. A supported answer must stay within available evidence; "
            "an abstention case should explicitly state what cannot be established. Use anchored integers: "
            "1 is materially wrong or unusable, 3 is adequate with important limitations, and 5 is fully "
            "grounded, complete, calibrated, useful, and concise. The treatment is intentionally hidden. "
            "Return one overall rationale under 120 words."
        ),
        messages=[
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "rubric_version": RUBRIC_VERSION,
                        "question": case["question"],
                        "expected_behavior": case["expected_behavior"],
                        "permitted_tables": case["tables"],
                        "required_caveats": case["required_caveats"],
                        "reference_evidence": case.get("reference_evidence"),
                        "answer": response,
                    },
                    sort_keys=True,
                    default=str,
                ),
            }
        ],
        tools=[
            {
                "name": "score_response",
                "description": "Return the five anchored evaluation scores and brief rationales.",
                "input_schema": {
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
                },
            }
        ],
        tool_choice={"type": "tool", "name": "score_response"},
    )
    block = next(block for block in result.content if block.type == "tool_use")
    payload = block.input
    if not isinstance(payload, dict) or not isinstance(payload.get("scores"), dict):
        raise ValueError("Anthropic judge returned an invalid score payload")
    return (
        {name: int(payload["scores"][name]) for name in DIMENSIONS},
        str(payload.get("rationale", ""))[:800],
        {
            "input_tokens": result.usage.input_tokens,
            "output_tokens": result.usage.output_tokens,
        },
    )
