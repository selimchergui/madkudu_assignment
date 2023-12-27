{{ config(
    materialized='incremental',
    unique_key='id'
    )
}}

with concatenated_data as (
    select * from {{ ref("int_merged_events") }}
)
select * from concatenated_data