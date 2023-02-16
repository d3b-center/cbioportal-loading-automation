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
      python 05.generate_genomics_cbio_file.py 
      -m  $(inputs.cbio_etl_file.path) 
      -d default_config.json 
      -s $(inputs.study_info.path)
      -seq $(inputs.seq_info.path)
      ${
        if (inputs.maf_files != null){
          return "-maf_dir " + inputs.maf_files[0].dirname;
        }
        else{
            return " "
        }
      }
      ${
        if (inputs.rsem_gene != null){
          return "-rsem_gene_dir " + inputs.rsem_gene[0].dirname;
        }
        else {
            return " "
        }
      }
      ${
        if (inputs.fusion != null){
          return "-fusion_dir " + inputs.fusion[0].dirname;
        } else {
            return " "
        }
      }
      ${
        if (inputs.cnv_seg != null){
          return "-ctrlfreec_bamseg_dir " + inputs.cnv_seg[0].dirname;
        } else {
            return " "
        }
      }
      -output $(inputs.output.path)
inputs:
  study_info: File
  cbio_etl_file: File
  seq_info: File
  cnv_seg: { type: 'File[]?' }
  maf_files: { type: 'File[]?' }
  rsem_gene: { type: 'File[]?' }
  fusion: { type: 'File[]?' }
  output: {type: Directory}


outputs:
  outputs:
    type: Directory
    outputBinding:
      glob: 'results'