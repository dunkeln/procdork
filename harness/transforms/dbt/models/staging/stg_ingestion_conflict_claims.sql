select
    event.event_id,
    json_extract_string(conflict.value, '$.conflict_id') as conflict_id,
    json_extract_string(conflict.value, '$.canonical_supplier_id') as canonical_supplier_id,
    json_extract_string(conflict.value, '$.field') as claim_field,
    json_extract_string(conflict.value, '$.status') as conflict_status,
    json_extract_string(conflict.value, '$.note') as conflict_note,
    json_extract_string(claim_id.value, '$') as claim_id
from {{ ref('stg_ingestion_events') }} as event,
    json_each(event.payload, '$.conflicts') as conflict,
    json_each(conflict.value, '$.claim_ids') as claim_id
