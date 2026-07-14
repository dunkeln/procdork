with scored as (
    select
        evaluated_at,
        dimension,
        judge_version,
        rubric_version,
        count(*) over (
            partition by dimension, judge_version, rubric_version
            order by evaluated_at
            rows between unbounded preceding and current row
        ) as judged_message_count,
        score,
        avg(score) over (
            partition by dimension, judge_version, rubric_version
            order by evaluated_at
            rows between 6 preceding and current row
        ) as rolling_average_score,
        stddev_samp(score) over (
            partition by dimension, judge_version, rubric_version
            order by evaluated_at
            rows between 6 preceding and current row
        ) as score_stddev
    from {{ ref('mart_app_message_judge_scores') }}
)

select
    evaluated_at,
    {{ chart_time('evaluated_at') }} as evaluated_at_bucket,
    dimension,
    rolling_average_score,
    greatest(1, rolling_average_score - coalesce(score_stddev, 0)) as lower_score,
    least(5, rolling_average_score + coalesce(score_stddev, 0)) as upper_score,
    score as latest_score,
    score_stddev,
    judged_message_count,
    judge_version,
    rubric_version
from scored
