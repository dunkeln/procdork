---
type: Table
title: Supplier Extraction Coverage
description: Structured supplier extraction coverage against the observed document landscape.
resource: procdork://tables/supplier_extraction_coverage
tags: [supplier, coverage, documents]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "table: compare observed_domain_count, source_observation_count, and structured_supplier_count before claiming supplier richness"
  - "bar: compare observed_domain_count and structured_supplier_count only as a coverage gap, not as equivalent business entities"
---

# Meaning

This table prevents supplier evidence density from being mistaken for total
supplier coverage. The supplier evidence matrix only describes suppliers that
were already extracted into structured claims. This table compares that small
structured set against the broader observed document landscape.

# Grain

One row for the currently loaded supplier extraction snapshot.

# Measures

* `observed_domain_count` counts source domains seen in document intelligence.
* `source_observation_count` counts observed document/source appearances.
* `structured_supplier_count` counts suppliers that reached structured supplier
  intelligence.
* `domain_to_supplier_coverage_proxy` is a rough gap indicator, not a true
  supplier recall metric.

# Useful Questions

* Is supplier extraction coverage broad enough to trust a supplier comparison?
* Are the heatmap suppliers only a tiny slice of the observed evidence base?
* Should operators run more claim extraction before using supplier recommendations?

# Caveats

Source domains are not suppliers. One supplier can have many domains, and one
domain can contain non-supplier evidence. Use this as a coverage warning, not
as a recall score.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_extraction_coverage.sql)
