#!/usr/bin/env python3
import sys
import os
from os.path import isfile, join
from fnmatch import fnmatch
import argparse
import pandas as pd
import json
import subprocess
import concurrent.futures
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "-o",
    "--output-dir",
    action="store",
    dest="output_dir",
    help="output folder;",
)
args = parser.parse_args()

out_dir = args.output_dir

study_list = "study_list_to_manifest.csv"
studys= pd.read_csv(study_list,delimiter = ",")

files = [file for file in sorted (os.listdir(out_dir)) if fnmatch(file, "*ticket_contents.txt") if isfile(join(out_dir, file))]

for f in files:
    filne = open(f)
    bonds_tmp = {}
    study_description = groups = short_name = type_of_cancer = reference_genome = display_name = ""
    for line in filne:
        if "Study Description" in line:
            study_description = next(filne).strip("\n")
            if "_No response_" in study_description or study_description == '' or study_description == "\n":
                # print("ERROR: without study description")
                # break
                sys.exit("ERROR: without study description")

        if "Study Display Name" in line:
            display_name = next(filne).strip("\n")
            if "_No response_" in display_name or display_name == '' or display_name == "\n":
                sys.exit("ERROR: without study display name")
                # print("ERROR: without study display name")
                # break

        if "Cancer Study Identifier" in line:
            short_name = next(filne).strip("\n")
            if "_No response_" in short_name or short_name == '' or short_name == "\n":
                sys.exit("ERROR: without short name")
                # print("ERROR: without short name")
                # break

        if "Type of Cancer" in line:
            type_of_cancer = next(filne).strip("\n")
            if "_No response_" in type_of_cancer or type_of_cancer == '' or type_of_cancer == "\n":
                sys.exit("ERROR: without type of cancer")

        if "Reference Genome" in line:
            reference_genome = next(filne).strip("\n")
            if "_No response_" in reference_genome or reference_genome == '' or reference_genome == "\n" or reference_genome == "None":
                sys.exit("ERROR: without reference genome")
                # print("ERROR: without reference genome")
                # break

        if "Study Manifest" in line:
            name = next(filne).strip("\n")
            name = name.replace(" ", "")
            if "," in name:
                list_study_name = name.split(",")
            else:
                list_study_name = [name]

            if "_No response_" in list_study_name or list_study_name == '' or list_study_name == "\n":
                # print("ERROR: without study name")
                # break
                sys.exit("ERROR: without study name")

            for pr_study_name in list_study_name:
                if '.' in pr_study_name:
                    (manifest_schema,manifest_name) = pr_study_name.split(".")
                    
                    study_name = studys.loc[(studys.manifest_name == manifest_name), 'study_name'].values[0]
                    study_id = studys.loc[(studys.manifest_name == manifest_name), 'study_id'].values[0]
                    table = pr_study_name
                else:
                    study_name = pr_study_name
                    try:
                        print(study_name)
                        study_id = studys.loc[(studys.study_name == study_name), 'study_id'].values[0]
                        print(study_id)
                        manifest_schema = studys.loc[(studys.study_name == study_name), 'manifest_schema'].values[0]
                        manifest_name = studys.loc[(studys.study_name == study_name), 'manifest_name'].values[0]
                        table = manifest_schema + '.' + manifest_name
                    except:
                        sys.exit("ERROR: The request manifest is not in the data warehouse")
                study_id = study_id.upper()
                bonds_tmp[study_name] = {"study_id": study_id,"table":table}
            
        if "File Types" in line:
            file_types = next(filne).strip("\n")
            if "_No response_" in file_types or file_types == '' or file_types == "\n" or file_types == "None":
                # print("ERROR: without file types")
                # break
                sys.exit("ERROR: without file types")
            new_file_types = file_types.replace(" ", "").split(",")

        if "Groups" in line:
            groups = next(filne).strip("\n")
            if "_No response_" in groups or groups == '' or groups == "\n" or groups == "None":
                groups = "PUBLIC"
            else:
                groups = groups
    
    final_manifest = {}
    for item in bonds_tmp:
        s_file = bonds_tmp[item]
        s_file.update({"file_type":new_file_types})
        final_manifest[item] = s_file

    dictionary = {
        "description": study_description,
        "groups": groups.upper(),
        "cancer_study_identifier": short_name,
        "type_of_cancer": type_of_cancer,
        "short_name": short_name,
        "reference_genome": reference_genome,
        "display_name": display_name,
        "manifests": final_manifest
    }

    output = f.split("_")[0]
    # Serializing json
    json_object = json.dumps(dictionary, indent=4)

    # Writing to sample.json
    with open(out_dir + '/' +output+"_ticket.json", "w") as outfile:
        outfile.write(json_object)