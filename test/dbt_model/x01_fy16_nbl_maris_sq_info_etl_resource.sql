{{ config(schema='cbio') }}
with cbio_sample_ids as (
	select * from {{ ref('x01_fy16_nbl_maris_cbio_sample') }} 
),

exploded as (
    select
        unnest(sequencing_center_ids) as sq_id,
        formatted_sample_id,
        unnest(specimen_id) as kf_biospecimen_id,
        unnest(analyte_types) as ana_type
    from cbio_sample_ids
),

rna_info as (
    select exploded.*
    from exploded
    join {{ref('x01_fy16_nbl_maris_data_clinical_sample')}}
        on "SAMPLE_ID" = formatted_sample_id
    where ana_type = 'RNA'
)

select
    kf_biospecimen_id as "BS_ID",
    coalesce(sq_id::text, 'NA') as "SQ_ID",
    case
        when sq_id = 'SC_WWEQ9HFY' then 'BGI-CHOP Genome Center'
        when sq_id = 'SC_N1EVHSME' then 'NantOmics'
        when sq_id = 'SC_FAD4KCQG' then 'BGI'
        when sq_id = 'SC_0CNMF82N' then 'Ashion'
        when sq_id = 'SC_2ZBAMKK0' then 'Novogene'
        when sq_id = 'SC_1K3QGW4V' then 'St Jude'
        else 'NA'
    end as "SQ_Value"
from rna_info
