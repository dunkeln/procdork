with observed_sources as (
    select
        count(distinct source_domain) as observed_domain_count,
        sum(source_count) as observed_source_count,
        sum(citation_count) as source_observation_count
    from {{ ref('mart_source_reach') }}
),
structured_suppliers as (
    select
        count(*) as structured_supplier_count,
        coalesce(sum(claim_count), 0) as supplier_claim_count,
        coalesce(sum(open_conflict_count), 0) as open_conflict_count
    from {{ ref('mart_supplier_intelligence') }}
),
coverage as (
    select
        observed_sources.observed_domain_count,
        observed_sources.observed_source_count,
        observed_sources.source_observation_count,
        structured_suppliers.structured_supplier_count,
        structured_suppliers.supplier_claim_count,
        structured_suppliers.open_conflict_count,
        structured_suppliers.structured_supplier_count::double
            / nullif(observed_sources.observed_domain_count, 0) as domain_to_supplier_coverage_proxy
    from observed_sources
    cross join structured_suppliers
)

select 'observed evidence' as coverage_stage, 'source domains' as coverage_metric, observed_domain_count as coverage_value
from coverage
union all
select 'observed evidence', 'distinct cited sources', observed_source_count
from coverage
union all
select 'observed evidence', 'source observations', source_observation_count
from coverage
union all
select 'structured supplier facts', 'structured suppliers', structured_supplier_count
from coverage
union all
select 'structured supplier facts', 'supplier claims', supplier_claim_count
from coverage
union all
select 'structured supplier facts', 'open conflicts', open_conflict_count
from coverage
union all
select
    'coverage proxy',
    'structured suppliers per 100 source domains',
    round(domain_to_supplier_coverage_proxy * 100, 2)
from coverage
