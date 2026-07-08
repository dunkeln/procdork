<h1 align="center">procdork - harness</h1>

The harness is the backend for procdork's data moat.

It is not just an ETL script. It is where raw evidence lands, where repeated SQL behavior is observed, where durable marts get promoted, and where MCP tools eventually serve stable answers back to clients.

## The Simple Story

Traditional ELT usually asks us to build the highway before we know where people actually drive.

```text
source -> connector -> warehouse -> dbt -> marts -> BI/API/MCP
```

That can work, but it makes the slowest part happen early. Before we know the useful questions, we are already choosing vendor paths, shaping schemas, writing dbt models, and creating product surfaces.

The harness flips that around.

```text
source -> raw evidence -> DuckDB/MotherDuck -> read-only SQL -> observations -> promoted mart -> semantic MCP -> OKF
```

We capture the source first. We keep the raw bytes. We make the evidence queryable. Then we watch what questions repeat. Only after a pattern proves useful do we promote it into a dbt mart, expose it as a semantic MCP tool, and document it in OKF.

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
observe repeated patterns
promote only what repeats
```

So the point is not "DuckDB is faster than a warehouse." The point is:

```text
Traditional ELT serializes learning behind pipeline/modeling work.
Harness parallelizes learning over raw evidence, then serializes only promotion.
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

Those numbers are placeholders until measured. The thing we should measure is not generic query speed. It is time from source arrival to first validated reusable mart or MCP tool.

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
repeated joins become promoted marts
OKF records the durable meaning
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

This layer is where manifests, SQL observations, and eventually marts are queryable. It is not the raw evidence store. It is the place where we inspect, count, aggregate, and serve.

Set `DUCKDB_PATH=md:procdork_analytics` and `MOTHERDUCK_TOKEN` to send harness manifest and observation tables to MotherDuck. Without `DUCKDB_PATH`, the harness falls back to `data/harness.duckdb`.

Run `uv run python main.py sync-neon-chat` to copy the demo web app's Neon chat tables into the harness OLAP database as `app_*` tables.

## What Gets Promoted

Read-only SQL is for discovery.

Repeated SQL sessions become evidence. Evidence can create a promotion candidate. A human decides if the candidate is real. Then it can become:

```text
dbt mart -> semantic MCP tool -> OKF concept
```

This is deliberate. Promotion is the serial gate that prevents schema sprawl.

## MCP Shape

The harness should eventually serve MCP over HTTP.

It has two faces:

```text
admin/exploration MCP:
  run_readonly_sql
  observe_sql_session
  list_promotion_candidates

product/semantic MCP:
  get_capture_summary
  get_supplier_risk_summary
  explain_metric
```

The product client should not know table names, SQL text, storage paths, or whether compute is local DuckDB or MotherDuck. The client should consume stable tools exposed by the harness.

Raw SQL MCP is the discovery backdoor. Semantic MCP is the product surface.

## OKF Shape

OKF is not the database, not telemetry, and not the transform engine.

OKF explains durable promoted behavior:

```text
DuckDB records evidence.
dbt/MCP materialize durable behavior.
OKF explains durable behavior.
```

That means no one-off SQL in OKF, no raw captures in OKF, and no per-run diary. OKF gets updated after a promoted mart/tool/metric/source contract exists.

Run `uv run python main.py okf-flush` from this directory to refresh OKF from promoted dbt marts.

## The Leverage

The moat is not one vendor or one clever model, it's the loop:

```text
preserve raw evidence
observe real analytical behavior
promote only repeated value
serve stable MCP tools
document durable knowledge
```

Small first. Measured later. Promotion only when the evidence earns it.
