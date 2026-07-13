---
type: Table
title: Benchmark Runs
description: Run-level evidence for paired harness, raw-SQL, and human analytical tasks.
resource: procdork://tables/benchmark_runs
tags: [benchmark, reliability, cost]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: inspect individual failures, latency, tokens, tool errors, and semantic dimensions before using an aggregate claim"
  - "bar: compare elapsed_ms or cost_proxy_usd by treatment only within the same dataset and system version"
---

# Meaning

This table is the evidence ledger for the diverse analytical benchmark. Automated
questions run through both the normal harness and a raw read-only SQL baseline;
manual timings use the `human` treatment. Browser-operated timings use
`operator_agent` and must not be presented as human evidence.

# Grain

One row per case attempt and treatment.

# Measures

* Deterministic scores measure observable completion and contract checks.
* Five semantic scores are report-only judgments from the pinned external judge.
* Token counts and elapsed time come from the captured workflow events.
* `cost_proxy_usd` uses the dated rates retained with the run; it is not a bill.

# Caveats

Human timings have no token, tool, or semantic-judge fields. Automated latency
includes the agent workflow and tool calls. Comparisons are valid only when
dataset, system, and agent versions match.

# Citations

[1] [Benchmark runs transform](../../transforms/dbt/models/marts/evals/mart_benchmark_runs.sql)
[2] [Benchmark corpus](../../e2e/benchmarks/cases.jsonl)
