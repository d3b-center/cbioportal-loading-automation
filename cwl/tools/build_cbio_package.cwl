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
      merged_file="${
        var arr = [];
        for (var i=0; i<inputs.merged_files.length; i++)
            arr = arr.concat(inputs.merged_files[i].path)
        return (arr.join(' '))
      }"

      merged_clinical="${
        var arr = [];
        for (var i=0; i<inputs.clinical_files.length; i++)
            arr = arr.concat(inputs.clinical_files[i].path)
        return (arr.join(' '))
      }"

      mkdir ./merged ./clinical

      mv $merged_file ./merged && mv $merged_clinical ./clinical

      python3 06.build_cbio_package.py
      -c study_case_meta_config.json
      -d default_config.json 
      -s $(inputs.study_info.path)
      -merged_file_dir ./merged
      -clinical_file_dir ./clinical
      -o $(inputs.output.path)
inputs:
  study_info: File
  merged_files: { type: 'File[]' }
  clinical_files: { type: 'File[]' }
  output: {type: Directory}

outputs:
  outputs:
    type: Directory
    outputBinding:
      glob: 'results'