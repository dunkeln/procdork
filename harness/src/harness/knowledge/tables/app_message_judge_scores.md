---
type: Table
title: App Message Judge Scores
description: Long-form score table for charting answer quality dimensions over time and versions.
resource: procdork://tables/app_message_judge_scores
tags: [evaluations, quality, charts]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "line: chart average score by evaluated_day and dimension for end-of-day quality movement"
  - "bar: compare average score by dimension for one batch or version"
  - "heatmap: compare judge_version or rubric_version by dimension when checking evaluator drift"
  - "line: use app_message_judge_drift when a shaded standard-deviation band is needed"
---

# Meaning

This table reshapes judged answer scores into one row per quality dimension.
It is the chart-friendly companion to `app_message_judgements`.

# Grain

One row per judged message and score dimension.

# Measures

* `dimension` names the judged quality axis.
* `score` is an anchored 1-5 score where 3 is adequate and 5 is strong.
* Version columns preserve the exact judge, rubric, and prompt that produced the score.

# Useful Charts

* End-of-day trend: `evaluated_day`, `dimension`, `avg(score)` as a segmented line chart.
* Quality mix: `dimension`, `avg(score)` as a bar chart.
* Evaluator drift: `judge_version`, `dimension`, `avg(score)` as a heatmap.
* Judge stability: use `app_message_judge_drift` for `rolling_average_score`
  with `lower_score` and `upper_score` as a shaded band.

# Caveats

Do not average across judge or rubric versions without showing those versions.
Version changes can move scores even when app behavior did not change.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/evals/mart_app_message_judge_scores.sql)
