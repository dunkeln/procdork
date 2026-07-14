{{ config(materialized='view') }}

select
    run_id,
    started_at,
    completed_at,
    status,
    revision,
    source_results,
    transform_status
from {{ source('harness', 'raw_refresh_runs') }}
