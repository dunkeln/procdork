with sessions as (
    select
        *,
        row_number() over (order by created_at, slug) as session_number
    from {{ source('app', 'app_sessions') }}
),
message_rollup as (
    select
        session_slug,
        count(*) as message_count,
        sum(case when role = 'user' then 1 else 0 end) as user_message_count,
        sum(case when role = 'assistant' then 1 else 0 end) as assistant_message_count,
        sum(case when role = 'assistant' and completed_at is not null then 1 else 0 end) as completed_assistant_count,
        avg(
            case
                when role = 'assistant' and completed_at is not null
                    then date_diff('millisecond', created_at, completed_at)
            end
        ) as avg_assistant_latency_ms,
        sum(length(coalesce(content, ''))) as transcript_chars
    from {{ source('app', 'app_messages') }}
    group by 1
),
event_rollup as (
    select
        session_slug,
        count(*) as event_count,
        count(distinct turn_id) as turn_count,
        sum(case when event_type = 'tool' then 1 else 0 end) as tool_event_count,
        sum(case when event_type = 'evidence' then 1 else 0 end) as evidence_event_count,
        sum(case when event_type = 'final' then 1 else 0 end) as final_event_count,
        sum(case when event_type = 'done' then 1 else 0 end) as done_event_count,
        sum(case when event_type = 'tool' and json_extract_string(event, '$.status') = 'error' then 1 else 0 end)
            as tool_error_count,
        max(created_at) as last_event_at
    from {{ source('app', 'app_message_events') }}
    group by 1
),
source_rollup as (
    select
        message.session_slug,
        count(*) as citation_count,
        count(distinct link.source_url) as source_count
    from {{ source('app', 'app_message_sources') }} as link
    join {{ source('app', 'app_messages') }} as message
        on message.id = link.message_id
    group by 1
)

select
    session.session_number,
    coalesce(nullif(session.title, ''), 'Untitled session') as session_title,
    session.created_at,
    {{ chart_time('session.created_at') }} as created_at_bucket,
    session.updated_at,
    {{ chart_time('session.updated_at') }} as updated_at_bucket,
    event.last_event_at,
    {{ chart_time('event.last_event_at') }} as last_event_at_bucket,
    date_diff('second', session.created_at, session.updated_at) as session_duration_seconds,
    coalesce(message.message_count, 0) as message_count,
    coalesce(message.user_message_count, 0) as user_message_count,
    coalesce(message.assistant_message_count, 0) as assistant_message_count,
    coalesce(message.completed_assistant_count, 0) as completed_assistant_count,
    coalesce(event.turn_count, 0) as turn_count,
    coalesce(event.event_count, 0) as event_count,
    coalesce(event.tool_event_count, 0) as tool_event_count,
    coalesce(event.evidence_event_count, 0) as evidence_event_count,
    coalesce(event.final_event_count, 0) as final_event_count,
    coalesce(event.done_event_count, 0) as done_event_count,
    coalesce(event.tool_error_count, 0) as tool_error_count,
    coalesce(source.citation_count, 0) as citation_count,
    coalesce(source.source_count, 0) as source_count,
    message.avg_assistant_latency_ms,
    coalesce(message.transcript_chars, 0) as transcript_chars,
    case
        when coalesce(message.assistant_message_count, 0) = 0 then 'no_assistant_response'
        when coalesce(event.final_event_count, 0) = 0 or coalesce(event.done_event_count, 0) = 0 then 'incomplete_lifecycle'
        when coalesce(event.tool_error_count, 0) > 0 then 'completed_with_tool_errors'
        else 'completed'
    end as workflow_state
from sessions as session
left join message_rollup as message on message.session_slug = session.slug
left join event_rollup as event on event.session_slug = session.slug
left join source_rollup as source on source.session_slug = session.slug
