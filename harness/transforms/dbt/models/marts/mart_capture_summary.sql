select
    source_type,
    source_adapter_name,
    count(*) as artifact_count,
    sum(bytes) as total_bytes,
    min(loaded_at) as first_loaded_at,
    max(loaded_at) as last_loaded_at
from {{ ref('stg_raw_manifest') }}
group by 1, 2
