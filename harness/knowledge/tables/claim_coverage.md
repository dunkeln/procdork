---
type: Table
title: Claim Coverage
description: Evidence coverage, extraction confidence, and open-conflict exposure by procurement claim field.
resource: procdork://tables/claim_coverage
tags: [coverage, sourcing, compliance]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "bar: compare supplier_coverage_ratio or open_conflict_claim_count by claim_field to find the weakest shared evidence surface"
  - "table: inspect confidence counts and latest_evidence_at before treating a coverage gap as a supplier gap"
---

# Meaning

This table answers which procurement facts are actually supported across the
currently discovered supplier set. It is the compact coverage view for deciding
where additional document work or operator follow-up is justified.

# Grain

One row per extracted `claim_field` across loaded ingestion events.

# Measures

* `supplier_coverage_ratio` is the share of canonical suppliers with at least one claim for the field.
* `evidence_source_count` and `evidence_url_count` show distinct retained support.
* Confidence counts and `open_conflict_claim_count` show evidence quality and disagreement exposure.
* `first_evidence_at` and `latest_evidence_at` bound the observed evidence window.

# Useful Questions

* CEO: which shared sourcing signals are broadly evidenced versus thin?
* COO: where should the team ask for documents, quotes, or confirmations next?
* QA and data teams: which fields have low-confidence or conflicting extraction that merits review?

# Caveats

Coverage is based only on currently ingested evidence and currently canonicalized
suppliers. It is not supplier approval coverage, spend coverage, savings, or a
measure of market availability.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_claim_coverage.sql)
