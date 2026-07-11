---
type: dbt model
title: Capture Summary
description: Capture volume grouped by source type and extraction adapter.
resource: ../../transforms/dbt/models/marts/mart_capture_summary.sql
tags: [harness, captures, transform]
timestamp: 2026-07-10T00:00:00Z
interpretations:
  - "bar: compare artifact_count or total_bytes by source_type and source_adapter_name"
  - "table: inspect exact first_loaded_at and last_loaded_at bounds; they are not a time series"
---

# Meaning

This model describes what the harness has captured, not the business entities
inside those captures.

# Grain

One row per `source_type` and `source_adapter_name` pair.

# Measures

* `artifact_count` counts manifest records.
* `total_bytes` sums stored payload bytes.
* `first_loaded_at` and `last_loaded_at` bound observed load time.

# Caveats

Repeated captures count as separate manifest records. This model does not infer
source freshness, uniqueness, or analytical quality.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_capture_summary.sql)
