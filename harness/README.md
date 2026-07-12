<h1 align="center">procdork - harness</h1>

The harness is the backend for procdork's data moat.

It is not just an ETL script. It is where raw evidence lands, repeatable transforms run, and MCP clients receive both live answers and reviewed organizational context.

## The Simple Story

Traditional ELT usually asks us to build the highway before we know where people actually drive.

```text
source -> connector -> warehouse -> dbt -> marts -> BI/API/MCP
```

That can work, but it makes the slowest part happen early. Before we know the useful questions, we are already choosing vendor paths, shaping schemas, writing dbt models, and creating product surfaces.

The harness separates the data plane from the knowledge plane.

```text
data:      source -> raw evidence -> DuckDB/MotherDuck -> dbt marts -> MCP tools
knowledge: reviewed OKF bundle -------------------------------> MCP resources
```

We capture the source first, keep the raw bytes, and make the evidence queryable. Engineers can add dbt models when reproducibility or a product contract requires one. Stable definitions, join guidance, caveats, and playbooks are reviewed separately into the Git-authored OKF bundle. Agents can read that context before and while they use live tools.

## Code Boundary

The harness owns typed evidence, loading rules, transforms, knowledge, and the MCP surface. External systems live under `connectors/` and translate into those contracts.

```text
connectors -> typed harness stages -> DuckDB/dbt -> MCP
```

Entrypoints wire connectors into stages with ordinary callables or open connections. Core stages do not select providers. This keeps future schedulers or agent loops free to wrap the same stages without putting orchestration, state, or provider registries into the harness today.

## The Amdahl's Law Bet

Amdahl's Law says speedup is capped by the part of the system that cannot be parallelized.

In normal words: if half the work must happen in one slow line, adding more workers only helps the other half.

Traditional ELT has a big serial section before learning starts:

```text
pick connector
model schema
load warehouse
write dbt
build mart
then learn if anyone needed it
```

The harness tries to make the serial section smaller:

```text
capture raw evidence
load manifest/index
let people/agents explore
build shared transforms only when useful
```

So the point is not "DuckDB is faster than a warehouse." The point is:

```text
Traditional ELT serializes learning behind pipeline/modeling work.
Harness lets learning begin over raw evidence before shared modeling is required.
```

Example hypothesis:

```text
Traditional ELT:
serial fraction = 0.60
4 workers speedup = 1 / (0.60 + 0.40 / 4) = 1.43x

Harness:
serial fraction = 0.25
4 workers speedup = 1 / (0.25 + 0.75 / 4) = 2.29x
```

Those numbers are placeholders until measured. The thing we should measure is not generic query speed. It is time from source arrival to a validated reusable answer.

## The Gustafson's Law Moat

Gustafson's Law looks at scaling from the other direction.

Amdahl's Law asks how fast one fixed job can get when more workers help. Gustafson's Law asks how much larger the useful job can become when more workers show up.

In normal words: if the serial part stays small, more people and agents can take on more real work instead of waiting in one line.

That matters for the harness because the useful workload is not one dashboard. It is many teams asking many questions over many sources:

```text
BI asks for reporting cuts
QA asks for failure patterns
DS asks for feature evidence
programmers ask for operational traces
execs ask for compact business answers
```

The moat is that the harness lets that work expand without forcing every question through a modeling bottleneck first.

```text
raw evidence stays available
agents explore in parallel
server-side compute keeps answers compact
shared dbt models remove known recomputation
OKF supplies durable meaning to every client
```

As the number of teams and agents grows, the goal is not just faster execution. The goal is more validated analytical surface area per scarce review hour.

The useful measure is:

```text
reusable answers created per human review hour
```

If that number grows as more agents explore the moat, Gustafson's Law is working in our favor.

## What Stays Raw

Raw evidence belongs in blob storage.

Today that can be local disk. Later it can be S3 or R2. The contract is the same: store the original bytes, content hash, source pointer, adapter name, and load timestamp.

Raw evidence is the source of truth. It should not be rewritten to fit the first idea we had.

