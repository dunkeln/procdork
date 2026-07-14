---
type: Table
title: Workflow Sessions
description: Session-level product activity, completion state, evidence volume, and response latency.
resource: procdork://tables/workflow_sessions
tags: [sessions, product, reliability]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "bar: compare workflow_state counts to see completion and lifecycle gaps"
  - "bar: compare source_count or citation_count by session when evidence breadth matters"
  - "table: inspect latency, tool errors, and final/done counts before diagnosing one run"
---

# Meaning

This table is the compact session health view. It shows whether a workflow
produced assistant output, reached terminal lifecycle events, used tools, and
attached evidence.

# Grain

One row per application session.

# Measures

* `workflow_state` separates completed runs from missing-assistant, incomplete-lifecycle, and tool-error runs.
* `turn_count`, `tool_event_count`, and `evidence_event_count` describe operating effort.
* `source_count` and `citation_count` describe captured evidence breadth.
* `avg_assistant_latency_ms` measures completed assistant response time when available.

# Useful Questions

* Which sessions completed cleanly, and which need operator review?
* Which sessions required the most tool work or evidence retrieval?
* Where did the product capture enough evidence to support later analysis?

# Caveats

This table measures workflow telemetry, not answer quality. A completed session
can still be wrong, and an incomplete lifecycle can still contain useful partial
evidence. Use evaluation tables for judged output quality.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_workflow_sessions.sql)
