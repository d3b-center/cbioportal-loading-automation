 ---- This part will be generated according to the study_info
    -- {{ config(schema='cbio') }}
    -- with merged as (
    -- 	select
    -- 		biospecimen_id
    -- 		tumor_id
    -- 		normal_id
    -- 		file_type
    -- 		file_name
    -- 	from {{ source('bix_genomics_file','sd_dypmehhf-genomics_file_manifest') }} 
    -- ),

    -- merged_cbio_sample_ids as (
    -- 	select * from {{ ref('x01_fy16_nbl_maris_cbio_sample') }} 
    -- ),
---------------------------------

genomic_manifest as (
    select distinct
        g.biospecimen_id,
        tumor_id,
        normal_id,
        file_type,
        file_name,
        formatted_sample_id
    from merged as g
    left join bix_workflows.cbio_hide_reasons as c
        on c.biospecimen_id = g.biospecimen_id
    join merged_cbio_sample_ids on
        (g.biospecimen_id = specimen_id[1] or g.biospecimen_id = specimen_id[2])
    where status = 'active' and c.biospecimen_id is null and file_type in ('RSEM_gene',
                                                     'annofuse_filtered_fusions_tsv',
                                                     'annotated_public_outputs',
                                                     'ctrlfreec_pval',
                                                     'ctrlfreec_info',
                                                     'ctrlfreec_bam_seg')
                                                     and formatted_sample_id in (
            select distinct "SAMPLE_ID" from {{ref('$clinical_sample_name')}}
        )

)

select
    case
        when biospecimen_id is not null then '$study_name' 
    end as "Cbio_project",
    biospecimen_id as "T_CL_BS_ID",
    coalesce(normal_id, '') as "Norm_BS_ID",
    case
        when file_type = 'RSEM_gene' then 'rsem'
        when file_type = 'annotated_public_outputs' then 'maf'
        when file_type = 'ctrlfreec_pval' then 'cnv'
        when file_type = 'ctrlfreec_bam_seg' then 'seg'
        when file_type = 'ctrlfreec_info' then 'info'
        when file_type = 'annofuse_filtered_fusions_tsv' then 'fusion'
    end as "File_Type",
    formatted_sample_id as "Cbio_Tumor_Name",
    normal_id as "Cbio_Matched_Normal_Name",
    file_name as "File_Name"
from genomic_manifest
where file_name not like '%.vcf.gz%'

