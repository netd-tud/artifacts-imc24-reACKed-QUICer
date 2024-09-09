#!/bin/bash


IN="$1"
OUT="$2" 
KEYS="$3"

# We force quic evaluation for traffic on port 443.
tshark -2 -d udp.port==443,quic -r "$IN" -T fields \
         -o "tls.keylog_file:$KEYS" \
         -e _ws.col.Time -t ud \
         -e ip.src -e ip.dst \
         -e udp.length -e udp.srcport -e udp.dstport \
         -e quic.version \
         -e quic.long.packet_type \
         -e quic.scid -e quic.dcid \
         -e quic.frame_type -e quic.ack.ack_delay \
         -e quic.ack.ack_range \
         -e quic.ack.first_ack_range \
         -e tls.quic.parameter.ack_delay_exponent \
         -e tls.handshake.type -e tls.handshake.extensions_server_name \
         -e ip.ttl \
         -E separator=\| > "$OUT"

