#!/usr/bin/env python3
"""
This is a genomics file + clinical data file to cBio package conversion workflow script.
It is designed to work with standard KF somatic workflow outputs as well as DGD outputs.
Clinical files should have been produced ahead of time, while supporting sample ID file manifest, case_meta config json file, and data json config.
If there are fusion files, they also need a table outlining sequencing center location.
See README for prequisite details.
"""
import sys
import argparse
import json
import subprocess


def process_maf(maf_dir, manifest,outputdir):
    maf_cmd = "{}maf_merge.py -t {} -p {} -m {} -o {} ".format(
        script_dir, manifest, maf_header, maf_dir, outputdir
    )
    subprocess.call(maf_cmd, shell=True)

def process_cnv_pval(cnv_pval, data_config_file, manifest,outputdir):
    """
    Add gene pvalue to CNV calls, merge into table
    """
    gene_annot_cmd = "{}cnv_1_genome2gene.py -c {} -f {} -o {}".format(
        script_dir, cnv_pval, data_config_file, outputdir
    )
    subprocess.call(gene_annot_cmd, shell=True)

def process_cnv_info(cnv_info, data_config_file, manifest,outputdir):
    """
    Add gene info to CNV calls, merge into table, and create GISTIC-style output
    """

    merge_gene_cmd = "{}cnv_2_merge.py -t {}  -f {} -i {} -o {}".format(
        script_dir, manifest, data_config_file, cnv_info, outputdir
    )
    subprocess.call(merge_gene_cmd, shell=True)

    gistic_style_cmd = "{}cnv_3_gistic_style.py -t {} -j {} -i {} -o {}".format(
        script_dir, manifest, data_config_file, cnv_info, outputdir
    )

    subprocess.call(gistic_style_cmd, shell=True)

def process_seg(cnv_seg, manifest, data_config_file, outputdir):
    """
    Collate and process CNV seg files
    """
    merge_seg_cmd = "{}cnv_merge_seg.py -t {} -m {} -j {} -o {}".format(
        script_dir, manifest, cnv_seg, data_config_file, outputdir
    )
    subprocess.call(merge_seg_cmd, shell=True)

def process_rsem(rsem_gene,manifest, outputdir):
    """
    Merge rsem results by FPKM, calculate z-scores
    """
    sys.stderr.write("Processing RNA expression data\n")
    
    merge_rsem_cmd = "{}rna_merge_rename_expression.py -t {} -r {} -o {} ".format(
        script_dir, manifest, rsem_gene, outputdir
    )
    subprocess.call(merge_rsem_cmd, shell=True)

def process_fusion(fusions,manifest, outputdir):
    """
    Collate and process annoFuse output
    """
    sys.stderr.write("Processing KF fusion calls\n")
    fusion_cmd = "{}rna_convert_fusion.py -t {} -f {} -m annofuse -s {} -o {} ".format(
        script_dir, manifest, fusions, fusion_sq_file, outputdir
    )
    print(fusion_cmd)
    subprocess.call(fusion_cmd, shell=True)

parser = argparse.ArgumentParser(
    description="Download files (if needed), collate genomic files, organize load package."
)
parser.add_argument(
    "-m",
    "--genomics_etl",
    action="store",
    dest="manifest",
    help="Table with cbio project, kf bs ids, cbio IDs, and file names. genomics etl file manifest",
)
parser.add_argument(
    "-seq",
    action="store",
    help="seq center resource",
)
parser.add_argument(
    "-d",
    "--data-config",
    action="store",
    dest="data_config",
    help="json config file with data types and " "data locations",
)
parser.add_argument(
    "-s",
    "--study-config",
    action="store",
    dest="study_config",
    help="json config file with study info",
)
parser.add_argument(
    "-maf_dir",
    action="store",
    help="maf files",
)
parser.add_argument(
    "-ctrlfreec_info_dir",
    action="store",
    help="ctrlfreec info files dir",
)
parser.add_argument(
    "-ctrlfreec_pval_dir",
    action="store",
    help="ctrlfreec pval files dir",
)
parser.add_argument(
    "-ctrlfreec_bamseg_dir",
    action="store",
    help="ctrlfreec bam seg files dir",
)
parser.add_argument(
    "-rsem_gene_dir",
    action="store",
    help="RSEM files dir",
)
parser.add_argument(
    "-fusion_dir",
    action="store",
    help="fusion files dir",
)
parser.add_argument(
    "-output",
    action="store",
    help="output dir",
)


args = parser.parse_args()

with open(args.study_config) as f:
    config_study = json.load(f)

cbio_study_id = config_study["cancer_study_identifier"]
maf_header = 'refs/maf_KF_CONSENSUS.txt'
fusion_sq_file= args.seq
script_dir = 'scripts/'

if args.maf_dir:
    process_maf(
        args.maf_dir,
        args.manifest,
        args.output
    )

if args.ctrlfreec_pval_dir:
    process_cnv_pval(
        args.ctrlfreec_pval_dir,
        args.data_config, 
        args.manifest,
        args.output
    )

if args.ctrlfreec_info_dir:
    process_cnv_info(
        args.ctrlfreec_info_dir,
        args.data_config, 
        args.manifest,
        args.output
    )

if args.ctrlfreec_bamseg_dir:
    process_seg(
        args.ctrlfreec_bamseg_dir,
        args.manifest,
        args.data_config, 
        args.output
    )

if args.rsem_gene_dir:
    process_rsem(
        args.rsem_gene_dir, 
        args.manifest,
        args.output
    )

if args.fusion_dir:
    process_fusion(
        args.fusion_dir,
        args.manifest,
        args.output
    )

