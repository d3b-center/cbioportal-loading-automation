{{ config(schema='cbio') }}

-- Create cBio sample names from genomics manifest
with genomic_manifest as (
    select distinct
        g.biospecimen_id,
        normal_id,
        file_type,
        experiment_strategy
    from {{ source('bix_genomics_file', 'sd_dypmehhf-genomics_file_manifest') }} g
    left join {{ source('bix', 'cbio_hide_reasons') }} c
    on c.biospecimen_id = g.biospecimen_id
    where status = 'active' and c.biospecimen_id is null and file_type in ('RSEM_gene', 'annofuse_filtered_fusions_tsv', 'annotated_public_outputs', 'ctrlfreec_pval', 'ctrlfreec_info', 'ctrlfreec_bam_seg')
),

-- create table with sequenced specimens and filter by those in the genomics manifest.
sequenced_samples as (
    select distinct
        participant_id,
        bs.external_sample_id as sample_id,

        case
            when bs.source_text_tissue_type in ('Tumor','tumor','metastasis') then 'Tumor'
            when bs.source_text_tissue_type in ('Normal','normal') then 'Normal'
        end as source_text_tissue_type,

        bs.analyte_type,
        bs.composition,
        cl.cell_line_type,
        bs.kf_id as specimen_id,
        bs.external_aliquot_id,
        bs.sequencing_center_id
        bs.method_of_sample_procurement
        gm.experiment_strategy

    from {{ source( 'kidsfirst', 'biospecimen') }} as bs
    join genomic_manifest as gm
        on gm.biospecimen_id = bs.kf_id
    left outer join {{ source('bix', 'cell_line_supplemental') }} as cl
        on bs.kf_id = cl.kf_biospecimen_id
    where (gm.biospecimen_id is not null
           or (bs.composition = 'Derived Cell Line'
               and cell_line_type in ('sus', 'adh')
            )) and bs.source_text_tissue_type in ('Tumor', 'tumor', 'metastasis', 'Normal', 'normal')
and bs.analyte_type <> 'Not Applicable'
and bs.visible = true
),

-- Find primary specimens that have a pair of DNA and RNA and are not autopsy
collect_primary_samples as (
    select
        sample_id,
        count(distinct specimen_id) as sequenced_specimens
    from sequenced_samples
    where source_text_tissue_type = 'Tumor'
           and analyte_type in ('RNA', 'DNA')
           and composition <> 'Derived Cell Line'
    group by sample_id
    having count(distinct analyte_type) = 2 and count(distinct specimen_id) = 2
),

-- Find primary specimens that have a pair of DNA and RNA and are not autopsy
collect_primary_cl_samples as (
    select
        sample_id,
        count(distinct specimen_id) as sequenced_specimens
    from sequenced_samples
    where source_text_tissue_type = 'Tumor'
           and analyte_type in ('RNA', 'DNA')
           and composition = 'Derived Cell Line'
    group by sample_id
    having count(distinct analyte_type) = 2 and count(distinct specimen_id) = 2
),

-- Find simple experimental strategy specimens that only have DNA or RNA samples.
collect_simple_samples as (
    select
        sample_id,
        count(distinct analyte_type) as sequenced_specimens
    from sequenced_samples
    where source_text_tissue_type = 'Tumor'
           and analyte_type in ('RNA', 'DNA', 'Virtual')
    group by sample_id
    having count(distinct analyte_type) = 1
),

-- add in normal sample info
normal_info as (
    select
         genomic_manifest.biospecimen_id,
         normal_id as normal_bs_id,
         external_sample_id as normal_sample_id
    from genomic_manifest
    join {{ source( 'kidsfirst', 'biospecimen') }} as bs
        on bs.kf_id = genomic_manifest.normal_id
),

-- Formatting sample IDs with paired samples or single sequencing
formatted as (
    select distinct
        case
             when pri.sample_id is not null then sm.sample_id
             -- 7316-2189_WGS_T_BS_02YBZSBY and 7316-2189_RNAseq_T_BS_HJRTC9JQ --> 7316-2189
            
            when prc.sample_id is not null then sm.sample_id ||  '_CL_' || coalesce(sm.cell_line_type, 'NA')
             -- 7316-2189_WGS_T_CL_BS_ERFMPQN3 and 7316-2189_RNAseq_T_CL_BS_PGK832G2 --> 7316-2189_CL_adh

             when sim.sample_id is not null and sm.composition <> 'Derived Cell Line' then sm.sample_id || '_' || sm.experiment_strategy || '_' || sm.external_aliquot_id
             -- 77316-1455_RNAseq_T_BS_HWGWYCY7 -> 77316-1455_RNAseq_400856
             -- 77316-1455_RNAseq_T_BS_HE0WJRW6 -> 77316-1455_RNAseq_994695

             when sim.sample_id is not null and sm.composition = 'Derived Cell Line' then sm.sample_id || '_' || sm.experiment_strategy || '_CL_' || coalesce(sm.cell_line_type, 'NA')
             -- 7316-1746_WGS_CL_BS_68TZMZH1 -> 7316-1746_WGS_CL_adh
             -- 7316-1746_WGS_CL_BS_AFBPM6CN -> 7316-1746_WGS_CL_susp

             when sim.sample_id is not null and sm.method_of_sample_procurement = 'Autopsy' then sm.sample_id || '_Autopsy_' || sm.external_aliquot_id
             -- 7316-3230_WGS_BS_EE73VE7V -> 7316-3230_WGS_Autopsy_SF5606-12
             -- 7316-3230_WGS_BS_HYKV2TH9 -> 7316-3230_WGS_Autopsy_SF5606-6
             
        end as formatted_sample_id,
        sm.*,
        normal_bs_id,
        normal_sample_id
    from sequenced_samples as sm
    left join collect_primary_samples as pri
        on pri.sample_id = sm.sample_id
    left join collect_primary_cl_samples as prc
        on prc.sample_id = sm.sample_id
    left join collect_simple_samples as sim
        on sim.sample_id = sm.sample_id
    left outer join normal_info
        on specimen_id = normal_info.biospecimen_id
    where sm.source_text_tissue_type = 'Tumor'
)

select
    participant_id,
    array_agg( sequencing_center_id) as sequencing_center_ids,
    collection_event_id,
    formatted_sample_id,
    array_agg(specimen_id) as specimen_id,
    array_agg(analyte_type) as analyte_types,
    array_to_string(array_agg(normal_bs_id), ',') as normal_bs_id,
    array_to_string(array_agg(normal_sample_id), ',') as normal_sample_id
from
    formatted
group by
    participant_id,
    collection_event_id,
    formatted_sample_id
order by formatted_sample_id