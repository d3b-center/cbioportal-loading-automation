import sevenbridges as sbg
import argparse
from sevenbridges.http.error_handlers import rate_limit_sleeper, maintenance_sleeper
import time

parser = argparse.ArgumentParser()
parser.add_argument("-pjt_id", required=True)
parser.add_argument("-input_list", required=True)
args = parser.parse_args()

c = sbg.Config(profile='turbo')
api = sbg.Api(config=c, error_handlers=[rate_limit_sleeper, maintenance_sleeper])

project_id = args.pjt_id
input_list= args.input_list

f = open (input_list)

exports = []
my_project = api.projects.get(id= project_id)

for line in f.readlines():
    line = line.strip("\n")
    line = line.split("\t")
    file_id = line[8]
    file_name = line[9]
    s3_path = line[-1]
    bucket_location = s3_path.replace("s3://cds-246-phs002517-p30-fy20/kf-study-us-east-1-prd-sd-bhjxbdqk/","")
    bucket_location = bucket_location.replace("s3://cds-246-phs002517-sequencefiles-p30-fy20/kf-study-us-east-1-prd-sd-8y99qzjj/","")
    bucket_location = bucket_location.replace("s3://cds-246-phs002517-sequencefiles-p30-fy20/kf-study-us-east-1-prd-sd-bhjxbdqk/","")
    bucket_location = bucket_location.replace("s3://cds-246-phs002517-sequencefiles-p30-fy20/kf-study-us-east-1-prd-sd-m3dbxd12/","")
    bucket_location = bucket_location.replace("s3://kf-study-us-east-1-prd-sd-8y99qzjj/","")
    bucket_location = bucket_location.replace("s3://kf-study-us-east-1-prd-sd-dypmehhf/","")
    volume_name = line[-2]
    if s3_path == 's3_path':
        continue
    if volume_name == '' or volume_name == 'None':
        my_file = api.files.get(file_id)
        new_file = my_file.copy(project=project_id)
    else:
        export = api.imports.submit_import(volume=volume_name, project=my_project, location=bucket_location)
        exports.append(export)

num_exports = len(exports)
done = False
while not done:
      done_len = 0
      for e in exports:
             if e.reload().state in ("COMPLETED", "FAILED"):
                    done_len += 1
             else:
                 time.sleep(5)
      if done_len == num_exports:
             done = True