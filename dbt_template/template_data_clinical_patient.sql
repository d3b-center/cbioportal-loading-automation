---- This part will be generated according to the study_info
    -- {{ config(schema='cbio') }}
    -- with cbio_sample_ids as (
    -- 	select * from {{ ref('x01_fy16_nbl_maris_cbio_sample') }} 
    -- ),
-----------------------------

pt_list as (
    select distinct "participant_id"
    from cbio_sample_ids

),

pt_info as (
    select distinct
        participant_id,
        external_id as "EXTERNAL_PATIENT_ID",
        gender,
        race,
        ethnicity
    from {{ source('kidsfirst', 'participant') }} as pt
    join pt_list on pt_list.participant_id = pt.kf_id
),

survival as (
    select distinct
        kd.participant_id,
        case
            when vital_status = 'Deceased' then 'DECEASED'
            when vital_status = 'Alive' then 'LIVING'
        end as "OS_STATUS",
        kd.age_at_event_days as "AGE_IN_DAYS",
        floor(cast(kd.age_at_event_days as INT) / 365.25) as "AGE",
        floor(cast(o.age_at_event_days as FLOAT) / (365.25 / 12)) as "OS_MONTHS"
    from pt_info
    join {{ source('kidsfirst', 'diagnosis') }} as kd
        on pt_info.participant_id = kd.participant_id
    join {{ source('kidsfirst', 'outcome') }} as o
        on pt_info.participant_id = o.participant_id
)

select distinct
    participant_id as "PATIENT_ID",
    "EXTERNAL_PATIENT_ID",
    gender as "SEX",
    race as "RACE",
    ethnicity as "ETHNICITY",

    coalesce("AGE"::text, 'NA') as "AGE",
    coalesce("AGE_IN_DAYS"::text, 'NA') as "AGE_IN_DAYS",
    coalesce("OS_STATUS", 'NA') as "OS_STATUS",
    coalesce("OS_MONTHS"::text, 'NA') as "OS_MONTHS"
from pt_info
left outer join survival
    using (participant_id)
