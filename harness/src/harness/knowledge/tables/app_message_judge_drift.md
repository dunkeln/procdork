---
type: Table
title: App Message Judge Drift
description: Sequential answer-quality trend with a rolling score-variance band for judge drift review.
resource: procdork://tables/app_message_judge_drift
tags: [evaluations, quality, drift, charts]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "line: use evaluated_at, dimension, rolling_average_score, lower_score, upper_score for a shaded judge-drift band"
  - "table: inspect score_stddev and judged_message_count before trusting the band"
---

# Meaning

This table shows whether judged answer quality is moving across evaluation
events, and whether the judge is stable enough to trust that movement.

# Grain

One row per judged message, score dimension, judge version, and rubric version.

# Measures

* `rolling_average_score` smooths the latest seven judged-message scores.
* `lower_score` and `upper_score` are the rolling average plus or minus one
  rolling standard deviation, clipped to the 1-5 score range.
* `latest_score` is the raw score from the current judged message.
* `score_stddev` is `null` until the second judged message for the same
  dimension, judge version, and rubric version.
* `judged_message_count` prevents a thin sequence from looking more certain than it is.

# Useful Charts

Use a line chart with columns ordered as `evaluated_at`, `dimension`,
`rolling_average_score`, `lower_score`, `upper_score`. The chart renderer treats
that five-column line shape as a line with a shaded uncertainty band.

# Caveats

The band is a judge-stability signal, not a statistical guarantee. It shows
within-day progress when several evaluations were run in one batch. Do not
compare across judge or rubric versions without showing those versions.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/evals/mart_app_message_judge_drift.sql)
