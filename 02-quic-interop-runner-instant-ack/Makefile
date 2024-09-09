SHELL:=/bin/bash

comma=,
### LATENCY CONFIGURATION ###
# Channel delay, i.e. RTT = 2*Channel delay.
VERY_LOW_LATENCY=$(shell seq 0.5 0.5 7)
LOW_LATENCY=$(shell seq 7.5 2.5 22.5)
HIGH_LATENCY=$(shell seq 25 5.0 150)
# Subset of representative one way delays
MINI_LATENCIES=0.5 4.5 10.0 50.0 150.0

# Combine all Latencies
LATENCIES=$(VERY_LOW_LATENCY) $(LOW_LATENCY) $(HIGH_LATENCY) 5000.0
# Create alternative targets for pairwise execution
LATENCIES_PAIRS=$(addsuffix -p,$(LATENCIES))
### END LATENCY CONFIGURATION ###

### PARAMETER CONFIGURATION ###
# Most parameters are supposed to be replaced, by `make PARAM=val`
SERVERS=quic-go-instant-ack
CLIENTS=aioquic quic-go neqo ngtcp2 quiche picoquic mvfst
SCENARIOS=goodput,goodputdroplist http3c,http3cdroplist
NO_LOSS_SCENARIO=goodput,http3c
GENERIC_DELAY=0
IACK_DELAY=$(GENERIC_DELAY)
WFC_DELAY=$(GENERIC_DELAY)
CERT_CHAIN=1
TO_CLIENT_DROPS=2 3 4 5 2,3
# Extended set of to client drops not interleaved with default
# TO_CLIENT_DROPS=2,4, 2,5, 3,4, 3,5, 4,5, 2,3,4, 2,3,5, 2,4,5, 3,4,5, 2,3,4,5
TO_CLIENT_DROPS_PAIRS="2 2,3" "2,4 3,5" "4 5" "2 3" "3 4"

TO_SERVER_DROPS=2 2,3 2,3,4 2,3,4,5
# Extende set of to server drops not interleaved with default
# TO_SERVER_DROPS=3 4 5 2,4, 2,5, 3,4, 3,5, 4,5, 2,3,5, 2,4,5, 3,4,5,

FILE_SIZES=10KB
FILE_SIZE=$(word 1,$(FILE_SIZES))
REPETITIONS=100
### END PARAMETER CONFIGURATION ###

### GNU PARALLEL CONFIGURATION ###
SET1=1/172.26.63.201,1/172.26.63.237,1/172.26.63.207,1/172.26.63.213,1/172.26.123.185,1/172.26.63.137,1/172.26.63.140,1/172.26.63.141,1/172.26.63.149,1/172.26.63.154,1/172.26.63.156,1/172.26.63.158,1/172.26.63.165
SET2=1/172.26.123.201,1/172.26.123.202,1/172.26.123.203,1/172.26.123.204,1/172.26.123.205
SSH_LOGIN=$(SET1),$(SET2)
DEFAULT_PARAMS=--sshlogin $(SSH_LOGIN) --workdir /data/quic-interop-runner-instant-ack --bar --resume

### END GNU PARALLEL CONFIGURATION ###

all: clean_jl pairs to_client_loss to_server_loss default_pto cert_size_example all_latencies all_latencies_wo_qlog

all-go-x-net: SCENARIOS=goodput,goodputdroplist
all-go-x-net: CLIENTS=go-x-net
all-go-x-net: NO_LOSS_SCENARIO=goodput
all-go-x-net: clean_jl pairs to_client_loss to_server_loss default_pto cert_size_example all_latencies all_latencies_wo_qlog



clean_jl:
	-rm *.jl

# Large files needs larger storage volume, execute only SET2 with 200GB /data
large_files: SSH_LOGIN=$(SET2)
large_files:
	# We compare the same implementation on the same host with the same packet loss in iack and WFC for all to_server_drops scenarios
	echo "Execute measurement with large_file transfer"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_CLIENT_DROP={4} TO_SERVER_DROP="" FILE_SIZE={5} {1} ENAME=large_file ::: $(MINI_LATENCIES) ::: $(SCENARIOS) ::: $(CLIENTS) ::: 2,3 ::: 10MB

