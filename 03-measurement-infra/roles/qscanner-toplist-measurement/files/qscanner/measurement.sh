#!/usr/bin/env bash

sysctl -w net.core.rmem_max=2500000
ulimit -Hn 1000000
ulimit -Sn 1000000

DATE=$(date -Ins)
# Resolve DNS entries
# ./dns-resolve.sh intargets dns-resolution
# Inner join valid results
# python3 inner-join.py dns-resolution intargets targets

PCAP="$(date -Im)-capture.pcap"
touch "$PCAP"
dumpcap -i $1 -w "$PCAP" -f "udp and port 443" &
sleep 3
echo "tcpdump active"

./qscanner -input targets -keylog -http3 -output "data/${DATE}" -bucket-refill-duration 5 -bucket-size 100

echo "terminated qscanner"

sleep 20

echo "cooldown terminated"

kill %1

echo "terminated dumpcap"

mv "${PCAP}" "data/${DATE}/capture.pcap"
cp "targets" "data/${DATE}"

sleep 3

zstd --rm "data/${DATE}/capture.pcap" "data/${DATE}/dns-resolution.json" "data/${DATE}/targets"
zstd --rm data/${DATE}/*.log data/${DATE}/*.csv
