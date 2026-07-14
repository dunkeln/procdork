with supplier_names as (
    select
        canonical_supplier_id,
        arg_max(supplier_name, emitted_at) as supplier_name
    from {{ ref('stg_ingestion_suppliers') }}
    group by 1
),
conflicts as (
    select
        event_id,
        claim_id,
        count(distinct conflict_id) as conflict_count,
        max(case when conflict_status = 'open' then 1 else 0 end) as has_open_conflict
    from {{ ref('stg_ingestion_conflict_claims') }}
    group by 1, 2
)

select
    {{ chart_id('claim.event_id', 'evt') }} as event_id,
    {{ chart_id('claim.job_id', 'job') }} as job_id,
    {{ chart_id('claim.session_id', 'ses') }} as session_id,
    {{ chart_id('claim.turn_id', 'turn') }} as turn_id,
    claim.emitted_at,
    {{ chart_time('claim.emitted_at') }} as emitted_at_bucket,
    {{ chart_id('claim.claim_id', 'claim') }} as claim_id,
    {{ chart_id('claim.canonical_supplier_id', 'sup') }} as canonical_supplier_id,
    supplier.supplier_name,
    {{ chart_id('claim.observed_supplier_id', 'obs') }} as observed_supplier_id,
    claim.claim_field,
    claim.claim_value,
    claim.claim_confidence,
    claim.extraction_method,
    claim.claim_retrieved_at,
    {{ chart_time('claim.claim_retrieved_at') }} as claim_retrieved_at_bucket,
    {{ chart_id('claim.source_id', 'src') }} as source_id,
    claim.artifact_type,
    claim.source_title,
    claim.source_url,
    claim.mime_hint,
    claim.source_page,
    claim.source_row,
    claim.source_text_span,
    coalesce(conflict.conflict_count, 0) as conflict_count,
    coalesce(conflict.has_open_conflict, 0) = 1 as has_open_conflict
from {{ ref('stg_ingestion_claims') }} as claim
left join supplier_names as supplier using (canonical_supplier_id)
left join conflicts as conflict
    on claim.event_id = conflict.event_id and claim.claim_id = conflict.claim_id
