---
type: source event contract
title: Document Ingestion Events
description: Append-only evidence events emitted after document-ingestion jobs complete.
tags: [ingestion, provenance, supplier]
timestamp: 2026-07-12T00:00:00Z
---

# Meaning

`ingestion.job.completed` is the bridge from the document-extraction service to
the Procdork harness. It preserves the exact input pointers, extracted supplier
observations, canonical suggestions, source claims, conflicts, parser evidence,
and the session or turn that caused the work.

# Delivery

Set `INGESTION_EVENT_JSONL` on the ingestion service to append one event after
each job. An external runner loads the stream with:

```sh
uv run harness sync-ingestion-events --event-jsonl /shared/ingestion-events.jsonl
```

The loader is idempotent by `event_id`; rerunning the same file does not create
duplicate rows.

# Evidence Boundary

* `sources` are pointers submitted to extraction, not asserted facts.
* `source_claims` retain field, value, provenance, extraction method, confidence, and retrieval time.
* `conflicts` preserve disagreement instead of choosing a winner.
* `artifacts` record parser attempts, extracted block count, and parser errors.

# Analytical Use

* [Ingestion Operations](tables/ingestion_operations.md) explains job health and yield.
* [Supplier Intelligence](tables/supplier_intelligence.md) explains supplier-level evidence coverage.
* [Supplier Claims](tables/supplier_claims.md) is the auditable fact surface.
* [Claim Coverage](tables/claim_coverage.md) identifies thin or conflicting shared evidence.

# Caveats

The current service keeps job lookup state in memory. The emitted event is the
durable analytical handoff, not a replacement for a future durable job API.
The local JSONL sink assumes one service writer; use a shared object or queue
transport when concurrent service writers are required.
