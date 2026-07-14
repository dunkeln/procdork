with evidence_links as (
    select
        message.session_slug,
        coalesce(
            nullif(source.document_type, ''),
            nullif(source.source_kind, ''),
            'unclassified'
        ) as evidence_type,
        link.source_url,
        link.created_at as linked_at
    from {{ source('app', 'app_messages') }} as message
    join {{ source('app', 'app_message_sources') }} as link
        on link.message_id = message.id
    join {{ source('app', 'app_sources') }} as source
        on source.url = link.source_url
)

select
    'evidence_' || substr(md5(session_slug || '|' || evidence_type), 1, 16)
        as evidence_capture_id,
    session_slug,
    evidence_type,
    count(distinct source_url) as source_count,
    min(linked_at) as first_linked_at,
    max(linked_at) as last_linked_at
from evidence_links
group by 1, 2, 3
