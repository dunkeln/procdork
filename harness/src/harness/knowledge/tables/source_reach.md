---
type: Table
title: Source Reach
description: Cited source-domain and evidence-type coverage across sessions and messages.
resource: procdork://tables/source_reach
tags: [evidence, sources, coverage]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "bar: compare source_count or citation_count by source_domain"
  - "heatmap: compare citation_count across source_domain and evidence_type"
  - "table: inspect retrieved and cited time bounds before making freshness claims"
---

# Meaning

This table shows where cited evidence came from, how often it appeared, and
which evidence type it represented.

# Grain

One row per `source_domain` and `evidence_type`.

# Measures

* `citation_count` counts source-link uses in assistant messages.
* `source_count` counts distinct cited URLs.
* `session_count` and `message_count` show how widely a source domain appeared.
* Retrieved and cited timestamps separate source freshness from citation timing.

# Useful Questions

* Which source domains keep supporting answers across sessions?
* Is the evidence mix mostly search snippets, fetched pages, certificates, SDS, price lists, or specs?
* Which cited sources are broad enough to audit before publishing a repeatable analysis?

# Caveats

Reach is not trust. A repeated domain is visible, not automatically authoritative.
Freshness depends on source retrieval time and the source page itself; this table
does not verify whether the upstream page changed after retrieval.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/mart_source_reach.sql)
