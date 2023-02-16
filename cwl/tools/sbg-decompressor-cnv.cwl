cwlVersion: 'sbg:draft-2'
class: CommandLineTool
$namespaces:
  sbg: 'https://sevenbridges.com'
id: sbg-decompressor-cnv
description: >-
  SBG Decompressor performs the extraction of the input archive file. 

  Supported formats are:

  1. TAR

  2. TAR.GZ (TGZ)

  3. TAR.BZ2 (TBZ2)

  4. GZ

  5. BZ2

  6. ZIP


  If the archive contains folder structure, it is going to be flatten because
  CWL doesn't support folders at the moment. In that case the output would
  contain all the files from all the folders from the archive.
baseCommand:
  - class: Expression
    engine: '#cwl-js-engine'
    script: |-
      {
        var available_ext = ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'gz', 'bz2', 'zip']
        var file = $job.inputs.input_archive_file.path.toLowerCase()
        if (available_ext.indexOf(file.split('.').pop()) > -1) { 
          return 'python /opt/sbg_decompressor.py'
        }
      }
inputs:
  - type:
      - File
    inputBinding:
      position: 0
      separate: true
      valueFrom:
        class: Expression
        engine: '#cwl-js-engine'
        script: "{\n  var available_ext = ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'gz', 'bz2', 'zip']\n  var file = $job.inputs.input_archive_file.path.toLowerCase()\n  if (available_ext.indexOf(file.split('.').pop()) > -1) { \n  \treturn '--input_archive_file ' + $job.inputs.input_archive_file.path\n  }\n}"
      'sbg:cmdInclude': true
      secondaryFiles: []
    label: Input archive file
    description: The input archive file to be unpacked.
    'sbg:fileTypes': 'TAR, TAR.GZ, TGZ, TAR.BZ2, TBZ2, GZ, BZ2, ZIP'
    id: '#input_archive_file'
outputs:
  - type:
      - type: array
        items: File
    description: Unpacked files from the input archive.
    outputBinding:
      glob: decompressed_files/*
      'sbg:inheritMetadataFrom': '#input_archive_file'
    id: '#output_cnv'
requirements:
  - class: ExpressionEngineRequirement
    id: '#cwl-js-engine'
    requirements:
      - class: DockerRequirement
        dockerPull: rabix/js-engine
hints:
  - class: 'sbg:CPURequirement'
    value: 1
  - class: 'sbg:MemRequirement'
    value: 1000
  - class: DockerRequirement
    dockerImageId: 58b79c627f95
    dockerPull: 'images.sbgenomics.com/markop/sbg-decompressor:1.0'
arguments:
  - position: 1
    separate: false
    valueFrom:
      class: Expression
      engine: '#cwl-js-engine'
      script: "{\n  var available_ext = ['tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'gz', 'bz2', 'zip']\n  var file = $job.inputs.input_archive_file.path.toLowerCase()\n  if (available_ext.indexOf(file.split('.').pop()) > -1) { \n  \treturn \"; find ./decompressed_files -mindepth 2 -type f -exec mv -i '{}' ./decompressed_files ';'; mkdir ./decompressed_files/dummy_to_delete ;rm -R -- ./decompressed_files/*/ \"\n  }\n}"
'sbg:appVersion':
  - 'sbg:draft-2'
'sbg:categories':
  - SBGTools
  - Utilities
  - File Format Conversion
'sbg:cmdPreview': >-
  python /opt/sbg_decompressor.py  --input_archive_file input_file.tar ; find
  ./decompressed_files -mindepth 2 -type f -exec mv -i '{}' ./decompressed_files
  ';'; mkdir ./decompressed_files/dummy_to_delete ;rm -R --
  ./decompressed_files/*/
'sbg:content_hash': a4782f78b420bfe9a3378e9c08ffc669d473f468de9ce6342183c46df5ff7172d
'sbg:contributors':
  - xiaoyan-huang
'sbg:copyOf': admin/sbg-public-data/sbg-decompressor-1-0/8
'sbg:createdBy': xiaoyan-huang
'sbg:createdOn': 1658756318
'sbg:expand_workflow': false
'sbg:homepage': 'https://igor.sbgenomics.com/'
'sbg:id': xiaoyan-huang/clinical-report-dev/sbg-decompressor-1-0/0
'sbg:image_url': null
'sbg:job':
  allocatedResources:
    cpu: 1
    mem: 1000
  inputs:
    input_archive_file:
      class: File
      path: input_file.tar
      secondaryFiles: []
      size: 0

