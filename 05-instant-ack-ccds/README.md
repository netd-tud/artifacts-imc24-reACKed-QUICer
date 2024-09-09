# instant-ack

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Analysis of instant ACK in QUIC

## Project Organization

```
├── Makefile           <- Makefile with convenience commands like `make data`. See section below. 
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── interim        <- Data that has been transformed into parquet files.
│   └── raw            <- The original data and slight preprocessed data.
│
├── notebooks          <- Jupyter notebooks. Structurd by topic.
│   ├── 01-numerical_analysis/     <- Numerical analysis.
│   ├── 02-interop-runner/         <- Analysis of QIR emulations, i.e., TTFB, First PTO improvement, # of RTT samples.
│   ├── 03-toplist/                <- Analysis of QScanner connections to Tranco Top 1M.
│   ├── 04-cloudflare/             <- Analysis of Cloudflare hosted otherwise unused domains.
│   └── 05-all-interop-servers/    <- Analysis of ACK delay in QUIC server implementations of public QIR.
│
├── pyproject.toml     <- Project configuration file with package metadata for instant_ack
│                         and configuration for tools like black
│
├── reports            
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── instant_ack        <- Source code for use in this project.
    │
    ├── __init__.py    <- Makes instant_ack a Python module
    ├── data/          <- Scripts to preprocess, load, store and validate data.
    ├── dataset.py     <- Scripts to transform raw data into parquet files.
    └── visualization/ <- Scripts to create exploratory and results oriented visualizations
```

--------

## Requirements
```
python3.10
tshark 4.0.15
```

## Makefile
> [!IMPORTANT]  
> Make sure you downloaded the required data from: [https://doi.org/10.25532/OPARA-615](https://doi.org/10.25532/OPARA-615). 
> Use `tar -xvf $FILENAME` and for compressed files: `tar -xvzf $FILENAME`

The Makefile is used for convenience, the following commands are available:
```
# Python env
make python_env             # Example of python env creation, use source .venv/bin/activate to activate the python environment.

# Data preprocessing
make cloudflare             # Preprocess Cloudflare hosted domain interactions.
                            #       -> requires raw-cloudflare.tar (140 GB) extracted into data/raw
make toplist                # Preprocess data from Tranco Top 1M QUIC connection attempts.
                            #       -> requires raw-toplist.tar (182 GB) extracted into data/raw
make interop                # Preprocess data from QIR emulations. (Run make qlog before)
                            #       -> requires raw-interop-runner.tar.gz (200 GB) extracted into data/raw
make interop-servers        # Preprocess data from public QIR.
make qlog                   # Preprocess qlog files.
                            #       -> requires raw-interop-runner.tar (200 GB) extracted into data/raw
make pyasn                  # Preprocess RIB dump 
                            #       -> requires rib.20240807.0600.bz2 (98 MB) extracted into data/raw
make data                   # Wrapper for all above.

# Reproducing jupyter notebook output
#       -> requires either extraction of interim-qlog.tar (572 MB), interim-cloudflare.tar (43 GB), all-interop-servers.pq.zst (300 KB)
#                            and download of rib.20240807.0600.pyasn (22 MB), toplist.pq.zst(3 GB) into data/interim 
                        or data preprocessing as described above
make nbconvert              # Convert jupyter notebooks to HTML.
make nbconvert-execute      # Convert jupyter notebooks to HTML but run them before.
```


