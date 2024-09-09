#!/bin/bash

# Run this once per measurement node, to capture a dns resolution that may be specific to the location

echo "Creating list of targets in qscanner format"
python create_list.py input-targets intargets
echo "resolving A record"
python add-ip-addr.py intargets targets
