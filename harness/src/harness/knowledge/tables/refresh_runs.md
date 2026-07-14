---
type: Table
title: Refresh Runs
description: Source-sync and transform publication outcomes for scheduled analytical batches.
resource: procdork://tables/refresh_runs
tags: [operations, freshness, reliability]
timestamp: 2026-07-13T00:00:00Z
interpretations:
  - "table: inspect status, source_results, and transform_status before treating the latest analytical tables as fully current"
---

# Meaning

This table records whether a scheduled refresh completed normally, preserved
partial work, or failed. It makes mixed freshness explicit without deleting
successful loads or previously published tables.

# Grain

One row per scheduled refresh attempt.

# Status

* `healthy` means every configured source and the dbt build succeeded.
* `degraded` means useful work survived but at least one stage failed.
* `failed` means neither source synchronization nor transformation succeeded.
* `running` without completion indicates an interrupted refresh.

# Caveats

A degraded run can leave independently built tables at different refresh times.
This table reports publication health; it does not make the complete dbt graph
transactional.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_refresh_runs.sql)
