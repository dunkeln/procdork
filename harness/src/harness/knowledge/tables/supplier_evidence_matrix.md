---
type: Table
title: Supplier Evidence Matrix
description: Heatmap-ready supplier evidence dimensions.
resource: procdork://tables/supplier_evidence_matrix
tags: [supplier, sourcing, heatmap]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "heatmap: supplier_name, evidence_dimension, sum(evidence_value)"
  - "table: inspect non-zero evidence cells when explaining a supplier recommendation"
---

# Meaning

This table explains supplier readiness as a matrix instead of a scalar score.
Each cell shows whether the current evidence contains a signal such as price,
lead time, MOQ, certification, low confidence, or conflicts.

# Grain

One non-zero supplier and evidence-dimension cell.

# Measures

* `evidence_value` counts the extracted evidence for that dimension.
* `low confidence` and `open conflicts` are review-risk dimensions, not positive
  readiness signals.

# Useful Questions

* Why is one supplier on the frontier and another dominated?
* Which supplier evidence cells are still missing?
* Are the strongest candidates strong because of proof breadth or just one
  repeated signal?

# Caveats

Heatmap color shows count intensity. It does not mean supplier quality, total
landed cost, approval, or business fit.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_evidence_matrix.sql)
