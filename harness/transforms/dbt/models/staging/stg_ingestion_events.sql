select
    event_id,
    event_type,
    schema_version,
    emitted_at,
    job_id,
    session_id,
    turn_id,
    status,
    duration_ms,
    payload
from {{ source('harness', 'raw_ingestion_events') }}
