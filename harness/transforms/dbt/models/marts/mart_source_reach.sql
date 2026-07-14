with citations as (
    select
        message.session_slug,
        link.message_id,
        link.source_url,
        link.created_at as cited_at,
        coalesce(
            nullif(source.document_type, ''),
            nullif(source.source_kind, ''),
            'unclassified'
        ) as evidence_type,
        regexp_replace(lower(regexp_extract(link.source_url, '^https?://([^/]+)', 1)), '^www\.', '') as source_domain,
        source.retrieved_at
    from {{ source('app', 'app_message_sources') }} as link
    join {{ source('app', 'app_messages') }} as message
        on message.id = link.message_id
    join {{ source('app', 'app_sources') }} as source
        on source.url = link.source_url
)

select
    nullif(source_domain, '') as source_domain,
    evidence_type,
    count(*) as citation_count,
    count(distinct source_url) as source_count,
    count(distinct session_slug) as session_count,
    count(distinct message_id) as message_count,
    min(retrieved_at) as first_retrieved_at,
    max(retrieved_at) as latest_retrieved_at,
    min(cited_at) as first_cited_at,
    max(cited_at) as latest_cited_at
from citations
group by 1, 2
