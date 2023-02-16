class: CommandLineTool
cwlVersion: v1.0
id: mkdir_wf
requirements:
  - class: ShellCommandRequirement
  - class: DockerRequirement
    dockerPull: 'xiaoyan0106/pedcbioportal:latest'
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
baseCommand: []
arguments:
  - position: 0
    shellQuote: false
    valueFrom: >-
      mkdir -p results
inputs: []

outputs:
  mkdirs_out:
    type: Directory
    outputBinding:
      glob: results