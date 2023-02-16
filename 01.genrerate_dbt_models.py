import psycopg2
from psycopg2 import sql
import pandas as pd
import pandas.io.sql as sqlio
import os
import argparse
import json
from string import Template

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--study-config",
    action="store",
    dest="study_config",
    help="json config file with study information;",
)
parser.add_argument(
    "-o",
    "--output-dir",
    action="store",
    dest="output_dir",
    help="output folder;",
)
args = parser.parse_args()

with open(args.study_config) as f:
    study_data = json.load(f)

out_dir = args.output_dir
study_tables = []
study_ids = []
cbio_tables = []

study_name = study_data["cancer_study_identifier"]
manifests = study_data["manifests"]
for manifest in manifests:
    cbio_table = manifest + '_cbio_sample'
    cbio_tables.append(cbio_table)

    # get all study master genomics files
    study_table = study_data["manifests"][manifest]["table"]
    (schema,master) = study_table.split(".")
    text = 'from {{ source(\'' + schema + '\',\'' + master + '\') }}'
    study_tables.append(text)

    # get all study ids
    study_id = study_data["manifests"][manifest]["study_id"]
    study_ids.append(study_id)
    
    # get all file types
    file_types = study_data["manifests"][manifest]["file_type"]
    new_file_types = ', '.join(f'\'{w}\'' for w in file_types)
    
    ### generate cbio samples sql
    template_cbio = open("dbt_template/template_cbio_sample.sql",'r')
    cbio_template_data = template_cbio.read()
    cbio_query = Template(cbio_template_data).substitute(
        schema = schema,
        master = master,
        file_types = new_file_types,
    )
    output_name = manifest + '_cbio_sample.sql'
    file = open(out_dir+'/'+output_name,'w+')
    file.write(cbio_query)

unique_study_ids = set(study_ids)
unique_study_ids = filter(None, unique_study_ids)

## generate clinical sample and patient sql
clinical_sql = '{{ config(schema=\'cbio\') }}\n' \
    'with cbio_sample_ids as (\n' + '\n\tunion distinct\n'.join(f'\tselect * from {{{{ ref(\'{w}\') }}}} ' for w in cbio_tables) + '\n),'

### clinical sample
sample_template_cbio = open("dbt_template/template_data_clinical_sample.sql",'r')
sample_template_data = sample_template_cbio.read()
sample_query = Template(sample_template_data).substitute(
    study_id = ', '.join(f'\'{w}\'' for w in unique_study_ids),
)
sample_output = study_name + '_data_clinical_sample.sql'
sample_file = open(out_dir+'/'+sample_output,'w+')
sample_file.write(clinical_sql + '\n\n' + sample_query)

### clinical patient
patient_template_cbio = open("dbt_template/template_data_clinical_patient.sql",'r')
patient_template_data = patient_template_cbio.read()
patient_output = study_name + '_data_clinical_patient.sql'
patient_file = open(out_dir+'/'+patient_output,'w+')
patient_file.write(clinical_sql + '\n\n' + patient_template_data)



## generate genomics etl sql
genomics_sql = '{{ config(schema=\'cbio\') }}\n' \
    'with merged as (\n' + '\n\tunion distinct\n'.join(f'\tselect\n\t\tbiospecimen_id,\n\t\ttumor_id,\n\t\tnormal_id,\n\t\tfile_type,\n\t\tfile_name\n\t{w} ' for w in study_tables) + '\n),'
merged_cbio_sample_ids_sql = 'merged_cbio_sample_ids as (\n' \
     + '\n\tunion distinct\n'.join(f'\tselect * from {{{{ ref(\'{w}\') }}}} ' for w in cbio_tables) + '\n),'

etl_template_cbio = open("dbt_template/template_genomics_etl_file.sql",'r')
etl_template_data = etl_template_cbio.read()
genomic_query = Template(etl_template_data).substitute(
    clinical_sample_name = study_name + '_data_clinical_sample',
    study_name = study_name,
)
etl_output = study_name + '_genomics_etl_file.sql'
etl_file = open(out_dir+'/'+etl_output,'w+')
etl_file.write(genomics_sql + '\n\n' + merged_cbio_sample_ids_sql +'\n' + genomic_query)


## generate sequence info etl sql
sq_sql = '{{ config(schema=\'cbio\') }}\n' \
    'with cbio_sample_ids as (\n' \
     + '\n\tunion distinct\n'.join(f'\tselect * from {{{{ ref(\'{w}\') }}}} ' for w in cbio_tables) + '\n),'
sq_template_cbio = open("dbt_template/template_sq_info_etl_resource.sql",'r')
sq_template_data = sq_template_cbio.read()
sq_query = Template(sq_template_data).substitute(
    clinical_sample_name = study_name + '_data_clinical_sample',
)
sq_output = study_name + '_sq_info_etl_resource.sql'
sq_file = open(out_dir+'/'+sq_output,'w+')
sq_file.write(sq_sql + '\n' +sq_query)

