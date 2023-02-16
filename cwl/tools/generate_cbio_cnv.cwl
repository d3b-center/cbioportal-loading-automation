class: CommandLineTool
cwlVersion: v1.0
id: build_cbio_package
requirements:
  - class: ShellCommandRequirement
  - class: DockerRequirement
    dockerPull: 'xiaoyan0106/pedcbioportal:latest'
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
    - entry: $(inputs.output)
      writable: true
baseCommand: [cd /pedcbioportal && ]
arguments:
  - position: 0
    shellQuote: false
    valueFrom: >-
      python 05.generate_merged_cnv_file.py
      -m  $(inputs.cbio_etl_file.path) 
      -d default_config.json 
      -s $(inputs.study_info.path)
      -seq $(inputs.seq_info.path)
      -ctrlfreec_pval_dir $(inputs.ctrlfreec_pval[0].dirname)
      -ctrlfreec_info_dir $(inputs.ctrlfreec_info[0].dirname)
      -output $(inputs.output.path)
inputs:
  study_info: File
  cbio_etl_file: File
  seq_info: File
  ctrlfreec_pval: {type: "File[]"}
  ctrlfreec_info: {type: "File[]"}
  output: {type: Directory}


outputs:
  outputs:
    type: Directory
    outputBinding:
      glob: 'results'