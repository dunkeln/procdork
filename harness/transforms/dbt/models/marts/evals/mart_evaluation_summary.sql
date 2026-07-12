select
    dataset_version,
    system_version,
    evaluator_name,
    evaluator_version,
    result,
    count(*) as case_count,
    avg(score) as average_score,
    min(evaluated_at) as first_evaluated_at,
    max(evaluated_at) as last_evaluated_at
from {{ ref('stg_eval_results') }}
group by 1, 2, 3, 4, 5
