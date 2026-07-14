<h1 align="center">the harness</h1>

The harness turns source evidence into governed answers for user agents.

The [project README](../README.md) explains the product argument and measured
evidence. This document explains how to operate and extend the runtime.

## One Loop

```text
sources
  -> connectors
  -> typed raw evidence
  -> DuckDB or MotherDuck
  -> dbt tables
  -> reviewed knowledge
  -> MCP
  -> user agents
```

Each part has one job.

Connectors translate external systems. Extraction and loading preserve source
evidence. dbt makes repeated computation explicit. Knowledge records meaning
and caveats. MCP gives every compatible agent the same read-only boundary.

The parts remain separate in code but ship as one small Python package.

## Start Here

```bash
cd harness
uv sync --frozen
uv run harness --help
```

Run the MCP server locally:

```bash
uv run harness serve-mcp
```

The local endpoint is `http://localhost:8000/mcp`. The deployed endpoint is
`https://procdork.vercel.app/mcp`.

Without configuration, analytical data lives in `data/harness.duckdb`. Point
`DUCKDB_PATH` at another DuckDB-compatible location to change the OLAP backend.

## What Agents Receive

The MCP exposes four tools:

| Tool | Purpose |
| --- | --- |
| `read_knowledge` | Read reviewed meaning and caveats before analysis |
| `list_tables` | Discover published analytical tables |
| `describe_table` | Inspect a table's columns and types |
| `query` | Run one bounded, read-only analytical statement |

Knowledge documents are also exposed as MCP resources under
`okf://bundle/...`.

`query` returns a Markdown table when the result is not safely chartable.
Otherwise it can render line, bar, segmented, or heatmap SVGs and return
deterministic key facts. SQL performs the computation; the agent does not need
to recalculate the result in chat.

The server accepts one `SELECT`, `DESCRIBE`, `SHOW`, or `EXPLAIN` statement,
disables external access during execution, and bounds returned rows. This is an
application-enforced read-only boundary; database credentials still need the
appropriate operating controls.

## Operator Surfaces

An operator normally works in four places:

| Surface | Location | Responsibility |
| --- | --- | --- |
| Connectors | `src/harness/connectors/` | Translate external systems into harness contracts |
| Transforms | `transforms/dbt/` | Publish repeatable analytical tables |
| Knowledge | `src/harness/knowledge/` | Record reviewed meaning, caveats, and interpretations |
| Evaluators | `src/harness/evaluators/` | Score source-backed outcomes with ordinary functions |

The stable runtime lives in `src/harness/`. Benchmarks and smoke evidence stay
under `e2e/`; they are not application features.

### Add a source

Keep provider behavior in a connector. Feed its output into the existing typed
extraction or loading boundary instead of teaching the core about a vendor.

```bash
uv run harness extract <url-or-path>
uv run harness sync-neon-chat
uv run harness sync-ingestion-events <events.jsonl>
```

### Publish an analysis

Exploration may remain in notebooks or transient SQL. When an answer must be
repeatable, add a dbt model. Its adjacent knowledge document should explain the
table's grain, measures, caveats, and useful presentation shapes.

```text
dbt determines the answer
knowledge explains the answer
MCP delivers the answer
```

The runtime never writes knowledge. A person edits it, reviewers approve it,
and deployment serves it read-only.

### Evaluate a release

Evaluators share one provider-neutral result contract. Provider SDK details
belong in connectors; evaluator logic remains an ordinary operator-editable
function.

```bash
uv run harness eval-replay --system-version <release-or-commit>
```

The larger comparison corpus and its raw-SQL baseline are isolated under
`e2e/benchmarks/`. They produce evidence for the analytical tables; they do not
expand the production MCP surface.

## Refresh And Publication

The harness does not contain a scheduler. An external trigger runs the existing
commands:

```text
sync sources -> dbt build -> record refresh outcome
```

The repository's GitHub Actions workflow runs that chain every 15 minutes and
preserves a refresh receipt. A failed source or transform is reported as
degraded or failed while previously published tables remain available.

This stays one scheduled workflow until retries, backfills, or dependencies
prove that a workflow engine is necessary.

## Configuration

| Variable | Purpose |
| --- | --- |
| `DUCKDB_PATH` | Local DuckDB path or remote MotherDuck database |
| `MOTHERDUCK_TOKEN` | Server-side MotherDuck credential |
| `DATABASE_URL` | Source Postgres connection used by the Neon connector |
| `WORKOS_AUTHKIT_DOMAIN` | WorkOS issuer for OAuth-protected MCP |
| `MCP_RESOURCE_URL` | Public MCP resource URL used by OAuth and chart links |
| `CHART_SIGNING_KEY` | Encrypts short-lived stateless chart payloads |
| `MCP_MAX_QUERY_ROWS` | Maximum rows fetched by read-only execution |
| `HOST`, `PORT` | MCP HTTP bind address |

Set `WORKOS_AUTHKIT_DOMAIN` and `MCP_RESOURCE_URL` together for OAuth. Leave
both unset for local development.

## Change Safely

A small feature can cross several contracts:

```text
dbt shape -> knowledge interpretation -> MCP schema -> renderer -> runtime proof
```

Use [CONTRIBUTING.md](CONTRIBUTING.md) to identify the affected seams and run
only the checks reached by the change. Do not add registries, orchestration, or
parallel schemas before repeated operating evidence requires them.
