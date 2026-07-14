# Analytical Tables

Use chartable columns first: categorical dimensions, numeric measures, and
`*_bucket` time labels. Return tables when exact row inspection matters more
than shape. Public mart ids are stable labels, not source-system identifiers.

* [Capture Summary](capture_summary.md) - Capture volume grouped by source type and adapter.
* [Chat Summary](chat_summary.md) - All-time counts for the currently loaded chat snapshot.
* [Evidence Capture](evidence_capture.md) - Source coverage by session and evidence type.
* [Workflow Sessions](workflow_sessions.md) - Session-level completion, tool effort, evidence volume, and latency.
* [Tool Activity](tool_activity.md) - Tool usage volume and status by session and tool.
* [Source Reach](source_reach.md) - Cited source-domain and evidence-type coverage.
* [Document Intelligence](document_intelligence.md) - Document-source reach by domain and artifact type.
* [Evaluation Cases](evaluation_cases.md) - Latest evaluation outcome for each case and evaluator.
* [App Message Judgements](app_message_judgements.md) - Versioned LLM-as-judge scores for stored application answers.
* [App Message Judge Scores](app_message_judge_scores.md) - Chart-ready answer-quality scores by dimension.
* [App Message Judge Drift](app_message_judge_drift.md) - Sequential judged-quality trend with a variance band.
* [Benchmark Runs](benchmark_runs.md) - Run-level quality, reliability, efficiency, and cost evidence.
* [Benchmark Summary](benchmark_summary.md) - Comparable metrics by treatment and analytical behavior.
* [Benchmark Calibration](benchmark_calibration.md) - Human agreement with the semantic judge.
* [Ingestion Operations](ingestion_operations.md) - Job-level extraction health and evidence yield.
* [Refresh Runs](refresh_runs.md) - Source-sync and transform publication outcomes for each scheduled batch.
* [Supplier Intelligence](supplier_intelligence.md) - Evidence coverage and unresolved claim conflicts by supplier.
* [Supplier Claims](supplier_claims.md) - Source-backed extracted procurement facts at claim grain.
* [Supplier Extraction Coverage](supplier_extraction_coverage.md) - Coverage gap between observed documents and structured suppliers.
* [Claim Coverage](claim_coverage.md) - Evidence coverage and conflict exposure by procurement field.
