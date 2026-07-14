select
    judgement.run_id,
    judgement.message_id,
    judgement.dataset_version,
    judgement.system_version,
    judgement.evaluator_version,
    judgement.judge_model,
    judgement.judge_version,
    judgement.rubric_version,
    judgement.judge_prompt_version,
    judgement.session_slug,
    judgement.session_title,
    judgement.citation_count,
    judgement.response_chars,
    judgement.result,
    judgement.evidence_uri,
    judgement.message_created_at,
    judgement.message_created_at_bucket,
    judgement.message_completed_at,
    judgement.message_completed_at_bucket,
    judgement.evaluated_at,
    judgement.evaluated_at_bucket,
    judgement.evaluated_day,
    score.dimension,
    score.score
from {{ ref('mart_app_message_judgements') }} as judgement
cross join lateral (
        values
            ('grounding', judgement.grounding_score),
            ('task_resolution', judgement.task_resolution_score),
            ('uncertainty_calibration', judgement.uncertainty_calibration_score),
            ('consistency', judgement.consistency_score),
            ('answer_composability', judgement.answer_composability_score),
            ('style_clarity', judgement.style_clarity_score)
    ) as score(dimension, score)
