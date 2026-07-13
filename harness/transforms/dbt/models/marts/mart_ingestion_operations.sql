with source_counts as (
    select event_id, count(*) as source_count
    from {{ ref('stg_ingestion_sources') }}
    group by 1
),
supplier_counts as (
    select event_id, count(*) as supplier_count
    from {{ ref('stg_ingestion_suppliers') }}
    group by 1
),
claim_counts as (
    select event_id, count(*) as claim_count
    from {{ ref('stg_ingestion_claims') }}
    group by 1
),
conflict_counts as (
    select event_id, count(distinct conflict_id) as conflict_count
    from {{ ref('stg_ingestion_conflict_claims') }}
    group by 1
),
artifact_counts as (
    select
        event_id,
        sum(block_count) as extracted_block_count,
        sum(parser_error_count) as parser_error_count,
        sum(parser_attempt_count) as parser_attempt_count
    from {{ ref('stg_ingestion_artifacts') }}
    group by 1
)

select
    event.event_id,
    event.job_id,
    event.session_id,
    event.turn_id,
    event.status,
    event.emitted_at,
    event.duration_ms,
    coalesce(source.source_count, 0) as source_count,
    coalesce(supplier.supplier_count, 0) as supplier_count,
    coalesce(claim.claim_count, 0) as claim_count,
    coalesce(conflict.conflict_count, 0) as conflict_count,
    coalesce(artifact.extracted_block_count, 0) as extracted_block_count,
    coalesce(artifact.parser_error_count, 0) as parser_error_count,
    coalesce(artifact.parser_attempt_count, 0) as parser_attempt_count
from {{ ref('stg_ingestion_events') }} as event
left join source_counts as source using (event_id)
left join supplier_counts as supplier using (event_id)
left join claim_counts as claim using (event_id)
left join conflict_counts as conflict using (event_id)
left join artifact_counts as artifact using (event_id)
