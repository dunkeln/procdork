with documents as (
    select
        count(distinct source_domain) as observed_domain_count,
        sum(distinct_source_count) as distinct_source_count,
        sum(source_observation_count) as source_observation_count
    from {{ ref('mart_document_intelligence') }}
),
suppliers as (
    select
        count(*) as structured_supplier_count,
        sum(claim_count) as supplier_claim_count,
        sum(open_conflict_count) as open_conflict_count
    from {{ ref('mart_supplier_intelligence') }}
)

select
    documents.observed_domain_count,
    documents.distinct_source_count,
    documents.source_observation_count,
    suppliers.structured_supplier_count,
    suppliers.supplier_claim_count,
    suppliers.open_conflict_count,
    suppliers.structured_supplier_count::double
        / nullif(documents.observed_domain_count, 0) as domain_to_supplier_coverage_proxy
from documents
cross join suppliers
