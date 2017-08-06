"""
Concatinates streams of json data, each looking like:
    [
        {json record 1},
        {json record 2},
        ...
        {json record N}
    ]

Usage:
    concat-json.py f1.json f2.json ... jk_json
"""
import sys
import json

json_filenames = sys.argv[1:]
output_json = []

for fname in json_filenames:
    with open(fname) as f:
        output_json.extend(json.load(f))

json.dump(output_json, sys.stdout)
