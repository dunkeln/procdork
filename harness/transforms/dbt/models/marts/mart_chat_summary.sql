select
    count(distinct s.slug) as session_count,
    count(distinct m.id) as message_count,
    count(distinct e.id) as event_count,
    count(distinct src.url) as cited_source_count,
    min(s.created_at) as first_session_at,
    max(s.updated_at) as last_session_at,
    {{ chart_time('min(s.created_at)') }} as first_session_at_bucket,
    {{ chart_time('max(s.updated_at)') }} as last_session_at_bucket
from {{ source('app', 'app_sessions') }} s
left join {{ source('app', 'app_messages') }} m on m.session_slug = s.slug
left join {{ source('app', 'app_message_events') }} e on e.session_slug = s.slug
left join {{ source('app', 'app_message_sources') }} ms on ms.message_id = m.id
left join {{ source('app', 'app_sources') }} src on src.url = ms.source_url
