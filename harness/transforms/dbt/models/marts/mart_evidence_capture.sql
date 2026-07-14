with sessions as (
    select
        slug,
        row_number() over (order by created_at, slug) as session_number,
        coalesce(nullif(title, ''), 'Untitled session') as session_title
    from {{ source('app', 'app_sessions') }}
),
evidence_links as (
    select
        session.session_number,
        session.session_title,
        coalesce(
            nullif(source.document_type, ''),
            nullif(source.source_kind, ''),
            'unclassified'
        ) as evidence_type,
        link.source_url,
        link.created_at as linked_at
    from {{ source('app', 'app_messages') }} as message
    join sessions as session on session.slug = message.session_slug
    join {{ source('app', 'app_message_sources') }} as link
        on link.message_id = message.id
    join {{ source('app', 'app_sources') }} as source
        on source.url = link.source_url
)

select
    session_number,
    session_title,
    evidence_type,
    count(distinct source_url) as source_count,
    min(linked_at) as first_linked_at,
    max(linked_at) as last_linked_at,
    {{ chart_time('min(linked_at)') }} as first_linked_at_bucket,
    {{ chart_time('max(linked_at)') }} as last_linked_at_bucket
from evidence_links
group by 1, 2, 3
