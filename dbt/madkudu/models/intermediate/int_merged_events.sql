{% set tables_to_concat = ["stg_events_2021_04"] %}

{{ config(
    materialized='incremental',
    unique_key='id'
) }}

with concatenated_data as (
    select * from {{ ref(tables_to_concat[0]) }}
    {% for table in tables_to_concat[1:] %}
        union all
        select * from {{ ref(table) }}
    {% endfor %}
)
select * from concatenated_data