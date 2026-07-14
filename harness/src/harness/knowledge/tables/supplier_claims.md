---
type: Table
title: Supplier Claims
description: Source-backed extracted procurement facts with supplier identity, provenance, confidence, and conflict state.
resource: procdork://tables/supplier_claims
tags: [supplier, claims, provenance]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: filter claim_field and inspect source_url, source_text_span, claim_confidence, and has_open_conflict before using a fact in an operator answer"
  - "heatmap: compare claim_count across supplier_name and artifact_type to show supplier evidence flow by document kind"
  - "bar: compare claim counts only after grouping by an explicit field; mixed fields are not comparable measures"
---

# Meaning

This is the auditable fact surface. It retains each claim emitted from document
ingestion beside the exact source pointer, extraction method, confidence label,
and any linked conflict.

# Grain

One extracted claim observation per ingestion event and claim ID.

# Measures and Dimensions

* `claim_field` and `claim_value` retain the extracted procurement fact.
* `supplier_name` and `artifact_type` show which supplier received evidence from which document kind.
* `source_url`, `source_page`, `source_row`, and `source_text_span` carry source provenance when available.
* `claim_confidence` describes extraction confidence, not business approval.
* `has_open_conflict` marks a disagreement that should remain visible to an operator.

# Chart Contracts

For supplier evidence flow, use one chart-ready heatmap query:

```sql
select
    supplier_name,
    artifact_type,
    count(*) as claim_count
from supplier_claims
where supplier_name is not null and artifact_type is not null
group by 1, 2
order by claim_count desc
```

If this returns no rows, say structured supplier claims are unavailable; do not
probe with separate row-count queries or fall back to cached supplier data.

# Useful Questions

* Operators: what exact price, MOQ, lead-time, grade, or certification evidence supports the next action?
* Operators: which document kinds are feeding each supplier's evidence trail?
* Data scientists: where are extraction confidence and conflict patterns concentrated by source type or field?
* Developers: which parser/source combinations create low-confidence or conflicting facts?

# Caveats

Claims are observations from source material. They do not prove supplier truth,
current availability, approval, or total landed cost. Conflicting values are
preserved rather than silently resolved.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_claims.sql)
