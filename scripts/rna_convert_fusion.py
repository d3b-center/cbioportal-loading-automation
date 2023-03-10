#!/usr/bin/env python3

import sys
import argparse
import os
import pandas as pd
import numpy as np
import re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert openPBTA fusion table OR list of annofuse files to cbio format."
    )
    parser.add_argument(
        "-t",
        "--table",
        action="store",
        dest="table",
        help="Table with cbio project, kf bs ids, cbio IDs, and file names",
    )
    parser.add_argument(
        "-f",
        "--fusion-results",
        action="store",
        dest="fusion_results",
        help="openPBTA fusion file OR annoFuse results dir",
    )
    parser.add_argument(
        "-m",
        "--mode",
        action="store",
        dest="mode",
        help="describe source, pbta or annofuse",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--center-file",
        action="store",
        dest="sq_file",
        help="File with BS IDs and sequencing centers. Should have headered columns: BS_ID\tSQ_Value",
    )
    parser.add_argument(
        "-o",
        "--out-dir",
        action="store",
        dest="outdir",
        help="Result output dir.",
    )
    args = parser.parse_args()
    if args.mode != "pbta" and args.mode != "annofuse":
        sys.stderr.write(
            "-m mode argument must be one of pbta or annofuse. It is case sensitive. You put "
            + args.mode
            + "\n"
        )
        exit(1)

    def init_cbio_master(fusion_results, mode, rna_metadata):
        if mode == "pbta":
            fusion_data = pd.read_csv(fusion_results, sep="\t")
            return fusion_data[
                ["Gene1A", "Sample", "FusionName", "CalledBy", "Fusion_Type"]
            ]
        else:
            flist = rna_metadata.File_Name
            frame_list = []
            # concat annofuse file, rename Sample Column according to BS ID for later merge with SQ file
            for i in range(0, len(flist), 1):
                ann_file = pd.read_csv(fusion_results + "/" + flist[i], sep="\t")
                ann_file = ann_file.assign(Sample=rna_metadata.at[i, "Sample"])
                frame_list.append(ann_file)
            concat_frame = pd.concat(frame_list)
            del frame_list
            fusion_data = concat_frame[
                ["Gene1A", "Sample", "FusionName", "Caller", "Fusion_Type"]
            ]
            del concat_frame
            # Input has one per caller, but may exists multiple times. Collapse to avoid that
            fusion_data = (
                fusion_data.groupby(["Gene1A", "Sample", "FusionName", "Fusion_Type"])[
                    "Caller"
                ].unique()
                .apply(", ".join)
                .reset_index()
            )
            fusion_data["Caller"] = fusion_data["Caller"].str.upper()
            return fusion_data

    out_dir = args.outdir + '/merged_fusion/'
    try:
        os.makedirs(out_dir)
    except:
        sys.stderr.write("output dir already exists\n")
        sys.stderr.flush()

    # deal only with RNA metadata
    r_ext = "rsem"  # openPBTA data would cross-reference with expression results otherwise...
    sq_info = pd.read_csv(args.sq_file, sep="\t")
    all_file_meta = pd.read_csv(args.table, sep="\t")
    if args.mode == "annofuse":
        r_ext = "fusion"
    rna_subset = all_file_meta.loc[all_file_meta["File_Type"] == r_ext]
    # reset index so that references work later while iterating
    rna_subset = rna_subset.reset_index(drop=True)
    rna_subset.rename(columns={"T_CL_BS_ID": "Sample"}, inplace=True)
    project_list = rna_subset.Cbio_project.unique()
    cbio_master = init_cbio_master(args.fusion_results, args.mode, rna_subset)
    rna_subset.set_index("Sample", inplace=True)
    # Get relevant columns
    cbio_master.set_index("Sample", inplace=True)
    sq_info.rename(columns={"BS_ID": "Sample"}, inplace=True)
    sq_info.set_index("Sample", inplace=True)
    # get cbio IDs and seq center
    cbio_master = pd.merge(
        cbio_master, rna_subset[["Cbio_Tumor_Name"]], on="Sample", how="inner"
    )
    cbio_master = pd.merge(cbio_master, sq_info[["SQ_Value"]], on="Sample", how="inner")
    # drop bs ids
    cbio_master.reset_index(inplace=True)
    cbio_master.drop("Sample", axis=1, inplace=True)
    if args.mode == "pbta":
        cbio_master.rename(
            columns={
                "Gene1A": "Hugo_Symbol",
                "FusionName": "Fusion",
                "CalledBy": "Method",
                "Fusion_Type": "Frame",
                "Cbio_Tumor_Name": "Tumor_Sample_Barcode",
                "SQ_Value": "Center",
            },
            inplace=True,
        )
    else:
        cbio_master.rename(
            columns={
                "Gene1A": "Hugo_Symbol",
                "FusionName": "Fusion",
                "Caller": "Method",
                "Fusion_Type": "Frame",
                "Cbio_Tumor_Name": "Tumor_Sample_Barcode",
                "SQ_Value": "Center",
            },
            inplace=True,
        )

    cbio_master["DNA_support"] = "no"
    cbio_master["RNA_support"] = "yes"
    # create blank entrez ID column so that 3' gene names can be searched
    cbio_master["Entrez_Gene_Id"] = ""
    # Reorder table
    order_list = [
        "Hugo_Symbol",
        "Entrez_Gene_Id",
        "Center",
        "Tumor_Sample_Barcode",
        "Fusion",
        "DNA_support",
        "RNA_support",
        "Method",
        "Frame",
    ]
    cbio_master = cbio_master[order_list]
    # drop dupes as chrom coords not used yet
    cbio_master.drop_duplicates(subset=None, keep='first', inplace=True)
    cbio_master.set_index("Hugo_Symbol", inplace=True)
    for project in project_list:
        sub_sample_list = list(
            rna_subset.loc[rna_subset["Cbio_project"] == project, "Cbio_Tumor_Name"]
        )
        fus_fname = out_dir + project + ".fusions.txt"
        fus_file = open(fus_fname, "w")
        fus_tbl = cbio_master[cbio_master.Tumor_Sample_Barcode.isin(sub_sample_list)]
        fus_tbl.reset_index(inplace=True)
        fus_tbl.fillna("NA", inplace=True)
        fus_head = "\t".join(fus_tbl.columns) + "\n"
        fus_file.write(fus_head)
        fus_data = list(fus_tbl.values)
        # "hack" to allow 3' end of fusion to be searched
        for data in fus_data:
            a, b = data[4].split('--')
            # replace `--` with `-` in fusion names for proper cBio parsing
            data[4] = data[4].replace('--', '-') 
            fus_file.write("\t".join(data) + "\n")
            if a != b:
                data[0] = b
                fus_file.write("\t".join(data) + "\n")
        fus_file.close()
