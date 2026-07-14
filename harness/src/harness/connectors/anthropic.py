from __future__ import annotations

import json
import os


def judge_json(
    *,
    model: str,
    system: str,
    payload: dict[str, object],
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, object],
    max_tokens: int = 900,
) -> tuple[dict[str, object], dict[str, int]]:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError("Install the benchmark dependency group to use Anthropic judges") from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic judges")

    response = Anthropic(api_key=api_key).messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": json.dumps(payload, sort_keys=True)}],
        tools=[
            {
                "name": tool_name,
                "description": tool_description,
                "input_schema": input_schema,
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
    )
    block = next((item for item in response.content if item.type == "tool_use"), None)
    if block is None or not isinstance(block.input, dict):
        raise ValueError("Anthropic judge returned no structured tool result")
    return block.input, {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