pairs:
	# Special case: We compare loss of different packet loss. They need to execute on the same machine. First loss specifies WFC loss, second loss is IACK loss
	echo "Execute loss of different packets on same nodes"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_CLIENT_DROPS_PAIR="{4}" TO_SERVER_DROP="" FILE_SIZE={5} {1}-p  ::: $(MINI_LATENCIES) ::: $(SCENARIOS) ::: $(CLIENTS) ::: $(TO_CLIENT_DROPS_PAIRS) ::: $(FILE_SIZES)

to_client_loss:
	# We compare the same implementation on the same host with the same packet loss in iack and WFC for all to_server_drops scenarios
	echo "Execute all TO_CLIENT_LOSS emulations"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_CLIENT_DROP={4} TO_SERVER_DROP="" FILE_SIZE={5} {1}  ENAME=to_client_loss ::: $(MINI_LATENCIES) ::: $(SCENARIOS) ::: $(CLIENTS) ::: $(TO_CLIENT_DROPS) ::: $(FILE_SIZES)

to_server_loss:
	echo "Execute all TO_SERVER_LOSS emulations"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_SERVER_DROP={4} TO_CLIENT_DROP="" FILE_SIZE={5} {1} ENAME=to_server_loss  ::: $(MINI_LATENCIES) ::: $(SCENARIOS) ::: $(CLIENTS) ::: $(TO_SERVER_DROPS) ::: $(FILE_SIZES)

all_latencies:
	echo "Execute all latencies no loss"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_SERVER_DROP={4} TO_CLIENT_DROP="" FILE_SIZE={5} {1} ENAME=all_latencies ::: $(LATENCIES) ::: $(NO_LOSS_SCENARIO) ::: $(CLIENTS) :::  ::: $(FILE_SIZES)

# Specific to fixed RTTs
default_pto:
	# Limitation: Only determines default PTO if default PTO < 5000.0 ms; recommend in RFC9002 1000ms
	echo "Execute default PTO determination"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_SERVER_DROP={4} TO_CLIENT_DROP="" FILE_SIZE={5} {1} ENAME=default_pto  ::: 5000.0 ::: $(NO_LOSS_SCENARIO) ::: $(CLIENTS) :::  ::: $(FILE_SIZES)

cert_size_example:
	echo "Execute large certificate without loss"
	parallel $(DEFAULT_PARAMS) --joblog $@.jl $(MAKE) CLIENT={3} SCENARIO={2} TO_SERVER_DROP={4} TO_CLIENT_DROP="" GENERIC_DELAY=200 FILE_SIZE={5} {1} CERT_CHAIN=6 ENAME=certificate  ::: 4.5 ::: $(NO_LOSS_SCENARIO) ::: $(CLIENTS) :::  ::: $(FILE_SIZES)

$(LATENCIES): FOLDER=delay=$@,c=$(CLIENT),drop-to-client=$(subst $(comma),_,$(TO_CLIENT_DROP)),drop-to-server=$(subst $(comma),_,$(TO_SERVER_DROP)),file_size=$(FILE_SIZE),name=$(ENAME)
#$(LATENCIES): FOLDER=delay=$@,drop-to-client=$(patsubst ,=),drop-to-server=$(TO_SERVER_DROP:,=),file_size=$(FILE_SIZE),name=$(ENAME)
$(LATENCIES): FILE_WFC=$@-wfc
$(LATENCIES): FILE_IACK=$@-iack
$(LATENCIES):

	docker container prune -f
	docker network prune -f

	# WFC
	python run.py -c $(CLIENT) -s $(SERVERS) -t $(SCENARIO) \
		-a $@ms \
		--drop-to-client "$(TO_CLIENT_DROP)" \
		--drop-to-server "$(TO_SERVER_DROP)" \
		--delay-first-packet $(WFC_DELAY) \
		-b $(FOLDER),delay-first-packet=$(WFC_DELAY) \
		--repetitions $(REPETITIONS) \
		--cert-chain-length $(CERT_CHAIN) \
		$(PARAMS_ADD) \
		--file-size $(FILE_SIZE) 2>&1 | tee $(FILE_WFC)
	export FOLDER_WFC=$$(grep "Saving logs to logs_" $(FILE_WFC)) && cp $(FILE_WFC) "$${FOLDER_WFC:15:-1}/log.txt" 

	# IACK
	python run.py -c $(CLIENT) -s $(SERVERS) -t $(SCENARIO) \
		-a $@ms \
		--drop-to-client "$(TO_CLIENT_DROP)" \
		--drop-to-server "$(TO_SERVER_DROP)" \
		--instant-ack-delay $(IACK_DELAY) \
		--enable-instant-ack true \
		-b $(FOLDER),instant-ack-delay=$(IACK_DELAY),instant-ack=1 \
		--repetitions=$(REPETITIONS) \
		--cert-chain-length $(CERT_CHAIN) \
		$(PARAMS_ADD) \
		--file-size $(FILE_SIZE) 2>&1 | tee $(FILE_IACK)
	export FOLDER_IACK=$$(grep "Saving logs to logs_" $(FILE_IACK)) && cp $(FILE_IACK) "$${FOLDER_IACK:15:-1}/log.txt" 
	# Send files (delaying this ensures, that either one or all logs are transferred)
	export FOLDER_IACK=$$(grep "Saving logs to logs_" $(FILE_IACK)) && mv "$${FOLDER_IACK:15:-1}" /research-data
	export FOLDER_WFC=$$(grep "Saving logs to logs_" $(FILE_WFC)) && mv "$${FOLDER_WFC:15:-1}" /research-data
	rm -f $(FILE_IACK)
	rm -f $(FILE_WFC)

