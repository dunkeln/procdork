# Procdork Knowledge

This bundle contains reviewed, durable context for people and agents using the
procdork harness. Live values remain behind MCP tools and MotherDuck.

## Analytical Tables

* [Tables](tables/) - Grain, measures, and interpretation for reviewed analytical tables.

## Use Case Routing

Choose the table by decision type before writing SQL.

* Executive decisions: start with [Source Reach](tables/source_reach.md),
  [Supplier Coverage](tables/supplier_coverage.md), or
  [Benchmark Summary](tables/benchmark_summary.md). Use bars or heatmaps for
  breadth, concentration, and treatment tradeoffs. Do not use these as approval,
  vendor ranking, or release-gate scorecards without the caveats from each table.
* App health: start with [Workflow Sessions](tables/workflow_sessions.md),
  [Tool Activity](tables/tool_activity.md), and
  [App Message Judge Drift](tables/app_message_judge_drift.md). Use histograms
  for duration tails, heatmaps for tool/status concentration, and lines for
  judged quality movement over time.
* Evidence coverage: start with [Source Reach](tables/source_reach.md),
  [Chat Summary](tables/chat_summary.md), and
  [Document Intelligence](tables/document_intelligence.md). Use these to show
  observed source scale and evidence mix before discussing structured extraction.
* Supplier intelligence: start with [Supplier Coverage](tables/supplier_coverage.md),
  then [Supplier Claims](tables/supplier_claims.md) or
  [Supplier Intelligence](tables/supplier_intelligence.md) only when structured
  supplier rows exist. Use heatmaps for `supplier_name` by `claim_field`; explain
  thin coverage and conflicts before any supplier comparison.
* Benchmark tradeoffs: start with [Benchmark Summary](tables/benchmark_summary.md),
  [Benchmark Runs](tables/benchmark_runs.md), and
  [Benchmark Calibration](tables/benchmark_calibration.md). Use scatter or bubble
  plots for speed/quality/cost tradeoffs, grouped box plots for latency spread,
  and calibration views before trusting semantic scores.

## Query Order

Prefer chartable summaries before plain tables. Look for categorical dimensions,
numeric measures, and `*_bucket` time labels before returning row-level output.
Do not run separate count-table probes when one chart-ready aggregate can answer
the question. Use table docs for planning, then make the first query the chart
or final inspection table.
Use raw timestamp columns for filtering and freshness checks, but use the
15-minute bucket columns for chart axes. Public mart ids are short stable hashes;
do not infer business meaning from them.

## Source Events

* [Document Ingestion Events](ingestion-events.md) - The source-backed completion event contract that feeds supplier intelligence.

## Authoring Boundary

Concept documents are edited in Git and reviewed by the relevant domain owner.
Runtime services consume this bundle read-only; they do not generate or mutate it.
