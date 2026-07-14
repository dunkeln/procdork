---
type: Table
title: Evidence Capture
description: Source coverage by session and evidence type.
resource: procdork://tables/evidence_capture
tags: [evidence, sessions, transform]
timestamp: 2026-07-13T00:00:00Z
interpretations:
  - "heatmap: compare source_count across session_slug and evidence_type"
  - "table: inspect exact first_linked_at and last_linked_at evidence bounds"
---

# Meaning

This table shows which kinds of evidence each session captured and how many
distinct source URLs support them.

# Grain

One row per `session_slug` and `evidence_type` pair.

# Measures

* `source_count` counts distinct linked source URLs.
* `first_linked_at` and `last_linked_at` bound when those links were recorded.

# Caveats

A higher source count means broader captured evidence, not stronger evidence.
Missing cells mean no captured source of that type; they do not prove that the
underlying evidence does not exist.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_evidence_capture.sql)
