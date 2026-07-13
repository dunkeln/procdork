select
    event.event_id,
    event.job_id,
    event.session_id,
    event.turn_id,
    event.emitted_at,
    source.key::integer as source_position,
    json_extract_string(source.value, '$.source_id') as source_id,
    json_extract_string(source.value, '$.artifact_type') as artifact_type,
    json_extract_string(source.value, '$.title') as source_title,
    json_extract_string(source.value, '$.url') as source_url,
    json_extract_string(source.value, '$.mime_hint') as mime_hint,
    try_cast(json_extract_string(source.value, '$.retrieved_at') as timestamptz) as source_retrieved_at,
    json_extract_string(source.value, '$.reason') as source_reason
from {{ ref('stg_ingestion_events') }} as event,
    json_each(event.payload, '$.sources') as source
