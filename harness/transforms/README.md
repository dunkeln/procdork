# Harness transforms

This directory is the promotion boundary for transform work.

- `dbt/` holds promoted, repeatable SQL transforms.
- Ad hoc DuckDB SQL stays transient until it proves useful enough to promote.
- OKF files describe promoted assets later; they do not execute transforms.
