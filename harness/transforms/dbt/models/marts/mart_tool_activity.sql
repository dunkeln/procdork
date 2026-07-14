select
    session_slug,
    coalesce(json_extract_string(event, '$.name'), 'unknown') as tool_name,
    coalesce(json_extract_string(event, '$.label'), 'unknown') as tool_label,
    coalesce(json_extract_string(event, '$.status'), 'unknown') as tool_status,
    count(*) as event_count,
    count(distinct turn_id) as turn_count,
    min(created_at) as first_seen_at,
    max(created_at) as last_seen_at
from {{ source('app', 'app_message_events') }}
where event_type = 'tool'
group by 1, 2, 3, 4
