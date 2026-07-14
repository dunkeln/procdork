select
    source_type,
    source_adapter_name,
    count(*) as artifact_count,
    sum(bytes) as total_bytes,
    min(loaded_at) as first_loaded_at,
    max(loaded_at) as last_loaded_at,
    {{ chart_time('min(loaded_at)') }} as first_loaded_at_bucket,
    {{ chart_time('max(loaded_at)') }} as last_loaded_at_bucket
from {{ ref('stg_raw_manifest') }}
group by 1, 2
