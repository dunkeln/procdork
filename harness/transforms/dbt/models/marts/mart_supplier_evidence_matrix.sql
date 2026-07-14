with suppliers as (
    select *
    from {{ ref('mart_supplier_intelligence') }}
),
dimensions as (
    select canonical_supplier_id, supplier_name, 'evidence sources' as evidence_dimension, evidence_source_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'price' as evidence_dimension, price_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'lead time' as evidence_dimension, lead_time_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'moq' as evidence_dimension, moq_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'grade' as evidence_dimension, grade_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'certification' as evidence_dimension, certification_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'low confidence' as evidence_dimension, low_confidence_claim_count as evidence_value from suppliers
    union all
    select canonical_supplier_id, supplier_name, 'open conflicts' as evidence_dimension, open_conflict_count as evidence_value from suppliers
)

select
    supplier_name,
    evidence_dimension,
    evidence_value,
    canonical_supplier_id
from dimensions
where evidence_value > 0
