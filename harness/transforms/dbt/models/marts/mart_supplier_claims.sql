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
    claim.event_id,
    claim.job_id,
    claim.session_id,
    claim.turn_id,
    claim.emitted_at,
    claim.claim_id,
    claim.canonical_supplier_id,
    supplier.supplier_name,
    claim.observed_supplier_id,
    claim.claim_field,
    claim.claim_value,
    claim.claim_confidence,
    claim.extraction_method,
    claim.claim_retrieved_at,
    claim.source_id,
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
