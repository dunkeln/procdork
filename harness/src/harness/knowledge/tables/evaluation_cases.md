---
type: Table
title: Evaluation Cases
description: Latest evaluation outcome for every case and evaluator.
resource: procdork://tables/evaluation_cases
tags: [evaluations, regression]
timestamp: 2026-07-12T00:00:00Z
interpretations:
  - "table: inspect case outcomes, scores, versions, and comparison state"
---

# Evaluation Cases

`evaluation_cases` contains the latest result for every case and evaluator.
It compares that result with the preceding system version.

## Interpretations

* `regressed` means a previously successful case now fails and should block promotion.
* `improved` means a previous failure now passes and should remain as a regression case.
* `unchanged` means the pass/fail outcome held across the two latest versions.
* `new` means no prior result exists; it is evidence, not yet a regression anchor.
* `evaluation_failures` is the operator repair queue.
* `evaluation_successes` is the known-good regression set.

## Caveats

The first evaluator covers source-backed chat answers only. A pass means the
answer is non-empty, returned citations, used valid inline citation markers,
and did not reference citations outside the returned list. It does not prove
that every factual claim is correct.

# Citations

[1] [Evaluation cases transform](../../transforms/dbt/models/marts/evals/mart_evaluation_cases.sql)
[2] [Evaluation failures transform](../../transforms/dbt/models/marts/evals/mart_evaluation_failures.sql)
[3] [Evaluation successes transform](../../transforms/dbt/models/marts/evals/mart_evaluation_successes.sql)
