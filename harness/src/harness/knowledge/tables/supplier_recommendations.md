---
type: Table
title: Supplier Recommendations
description: Pareto frontier for supplier candidates by evidence dimensions.
resource: procdork://tables/supplier_recommendations
tags: [supplier, sourcing, recommendation]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "table: inspect pareto-frontier suppliers before naming a preferred candidate"
  - "heatmap: use supplier_evidence_matrix to explain why candidates differ"
---

# Meaning

This table shows which supplier candidates are not dominated by another
candidate across the current evidence dimensions. It is a prioritization
surface for operator review, not an approved vendor decision.

# Grain

One row per canonical supplier.

# Measures

* `review_group` is `pareto-frontier` when no other supplier is at least as good
  on every evidence dimension and better on one.
* `dominated_by_supplier_count` counts how many suppliers dominate this one.
* Claim count columns show which evidence dimensions exist; they are not a
  weighted score.

# Useful Questions

* Which supplier should be reviewed first based on available evidence?
* Which candidates have price and lead-time evidence?
* Which promising candidates still carry unresolved conflicts?

# Caveats

This is not total landed cost, supplier quality, approval status, capacity, or
contract fit. It only compares the evidence currently extracted into the
harness.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_recommendations.sql)
