---
type: Table
title: App Message Judge Drift
description: Daily answer-quality trend with a score-variance band for judge drift review.
resource: procdork://tables/app_message_judge_drift
tags: [evaluations, quality, drift, charts]
timestamp: 2026-07-14T00:00:00Z
interpretations:
  - "line: use evaluated_day, dimension, rolling_average_score, lower_score, upper_score for a shaded judge-drift band"
  - "table: inspect score_stddev and judged_message_count before trusting the band"
---

# Meaning

This table shows whether judged answer quality is moving, and whether the judge
is stable enough to trust that movement.

# Grain

One row per day, score dimension, judge version, and rubric version.

# Measures

* `rolling_average_score` smooths the latest seven daily score averages.
* `lower_score` and `upper_score` are the daily average plus or minus one
  standard deviation, clipped to the 1-5 score range.
* `score_stddev` is `null` until there are at least two judged messages in the
  same day, dimension, judge version, and rubric version.
* `judged_message_count` prevents a thin batch from looking more certain than it is.

# Useful Charts

Use a line chart with columns ordered as `evaluated_day`, `dimension`,
`rolling_average_score`, `lower_score`, `upper_score`. The chart renderer treats
that five-column line shape as a line with a shaded uncertainty band.

# Caveats

The band is a judge-stability signal, not a statistical guarantee. Do not compare
across judge or rubric versions without showing those versions.

# Citations

[1] [dbt model](../../transforms/dbt/models/marts/evals/mart_app_message_judge_drift.sql)
