with video_episode as (
    select
        work_id,
        series_name,
        episode
    from 
        default.video_episode
    where
        _remove is NULL
)

select 
    a.id as content_id, 
    a.name as title, 
    a.introduction, 
    a.published_at,
    b.series_name,
    b.episode
from 
    sql.works as a
left join
    video_episode as b
on
    a.id = b.work_id
