#!/bin/bash

./zdns alookup --ipv4-lookup --name-servers 8.8.8.8 --result-verbosity short --input-file <(cut -d , -f 2 $1) --output-file dns-resolution.json --include-fields ttl
jq "[.data.ipv4_addresses[0], .name] | @csv" -r dns-resolution.json >$2