## What Gets Queried

DuckDB is the local OLAP surface. MotherDuck can become the shared remote OLAP surface.

This layer is where manifests, loaded source tables, and marts are queryable. It is not the raw evidence store. It is the place where we inspect, count, aggregate, and serve.

Set `DUCKDB_PATH=md:procdork_analytics` and `MOTHERDUCK_TOKEN` to send harness tables to MotherDuck. Without `DUCKDB_PATH`, the harness falls back to `data/harness.duckdb`.

Run `uv run python main.py sync-neon-chat` to copy the demo web app's Neon chat tables into the harness OLAP database as `app_*` tables.

## Evaluation Replay

Evaluation starts from a real historical case, reruns its original request
against a chosen deployment, evaluates the new response, and records the exact
request, response, citations, versions, and evidence URL.

```text
historical case -> live/preview deployment -> evaluator -> raw result -> dbt marts -> MCP
```

Run both prior successes and failures by default:

```bash
uv run python main.py eval-replay --system-version <release-or-commit>
```

Use `--previous-result fail` while repairing known failures. Use
`--previous-result pass` before promotion to check that known-good behavior did
not regress. Replay sessions use an `eval-` prefix, remain auditable in the app,
and are excluded from future seed-case selection.

dbt publishes the latest case state in `mart_evaluation_cases`, the repair queue
in `mart_evaluation_failures`, known-good anchors in
`mart_evaluation_successes`, and pass-to-fail changes in
`mart_evaluation_regressions`. These marts appear through the existing MCP mart
tools without a new runtime surface.

## What Gets Built

Read-only SQL is for discovery.

The harness does not rank queries or infer what deserves permanence. Notebook and ad hoc SQL can remain exploratory. An engineer writes a dbt model when a result needs to be reproducible, shared, tested, or served through a stable product contract.

```text
exploration -> explicit engineering decision -> dbt model or MCP tool
```

Knowledge remains independent:

```text
stable understanding -> reviewed OKF concept -> MCP resource
```

One path may reference the other, but neither waits for the other. This avoids speculative machinery while keeping both computation and meaning reviewable.

## MCP Shape

The harness serves an agent-agnostic MCP endpoint named `procdork` over HTTP.

```text
resources: reviewed OKF context
tools:     mart discovery, mart description, and bounded read-only SQL
```

The server uses DuckDB's parser to accept one `SELECT`, `DESCRIBE`, `SHOW`, or `EXPLAIN` statement, disables external access, and caps returned rows. Any MCP client can connect to the same `/mcp` endpoint without repository-specific client configuration.

This is an application-enforced boundary, not a database permission boundary: the current `MOTHERDUCK_TOKEN` remains write-capable. Keep the endpoint private and the token server-side. Add database-enforced read-only credentials when the operating risk or plan justifies them.

Set `WORKOS_AUTHKIT_DOMAIN` and `MCP_RESOURCE_URL` together to require WorkOS OAuth. Leave both unset for local development. The WorkOS dashboard must list the MCP URL as a Resource Indicator and enable CIMD or DCR for client registration.

## OKF Shape

OKF is not the database, telemetry, transform engine, or runtime-owned state. It is a versioned knowledge bundle written in Markdown and reviewed in Git.

```text
DuckDB/MotherDuck hold current evidence.
dbt models hold repeatable computation.
OKF holds durable meaning.
MCP serves resources and tools without owning either source of truth.
```

That means no one-off SQL, raw captures, volatile values, or per-run diary in OKF. A data engineer can steward the bundle, but the relevant domain owner reviews business, QA, compliance, or operational claims.

Production serves the bundle read-only. New knowledge is drafted, reviewed, merged, and deployed; runtime never writes it.

## The Leverage

The moat is not one vendor or one clever model, it's the loop:

```text
preserve raw evidence
explore without pre-modeling every question
author shared transforms only where useful
review durable knowledge in Git
serve stable MCP resources and tools
```

Small first. Measured later. Add machinery only when operating evidence earns it.
