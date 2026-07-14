---
type: Table
title: App Message Judgements
description: Versioned LLM-as-judge scores for stored application answers.
resource: procdork://tables/app_message_judgements
tags: [evaluations, quality, messages]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "table: audit one judged answer, its rubric version, judge version, scores, and rationale"
  - "bar: compare average_score by judge_version or rubric_version after multiple batches exist"
  - "table: inspect low scoring rows before changing prompts, data, or transforms"
---

# Meaning

This table is the audit surface for manually triggered answer-quality batches.
Each row is one stored assistant message judged by one evaluator run.

# Grain

One row per judged message, judge batch, evaluator version, and rubric version.

# Measures

* `average_score` is the mean of the rubric dimensions on a 1-5 scale.
* Dimension columns score grounding, task resolution, uncertainty calibration,
  consistency, answer composability, and style clarity.
* `judge_model`, `judge_version`, `rubric_version`, and `judge_prompt_version`
  make score drift visible across evaluator changes.
* `rationale` is report-only evidence, not a release gate.

# Caveats

The judge sees the saved answer and source metadata, not a full external
reconstruction of every cited page. Treat scores as product-quality evidence,
not factual proof.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/evals/mart_app_message_judgements.sql)
