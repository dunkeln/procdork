select
    run_id,
    case_id,
    dataset_version,
    system_version,
    evaluator_name,
    evaluator_version,
    score,
    result,
    evidence_uri,
    metadata,
    evaluated_at
from {{ source('harness', 'raw_evaluation_results') }}
