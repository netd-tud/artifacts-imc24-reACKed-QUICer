### PCAP processing for verification

PCAPS:=$(shell ls */*/*/sim/*.pcap | sort)
PCAPS_CSV:=$(subst .pcap,.pcap.csv,$(PCAPS))

### Existing extracted files
FIND_QLOG_EXTRACTED:=$(shell ls */*/*/client/qlog/*.qlog.extracted | sort)
### QLOG in incorrect folder
CLIENT_QLOG_OTHER_FOLDER:=$(shell ls  */*/*/client/*.qlog | sort )
CLIENT_QLOG_OTHER_MOVED:=$(subst /client/,/client/qlog/,$(CLIENT_QLOG_OTHER_FOLDER))

### QLOG with different file extensions
CLIENT_SQLOG:=$(shell ls */*/*/client/qlog/*.sqlog | sort)
CLIENT_SQLOG_RENAMED:=$(patsubst %.sqlog,%.qlog,$(CLIENT_SQLOG))

### Chrome netlog to qlog
CLIENT_NETLOG=$(shell ls */*/*/client/chrome.json | sort)
CLIENT_NETLOG_CONVERTED=$(subst .json,.qlog,$(subst /client/,/client/qlog/,$(CLIENT_NETLOG)))


### All qlog files
CLIENT_QLOG:=$(shell ls */*/*/client/qlog/*.qlog | sort)
CLIENT_QLOG_EXTRACTED:=$(subst .qlog,.qlog.extracted,$(CLIENT_QLOG) $(CLIENT_QLOG_OTHER_MOVED) $(CLIENT_SQLOG_RENAMED)) 

SERVER=quic-go-instant-ack

echo: 
	echo $(PCAPS)
	echo $(CLIENT_QLOG)
	echo $(CLIENT_QLOG_EXTRACTED)


all: tshark_pcaps qlog_extraction

clean: clean_tshark_pcaps clean_qlog_extracted

clean_tshark_pcaps:
	rm -f $(PCAPS_CSV)
clean_qlog_extraction:
	rm -f $(FIND_QLOG_EXTRACTED)

debug: debug_pcaps debug_pcaps_csv debug_client_qlog debug_client_qlog_extracted debug_client_sqlog_renamed
debug_pcaps:
	echo ########## PCAPS ###########
	echo $(PCAPS)
debug_pcaps_csv:
	echo ########## PCAPS_CSV ###########
	echo $(PCAPS_CSV)
debug_client_qlog:
	echo ########## QLOG ###########
	echo $(CLIENT_QLOG)
debug_client_qlog_extracted:
	echo ########## QLOG_EXTRACTED ###########
	echo $(CLIENT_QLOG_EXTRACTED)
debug_client_sqlog_renamed:
	echo ########## QLOG_RENAMED ##########
	echo $(CLIENT_SQLOG_RENAMED)

qlog_extraction: netlog_to_qlog qlog_move $(CLIENT_QLOG_EXTRACTED) 

qlog_move: $(CLIENT_SQLOG_RENAMED) $(CLIENT_QLOG_OTHER_MOVED)

%.qlog: %.sqlog
	mv "$<" "$@"

netlog_to_qlog: $(CLIENT_NETLOG_CONVERTED)

$(CLIENT_NETLOG_CONVERTED): SOURCE=$(subst .qlog,.json,$(subst /client/qlog/,/client/,$@))
$(CLIENT_NETLOG_CONVERTED): QLOG_DIR=$(subst chrome.qlog,,$@)
$(CLIENT_NETLOG_CONVERTED): 
	-docker run --rm --mount "type=bind,\"source=$${PWD}/$(QLOG_DIR)\",destination=/data" --mount "type=bind,\"source=$${PWD}/$(SOURCE)\",destination=/data/netlog.netlog" netlog-to-qlog

$(CLIENT_QLOG_OTHER_MOVED): 
	mv "$(subst /client/qlog/,/client/,$@)" "$@"

tshark_pcaps: $(PCAPS_CSV)

# convert to csv with tshark
%.pcap.csv: keyfile=$(subst sim/trace_node_right.pcap,client/keys.log,$(subst sim/trace_node_left.pcap,server/keys.log,$<))
%.pcap.csv: %.pcap
	tshark -2 -d udp.port==443,quic -Y "quic" -r "$<" -T fields \
		-o tls.keylog_file:$(keyfile)\
	 -e _ws.col.Time -t ud \
	 -e ip.src -e ip.dst \
		 -e ipv6.src -e ipv6.dst \
		 -e ip.len \
		 -e ipv6.plen \
		 -e udp.srcport -e udp.dstport \
		 -e quic.long.packet_type \
		 -e quic.long.packet_type_v2 \
		 -e quic.header_form \
		 -e quic.scid -e quic.dcid \
		 -e quic.packet_number \
		 -e quic.frame \
		 -e quic.ack.largest_acknowledged \
		 -e quic.ack.ack_delay \
		 -e quic.version -e quic.token_length \
		 -e quic.frame_type -e tls.handshake.type -e tls.handshake.extensions_server_name \
		 -e quic.retry_token \
		 -e quic.decryption_failed \
		 -e _ws.expert \
	 -E separator=\| > "$@.tmp"
	mv "$@.tmp" "$@"
	rm -f "$@.tmp"

# Filter for specific events
EVENT_FILTER=.name == "recovery:metric_update" or .name == "recovery:metrics_updated" or .name == "transport:packet_sent" or .name == "transport:packet_received" or .name == "recovery:congestion_state_updated" or .name == "transport:parameters_set" or .name == "security:key_updated" or .name == "security:key_discarded" or .name == "recovery:loss_timer_updated" or .name == "recovery:ecn_state_updated" or .name == "connectivity:spin_bit_updated"
# flatten frame information
FRAME_INFO=["frame_type", "length", "id", "offset", "ack_delay", "reset_token", "connection_id", "retire_prior_to", "sequence_number", "acked_ranges", "fin", "stream_id", "maximum", "raw_error_code", "error_code", "error_space", "reason", "token"]
REMAP_FRAMES=map(del(.data.frames) +(.data.frames as $$frames| $(FRAME_INFO) as $$info | reduce ($$info|.[]) as $$k ({}; . +{"frame_\($$k)": [($$frames|.[]?[$$k]|tostring|sub("null"; ""; "g"))] | join(",")})))
# Flatten remaining information
FLATTEN_REMAINDER=map([leaf_paths as $$path | { "key": $$path | join("_"), "value": getpath($$path)}] | from_entries)

$(SERVER)_quiche/%.qlog.extracted: $(SERVER)_quiche/%.qlog
	cat "$<"  | jq --slurp '[{meta: .[0], events: .[1:]}] | map(.events[] + del(.events)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2

# Same Qlog format
$(SERVER)_quic-go/%.qlog.extracted: $(SERVER)_quic-go/%.qlog
	cat "$<" | jq --slurp '.' |jq 'map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2
$(SERVER)_go-x-net/%.qlog.extracted: $(SERVER)_go-x-net/%.qlog
	cat "$<" | jq --slurp '.' |jq 'map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2

# Same Qlog format
$(SERVER)_neqo/%.qlog.extracted: $(SERVER)_neqo/%.qlog
	cat "$<"  | jq '.traces | to_entries | map_values(.value + {index: .key}) | map(.events[] + [del(.events)]) | map(.) | map({time: .[0], name: (.[1]+":"+.[2]), data: .[3]} + .[4])| map(.data.header.packet_type=.data.packet_type | del(.data.packet_type)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2
$(SERVER)_picoquic/%.qlog.extracted: $(SERVER)_picoquic/%.qlog
	cat "$<"  | jq '.traces | to_entries | map_values(.value + {index: .key}) | map(.events[] + [del(.events)]) | map(.) | map({time: .[0], name: (.[1]+":"+.[2]), data: .[3]} + .[4])| map(.data.header.packet_type=.data.packet_type | del(.data.packet_type)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2
$(SERVER)_mvfst/%.qlog.extracted: $(SERVER)_mvfst/%.qlog
	cat "$<"  | jq '.traces | to_entries | map_values(.value + {index: .key}) | map(.events[] + [del(.events)]) | map(.) | map({time: .[0], name: (.[1]+":"+.[2]), data: .[3]} + .[4])| map(.data.header.packet_type=.data.packet_type | del(.data.packet_type)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2
$(SERVER)_chrome/%.qlog.extracted: $(SERVER)_chrome/%.qlog
	cat "$<"  | jq '.traces | to_entries | map_values(.value + {index: .key}) | map(.events[] + [del(.events)]) | map(.) | map({time: .[0], name: (.[1]+":"+.[2]), data: .[3]} + .[4])| map(select($(EVENT_FILTER))) | map(.data.frames[]?.acked_ranges[]?[]? |= tonumber  )| $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2

$(SERVER)_ngtcp2/%.qlog.extracted: $(SERVER)_ngtcp2/%.qlog
	cat "$<"  | jq --slurp '[{meta: .[0], events: .[1:]}] | map(.events[] + (.meta)) | map(.trace + del(.trace)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2

# aioquic
%.qlog.extracted: %.qlog
	cat "$<"  | jq '.traces | to_entries | map_values(.value + {index: .key}) | map(.events[] + del(.events)) | map(select($(EVENT_FILTER))) | $(REMAP_FRAMES) | $(FLATTEN_REMAINDER)' -c > $@.temp ; 
	add-pto-info -i $@.temp -o $@.temp2
	# Fix edge case where uint64 maximum value is interpreted as float64
	sed 's/18446744073709552000/18446744073709551615/g' $@.temp2 > $@
	rm -f $@.temp $@.temp2
