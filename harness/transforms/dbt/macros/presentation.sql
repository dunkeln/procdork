{% macro chart_id(expr, prefix) -%}
    case
        when {{ expr }} is null then null
        else '{{ prefix }}_' || substr(sha256(cast({{ expr }} as varchar)), 1, 8)
    end
{%- endmacro %}

{% macro chart_time(expr) -%}
    case
        when {{ expr }} is null then null
        else strftime(to_timestamp(floor(epoch({{ expr }}) / 900) * 900), '%Y-%m-%d %H:%M')
    end
{%- endmacro %}
