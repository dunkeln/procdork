with sources as (
    select
        source.event_id,
        source.job_id,
        source.session_id,
        source.turn_id,
        source.artifact_type,
        source.source_url,
        nullif(
            regexp_replace(
                lower(regexp_extract(source.source_url, '^https?://([^/]+)', 1)),
                '^www\\.',
                ''
            ),
            ''
        ) as source_domain,
        source.source_retrieved_at,
        coalesce(artifact.block_count, 0) as extracted_block_count,
        coalesce(artifact.parser_attempt_count, 0) as parser_attempt_count,
        coalesce(artifact.parser_error_count, 0) as parser_error_count
    from {{ ref('stg_ingestion_sources') }} as source
    left join {{ ref('stg_ingestion_artifacts') }} as artifact
        on source.event_id = artifact.event_id
        and source.source_id = artifact.source_id
)

select
    coalesce(source_domain, 'unknown') as source_domain,
    artifact_type,
    count(*) as source_observation_count,
    count(distinct source_url) as distinct_source_count,
    count(distinct event_id) as ingestion_event_count,
    count(distinct session_id) as session_count,
    count(distinct turn_id) as turn_count,
    sum(extracted_block_count) as extracted_block_count,
    sum(parser_attempt_count) as parser_attempt_count,
    sum(parser_error_count) as parser_error_count,
    min(source_retrieved_at) as first_retrieved_at,
    max(source_retrieved_at) as latest_retrieved_at,
    {{ chart_time('min(source_retrieved_at)') }} as first_retrieved_at_bucket,
    {{ chart_time('max(source_retrieved_at)') }} as latest_retrieved_at_bucket
from sources
group by 1, 2
