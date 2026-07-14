# Contributing

The harness is a chain of small contracts:

```text
source data -> typed load -> dbt table -> knowledge -> MCP -> presentation
```

A change is complete when every affected contract still agrees. Do not update
every layer by default; trace the change and touch only the seams it reaches.

## Change Map

| Change | Check or update |
| --- | --- |
| Add a source | `src/harness/connectors/`, typed extraction/load boundary, CLI wiring |
| Change loaded data | Pydantic contract, persistence shape, dependent staging models |
| Add or change a table | dbt model, its knowledge grain, measures, and caveats |
| Recommend a visualization | That table's `interpretations` knowledge metadata |
| Add a chart kind | `ChartKind`, payload validation, renderer, MCP input schema |
| Add an evaluator | One function in `src/harness/evaluators/`; connector only for external SDK work |
| Change a scheduled stage | Existing CLI command, external workflow, refresh receipt |
| Change an MCP tool | Tool description, input/output contract, one real client smoke |

## Tables And Knowledge

A dbt table defines reproducible computation. Its knowledge document defines
how people and agents should understand it.

When adding or changing a table:

1. Define a stable grain in `transforms/dbt/models/`.
2. Add or update its document under `src/harness/knowledge/tables/`.
3. Record its meaning, grain, measures, caveats, and useful interpretations.
4. Link the document from `src/harness/knowledge/tables/index.md`.
5. Query the published table through the MCP using its public name.

Do not put live values in knowledge. Do not claim that counts, missing rows, or
conflicts mean more than the table establishes.

## Visualizations

Visualization intent belongs with the table's knowledge, not in a global chart
playbook. For example:

```yaml
interpretations:
  - "heatmap: compare source_count across session_number and evidence_type"
```

Before adding a visualization:

1. Confirm the table emits the required dimensions and numeric measure.
2. Check `src/harness/chart_payload.py` for an existing chart kind.
3. If supported, add only the table-specific knowledge interpretation.
4. If unsupported, extend the chart literal, payload validation, renderer, and
   `query` tool schema together.
5. Render one representative result through the MCP App or inspect the Markdown output.

Keep query columns ordered according to the renderer contract:

```text
bar or line: category, value
segmented:   category, segment, value
heatmap:     category, segment, value
table:       any bounded tabular result
```

`auto` may choose a line, bar, or Markdown table from the result shape. Request
specialized presentations such as `heatmap` explicitly.

## Evaluations

Keep one provider-neutral `EvaluationResult`. Evaluators are ordinary functions;
provider SDK mechanics stay in connectors. Do not add evaluator registries,
recipe types, or runner frameworks until several real evaluators repeat the same
mechanics.

## Checks

Run only the checks reached by the change:

```bash
uv sync --frozen
uvx ruff check src/harness e2e/benchmarks vercel_app.py
uv run python -m compileall -q src
uv run harness --help
uv run dbt parse --project-dir transforms/dbt --profiles-dir <profiles-dir> --target <target>
```

Then exercise one real vertical path. Examples include extracting one local
file, rendering one chart, building the changed dbt model, or calling the
changed MCP tool through an MCP client.

## Restraint

Prefer existing contracts and ordinary functions. Do not add a registry,
factory, provider interface, duplicated schema, dashboard, or workflow engine
for a single implementation. Add machinery only after repeated production work
shows the smaller seam is insufficient.
