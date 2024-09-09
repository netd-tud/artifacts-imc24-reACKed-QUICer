#!/bin/bash

# Run this once per measurement node, to capture a dns resolution that may be specific to the location

echo "Creating list of targets in qscanner format"
python create_list.py top-1m.csv intargets
echo "resolving A record"
./dns-resolve.sh intargets dns-resolution
echo "merging resolved names into qscanner format"
python inner-join.py dns-resolution intargets targets
