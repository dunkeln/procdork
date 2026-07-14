---
type: Table
title: Tool Activity
description: Tool usage volume and status by session, tool, and tool label.
resource: procdork://tables/tool_activity
tags: [tools, operations, reliability]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "bar: compare event_count by tool_name and tool_status"
  - "heatmap: compare event_count across tool_name and tool_status"
  - "table: inspect first_seen_at and last_seen_at when debugging one session"
---

# Meaning

This table shows which tools the application agent used and whether their
events were running, done, unknown, or errored.

# Grain

One row per `session_slug`, `tool_name`, `tool_label`, and `tool_status`.

# Measures

* `event_count` counts emitted tool events at that status.
* `turn_count` counts distinct turns that emitted that tool/status pair.
* `first_seen_at` and `last_seen_at` bound when the tool activity happened.

# Useful Questions

* Which tools dominate a workflow?
* Are tool errors concentrated in one session or one tool?
* Which sessions required repeated external retrieval before final output?

# Caveats

This table counts emitted events, not external API latency, token cost, or
semantic success. A `done` status means the tool lifecycle reported completion;
it does not prove the returned evidence was sufficient.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_tool_activity.sql)
