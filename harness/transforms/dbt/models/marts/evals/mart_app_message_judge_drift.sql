with daily as (
    select
        evaluated_day,
        dimension,
        judge_version,
        rubric_version,
        count(distinct message_id) as judged_message_count,
        avg(score) as average_score,
        stddev_samp(score) as score_stddev
    from {{ ref('mart_app_message_judge_scores') }}
    group by 1, 2, 3, 4
)

select
    evaluated_day,
    dimension,
    avg(average_score) over (
        partition by dimension, judge_version, rubric_version
        order by evaluated_day
        rows between 6 preceding and current row
    ) as rolling_average_score,
    greatest(1, average_score - coalesce(score_stddev, 0)) as lower_score,
    least(5, average_score + coalesce(score_stddev, 0)) as upper_score,
    average_score,
    score_stddev,
    judged_message_count,
    judge_version,
    rubric_version
from daily
