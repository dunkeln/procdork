# Procdork Knowledge

This bundle contains reviewed, durable context for people and agents using the
procdork harness. Live values remain behind MCP tools and MotherDuck.

## Analytical Tables

* [Tables](tables/) - Grain, measures, and interpretation for reviewed analytical tables.

## Query Order

Prefer chartable summaries before plain tables. Look for categorical dimensions,
numeric measures, and `*_bucket` time labels before returning row-level output.
Use raw timestamp columns for filtering and freshness checks, but use the
15-minute bucket columns for chart axes. Public mart ids are short stable hashes;
do not infer business meaning from them.

## Source Events

* [Document Ingestion Events](ingestion-events.md) - The source-backed completion event contract that feeds supplier intelligence.

## Authoring Boundary

Concept documents are edited in Git and reviewed by the relevant domain owner.
Runtime services consume this bundle read-only; they do not generate or mutate it.
