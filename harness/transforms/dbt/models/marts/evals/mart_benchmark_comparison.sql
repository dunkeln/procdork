with treatment_times as (
    select
        dataset_version,
        system_version,
        case_family,
        treatment,
        avg(elapsed_ms) as average_elapsed_ms,
        avg(deterministic_score) as average_deterministic_score,
        avg(semantic_score) as average_semantic_score
    from {{ ref('mart_benchmark_runs') }}
    group by 1, 2, 3, 4
)

select
    harness.dataset_version,
    harness.system_version,
    harness.case_family,
    harness.average_elapsed_ms as harness_average_elapsed_ms,
    raw.average_elapsed_ms as raw_sql_average_elapsed_ms,
    human.average_elapsed_ms as human_average_elapsed_ms,
    operator.average_elapsed_ms as operator_agent_average_elapsed_ms,
    1 - harness.average_elapsed_ms / nullif(raw.average_elapsed_ms, 0) as time_reduction_vs_raw_sql,
    1 - harness.average_elapsed_ms / nullif(human.average_elapsed_ms, 0) as time_reduction_vs_human,
    1 - harness.average_elapsed_ms / nullif(operator.average_elapsed_ms, 0) as time_reduction_vs_operator_agent,
    harness.average_deterministic_score - raw.average_deterministic_score as deterministic_score_delta,
    harness.average_semantic_score - raw.average_semantic_score as semantic_score_delta
from treatment_times harness
left join treatment_times raw
    on raw.dataset_version = harness.dataset_version
    and raw.system_version = harness.system_version
    and raw.case_family = harness.case_family
    and raw.treatment = 'raw_sql'
left join treatment_times human
    on human.dataset_version = harness.dataset_version
    and human.system_version = harness.system_version
    and human.case_family = harness.case_family
    and human.treatment = 'human'
left join treatment_times operator
    on operator.dataset_version = harness.dataset_version
    and operator.system_version = harness.system_version
    and operator.case_family = harness.case_family
    and operator.treatment = 'operator_agent'
where harness.treatment = 'harness'
