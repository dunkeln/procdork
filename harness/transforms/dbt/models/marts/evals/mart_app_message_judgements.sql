select
    {{ chart_id('run_id', 'run') }} as run_id,
    {{ chart_id('case_id', 'msg') }} as message_id,
    dataset_version,
    system_version,
    evaluator_version,
    json_extract_string(metadata, '$.judge_model') as judge_model,
    json_extract_string(metadata, '$.judge_version') as judge_version,
    json_extract_string(metadata, '$.rubric_version') as rubric_version,
    json_extract_string(metadata, '$.judge_prompt_version') as judge_prompt_version,
    json_extract_string(metadata, '$.session_slug') as session_slug,
    json_extract_string(metadata, '$.session_title') as session_title,
    cast(json_extract(metadata, '$.citation_count') as bigint) as citation_count,
    cast(json_extract(metadata, '$.response_chars') as bigint) as response_chars,
    {{ chart_id("json_extract_string(metadata, '$.response_sha256')", 'resp') }} as response_sha256,
    cast(json_extract(metadata, '$.scores.grounding') as integer) as grounding_score,
    cast(json_extract(metadata, '$.scores.task_resolution') as integer) as task_resolution_score,
    cast(json_extract(metadata, '$.scores.uncertainty_calibration') as integer)
        as uncertainty_calibration_score,
    cast(json_extract(metadata, '$.scores.consistency') as integer) as consistency_score,
    cast(json_extract(metadata, '$.scores.answer_composability') as integer)
        as answer_composability_score,
    cast(json_extract(metadata, '$.scores.style_clarity') as integer) as style_clarity_score,
    score * 5 as average_score,
    result,
    json_extract_string(metadata, '$.rationale') as rationale,
    cast(json_extract(metadata, '$.judge_usage.input_tokens') as bigint) as judge_input_tokens,
    cast(json_extract(metadata, '$.judge_usage.output_tokens') as bigint) as judge_output_tokens,
    evidence_uri,
    cast(json_extract_string(metadata, '$.message_created_at') as timestamptz)
        as message_created_at,
    {{ chart_time("cast(json_extract_string(metadata, '$.message_created_at') as timestamptz)") }}
        as message_created_at_bucket,
    cast(json_extract_string(metadata, '$.message_completed_at') as timestamptz)
        as message_completed_at,
    {{ chart_time("cast(json_extract_string(metadata, '$.message_completed_at') as timestamptz)") }}
        as message_completed_at_bucket,
    evaluated_at,
    {{ chart_time('evaluated_at') }} as evaluated_at_bucket,
    date_trunc('day', evaluated_at) as evaluated_day
from {{ ref('stg_eval_results') }}
where evaluator_name = 'app_message_judge'
