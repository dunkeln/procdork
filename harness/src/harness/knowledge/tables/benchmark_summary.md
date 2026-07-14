---
type: Table
title: Benchmark Summary
description: Quality, reliability, time, token, and cost metrics grouped by treatment and case family.
resource: procdork://tables/benchmark_summary
tags: [benchmark, quality, efficiency]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "bar: compare deterministic_pass_rate or semantic dimensions across treatments for the same case family"
  - "table: retain run_count, variability, and version fields beside any headline metric"
---

# Meaning

This table compresses run evidence into comparable views without creating
role-specific scorecards. The same metrics can support product, engineering,
data, reliability, and operating questions.

# Grain

One row per dataset version, system version, treatment, and case family.

# Measures

* Pass rate and semantic dimensions describe answer quality.
* median and p95 elapsed time describe workflow responsiveness.
* Tool errors and score deviation expose reliability and repeatability.
* Tokens and dated cost proxy describe agent usage.
* Human interventions describe coordination work.

# Caveats

Semantic scores do not gate releases. Averages must be read with run counts and
variation. Time reduction is task-specific and is not a claim about total
historical development effort.

# Citations

[1] [Benchmark summary transform](../../transforms/dbt/models/marts/evals/mart_benchmark_summary.sql)
[2] [Benchmark comparison transform](../../transforms/dbt/models/marts/evals/mart_benchmark_comparison.sql)
