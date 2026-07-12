select *
from {{ ref('mart_evaluation_cases') }}
where comparison = 'regressed'
