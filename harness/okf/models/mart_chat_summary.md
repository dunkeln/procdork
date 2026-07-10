---
type: dbt model
title: Chat Summary
description: All-time counts for the chat snapshot currently loaded from Neon.
resource: ../../transforms/dbt/models/marts/mart_chat_summary.sql
tags: [chat, neon, transform]
timestamp: 2026-07-10T00:00:00Z
---

# Meaning

This model summarizes the chat records currently loaded into the analytical
database by `sync-neon-chat`.

# Grain

Exactly one row for the full loaded snapshot.

# Measures

* `session_count`, `message_count`, `event_count`, and `cited_source_count` are distinct counts.
* `first_session_at` is the earliest session creation time.
* `last_session_at` is the latest session update time.

# Caveats

The model has no time or tenant filter. Its values reflect the latest loaded
snapshot, not necessarily the current source database.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_chat_summary.sql)
