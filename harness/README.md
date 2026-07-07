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

So the A/B is not "DuckDB is faster than a warehouse." The A/B is:

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

## What Stays Raw

Raw evidence belongs in blob storage.

Today that can be local disk. Later it can be S3 or R2. The contract is the same: store the original bytes, content hash, source pointer, adapter name, and load timestamp.

Raw evidence is the source of truth. It should not be rewritten to fit the first idea we had.

## What Gets Queried

DuckDB is the local OLAP surface. MotherDuck can become the shared remote OLAP surface.

This layer is where manifests, SQL observations, and eventually marts are queryable. It is not the raw evidence store. It is the place where we inspect, count, aggregate, and serve.

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
