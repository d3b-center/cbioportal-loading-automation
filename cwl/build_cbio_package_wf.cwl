cwlVersion: v1.0
class: Workflow
id: generate-cbio-file-wf
requirements:
  - class: MultipleInputFeatureRequirement
  - class: SubworkflowFeatureRequirement
  - class: ScatterFeatureRequirement
inputs:
  study_info: File
  merged_files: { type: 'File[]' }
  clinical_files: { type: 'File[]' }

outputs:
  outputs: { type: "Directory", outputSource: build_cbio_package/outputs}


steps:
  mkdirs:
    run: tools/mkdir.cwl
    in: []
    out: [mkdirs_out]
    
  build_cbio_package:
    run: tools/build_cbio_package.cwl
    in:
      study_info: study_info
      merged_files: merged_files
      clinical_files: clinical_files
      output: mkdirs/mkdirs_out
    out: [outputs]

$namespaces:
  sbg: https://sevenbridges.com
hints:
  - class: 'sbg:maxNumberOfParallelInstances'
    value: 4
  - class: 'https://sevenbridges.comAWSInstanceType'
    value: c5.24xlarge;ebs-gp2;1024
