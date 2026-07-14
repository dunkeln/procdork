with ranked as (
    select
        *,
        row_number() over (
            partition by case_id, evaluator_name
            order by evaluated_at desc
        ) as evaluation_order,
        lead(result) over (
            partition by case_id, evaluator_name
            order by evaluated_at desc
        ) as previous_result,
        lead(score) over (
            partition by case_id, evaluator_name
            order by evaluated_at desc
        ) as previous_score,
        lead(system_version) over (
            partition by case_id, evaluator_name
            order by evaluated_at desc
        ) as previous_system_version
    from {{ ref('stg_eval_results') }}
)

select
    {{ chart_id('run_id', 'run') }} as run_id,
    {{ chart_id('case_id', 'case') }} as case_id,
    dataset_version,
    system_version,
    evaluator_name,
    evaluator_version,
    score,
    result,
    previous_score,
    previous_result,
    previous_system_version,
    case
        when previous_result = 'pass' and result = 'fail' then 'regressed'
        when previous_result = 'fail' and result = 'pass' then 'improved'
        when previous_result is null then 'new'
        else 'unchanged'
    end as comparison,
    evidence_uri,
    metadata,
    evaluated_at,
    {{ chart_time('evaluated_at') }} as evaluated_at_bucket
from ranked
where evaluation_order = 1
