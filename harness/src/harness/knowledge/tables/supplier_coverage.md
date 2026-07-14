---
type: Table
title: Supplier Coverage
description: Structured supplier fact coverage against the observed source landscape.
resource: procdork://tables/supplier_coverage
tags: [supplier, coverage, documents]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "bar: coverage_metric, coverage_stage, coverage_value"
  - "table: inspect all rows before claiming supplier richness"
---

# Meaning

This table prevents structured supplier claims from being mistaken for total
supplier coverage. It compares the stable observed-source landscape with the
smaller structured supplier fact surface.

# Grain

One row per coverage metric.

# Measures

* `coverage_stage` separates observed evidence from structured supplier facts.
* `coverage_metric` names the count or proxy.
* `coverage_value` is the chartable value.
* `structured suppliers per 100 source domains` is a rough gap indicator, not a
  true supplier recall metric.

# Useful Questions

* Is supplier fact coverage broad enough to trust a supplier comparison?
* Are the heatmap suppliers only a tiny slice of the observed evidence base?
* Should operators add more structured supplier facts before using supplier comparisons?

# Caveats

Source domains are not suppliers. One supplier can have many domains, and one
domain can contain non-supplier evidence. Use this as a coverage warning, not
as a recall score.

# Query Shape

Use this table directly for the coverage chart:

```sql
select coverage_metric, coverage_stage, coverage_value
from supplier_coverage
order by coverage_stage, coverage_metric
```

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_coverage.sql)
