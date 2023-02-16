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
  tar_ctrlfreec_pval: { type: 'File' }
  tar_ctrlfreec_info: { type: 'File' }

outputs:
  outputs: { type: "Directory", outputSource: generate_cbio_cnv/outputs}


steps:
  mkdirs:
    run: tools/mkdir.cwl
    in: []
    out: [mkdirs_out]
    
  untar_pval:
    run: tools/sbg-decompressor-cnv.cwl
    in:
      input_archive_file: tar_ctrlfreec_pval
    out: [output_cnv]
    
  untar_info:
    run: tools/sbg-decompressor-cnv.cwl
    in:
      input_archive_file: tar_ctrlfreec_info
    out: [output_cnv]
    
  generate_cbio_cnv:
    run: tools/generate_cbio_cnv.cwl
    in:
      study_info: study_info
      cbio_etl_file: cbio_etl_file
      seq_info: seq_info
      ctrlfreec_pval: untar_pval/output_cnv
      ctrlfreec_info: untar_info/output_cnv
      output: mkdirs/mkdirs_out
    out: [outputs]

$namespaces:
  sbg: https://sevenbridges.com
hints:
  - class: 'sbg:maxNumberOfParallelInstances'
    value: 4
  - class: 'https://sevenbridges.comAWSInstanceType'
    value: c5.24xlarge;ebs-gp2;1024
