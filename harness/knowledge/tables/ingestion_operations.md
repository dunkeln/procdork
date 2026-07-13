---
type: Table
title: Ingestion Operations
description: Job-level extraction health, parser effort, and evidence yield from document-ingestion completion events.
resource: procdork://tables/ingestion_operations
tags: [ingestion, operations, reliability]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: inspect partial jobs, parser_error_count, and source-to-claim yield before treating missing facts as supplier gaps"
  - "bar: compare source_count, claim_count, and parser_error_count across recent jobs; duration_ms is a per-job duration, not an SLA percentile"
---

# Meaning

This table makes the document-extraction seam observable. Each row states what
the ingestion service received, what it extracted, and whether parsers reported
errors before the results entered analytical use.

# Grain

One row per emitted ingestion completion event and ingestion job.

# Measures

* `source_count`, `supplier_count`, and `claim_count` describe evidence yield.
* `conflict_count` counts unresolved-or-resolved claim disagreements attached to the job.
* `parser_error_count`, `parser_attempt_count`, and `extracted_block_count` describe parser behavior.
* `duration_ms` is the synchronous work duration recorded by the service.

# Useful Questions

* Developers: which source shapes repeatedly produce parser errors or no claims?
* COO: is the current evidence pipeline producing supplier and claim coverage?
* Data scientists: which jobs are safe candidates for extraction-quality analysis?

# Caveats

`partial` does not mean every extracted claim is wrong. A successful job does
not prove a document contained all required procurement facts. This table has no
tenant, spend, or supplier-performance metric.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_ingestion_operations.sql)
