with paired as (
    select
        machine.run_id,
        machine.dataset_version,
        machine.system_version,
        case
            when human.evaluator_name = 'benchmark_human_judge' then 'human'
            else 'cross_model'
        end as reviewer_type,
        machine.metadata as machine_metadata,
        human.metadata as human_metadata
    from {{ ref('stg_eval_results') }} machine
    join {{ ref('stg_eval_results') }} human using (run_id)
    where machine.evaluator_name = 'benchmark_semantic_judge'
      and human.evaluator_name in ('benchmark_human_judge', 'benchmark_operator_judge')
),

scores as (
    select
        run_id,
        dataset_version,
        system_version,
        reviewer_type,
        dimension,
        cast(json_extract(machine_metadata, '$.scores.' || dimension) as integer) as machine_score,
        cast(json_extract(human_metadata, '$.scores.' || dimension) as integer) as human_score
    from paired
    cross join lateral
        (
            values
                ('grounding'),
                ('task_resolution'),
                ('uncertainty_calibration'),
                ('decision_usefulness'),
                ('clarity')
        ) as dimensions(dimension)
)

select
    dataset_version,
    system_version,
    reviewer_type,
    dimension,
    count(*) as calibrated_output_count,
    avg(abs(machine_score - human_score)) as mean_absolute_difference,
    avg((abs(machine_score - human_score) <= 1)::integer) as within_one_point_rate
from scores
group by 1, 2, 3, 4
