FILES:=$(shell ls test/*.extracted)
FILES_NEW=$(subst extracted,extracted2,$(FILES))
TEMP:=out.temp

compile:
	CGO_ENABLED=0 go build -ldflags="-extldflags=-static"	add-pto-info

test: $(FILES_NEW)
	echo $(FILES)

$(FILES_NEW):$(FILES)
	touch $(TEMP)
	rm $(TEMP)
	./add-pto-info -i $< -o $(TEMP)
	# Should contain at least one ACK, fails if no matches
	grep cc_newly_acked_ack_eliciting $(TEMP) 1>/dev/null 2>&1
	rm $(TEMP)

