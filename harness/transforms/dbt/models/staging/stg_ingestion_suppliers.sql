select
    event.event_id,
    event.job_id,
    event.session_id,
    event.turn_id,
    event.emitted_at,
    json_extract_string(supplier.value, '$.canonical_supplier_id') as canonical_supplier_id,
    json_extract_string(supplier.value, '$.name') as supplier_name,
    json_extract_string(supplier.value, '$.confidence') as supplier_confidence,
    json_array_length(json_extract(supplier.value, '$.observed_supplier_ids')) as observed_supplier_count,
    try_cast(json_extract_string(supplier.value, '$.updated_at') as timestamptz) as supplier_updated_at
from {{ ref('stg_ingestion_events') }} as event,
    json_each(event.payload, '$.canonical_suppliers') as supplier
