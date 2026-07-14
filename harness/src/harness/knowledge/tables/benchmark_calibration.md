---
type: Table
title: Benchmark Calibration
description: Agreement between a blind independent reviewer and the pinned semantic judge.
resource: procdork://tables/benchmark_calibration
tags: [benchmark, evaluation, calibration]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: inspect mean_absolute_difference and within_one_point_rate for every semantic dimension"
---

# Meaning

This table checks whether the semantic judge agrees with a blind independent
reviewer enough to support descriptive reporting. `reviewer_type` distinguishes
actual human review from cross-model Codex review.

# Grain

One row per dataset version, system version, reviewer type, and semantic dimension.

# Measures

* `mean_absolute_difference` measures average distance on the anchored 1-5 scale.
* `within_one_point_rate` measures how often human and judge scores are close.

# Caveats

Calibration uses 12 balanced outputs and does not make either reviewer ground
truth. Cross-model agreement is not human validation. Judge scores remain
report-only even when agreement is high.

# Citations

[1] [Calibration transform](../../transforms/dbt/models/marts/evals/mart_benchmark_calibration.sql)
