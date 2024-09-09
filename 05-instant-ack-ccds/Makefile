#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = instant-ack
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt

## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 instant_ack
	isort --check --diff --profile black instant_ack
	black --check --config pyproject.toml instant_ack

## Format source code with black
.PHONY: format
format:
	black --config pyproject.toml instant_ack

## Convert notebooks to html
notebooks=$(shell ls notebooks/0*/*.ipynb)
notebooks_html:=$(subst .ipynb,.html,$(notebooks))

%.html: %.ipynb
	jupyter nbconvert $(NBCONVERT_PARAMS) --to html $< 

nbconvert: $(notebooks_html)

nbconvert-execute: NBCONVERT_PARAMS=--execute
nbconvert-execute: $(notebooks_html)

python_env:
	python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


## Make Dataset
.PHONY: data
data: requirements cloudflare toplist qlog interop interop-servers pyasn
	$(PYTHON_INTERPRETER) instant_ack/dataset.py
clean_cloudflare: 
	$(PYTHON_INTERPRETER) instant_ack/dataset.py clean-cloudflare

cloudflare:
	$(PYTHON_INTERPRETER) instant_ack/dataset.py cloudflare 

toplist:
	$(PYTHON_INTERPRETER) instant_ack/dataset.py toplist --refresh

clean_toplist: 
	$(PYTHON_INTERPRETER) instant_ack/dataset.py clean-toplist

interop: 
	$(PYTHON_INTERPRETER) instant_ack/dataset.py interop

clean_interop: 
	$(PYTHON_INTERPRETER) instant_ack/dataset.py clean-interop

interop-servers:
	$(PYTHON_INTERPRETER) instant_ack/dataset.py interop-servers --refresh

clean_interop-servers: 
	$(PYTHON_INTERPRETER) instant_ack/dataset.py clean-interop-servers

pyasn: 
	pyasn_util_convert.py --single data/raw/rib.20240807.0600.bz2 data/interim/rib.20240807.0600.pyasn

## Extract and transform qlog in raw data
MAKEFILE_FOR_EXTRACTION:=$(CURDIR)/data/raw/Makefile

INTEROP_FOLDERS:=$(shell ls --quoting-style=shell-always -d ~+/data/raw/interop-runner/*/logs_delay=*)
INTEROP_FOLDERS_SELECTION:=$(shell ls --quoting-style=shell-always -d ~+/data/raw/interop-runner/*/logs_delay=*$(SELECTION)*)
qlog:
	-rm interop.jl
	parallel -j3 --bar --joblog interop.jl 'cd {} && make -j 6 -f $(MAKEFILE_FOR_EXTRACTION) qlog_extraction' ::: $(INTEROP_FOLDERS)

qlog_selection:
	-rm interop.jl
	parallel -j3 --bar --joblog interop.jl 'cd {} && make -j 6 -f $(MAKEFILE_FOR_EXTRACTION) qlog_extraction' ::: $(INTEROP_FOLDERS_SELECTION)

clean_qlog:
	-rm interop.jl
	parallel -j20 --bar --joblog interop.jl 'cd {} && make -f $(MAKEFILE_FOR_EXTRACTION) clean_qlog_extraction' ::: $(INTEROP_FOLDERS)

clean_qlog_selection:
	-rm interop.jl
	parallel -j20 --bar --joblog interop.jl 'cd {} && make -f $(MAKEFILE_FOR_EXTRACTION) clean_qlog_extraction' ::: $(INTEROP_FOLDERS_SELECTION)


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
