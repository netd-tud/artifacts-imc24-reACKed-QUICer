from pathlib import Path

import typer
from loguru import logger
from tqdm import tqdm

from instant_ack import config
from instant_ack.data import preprocess_qscanner
from instant_ack.data import convenience as cv
from instant_ack.data import preprocess_qlog as pre_qlog
import psutil
import subprocess
import sys
import polars as pl
import os

app = typer.Typer()


# Delete provided files
def clean_files(files: list[Path]):
    for file in files:
        file.unlink(missing_ok=True)


# Process qscanner results, i.e. use tshark to extract from the collected pcaps
def process_qscanner(
    procs: int,
    refresh: bool,
    task_list: Path,
    in_dir: Path,
    out_file: Path,
    glob: str = "*/data/*",
):
    pcaps = cv.glob_sort_folder(in_dir, f"{glob}/capture.pcap.zst")

    logger.info("Generating list of tshark tasks")
    preprocess_qscanner.generate_task_list(pcaps, task_list)

    logger.info(f"Running tshark extraction with {procs} parallel processes")
    with subprocess.Popen(
        f"parallel --bar -j {procs} -a {task_list}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    ) as p:
        while p.poll() is None:
            text = p.stderr.read1().decode("utf-8")
            print(text, end="", flush=True, file=sys.stderr)

    logger.info("Processing created csvs")
    csvs = cv.glob_sort_folder(in_dir, f"{glob}/pcap.csv")

    preprocess_qscanner.process_all_files(csvs, out_file)


# cloudflare defaults
cloudflare = {
    "in_dir": config.RAW_DATA_DIR / "cloudflare",
    "out_file": config.INTERIM_DATA_DIR / "cloudflare.pq.zst",
    "task_list": Path("cf_tasks.parallel"),
}


@app.command()
def clean_cloudflare(
    task_list: Path = cloudflare["task_list"],
    in_dir: Path = cloudflare["in_dir"],
    out_file: Path = cloudflare["out_file"],
):

    csvs = cv.glob_sort_folder(in_dir, "*/data/*/pcap.csv")
    clean_files([out_file, task_list] + csvs)


# Process pcaps and qscanner header files for measurement of Cloudflare IACK deployment
@app.command()
def cloudflare(
    procs: int = 10,
    refresh: bool = False,
    task_list: Path = cloudflare["task_list"],
    in_dir: Path = cloudflare["in_dir"],
    out_file: Path = cloudflare["out_file"],
):

    schema = {
        "targetid": pl.Int64,
        "address": pl.String,
        "port": pl.UInt16,
        "hostname": pl.String,
        "Header": pl.String,
        "Value": pl.String,
    }

    for location in cv.glob_sort_folder(in_dir, "*/"):
        out_file = (
            config.INTERIM_DATA_DIR / "cloudflare" / f"cloudflare.{location.parts[-1]}.pq.zst"
        )

        logger.info("Processing header files")
        dfs = []
        header_out_file = (
            config.INTERIM_DATA_DIR / "cloudflare" / f"header.{location.parts[-1]}.pq.zst"
        )
        files = cv.glob_sort_folder(location, "data/*/http_header.csv.zst")
        for file in tqdm(files):
            df = (
                pl.read_csv(file, schema=schema)
                .with_columns(
                    location=pl.lit(f"{file.parts[-4]}"),
                    measurement_ts=pl.lit(f"{file.parts[-2]}"),
                )
                .filter(pl.col("Header").str.contains("[cC]f"))
            )
            dfs.append(df)
        pl.concat(dfs, how="diagonal").write_parquet(header_out_file)

        # Release memory
        header_out_file = []

        process_qscanner(procs, refresh, task_list, location, out_file, glob="data/*")


# toplist defaults
toplist = {
    "in_dir": config.RAW_DATA_DIR / "toplist",
    "out_file": config.INTERIM_DATA_DIR / "toplist.pq.zst",
    "task_list": Path("tl_tasks.parallel"),
}


@app.command()
def clean_toplist(
    task_list: Path = toplist["task_list"],
    in_dir: Path = toplist["in_dir"],
    out_file: Path = toplist["out_file"],
):

    csvs = cv.glob_sort_folder(in_dir, "*/data/*/pcap.csv")
    clean_files([out_file, task_list] + csvs)


# Extract information from Qscanner run on toplist
@app.command()
def toplist(
    procs: int = 2,
    refresh: bool = False,
    task_list: Path = toplist["task_list"],
    in_dir: Path = toplist["in_dir"],
    out_file: Path = toplist["out_file"],
):
    process_qscanner(procs, refresh, task_list, in_dir, out_file)


# QIR defaults
interop = {
    "in_dir": config.INTEROP_DATA_DIR,
    "out_dir": config.INTERIM_DATA_DIR / "qlog",
}


@app.command()
def clean_interop(
    folder: Path = interop["out_dir"],
):

    files = cv.glob_sort_folder(folder, "qlog.*.pq.zst")
    clean_files(files)


# Process data from modified QUIC interop runner
@app.command()
def interop(
    refresh: bool = False,
    in_dir: Path = interop["in_dir"],
    out_dir: Path = interop["out_dir"],
    glob=config.PAT_INTEROP_RESULT_FOLDER,
):

    for client in [
        "aioquic",
        "go-x-net",
        "mvfst",
        "neqo",
        "ngtcp2",
        "picoquic",
        "quic-go",
        "quiche",
    ]:
        c_folder = in_dir / client

        # One output file per client
        dest = out_dir / f"qlog.{c_folder.parts[-1]}.pq.zst"

        # Get files to read
        folders = cv.glob_sort_folder(c_folder, glob)

        # Get files already read
        current_files, current_df = pre_qlog.get_files_if_dest_exists(dest, refresh=refresh)

        dfs = []
        for folder in (pbar := tqdm(folders)):
            pbar.set_postfix({"new": len(dfs), "folder": (folder.parts[-1])}, refresh=True)
            df = pre_qlog.folder_to_df(folder, current_files)
            if df is not None:
                dfs.append(
                    df.with_columns(
                        folder=pl.lit(str(folder)),
                    )
                )

            if psutil.virtual_memory()[1] / 1_000_000_000 < 40:
                # No more memory break and try to merge
                logger.warning(
                    "Not enough spare memory, aborting reading data, but concatenating read data. Restart data aggregation to continue..."
                )
                break

        if len(dfs) > 0:
            df = pl.concat(dfs, how="diagonal")

            cv.sink_parquet_and_merge_if_exists(current_df, df, dest)


public_interop = {
    "client": "quic-go",
    "server_names": [
        "quic-go",
        "ngtcp2",
        "mvfst",
        "quiche",
        "kwik",
        "picoquic",
        "aioquic",
        "neqo",
        "nginx",
        "msquic",
        "xquic",
        "lsquic",
        "haproxy",
        "quinn",
        "s2n-quic",
        "go-x-net",
    ],
    "runs": [
        "2024-08-14T01:43",
        "2024-08-15T01:36",
        "2024-08-16T01:42",
    ],
    "task_list": Path("pi_tasks.wget"),
    "task_list_parallel": Path("pi_tasks.parallel"),
    "in_dir": config.RAW_DATA_DIR / "all-interop-servers",
    "out_file": config.INTERIM_DATA_DIR / "all-interop-servers.pq.zst",
}


@app.command()
def clean_interop_servers(
    task_list: Path = public_interop["task_list"],
    in_dir: Path = public_interop["in_dir"],
    out_file: Path = public_interop["out_file"],
):

    csvs = cv.glob_sort_folder(in_dir, "*/*/*/*/pcap.csv")
    clean_files([out_file, task_list] + csvs)


# Pull from public interop-runner and extract information with tshark
@app.command()
def interop_servers(
    task_file: Path = public_interop["task_list"],
    client: str = public_interop["client"],
    server_names: list[str] = public_interop["server_names"],
    in_dir: Path = public_interop["in_dir"],
    runs: list[str] = public_interop["runs"],
    procs: int = 10,
    refresh: bool = False,
    task_list: Path = public_interop["task_list_parallel"],
    out_file: Path = public_interop["out_file"],
):

    logger.info("Generating download URLs")

    with open(task_file, "w") as file:
        for run in runs:
            for name in server_names:
                url = f"https://interop.seemann.io/logs/{run}/{name}_{client}/handshake/sim/trace_node_left.pcap"
                print(url, file=file)
                url = f"https://interop.seemann.io/logs/{run}/{name}_{client}/handshake/client/keys.log"
                print(url, file=file)

    logger.info("Downloading data")
    with subprocess.Popen(
        f"wget -m --cut-dirs 1 -nH -P {in_dir} $(cat {task_file})",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    ) as p:
        while p.poll() is None:
            text = p.stderr.read1().decode("utf-8")
            print(text, end="", flush=True, file=sys.stderr)

    # Client perspective
    pcaps = cv.glob_sort_folder(in_dir, "*/*/*/*/trace_node_left.pcap")
    logger.info("Generating list of tshark tasks")
    preprocess_qscanner.generate_task_list(pcaps, task_list)

    logger.info(f"Running tshark extraction with {procs} parallel processes")
    with subprocess.Popen(
        f"parallel --bar -j {procs} -a {task_list}",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    ) as p:
        while p.poll() is None:
            text = p.stderr.read1().decode("utf-8")
            print(text, end="", flush=True, file=sys.stderr)
    dfs = []

    for file in tqdm(cv.glob_sort_folder(in_dir, "*/*/*/*/pcap.csv")):
        if os.stat(file).st_size != 0:
            df = preprocess_qscanner.load_parsed(file).with_columns(
                measurement_ts=pl.lit(str(file.parts[-5])),
                server=pl.lit(str(file.parts[-4]).split("_", 1)[0]),
            )
            dfs.append(df)
    logger.info("Processing created csvs")
    pl.concat(dfs, how="diagonal").sink_parquet(out_file)


if __name__ == "__main__":
    app()
