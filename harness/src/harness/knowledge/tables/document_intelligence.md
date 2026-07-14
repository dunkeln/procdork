---
type: Table
title: Document Intelligence
description: Source-domain and artifact-type reach from document-ingestion events.
resource: procdork://tables/document_intelligence
tags: [documents, citations, evidence]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "bar: compare source_observation_count or distinct_source_count by artifact_type"
  - "heatmap: compare source_observation_count across source_domain and artifact_type"
  - "table: inspect parser_error_count before treating missing source families as product behavior"
---

# Meaning

This table shows which document-like sources reached the analytical layer. It is
useful for evidence coverage, citation concentration, and parser health.

# Grain

One row per source domain and artifact type.

# Measures

* `source_observation_count` counts source appearances across ingestion events.
* `distinct_source_count` counts unique source URLs.
* `ingestion_event_count`, `session_count`, and `turn_count` show spread across workflows.
* `extracted_block_count`, `parser_attempt_count`, and `parser_error_count` describe parser output.

# Useful Questions

* Which document types dominate the evidence base?
* Which source domains are over-represented?
* Are parser errors concentrated in one artifact type?

# Caveats

Recovered citation events prove that sources were cited or observed. They do not
prove supplier facts were extracted. Supplier claims and conflicts live in the
supplier claim tables when the ingestion service emits them.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_document_intelligence.sql)
