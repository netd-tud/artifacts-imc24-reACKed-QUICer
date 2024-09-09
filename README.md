Artifacts: ReACKed QUICer: Measuring the Performance of Instant Acknowledgments in QUIC Handshakes
===

This repository contains the artifacts for the following paper:
```
ReACKed QUICer: Measuring the Performance of Instant Acknowledgments in QUIC Handshakes
Jonas Mücke, Marcin Nawrocki, Raphael Hiesgen, Thomas C. Schmidt, Matthias Wählisch
Proc. of ACM Internet Measurement Conference (IMC), Madrid, Spain: ACM, 2024
https://doi.org/10.1145/3646547.3689022
```

# Structure
We include all software, data, and analysis scripts required to reproduce our results. 
```
├── 01-quic-go-instant-ack/               <- Fork of `quic-go/quic-go` at e2622bfad865bf4633fb752187c9663402515c6f that implements instant ACK.
├── 02-quic-interop-runner-instant-ack/   <- Fork of `quic-interop/quic-interop-runner` (QIR) at ca27dcb5272a82d994337ae3d14533c318d81b76 with additional configuration options
├── 03-measurement-infra/                 <- Ansible roles and playbook to configure QIR emulation nodes and vantage points of the paper.
│   └── playbook.yaml   <- run with: ansible-playbook -i inventory.yaml playbook.yaml -e @secrets_file.enc --ask-vault-pass 
├── 04-go-pto-tool/                       <- Go tool to link send and received packets in qlog files.
│   └── main.go         <- build with: CGO_ENABLED=0 go build -ldflags="-extldflags=-static" 
└── 05-instant-ack-ccds/                  <- Cookiecutter Data Science project,
    └── README.md      <- Readme with instructions on how to reproduce the paper graphs. 
```
# Reproduction of paper artifacts

Requirements: 256 GB of memory

Clone this repository, then: 
1. Make sure python and wireshark is installed.
1. `cd 05-instant-ack-ccds`
2. Make a virtual environment: `make python_env`
3. Activate python env: `source .venv/bin/activate`
4. Download required data from [https://doi.org/10.25532/OPARA-615](https://doi.org/10.25532/OPARA-615) and extract tars according to `05-instant-ack-ccds/README.md`

Now you can execute the existing notebooks with: 

5. `make nbconvert-execute`

Or if you want to do all preprocessing steps:

5. `make data`

For details or processing only a subset see `05-instant-ack-ccds/README.md`

