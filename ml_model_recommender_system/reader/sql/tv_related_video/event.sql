with url_to_work_id as (
select 
*,
regexp_extract_all(current_url, '\/([^\/\?]*)(?!\/)\??[^\/\?]*$', 1)[0] as url_work_id
from hive_metastore.mixpanel.events_without_fuck
where event = 'Watch Video Duration'
),
coalesce_id_work_id as(
select
*,
case when id is null then url_work_id else cast(id as int) end as work_id
from 
url_to_work_id
),
all_data as(
select *
from coalesce_id_work_id
where time >= '2022-07-22'
and work_id is not null
)

select 
    user_id,
    work_id as content_id,
    duration_seconds as duration,
    time as datetime
from 
    all_data
