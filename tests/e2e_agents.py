"""Run the deployed Procdork MCP through Codex and Claude Code."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
from time import monotonic
from typing import Any
from uuid import uuid4
from urllib.request import Request, urlopen

import logfire
from opentelemetry import propagate, trace

from telemetry import configure_logfire


ROOT = Path(__file__).resolve().parent
ARTIFACT_ROOT = ROOT / "artifacts"
CHART_URL = re.compile(r"https?://[^\s)\]\"']+/charts/[^\s)\]\"']+")
EXPECTED_TOOLS = {"read_knowledge", "list_tables", "query"}


@dataclass(frozen=True)
class Scenario:
    name: str
    prompt: str
    tools: frozenset[str]
    requires_chart: bool = False
    requires_media: bool = False
    requires_boundary: bool = False


SCENARIOS = (
    Scenario(
        name="catalog_heatmap",
        tools=frozenset(EXPECTED_TOOLS),
        requires_chart=True,
        prompt=(
            "Use only the procdork MCP. Call read_knowledge(path='tables/evidence_capture') "
            "and list_tables before querying. Treat the live catalog as authoritative. "
            "Produce the documented evidence_capture heatmap with category=session_slug, "
            "segment=evidence_type, and value=source_count. State one caveat."
        ),
    ),
    Scenario(
        name="supplier_boundary",
        tools=frozenset({"read_knowledge", "list_tables"}),
        requires_boundary=True,
        prompt=(
            "Use only the procdork MCP. Call read_knowledge(path='tables') and list_tables. "
            "Can you produce a supplier-level procurement coverage heatmap? Do not query an "
            "unavailable table, invent supplier claims, or substitute another chart. State the "
            "current data boundary in one concise answer."
        ),
    ),
    Scenario(
        name="chart_media",
        tools=frozenset(EXPECTED_TOOLS),
        requires_chart=True,
        requires_media=True,
        prompt=(
            "Use only the procdork MCP. Call read_knowledge(path='tables/evidence_capture') "
            "and list_tables before querying. Query the documented evidence_capture heatmap. "
            "Return the chart and its caveat exactly as the MCP provides it."
        ),
    ),
)


def main() -> int:
    require_environment()
    configure_logfire()
    run_root = ARTIFACT_ROOT / timestamped_run_id()
    violations: list[dict[str, Any]] = []
    for provider in ("codex", "claude"):
        for scenario in SCENARIOS:
            result = run_scenario(provider, scenario, run_root)
            violations.extend(result["violations"])
    print(json.dumps({"run_directory": str(run_root), "violations": violations}, indent=2))
    return 1 if violations else 0


def require_environment() -> None:
    missing = [
        name
        for name in ("E2E_MCP_URL",)
        if not os.environ.get(name)
    ]
    if missing:
        raise SystemExit(f"Missing required environment: {', '.join(missing)}")


def timestamped_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{uuid4()}"


def run_scenario(provider: str, scenario: Scenario, run_root: Path) -> dict[str, Any]:
    run_id = str(uuid4())
    started_at = datetime.now(UTC).isoformat()
    artifact_dir = run_root / provider / scenario.name
    artifact_dir.mkdir(parents=True)
    prompt_path = artifact_dir / "prompt.txt"
    prompt_path.write_text(scenario.prompt, encoding="utf-8")
    with logfire.span(
        "e2e.run",
        provider=provider,
        scenario=scenario.name,
        **{"e2e.run_id": run_id},
    ):
        with logfire.span("agent.cli", provider=provider, scenario=scenario.name):
            headers: dict[str, str] = {}
            propagate.inject(headers)
            output = run_cli(provider, prompt_path, artifact_dir, run_id, headers)
        result = assess(provider, scenario, output, run_id, headers)
        result["started_at"] = started_at
        result["completed_at"] = datetime.now(UTC).isoformat()
        result["traceparent"] = headers["traceparent"]
        result["mcp_echo"] = probe_mcp_echo(run_id, headers)
        if result["mcp_echo"]["echoed_run_id"] is not True:
            result["violations"].append("missing_trace_correlation")
        for tool in result["tools"]:
            with logfire.span("agent.mcp_tool", tool=tool, provider=provider):
                pass
        for check in result["chart_checks"]:
            with logfire.span("chart.asset", **check):
                pass
        write_artifact(
            artifact_dir / "events.json",
            {"events": normalized_events(json_events(str(output["stdout"])))},
        )
        write_artifact(artifact_dir / "summary.json", result)
        logfire.info(
            "e2e.contract_result",
            provider=provider,
            scenario=scenario.name,
            **{"e2e.run_id": run_id},
            violation_count=len(result["violations"]),
            elapsed_ms=output["elapsed_ms"],
        )
        return result


def run_cli(
    provider: str,
    prompt_path: Path,
    artifact_dir: Path,
    run_id: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    script = ROOT / f"run_{provider}.sh"
    env = {
        **os.environ,
        "E2E_RUN_ID": run_id,
        "E2E_TRACEPARENT": headers["traceparent"],
    }
    command = [str(script), str(prompt_path)]
    started = monotonic()
    process = subprocess.Popen(
        command,
        cwd=ROOT.parent,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr, first_output_ms = capture_process(process)
    elapsed_ms = round((monotonic() - started) * 1000)
    (artifact_dir / "stdout.jsonl").write_text(redact(stdout), encoding="utf-8")
    (artifact_dir / "stderr.log").write_text(redact(stderr), encoding="utf-8")
    return {
        "return_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "elapsed_ms": elapsed_ms,
        "first_output_ms": first_output_ms,
        "cli_version": cli_version(provider),
    }


def capture_process(process: subprocess.Popen[str]) -> tuple[str, str, int | None]:
    selector = selectors.DefaultSelector()
    assert process.stdout is not None and process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    lines = {"stdout": [], "stderr": []}
    started = monotonic()
    first_output_ms: int | None = None
    while selector.get_map():
        for key, _ in selector.select():
            line = key.fileobj.readline()
            if not line:
                selector.unregister(key.fileobj)
                continue
            lines[key.data].append(line)
            if first_output_ms is None and key.data == "stdout":
                first_output_ms = round((monotonic() - started) * 1000)
    process.wait()
    return "".join(lines["stdout"]), "".join(lines["stderr"]), first_output_ms


def assess(
    provider: str,
    scenario: Scenario,
    output: dict[str, Any],
    run_id: str,
    headers: dict[str, str],
) -> dict[str, Any]:
    events = json_events(str(output["stdout"]))
    tools = observed_tools(events)
    queries = observed_queries(events)
    response = final_response(provider, events, str(output["stdout"]))
    violations = []
    if output["return_code"] != 0:
        violations.append("cli_nonzero_exit")
    missing_tools = sorted(scenario.tools - tools)
    if missing_tools:
        violations.append(f"missing_tools:{','.join(missing_tools)}")
    if scenario.name != "supplier_boundary" and "evidence_capture" not in response.lower() + str(events).lower():
        violations.append("live_evidence_capture_not_used")
    if scenario.requires_boundary and not any(
        phrase in response.lower()
        for phrase in (
            "cannot",
            "not available",
            "unavailable",
            "not live",
            "not loaded",
            "limited to",
        )
    ):
        violations.append("supplier_boundary_not_stated")
    if scenario.requires_boundary and queries:
        violations.append("supplier_boundary_query_used")
    chart_checks = []
    urls = sorted(set(CHART_URL.findall(str(events) + "\n" + response)))
    if scenario.requires_chart and not urls:
        violations.append("missing_chart_url")
    for url in urls:
        check = fetch_chart(url, run_id, headers)
        chart_checks.append(check)
        if check["status"] != "ok":
            violations.append(f"chart_asset:{check['status']}")
        if check.get("echoed_run_id") is not True:
            violations.append("missing_chart_run_id_echo")
    if scenario.requires_media and not has_image_content(events):
        violations.append("markdown_only_chart_transport")
    return {
        "provider": provider,
        "scenario": scenario.name,
        "e2e_run_id": run_id,
        "trace_id": trace_id(),
        "tools": sorted(tools),
        "queries": queries,
        "response_sha256": sha256(response.encode()).hexdigest(),
        "response": redact(response),
        "elapsed_ms": output["elapsed_ms"],
        "first_output_ms": output["first_output_ms"],
        "cli_version": output["cli_version"],
        "model_identifier": model_identifier(events),
        "chart_checks": chart_checks,
        "violations": violations,
    }


def json_events(stdout: str) -> list[dict[str, Any]]:
    events = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def observed_tools(events: list[dict[str, Any]]) -> set[str]:
    tools = set()
    for value in walk(events):
        if not isinstance(value, dict):
            continue
        for key in ("tool", "name"):
            tool = value.get(key)
            if not isinstance(tool, str):
                continue
            normalized = tool.removeprefix("mcp__procdork__").split(".")[-1]
            if normalized in EXPECTED_TOOLS:
                tools.add(normalized)
    return tools


def observed_queries(events: list[dict[str, Any]]) -> list[str]:
    queries = []
    for value in walk(events):
        if not isinstance(value, dict):
            continue
        tool = value.get("tool") or value.get("name")
        if not isinstance(tool, str):
            continue
        if tool.removeprefix("mcp__procdork__").split(".")[-1] != "query":
            continue
        arguments = value.get("arguments", value.get("input", {}))
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                continue
        if isinstance(arguments, dict) and isinstance(arguments.get("sql"), str):
            queries.append(arguments["sql"])
    return queries


def final_response(provider: str, events: list[dict[str, Any]], stdout: str) -> str:
    candidates = []
    for value in walk(events):
        if not isinstance(value, dict):
            continue
        if provider == "codex" and value.get("type") == "agent_message":
            candidates.append(str(value.get("text", "")))
        if provider == "claude" and isinstance(value.get("result"), str):
            candidates.append(value["result"])
    return candidates[-1] if candidates else stdout


def has_image_content(events: list[dict[str, Any]]) -> bool:
    return any(
        isinstance(value, dict)
        and value.get("type") in {"image", "image_content"}
        and isinstance(value.get("data"), str)
        for value in walk(events)
    )


def normalized_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for event in events:
        item: dict[str, Any] = {"event_type": event.get("type", "unknown")}
        tool = event.get("tool") or event.get("name")
        if isinstance(tool, str):
            item["tool"] = tool.removeprefix("mcp__procdork__")
        model = model_identifier([event])
        if model:
            item["model"] = model
        if has_image_content([event]):
            item["has_image_content"] = True
        normalized.append(item)
    return normalized


def model_identifier(events: list[dict[str, Any]]) -> str | None:
    models = []
    for value in walk(events):
        if not isinstance(value, dict):
            continue
        model = value.get("model")
        if isinstance(model, str):
            models.append(model)
    return models[-1] if models else None


def probe_mcp_echo(run_id: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(
        os.environ["E2E_MCP_URL"],
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "e2e-echo-probe",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "procdork-e2e", "version": "1"},
                },
            }
        ).encode(),
        headers={
            **headers,
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": "2025-06-18",
            "X-E2E-Run-ID": run_id,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            return {
                "status": response.status,
                "echoed_run_id": response.headers.get("X-E2E-Run-ID") == run_id,
            }
    except Exception as error:  # E2E evidence needs the surfaced transport error.
        return {"status": type(error).__name__, "echoed_run_id": False}


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def fetch_chart(url: str, run_id: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers={**headers, "X-E2E-Run-ID": run_id})
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            body = response.read()
            return {
                "status": "ok" if body and response.status == 200 else "empty_response",
                "content_type": response.headers.get_content_type(),
                "echoed_run_id": response.headers.get("X-E2E-Run-ID") == run_id,
            }
    except Exception as error:  # E2E evidence needs the surfaced transport error.
        return {"status": type(error).__name__, "echoed_run_id": False}


def cli_version(provider: str) -> str:
    result = subprocess.run([provider, "--version"], capture_output=True, text=True, check=False)
    return (result.stdout or result.stderr).strip()


def trace_id() -> str:
    context = trace.get_current_span().get_span_context()
    return f"{context.trace_id:032x}" if context.is_valid else ""


def redact(value: str) -> str:
    return CHART_URL.sub("[redacted-chart-url]", value)


def write_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
