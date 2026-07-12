# Harness transforms

This directory holds repeatable transform work.

- `dbt/` holds shared, repeatable SQL transforms.
- Evaluation jobs live outside dbt, write `raw_evaluation_results`, and flow through `staging/evals` into `marts/evals`.
- Ad hoc DuckDB SQL can stay in notebooks until an engineer needs reproducibility.
- OKF may describe a model's durable meaning, but it is authored and reviewed independently.
