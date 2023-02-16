{{ config(schema='cbio') }}
with cbio_sample_ids as (
	select * from {{ ref('x01_fy16_nbl_maris_cbio_sample') }} 
),


sa_list as (
    select
        participant_id,
        formatted_sample_id,
        specimen_id,
        analyte_types
    from cbio_sample_ids
),

dx_info as (
    select distinct
        sp.participant_id,
        formatted_sample_id,
        specimen_id,
        analyte_types,
        string_agg(distinct ds.source_text_diagnosis, ';') as diagnoses,
        string_agg(
            distinct sp.source_text_anatomical_site, ';'
        ) as tumor_locations,
        sp.source_text_tumor_descriptor as event_type
    from {{ source('kidsfirst', 'biospecimen') }} as sp
    left join {{ source('kidsfirst', 'biospecimen_diagnosis') }} as bd
        on bd.biospecimen_id = sp.kf_id
    left join {{ source('kidsfirst', 'diagnosis') }} as ds
        on ds.kf_id = bd.diagnosis_id
    left join {{ source('kidsfirst', 'participant') }} as p
        on p.kf_id = sp.participant_id
    join sa_list
        on sa_list.specimen_id[1] = sp.kf_id
    where p.study_id in ('SD_DYPMEHHF')
    group by
        sp.participant_id,
        formatted_sample_id,
        specimen_id,
        analyte_types,
        sp.source_text_tumor_descriptor
),

onco_info as (
    select

        specimen_id,
        d3b_diagnosis,
        diagnoses,
        oncotree_value as onco_name,
        lower(oncotree_code) as code
    from {{ref('d3b_oncotree_mapping')}}
    right outer join dx_info
        on d3b_diagnosis = diagnoses
),

kf_info as (
    select
        kf_id,
        composition
    from {{ source('kidsfirst', 'biospecimen') }} as sp
    join dx_info
        on dx_info.specimen_id[1] = sp.kf_id
)

-- collate results
select distinct

    dx_info.participant_id as "PATIENT_ID",
    formatted_sample_id as "SAMPLE_ID",
    array_to_string( dx_info.specimen_id, ';') as "SPECIMEN_ID",

    coalesce(dx_info.diagnoses, 'NA') as "CANCER_TYPE",
    coalesce(onco_name, 'NA') as "CANCER_TYPE_DETAILED",
    coalesce(code, 'NA') as "ONCOTREE_CODE",

    coalesce(tumor_locations, 'NA') as "TUMOR_TISSUE_TYPE",
    coalesce(event_type, 'NA') as "TUMOR_TYPE",

    coalesce(kf_info.composition, 'NA') as "SAMPLE_TYPE"
from dx_info
join kf_info
    on kf_info.kf_id = dx_info.specimen_id[1]
left outer join onco_info
    on dx_info.specimen_id[1] = onco_info.specimen_id[1]
left outer join sa_list
    using (formatted_sample_id)
group by
    dx_info.participant_id,
    formatted_sample_id,
    dx_info.specimen_id,
    dx_info.analyte_types,
    dx_info.diagnoses,
    onco_name,
    code,
    tumor_locations,
    event_type,
    composition
