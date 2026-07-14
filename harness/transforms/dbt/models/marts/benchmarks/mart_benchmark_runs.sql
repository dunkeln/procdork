with deterministic as (
    select
        {{ chart_id('run_id', 'run') }} as run_id,
        {{ chart_id('case_id', 'case') }} as case_id,
        dataset_version,
        system_version,
        json_extract_string(metadata, '$.family') as case_family,
        json_extract_string(metadata, '$.treatment') as treatment,
        cast(json_extract(metadata, '$.attempt') as integer) as attempt,
        json_extract_string(metadata, '$.agent_model') as agent_model,
        json_extract_string(metadata, '$.expected_behavior') as expected_behavior,
        cast(json_extract(metadata, '$.abstained') as boolean) as abstained,
        {{ chart_id("json_extract_string(metadata, '$.response_sha256')", 'resp') }} as response_sha256,
        result as deterministic_result,
        score as deterministic_score,
        cast(json_extract(metadata, '$.elapsed_ms') as bigint) as elapsed_ms,
        cast(json_extract(metadata, '$.tool_call_count') as bigint) as tool_call_count,
        cast(json_extract(metadata, '$.tool_error_count') as bigint) as tool_error_count,
        cast(json_extract(metadata, '$.retry_count') as bigint) as retry_count,
        cast(json_extract(metadata, '$.max_tool_latency_ms') as bigint) as max_tool_latency_ms,
        cast(json_extract(metadata, '$.usage.input_tokens') as bigint) as input_tokens,
        cast(json_extract(metadata, '$.usage.cached_input_tokens') as bigint) as cached_input_tokens,
        cast(json_extract(metadata, '$.usage.output_tokens') as bigint) as output_tokens,
        cast(json_extract(metadata, '$.cost_proxy_usd') as double) as cost_proxy_usd,
        json_extract_string(metadata, '$.pricing.date') as pricing_date,
        evaluated_at,
        {{ chart_time('evaluated_at') }} as evaluated_at_bucket,
        evidence_uri
    from {{ ref('stg_eval_results') }}
    where evaluator_name = 'benchmark_deterministic'
),

semantic as (
    select
        {{ chart_id('run_id', 'run') }} as run_id,
        score as semantic_score,
        cast(json_extract(metadata, '$.scores.grounding') as integer) as grounding_score,
        cast(json_extract(metadata, '$.scores.task_resolution') as integer) as task_resolution_score,
        cast(json_extract(metadata, '$.scores.uncertainty_calibration') as integer) as uncertainty_calibration_score,
        cast(json_extract(metadata, '$.scores.decision_usefulness') as integer) as decision_usefulness_score,
        cast(json_extract(metadata, '$.scores.clarity') as integer) as clarity_score,
        json_extract_string(metadata, '$.judge_model') as judge_model,
        json_extract_string(metadata, '$.rubric_version') as rubric_version
    from {{ ref('stg_eval_results') }}
    where evaluator_name = 'benchmark_semantic_judge'
),

automated as (
    select
        d.*,
        s.semantic_score,
        s.grounding_score,
        s.task_resolution_score,
        s.uncertainty_calibration_score,
        s.decision_usefulness_score,
        s.clarity_score,
        s.judge_model,
        s.rubric_version,
        0::bigint as operator_interventions
    from deterministic d
    left join semantic s using (run_id)
),

human as (
    select
        {{ chart_id('run_id', 'run') }} as run_id,
        {{ chart_id('case_id', 'case') }} as case_id,
        dataset_version,
        system_version,
        json_extract_string(metadata, '$.family') as case_family,
        json_extract_string(metadata, '$.treatment') as treatment,
        cast(json_extract(metadata, '$.attempt') as integer) as attempt,
        json_extract_string(metadata, '$.agent_model') as agent_model,
        null::varchar as expected_behavior,
        null::boolean as abstained,
        null::varchar as response_sha256,
        result as deterministic_result,
        score as deterministic_score,
        cast(json_extract(metadata, '$.elapsed_ms') as bigint) as elapsed_ms,
        null::bigint as tool_call_count,
        null::bigint as tool_error_count,
        null::bigint as retry_count,
        null::bigint as max_tool_latency_ms,
        null::bigint as input_tokens,
        null::bigint as cached_input_tokens,
        null::bigint as output_tokens,
        null::double as cost_proxy_usd,
        null::varchar as pricing_date,
        evaluated_at,
        {{ chart_time('evaluated_at') }} as evaluated_at_bucket,
        evidence_uri,
        null::double as semantic_score,
        null::integer as grounding_score,
        null::integer as task_resolution_score,
        null::integer as uncertainty_calibration_score,
        null::integer as decision_usefulness_score,
        null::integer as clarity_score,
        null::varchar as judge_model,
        null::varchar as rubric_version,
        cast(json_extract(metadata, '$.interventions') as bigint) as operator_interventions
    from {{ ref('stg_eval_results') }}
    where evaluator_name in ('human_baseline', 'operator_agent_baseline')
)

select * from automated
union all by name
select * from human
