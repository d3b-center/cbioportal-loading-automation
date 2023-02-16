import psycopg2
from psycopg2 import sql
import pandas as pd
import pandas.io.sql as sqlio
import os
import json
import argparse

### connect to DW
hostname = 'd3b-warehouse-aurora.cluster-cxxdzxepyea2.us-east-1.rds.amazonaws.com'
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
database = 'postgres'
conn = psycopg2.connect(dbname=database, user=username, password=password, host=hostname)
db_cur = conn.cursor()

def generic_pull(db_cur, tbl_name):
    """
    Simple helper function for SELECT * database calls
    """
    if '.' not in tbl_name:
        tbl_sql = sql.SQL('SELECT * FROM {};').format(sql.Identifier(tbl_name))
    else:
        (schema, table) = tbl_name.split('.')
        tbl_sql = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(schema), sql.Identifier(table))

    db_cur.execute(tbl_sql)
    rows = db_cur.fetchall()
    colnames = [desc[0] for desc in db_cur.description]
    return (rows, colnames)

def generic_print(out_file, rows, colnames):
    """
    Simple helper function to print results to existing file handle as tsv
    """
    out_file.write("\t".join(colnames) + "\n")
    for row in rows:
        # convert None to empty str
        new_row = [str(i or '') for i in row]
        out_file.write("\t".join(new_row) + "\n")
    out_file.close()
    return 0

def get_data_clinical(study_name, default_data, prefix):
    """
    Depending on the prefix of patient or sample, will pull from related tables,
    only use related header info present in table, and print the combined results.
    This is because cBioportal flat file had 5 header rows and it can vary between projects which are used
    """

    schema = 'prod_cbio'
    tbl_name = study_name + '_data_clinical_' + prefix
    tbl_sql = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(schema), sql.Identifier(tbl_name))

    # get table contents
    db_cur.execute(tbl_sql)
    rows = db_cur.fetchall()
    colnames = [desc[0] for desc in db_cur.description]

    # use table header from colnames, and use to select file header
    head_name = default_data[prefix + '_head']['table']
    # get sample table contents, have to split if format schema.table
    if '.' not in head_name:
        head_sql = sql.SQL('SELECT {} FROM {};').format(sql.SQL(',').join(map(sql.Identifier, colnames)), sql.Identifier(head_name))
    else:
        (schema, table) = head_name.split('.')
        head_sql = sql.SQL('SELECT {} FROM {}.{};').format(sql.SQL(',').join(map(sql.Identifier, colnames)), sql.Identifier(schema), sql.Identifier(table))
    db_cur.execute(head_sql)
    head = db_cur.fetchall()

    # create output file and combine results for final product
    output_name = study_name + "_data_clinical_" + prefix + ".txt"
    out_file = open(datasheet_dir + "/" + output_name, 'w')
    for row in head:
        out_file.write("\t".join(row) + "\n")
    generic_print(out_file, rows, colnames)
    return 0

def get_cbio(study_name):
    """
    Download cbio_sample and sq_info from DW
    """
    schema = 'prod_cbio'
    ## download cbio sample info
    cbio_name = study_name + '_cbio_sample'
    cbio_sql = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(schema), sql.Identifier(cbio_name))
    db_cur.execute(cbio_sql)
    cbio_rows = db_cur.fetchall()
    cbio_colnames = [desc[0] for desc in db_cur.description]
    cbio_output_name = cbio_name + ".txt"
    cbio_out_file = open(datasheet_dir + "/" + cbio_output_name, 'w')
    generic_print(cbio_out_file, cbio_rows, cbio_colnames)

    ## download genomics etl file
    genomics_name = study_name + '_genomics_etl_file'
    genomics_sql = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(schema), sql.Identifier(genomics_name))
    db_cur.execute(genomics_sql)
    genomics_rows = db_cur.fetchall()
    genomics_colnames = [desc[0] for desc in db_cur.description]
    genomics_output_name = genomics_name + ".txt"
    genomics_out_file = open(datasheet_dir + "/" + genomics_output_name, 'w')
    generic_print(genomics_out_file, genomics_rows, genomics_colnames)

    ## download sequence center info
    sq_name = study_name + '_sq_info_etl_resource'
    sq_sql = sql.SQL('SELECT * FROM {}.{};').format(sql.Identifier(schema), sql.Identifier(sq_name))
    db_cur.execute(sq_sql)
    sq_rows = db_cur.fetchall()
    sq_colnames = [desc[0] for desc in db_cur.description]
    sq_output_name = sq_name + ".txt"
    sq_out_file = open(datasheet_dir + "/" + sq_output_name, 'w')
    generic_print(sq_out_file, sq_rows, sq_colnames)
    
    return 0

def get_manifests(study_data):
    """
    This iterates through the manifests section of the study configure file and grabs and outputs all listed file manifests for ec2 download
    """
    # Just a pointer variable for ease of reading and coding
    manifests = study_data['manifests']
    for manifest in manifests:
        try:
            tbl_name = manifests[manifest]['table']
            file_types = manifests[manifest]['file_type']
            if '.' not in tbl_name:
                manifest_sql = sql.SQL("SELECT * FROM {} WHERE status = 'active' AND file_type in ({});").format(sql.Identifier(tbl_name), sql.SQL(',').join(map(sql.Literal, file_types)))
            else:
                (schema, table) = tbl_name.split('.')
                manifest_sql = sql.SQL("SELECT * FROM {}.{} WHERE status = 'active' AND file_type in ({});").format(sql.Identifier(schema), sql.Identifier(table), sql.SQL(',').join(map(sql.Literal, file_types)))
            db_cur.execute(manifest_sql)
            rows = db_cur.fetchall()
            colnames = [desc[0] for desc in db_cur.description]

            output_name = tbl_name.split('.')[-1] + '.txt'
            out_file = open(datasheet_dir + "/" + output_name, 'w')
            generic_print(out_file, rows, colnames)
        except Exception as e:
            print(e)
            exit(1)
    return 0

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--study-config",
    action="store",
    dest="study_config",
    help="json config file with study information;",
)
parser.add_argument(
    "-c", 
    "--default-config", 
    action="store", 
    dest="default_config", 
    help="default config file",
)
parser.add_argument(
    "-o",
    "--output-dir",
    action="store",
    dest="output_dir",
    help="json config file with study information;",
)
args = parser.parse_args()


with open(args.study_config) as f:
    study_data = json.load(f)
with open(args.default_config) as c:
    default_data = json.load(c)

study_name = study_data["cancer_study_identifier"]
datasheet_dir = args.output_dir
try:
    try:
        os.mkdir(datasheet_dir)
    except Exception as e:
        print(str(e) + ' IGNORE!')
    
    get_data_clinical(study_name, default_data, 'sample')
    get_data_clinical(study_name, default_data, 'patient')
    get_manifests(study_data)
    get_cbio(study_name)

except (Exception, psycopg2.DatabaseError) as error:
    print(error)
    conn.close()
conn.close()