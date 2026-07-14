{% set raw_manifest = adapter.get_relation(database=target.database, schema='main', identifier='raw_manifest') %}

{% if raw_manifest %}
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
{% else %}
select
    cast(null as varchar) as artifact_id,
    cast(null as varchar) as source_id,
    cast(null as varchar) as source_type,
    cast(null as varchar) as source_uri,
    cast(null as timestamptz) as source_retrieved_at,
    cast(null as varchar) as source_content_type,
    cast(null as varchar) as source_adapter_name,
    cast(null as varchar) as storage_uri,
    cast(null as varchar) as sha256,
    cast(null as ubigint) as bytes,
    cast(null as timestamptz) as loaded_at
where false
{% endif %}
