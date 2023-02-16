cwlVersion: v1.0
class: Workflow
id: generate-cbio-file-wf
requirements:
  - class: MultipleInputFeatureRequirement
  - class: SubworkflowFeatureRequirement
  - class: ScatterFeatureRequirement
inputs:
  study_info: File
  cbio_etl_file: File
  seq_info: File
  cnv_seg: { type: 'File[]?' }
  maf_files: { type: 'File[]?' }
  rsem_gene: { type: 'File[]?' }
  fusion: { type: 'File[]?' }

outputs:
  outputs: { type: "Directory", outputSource: generate_cbio_file/outputs}


steps:
  mkdirs:
    run: tools/mkdir.cwl
    in: []
    out: [mkdirs_out]
    
  generate_cbio_file:
    run: tools/generate_cbio_file.cwl
    in:
      study_info: study_info
      cbio_etl_file: cbio_etl_file
      seq_info: seq_info
      cnv_seg: cnv_seg
      maf_files: maf_files
      rsem_gene: rsem_gene
      fusion: fusion
      output: mkdirs/mkdirs_out
    out: [outputs]

$namespaces:
  sbg: https://sevenbridges.com
hints:
  - class: 'sbg:maxNumberOfParallelInstances'
    value: 4
  - class: 'https://sevenbridges.comAWSInstanceType'
    value: c5.24xlarge;ebs-gp2;1024