# Pairs
$(LATENCIES_PAIRS): FOLDER=delay=$(@:-p=)ms,c=$(CLIENT),drop-to-server=$(subst $(comma),_,$(TO_SERVER_DROP)),file_size=$(FILE_SIZE),name=$(ENAME)tcdgroup$(subst $(comma),_,$(TO_CLIENT_DROPS_PAIR)),pair=1
$(LATENCIES_PAIRS): WFC_TO_CLIENT_DROP=$(word 1,$(TO_CLIENT_DROPS_PAIR))
$(LATENCIES_PAIRS): IACK_TO_CLIENT_DROP=$(word 2,$(TO_CLIENT_DROPS_PAIR))
$(LATENCIES_PAIRS): FILE_WFC=$@-wfc
$(LATENCIES_PAIRS): FILE_IACK=$@-iack
$(LATENCIES_PAIRS):

	docker container prune -f
	docker network prune -f

	# WFC
	python run.py -c $(CLIENT) -s $(SERVERS) -t $(SCENARIO) \
		-a $(@:-p=)ms \
		--drop-to-client "$(WFC_TO_CLIENT_DROP)" \
		--drop-to-server "$(TO_SERVER_DROP)" \
		--delay-first-packet $(WFC_DELAY) \
		-b "$(FOLDER),delay-first-packet=$(WFC_DELAY),drop-to-client=$(subst $(comma),_,$(WFC_TO_CLIENT_DROP))" \
		--repetitions=$(REPETITIONS) \
		--cert-chain-length $(CERT_CHAIN) \
		$(PARAMS_ADD) \
		--file-size $(FILE_SIZE) 2>&1 | tee $(FILE_WFC)
	export FOLDER=$$(grep "Saving logs to logs_" $(FILE_WFC)) && cp $(FILE_WFC) "$${FOLDER:15:-1}/log.txt"

	# IACK
	python run.py -c $(CLIENT) -s $(SERVERS) -t $(SCENARIO) \
		-a $(@:-p=)ms \
		--drop-to-client "$(IACK_TO_CLIENT_DROP)" \
		--drop-to-server "$(TO_SERVER_DROP)" \
		--instant-ack-delay $(IACK_DELAY) \
		--enable-instant-ack true \
		-b "$(FOLDER),instant-ack-delay=$(IACK_DELAY),instant-ack=1,drop-to-client=$(subst $(comma),_,$(IACK_TO_CLIENT_DROP))" \
		--repetitions=$(REPETITIONS) \
		--cert-chain-length $(CERT_CHAIN) \
		$(PARAMS_ADD) \
		--file-size $(FILE_SIZE) 2>&1 | tee $(FILE_IACK)
	export FOLDER=$$(grep "Saving logs to logs_" $(FILE_IACK)) && cp $(FILE_IACK) "$${FOLDER:15:-1}/log.txt" 

	export FOLDER=$$(grep "Saving logs to logs_" $(FILE_WFC)) && mv "$${FOLDER:15:-1}" /research-data
	export FOLDER=$$(grep "Saving logs to logs_" $(FILE_IACK)) && mv "$${FOLDER:15:-1}" /research-data
	rm -f $(FILE_IACK)
	rm -f $(FILE_WFC)
