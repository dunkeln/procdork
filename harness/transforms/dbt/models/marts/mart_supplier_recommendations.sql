with base as (
    select
        canonical_supplier_id,
        supplier_name,
        supplier_confidence,
        evidence_source_count,
        evidence_url_count,
        claim_count,
        price_claim_count,
        lead_time_claim_count,
        moq_claim_count,
        grade_claim_count,
        certification_claim_count,
        high_confidence_claim_count,
        low_confidence_claim_count,
        open_conflict_count,
        latest_evidence_url,
        latest_evidence_at,
        latest_evidence_at_bucket,
        first_seen_at_bucket,
        last_seen_at_bucket
    from {{ ref('mart_supplier_intelligence') }}
),
dominance as (
    select
        candidate.canonical_supplier_id,
        count(*) as dominated_by_supplier_count
    from base as candidate
    join base as challenger
        on candidate.canonical_supplier_id <> challenger.canonical_supplier_id
        and challenger.evidence_source_count >= candidate.evidence_source_count
        and challenger.price_claim_count >= candidate.price_claim_count
        and challenger.lead_time_claim_count >= candidate.lead_time_claim_count
        and challenger.moq_claim_count >= candidate.moq_claim_count
        and challenger.grade_claim_count >= candidate.grade_claim_count
        and challenger.certification_claim_count >= candidate.certification_claim_count
        and challenger.high_confidence_claim_count >= candidate.high_confidence_claim_count
        and challenger.low_confidence_claim_count <= candidate.low_confidence_claim_count
        and challenger.open_conflict_count <= candidate.open_conflict_count
        and (
            challenger.evidence_source_count > candidate.evidence_source_count
            or challenger.price_claim_count > candidate.price_claim_count
            or challenger.lead_time_claim_count > candidate.lead_time_claim_count
            or challenger.moq_claim_count > candidate.moq_claim_count
            or challenger.grade_claim_count > candidate.grade_claim_count
            or challenger.certification_claim_count > candidate.certification_claim_count
            or challenger.high_confidence_claim_count > candidate.high_confidence_claim_count
            or challenger.low_confidence_claim_count < candidate.low_confidence_claim_count
            or challenger.open_conflict_count < candidate.open_conflict_count
        )
    group by 1
)

select
    case
        when coalesce(dominance.dominated_by_supplier_count, 0) = 0 then 'pareto-frontier'
        else 'dominated'
    end as review_group,
    coalesce(dominance.dominated_by_supplier_count, 0) as dominated_by_supplier_count,
    base.*
from base
left join dominance using (canonical_supplier_id)
order by
    review_group desc,
    evidence_source_count desc,
    claim_count desc,
    open_conflict_count asc,
    latest_evidence_at desc nulls last
