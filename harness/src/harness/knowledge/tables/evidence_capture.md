---
type: Table
title: Evidence Capture
description: Source coverage by session and evidence type.
resource: procdork://tables/evidence_capture
tags: [evidence, sessions, transform]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "heatmap: compare source_count across session_number and evidence_type; use session_title to identify the session"
  - "table: inspect exact first_linked_at and last_linked_at evidence bounds"
---

# Meaning

This table shows which kinds of evidence each session captured and how many
distinct source URLs support them.

# Grain

One row per `session_number`, `session_title`, and `evidence_type` combination.

# Columns

* `session_number` is the chronological display index assigned by the dbt model.
* `session_title` is the readable application session title.
* `evidence_type` is the document type, source kind, or `unclassified` fallback.
* `source_count` counts distinct linked source URLs.
* `first_linked_at` and `last_linked_at` bound when those links were recorded.

# Measures

`source_count` is the measure. Session fields and `evidence_type` are dimensions;
the linked timestamps are observation bounds, not a time series.

# Caveats

A higher source count means broader captured evidence, not stronger evidence.
Missing cells mean no captured source of that type; they do not prove that the
underlying evidence does not exist.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_evidence_capture.sql)
