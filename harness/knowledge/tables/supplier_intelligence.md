---
type: Table
title: Supplier Intelligence
description: Evidence coverage, extracted procurement signals, and open claim conflicts by canonical supplier.
resource: procdork://tables/supplier_intelligence
tags: [supplier, sourcing, procurement]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: compare evidence_source_count, procurement-field claim counts, and open_conflict_count before prioritizing a supplier conversation"
  - "bar: compare claim_count or evidence_source_count by supplier; this measures observed evidence, not commercial value"
---

# Meaning

This table is the current evidence-backed supplier workspace. It shows which
canonical supplier identities surfaced through document ingestion, which buying
or qualification signals were extracted, and which facts remain in conflict.

# Grain

One row per canonical supplier across all loaded ingestion events.

# Measures

* `evidence_source_count` and `evidence_url_count` measure distinct cited inputs.
* `moq_claim_count`, `lead_time_claim_count`, `price_claim_count`, `grade_claim_count`, and `certification_claim_count` measure observed signal availability.
* `open_conflict_count` is a review queue indicator, not a supplier-quality score.
* `latest_evidence_at` and `latest_evidence_url` identify the newest retained source pointer.

# Useful Questions

* BDR: which supplier records have an evidence trail worth a concrete outreach or follow-up?
* COO: where is sourcing intelligence thin or contradictory before a qualification decision?
* CEO: how much of the discovered supplier universe has observable commercial or compliance support?

# Caveats

This is not a CRM, approved-vendor list, supplier ranking, or statement of
commercial fit. It has no contact, spend, capacity, audit approval, or customer
intent field. A zero claim count means the current extracted evidence did not
produce a supported claim; it does not establish that the supplier lacks it.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_supplier_intelligence.sql)
