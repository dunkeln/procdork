select
    artifact_id,
    source_id,
    source_type,
    source_uri,
    source_retrieved_at,
    source_content_type,
    source_adapter_name,
    storage_uri,
    sha256,
    bytes,
    loaded_at
from {{ source('harness', 'raw_manifest') }}
