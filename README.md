# PedCbioPortal Loading Automation
In general, we are creating upload packages converting our data and metadata to satisfy the requirements of PedcBioPortal loading. This process includes generating [dbt models](https://github.com/d3b-center/d3b-dbt-study-transforms/tree/master/models/cbio_metadata) and generating loading package in Cavatica.

# The whole process
The whole process will setup in the Airflow.    
### Generate cbio tables
1. Prepare study info file  
    Example: `example_study_info.json`
2. Generate dbt models  
    This script is only suitable for loading simple data, and complex data (like multiple somatic pairs) need to be re-evaluated. 
    
    Example(`x01_fy16_nbl_maris`):
    ```
    python 01.genrerate_dbt_models.py \
    -s test/test_study_info.json \
    -o test/dbt_model
    ```
    It is based on the template dbt models (`dbt_template/*.sql`) and uses the input study information to generate the test study dbt model.
    ```
    test/dbt_model
    ├── x01_fy16_nbl_maris_cbio_sample.sql
    ├── x01_fy16_nbl_maris_data_clinical_patient.sql
    ├── x01_fy16_nbl_maris_data_clinical_sample.sql
    ├── x01_fy16_nbl_maris_genomics_etl_file.sql
    └── x01_fy16_nbl_maris_sq_info_etl_resource.sql
    ```
3. Create a pull request to the [dbt repo](https://github.com/d3b-center/d3b-dbt-study-transforms/tree/master/models/cbio_metadata). Wait until the PR is merged into the master branch before proceeding to the next step. (**WIP***)

### Perform cavatica task to generate cbio loading packages

4. Pull dbt table from data warehouse.
    ```
    python 03.pull_table_from_dw.py \
    -c default_config.json \
    -s test/test_study_info.json \
    -o test/dw_manifest
    ```
    This will output the cbio table with the correct headers.
    ```
    test/dw_manifest
    ├── sd_dypmehhf-genomics_file_manifest.txt
    ├── x01_fy16_nbl_maris_cbio_sample.txt
    ├── x01_fy16_nbl_maris_data_clinical_patient.txt
    ├── x01_fy16_nbl_maris_data_clinical_sample.txt
    ├── x01_fy16_nbl_maris_genomics_etl_file.txt
    └── x01_fy16_nbl_maris_sq_info_etl_resource.txt

    ```
5. Import genomics files to Cavatica
    ```
    python 04.import_files_cavatica.py -pjt_id -input_list test/dw_manifest/sd_dypmehhf-genomics_file_manifest.txt

    ```
6. Run task to generate loading packages    
    1. Merge rsem, fusion, maf and cnv seg
        - workflow: `cwl/workflow/build_cbio_package_wf.cwl`
        - example: [cavatica task](https://cavatica.sbgenomics.com/u/xiaoyan-huang/pedcbioportal-dev/tasks/7c4bb5a6-9c8e-430f-958b-a3cb533233d1/)
    2. Merge cnv data (controlfreec_info and controlfreec_pvalue)
        - workflow: `cwl/workflow/generate-cbio-cnv-wf.cwl`
        - example: [cavatica task](https://cavatica.sbgenomics.com/u/xiaoyan-huang/pedcbioportal-dev/tasks/f836a543-936e-498c-8c36-a6ceab5a3289/)
    3. build cbio pacakge
        - workflow: `cwl/workflow/build-cbio-package-wf.cwl`
        - example: [cavatica task](https://cavatica.sbgenomics.com/u/xiaoyan-huang/pedcbioportal-dev/tasks/7973f632-6aa1-4360-b1e3-7e11539a6c2d/)
6. Export cbio package files to [s3 bucket](s3://kf-cbioportal-studies/public/)     
    (**WIP***)
7. Run Jenkins job  
    (**WIP***)

### Airflow dags development    
(**WIP***)