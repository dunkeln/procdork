# The data harness

## What this is

procdork is a supplier procurement workflow that keeps live evidence, document ingestion, and human review in separate boundaries.

The current vertical slice focuses on turning messy evidence pointers into reviewable supplier facts. It does not treat fetched pages, PDFs, spreadsheets, or email-like artifacts as trusted truth until they pass through extraction and provenance shaping.

## Boundaries

### Web app

SvelteKit surface for procurement sessions, chat turns, supplier review, and server-side route handlers.

### Ingestion service

FastAPI boundary that accepts evidence pointers, parses documents, and returns supplier facts through the OpenAPI contract.

### External evidence

Live web pages, PDFs, spreadsheets, email-like artifacts, and parser vendors stay outside the trusted application boundary.

## Core flow

1. User opens or resumes a procurement session in the web app.
2. The server-side agent searches live web evidence and records sources against the session.
3. Document-like evidence is submitted to the ingestion service as pointers, not trusted extracted truth.
4. The ingestion service classifies, fetches, parses, normalizes, and extracts supplier facts.
5. The web app receives observed suppliers, canonical supplier suggestions, source claims, and conflicts for review.

## Contract shape

The ingestion service is intentionally narrow:

- `POST /ingestion/jobs` accepts evidence pointers.
- `GET /ingestion/jobs/{job_id}` returns job status plus extracted facts.

The ingestion result includes:

- `observed_suppliers`
- `canonical_suppliers`
- `source_claims`
- `conflicts`

## Current decisions

- The web app remains the contract source of truth.
- Parser vendor response shapes stay behind ingestion adapters.
- Source claims preserve provenance and confidence instead of overwriting conflicts.
- Document ingestion accepts pointers first; private upload transfer is deferred.

## Deferred

- Durable ingestion job storage.
- Private upload transfer.
- Multi-tenant auth and ownership.
- Analytics and evaluation harness.
- Entity-resolution tuning beyond deterministic suggestions.
