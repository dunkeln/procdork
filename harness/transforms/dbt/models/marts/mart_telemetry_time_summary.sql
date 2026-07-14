{{ config(materialized='view') }}

with telemetry as (
    select
        session_number,
        created_at,
        coalesce(last_event_at, updated_at, created_at) as observed_at,
        session_duration_seconds,
        message_count,
        turn_count,
        event_count,
        tool_event_count,
        evidence_event_count,
        tool_error_count,
        citation_count,
        source_count,
        avg_assistant_latency_ms
    from {{ ref('mart_workflow_sessions') }}
),
bucketed as (
    select
        'all' as time_grain,
        0 as bucket_sort,
        cast(null as timestamp) as bucket_start,
        'All time' as bucket_label,
        *
    from telemetry

    union all

    select
        'hour' as time_grain,
        epoch(date_trunc('hour', created_at)) as bucket_sort,
        date_trunc('hour', created_at) as bucket_start,
        strftime(date_trunc('hour', created_at), '%Y-%m-%d %H:00') as bucket_label,
        *
    from telemetry

    union all

    select
        'day' as time_grain,
        epoch(date_trunc('day', created_at)) as bucket_sort,
        date_trunc('day', created_at) as bucket_start,
        strftime(date_trunc('day', created_at), '%Y-%m-%d') as bucket_label,
        *
    from telemetry

    union all

    select
        'weekday' as time_grain,
        cast(strftime(created_at, '%w') as integer) as bucket_sort,
        cast(null as timestamp) as bucket_start,
        strftime(created_at, '%A') as bucket_label,
        *
    from telemetry
),
rollup as (
    select
        time_grain,
        bucket_sort,
        bucket_start,
        bucket_label,
        count(*) as session_count,
        min(created_at) as first_session_at,
        max(observed_at) as latest_observed_at,
        {{ chart_time('min(created_at)') }} as first_session_at_bucket,
        {{ chart_time('max(observed_at)') }} as latest_observed_at_bucket,
        avg(session_duration_seconds) as avg_session_duration_seconds,
        avg(message_count) as avg_messages_per_session,
        avg(turn_count) as avg_turns_per_session,
        avg(event_count) as avg_events_per_session,
        avg(tool_event_count) as avg_tool_events_per_session,
        avg(evidence_event_count) as avg_evidence_events_per_session,
        avg(tool_error_count) as avg_tool_errors_per_session,
        avg(citation_count) as avg_citations_per_session,
        avg(source_count) as avg_sources_per_session,
        avg(avg_assistant_latency_ms) as avg_assistant_latency_ms,
        sum(event_count) as total_event_count,
        sum(tool_event_count) as total_tool_event_count,
        sum(evidence_event_count) as total_evidence_event_count,
        sum(tool_error_count) as total_tool_error_count
    from bucketed
    group by 1, 2, 3, 4
),
freshness as (
    select
        *,
        date_diff('minute', latest_observed_at, current_timestamp) as freshness_minutes
    from rollup
)

select
    *,
    case
        when freshness_minutes < 60 then cast(freshness_minutes as varchar) || ' minutes'
        when freshness_minutes < 1440 then cast(round(freshness_minutes / 60.0, 1) as varchar) || ' hours'
        else cast(round(freshness_minutes / 1440.0, 1) as varchar) || ' days'
    end as freshness_label
from freshness
