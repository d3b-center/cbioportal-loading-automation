#!/usr/bin/env python3
import sys
import os
from os.path import isfile, join
import argparse
import json
import subprocess
import concurrent.futures
parser = argparse.ArgumentParser()
parser.add_argument(
    "-r",
    action="store",
    dest="ticket_repo",
    help="ticket repo, e.g. HuangXiaoyan0106/test-cbioportal;",
)
parser.add_argument(
    "-o",
    action="store",
    dest="output_dir",
    help="output folder;",
)
args = parser.parse_args()

out_dir = args.output_dir
repo = args.ticket_repo


open_tickets = "ticket_number.txt"
list_tickets_cmd = (
    "gh issue list \
        --repo " + repo + " --state open   \
        --assignee HuangXiaoyan0106 \
        --label automation \
        --label pedcbioportal \
        --json number \
        --jq 'map(\"\(.number)\")[]' > " + out_dir + '/' +open_tickets
)
subprocess.call(list_tickets_cmd, shell=True)

if isfile(join(out_dir, open_tickets)):
    file = open(open_tickets)
    for f in file:
        number = f.strip("\n")
        out_name = "t" + number + "_ticket_contents.txt"
        ticket_body_cmd = (
            "gh issue view " + str(number) + \
             " --repo " + repo + " --json body --jq '(.body)' |tr -d $'\\r' |sed '/^$/d' > " + out_dir + '/' +out_name
        )
        subprocess.call(ticket_body_cmd, shell=True)