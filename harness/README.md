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

The harness serves MCP over HTTP using three distinct protocol surfaces:

```text
resources: reviewed OKF context
prompts:   user-selected workflows for QA, engineering, or executive work
tools:     live queries and computations over shared models
```

The current `serve-mcp` slice exposes the OKF bundle as read-only resources. Query tools and audience prompts arrive only when their contracts are backed by real usage.

The product client should not know table names, SQL text, storage paths, or whether compute is local DuckDB or MotherDuck. Stable MCP tools will hide those implementation details.

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

## Deployment Shape

The code boundaries stay separate while deployment remains one container image.

```text
docker build -t procdork-harness .
docker run --rm -p 8000:8000 procdork-harness
```

The image defaults to `python main.py serve-mcp`. On AWS, run it as one private ECS/Fargate service. EventBridge can start the same image as finite ECS tasks with command overrides such as `python main.py sync-neon-chat` or `dbt run`. Storage stays outside the container in S3/R2 and MotherDuck.

There is no OKF refresh job. A merged bundle ships with the next image. Keep the MCP endpoint private until an explicit authentication boundary exists.

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
