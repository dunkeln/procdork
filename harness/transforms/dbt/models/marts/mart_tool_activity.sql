with sessions as (
    select
        slug,
        row_number() over (order by created_at, slug) as session_number,
        coalesce(nullif(title, ''), 'Untitled session') as session_title
    from {{ source('app', 'app_sessions') }}
)

select
    session.session_number,
    session.session_title,
    coalesce(json_extract_string(activity.event, '$.name'), 'unknown') as tool_name,
    coalesce(json_extract_string(activity.event, '$.label'), 'unknown') as tool_label,
    coalesce(json_extract_string(activity.event, '$.status'), 'unknown') as tool_status,
    count(*) as event_count,
    count(distinct turn_id) as turn_count,
    min(created_at) as first_seen_at,
    max(created_at) as last_seen_at
from {{ source('app', 'app_message_events') }} as activity
join sessions as session on session.slug = activity.session_slug
where activity.event_type = 'tool'
group by 1, 2, 3, 4, 5
