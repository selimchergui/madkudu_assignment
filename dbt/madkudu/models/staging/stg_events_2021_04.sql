with final as (
    select
        id,
        "timestamp",
        email,
        ip,
        uri,
        action,
        tags
    from {{ source("source", "src_2021_04_events") }}

)
select * from final