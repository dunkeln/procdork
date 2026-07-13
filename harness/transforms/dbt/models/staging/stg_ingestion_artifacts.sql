select
    event.event_id,
    event.job_id,
    event.emitted_at,
    json_extract_string(artifact.value, '$.source_id') as source_id,
    try_cast(json_extract_string(artifact.value, '$.block_count') as integer) as block_count,
    json_array_length(json_extract(artifact.value, '$.parsers_attempted')) as parser_attempt_count,
    json_array_length(json_extract(artifact.value, '$.errors')) as parser_error_count,
    json_extract(artifact.value, '$.parsers_attempted') as parsers_attempted,
    json_extract(artifact.value, '$.errors') as parser_errors
from {{ ref('stg_ingestion_events') }} as event,
    json_each(event.payload, '$.artifacts') as artifact
