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


def process_cnv(cnv_pval, cnv_info, data_config_file, manifest, outputdir):
    """
    Add gene info to CNV calls, merge into table, and create GISTIC-style output
    """
    gene_annot_cmd = "{}cnv_1_genome2gene.py -c {} -f {} -o {}".format(
        script_dir, cnv_pval, data_config_file, outputdir
    )
    subprocess.call(gene_annot_cmd, shell=True)

    merge_gene_cmd = "{}cnv_2_merge.py -t {}  -f {} -i {} -o {}".format(
        script_dir, manifest, data_config_file, cnv_info, outputdir
    )
    subprocess.call(merge_gene_cmd, shell=True)

    gistic_style_cmd = "{}cnv_3_gistic_style.py -t {} -j {} -i {} -o {}".format(
        script_dir, manifest, data_config_file, cnv_info, outputdir
    )
    subprocess.call(gistic_style_cmd, shell=True)


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
    print(merge_gene_cmd)
    subprocess.call(merge_gene_cmd, shell=True)

    gistic_style_cmd = "{}cnv_3_gistic_style.py -t {} -j {} -i {} -o {}".format(
        script_dir, manifest, data_config_file, cnv_info, outputdir
    )
    print(gistic_style_cmd)
    subprocess.call(gistic_style_cmd, shell=True)

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
    "-ctrlfreec_pval_dir",
    action="store",
    help="ctrlfreec pval files",
)
parser.add_argument(
    "-ctrlfreec_info_dir",
    action="store",
    help="ctrlfreec info files dir",
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


process_cnv(
    args.ctrlfreec_pval_dir,
    args.ctrlfreec_info_dir,
    args.data_config, 
    args.manifest,
    args.output
)