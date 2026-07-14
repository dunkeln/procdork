with supplier_events as (
    select
        canonical_supplier_id,
        arg_max(supplier_name, emitted_at) as supplier_name,
        arg_max(supplier_confidence, emitted_at) as supplier_confidence,
        sum(observed_supplier_count) as observed_supplier_count,
        count(distinct event_id) as ingestion_event_count,
        min(emitted_at) as first_seen_at,
        max(emitted_at) as last_seen_at
    from {{ ref('stg_ingestion_suppliers') }}
    group by 1
),
claim_metrics as (
    select
        canonical_supplier_id,
        count(*) as claim_count,
        count(distinct source_id) as evidence_source_count,
        count(distinct source_url) as evidence_url_count,
        sum(case when claim_field = 'moq' then 1 else 0 end) as moq_claim_count,
        sum(case when claim_field = 'lead-time-text' then 1 else 0 end) as lead_time_claim_count,
        sum(case when claim_field = 'price' then 1 else 0 end) as price_claim_count,
        sum(case when claim_field = 'grade' then 1 else 0 end) as grade_claim_count,
        sum(case when claim_field = 'certification' then 1 else 0 end) as certification_claim_count,
        sum(case when claim_confidence = 'high' then 1 else 0 end) as high_confidence_claim_count,
        sum(case when claim_confidence in ('low', 'unknown') then 1 else 0 end) as low_confidence_claim_count,
        arg_max(source_url, claim_retrieved_at) as latest_evidence_url,
        max(claim_retrieved_at) as latest_evidence_at
    from {{ ref('stg_ingestion_claims') }}
    where canonical_supplier_id is not null
    group by 1
),
conflict_metrics as (
    select
        canonical_supplier_id,
        count(distinct conflict_id) as open_conflict_count
    from {{ ref('stg_ingestion_conflict_claims') }}
    where conflict_status = 'open' and canonical_supplier_id is not null
    group by 1
)

select
    {{ chart_id('supplier.canonical_supplier_id', 'sup') }} as canonical_supplier_id,
    supplier.supplier_name,
    supplier.supplier_confidence,
    supplier.observed_supplier_count,
    supplier.ingestion_event_count,
    coalesce(claim.evidence_source_count, 0) as evidence_source_count,
    coalesce(claim.evidence_url_count, 0) as evidence_url_count,
    coalesce(claim.claim_count, 0) as claim_count,
    coalesce(claim.moq_claim_count, 0) as moq_claim_count,
    coalesce(claim.lead_time_claim_count, 0) as lead_time_claim_count,
    coalesce(claim.price_claim_count, 0) as price_claim_count,
    coalesce(claim.grade_claim_count, 0) as grade_claim_count,
    coalesce(claim.certification_claim_count, 0) as certification_claim_count,
    coalesce(claim.high_confidence_claim_count, 0) as high_confidence_claim_count,
    coalesce(claim.low_confidence_claim_count, 0) as low_confidence_claim_count,
    coalesce(conflict.open_conflict_count, 0) as open_conflict_count,
    claim.latest_evidence_url,
    claim.latest_evidence_at,
    {{ chart_time('claim.latest_evidence_at') }} as latest_evidence_at_bucket,
    supplier.first_seen_at,
    supplier.last_seen_at,
    {{ chart_time('supplier.first_seen_at') }} as first_seen_at_bucket,
    {{ chart_time('supplier.last_seen_at') }} as last_seen_at_bucket
from supplier_events as supplier
left join claim_metrics as claim using (canonical_supplier_id)
left join conflict_metrics as conflict using (canonical_supplier_id)
