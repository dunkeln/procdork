{{ config(materialized='view') }}

select
    {{ chart_id('run_id', 'run') }} as run_id,
    started_at,
    {{ chart_time('started_at') }} as started_at_bucket,
    completed_at,
    {{ chart_time('completed_at') }} as completed_at_bucket,
    status,
    revision,
    source_results,
    transform_status
from {{ source('harness', 'raw_refresh_runs') }}
