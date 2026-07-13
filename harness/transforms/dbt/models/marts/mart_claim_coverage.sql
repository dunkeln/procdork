with supplier_total as (
    select count(distinct canonical_supplier_id) as supplier_count
    from {{ ref('stg_ingestion_suppliers') }}
),
claim_conflicts as (
    select event_id, claim_id, max(case when conflict_status = 'open' then 1 else 0 end) as has_open_conflict
    from {{ ref('stg_ingestion_conflict_claims') }}
    group by 1, 2
)

select
    claim.claim_field,
    count(*) as claim_count,
    count(distinct claim.canonical_supplier_id) as supplier_count,
    count(distinct claim.source_id) as evidence_source_count,
    count(distinct claim.source_url) as evidence_url_count,
    sum(case when claim.claim_confidence = 'high' then 1 else 0 end) as high_confidence_claim_count,
    sum(case when claim.claim_confidence in ('low', 'unknown') then 1 else 0 end) as low_confidence_claim_count,
    sum(coalesce(conflict.has_open_conflict, 0)) as open_conflict_claim_count,
    count(distinct claim.canonical_supplier_id)::double / nullif(supplier_total.supplier_count, 0) as supplier_coverage_ratio,
    min(claim.claim_retrieved_at) as first_evidence_at,
    max(claim.claim_retrieved_at) as latest_evidence_at
from {{ ref('stg_ingestion_claims') }} as claim
cross join supplier_total
left join claim_conflicts as conflict
    on claim.event_id = conflict.event_id and claim.claim_id = conflict.claim_id
group by 1, supplier_total.supplier_count
