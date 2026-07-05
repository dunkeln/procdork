# Microservices Spec

## Source Of Truth

The web app owns the service contract at `../web/openapi.yaml`.

Microservices must implement that contract before adding extra endpoints. Any contract change should start in `web/openapi.yaml`, then this file can be updated to explain the implementation choice.

## Service Boundaries

This folder can host multiple independent microservices or deployables, including separate AWS Lambda handlers. Do not build shared global runtime assumptions into this slice.

Each microservice should own one job shape, one contract boundary, and one deployment path. Shared utilities are fine only when they do not couple service lifecycles.

The current slice is the MIME/document extraction waystation. It turns messy inbound evidence pointers into structured supplier facts. It should not know about future email delivery, browser automation, supplier-ranking, UI sessions, or ERP workflows except through explicit contracts.

## MIME Document Extraction Service

Build the document extraction service behind:

- `POST /ingestion/jobs`
- `GET /ingestion/jobs/{job_id}`

The web app submits evidence pointers. This service fetches and parses documents or email-like artifacts, normalizes vendor parser output, and returns supplier facts in the contract shapes.

This is not an endpoint stub. The service must contain the real extraction boundary:

1. Source classification from `DocumentIngestionRequest`.
2. Artifact fetch for URL-backed documents.
3. Vendor extraction:
   - Unstructured for broad file variation and document element partitioning.
   - LlamaParse/LlamaIndex for layout-heavy PDFs, tables, spreadsheets, and visual documents.
4. Vendor output normalization into a small internal analytical artifact: text blocks, table blocks, source provenance, parser name, and parser errors.
5. Custom Python extraction from normalized artifacts into observed suppliers, canonical supplier suggestions, source claims, and conflicts.
6. OpenAPI response shaping.

Vendor-specific response shapes must not leak into the OpenAPI contract. Keep them behind internal parser adapters.

## Inputs

Accept `DocumentIngestionRequest` objects from the OpenAPI contract.

Trigger ingestion for artifacts that have one or more of:

- `mime_hint`, especially `application/pdf`, Office document, spreadsheet, or CSV types.
- document-like URL extensions such as `.pdf`, `.docx`, `.xlsx`, `.csv`.
- procurement artifact types such as `coa`, `sds`, `spec-sheet`, `certificate`, `price-list`, `quote`, or `email-thread`.

The service should treat the web app input as a pointer, not as trusted extracted truth.

## Parser Routing

Use parser routing instead of a single default parser:

- Prefer LlamaParse for PDFs, scanned/visual documents, spreadsheets, and any artifact likely to contain tables or layout-sensitive claims.
- Use Unstructured for broad MIME coverage and general document partitioning.
- If one vendor fails, try the other when the source shape supports it.
- If both vendors fail but pointer metadata contains useful text, return a partial job with pointer-derived facts and parser errors.
- If neither vendor nor pointer text yields facts, return a partial job with empty result arrays and the parser error.

The service resolves API keys from the root dotenv with `load_dotenv(find_dotenv())`. Support the local key names already present in this repo as aliases for vendor standard names.

## Outputs

Return an `IngestionJob` with:

- `observed_suppliers`: exact supplier mentions from source material.
- `canonical_suppliers`: normalized supplier entities suggested by the service.
- `source_claims`: evidence-backed facts with source provenance.
- `conflicts`: disagreements that should not be silently overwritten.

Canonical supplier records should not carry MIME type. MIME belongs on source provenance and ingestion requests.

Internally, keep the normalized extraction artifact available to the job orchestration layer while shaping only the OpenAPI fields in HTTP responses. The current prototype can keep that artifact in memory; do not add a database until the contract needs durable reads.

## Claim Rules

Every `source_claim` must include:

- `field`: kebab-case claim name, for example `moq`, `lead-time-days`, `lead-time-text`, `grade`, `certification`, `price`.
- `value`: extracted value. Keep original text when normalization is not supported.
- `source`: URL/file/page/row/text-span provenance when available.
- `retrieved_at`: when the source was retrieved or ingested.
- `extraction_method`: usually `document-ingestion` or `email-ingestion`.
- `confidence`: `high`, `medium`, `low`, `unknown`, or `other`.

Do not collapse conflicting claims. Emit a `SupplierConflict`.

## First Complete Prototype

The first complete prototype should:

1. Accept PDF/document/email-thread URL pointers from the web contract.
2. Fetch URL-backed artifacts with bounded timeouts.
3. Route extraction through LlamaParse and/or Unstructured based on source shape.
4. Normalize vendor output into text/table blocks with provenance.
5. Extract supplier names and procurement fields from normalized blocks.
6. Return observed suppliers, source claims, canonical supplier suggestions, and unresolved conflicts.
7. Preserve parser errors as job-level partial status instead of hiding them.

Do not add auth, persistence strategy, retries, webhooks, or analytics until the web app needs them.

## Deferred

- Durable database schema.
- DuckDB analytics/eval layer.
- Gold-label evaluation harness.
- Private upload transfer.
- Multi-tenant auth and ownership.
- Entity-resolution tuning beyond simple deterministic suggestions.
- OCR/model prompt tuning beyond basic parser configuration.
