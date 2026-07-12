# Evaluation Cases

`mart_evaluation_cases` contains the latest result for every case and evaluator.
It compares that result with the preceding system version.

## Interpretations

* `regressed` means a previously successful case now fails and should block promotion.
* `improved` means a previous failure now passes and should remain as a regression case.
* `unchanged` means the pass/fail outcome held across the two latest versions.
* `new` means no prior result exists; it is evidence, not yet a regression anchor.
* `mart_evaluation_failures` is the operator repair queue.
* `mart_evaluation_successes` is the known-good regression set.

## Caveats

The first evaluator covers source-backed chat answers only. A pass means the
answer is non-empty, returned citations, used valid inline citation markers,
and did not reference citations outside the returned list. It does not prove
that every factual claim is correct.
