import polars as pl
from instant_ack.data import convenience as cv
import os
from tqdm.auto import tqdm


# Read target file that includes quic.scid to join domains
def read_targets(file):
    schema = {
        "scid": pl.String,
    }
    usecols = ["scid", "sni"]

    df = pl.read_csv(file, schema_overrides=schema).select(usecols).drop_nulls().lazy()
    return df


def load_parsed(fname, **kwargs):

    names = [
        "ts",
        "ip.src",
        "ip.dst",
        "udp.length",
        "udp.srcport",
        "udp.dstport",
        "quic.version",
        "quic.long.packet_type",
        "quic.scid",
        "quic.dcid",
        "quic.frame_type",
        "quic.ack.ack_delay",
        "quic.ack.ack_range",
        "quic.ack.first_ack_range",
        "tls.quic.parameter.ack_delay_exponent",
        "tls.handshake.type",
        "tls.handshake.extensions_server_name",
        "ip.ttl",
    ]

    schema = {
        "ip.src": pl.String,
        "ip.dst": pl.String,
        "udp.length": pl.UInt16,
        "udp.srcport": pl.UInt16,
        "udp.dstport": pl.UInt16,
        "protocol": pl.String,
        "info": pl.String,
        "quic.version": pl.String,
        "quic.crypto.length": pl.Int64,
        "quic.padding_length": pl.Int64,
        "quic.long.packet_type": pl.String,
        "quic.connection.number": pl.Int64,
        "quic.fixed_bit": pl.String,
        "quic.packet_length": pl.String,
        "quic.packet_number": pl.Int64,
        "quic.scid": pl.String,
        "quic.dcid": pl.String,
        "quic.length": pl.String,
        "quic.ack.ack_delay": pl.String,
        "quic.ack.ack_range": pl.String,
        "quic.ack.first_ack_range": pl.String,
        "tls.handshake.type": pl.String,
        "tls.quic.parameter.ack_delay_exponent": pl.UInt32,
        "ip.ttl": pl.String,
        "ts": pl.Datetime("us"),
    }

    df = pl.scan_csv(
        fname,
        separator="|",
        has_header=False,
        new_columns=names,
        low_memory=True,
        schema_overrides=schema,
        **kwargs,
    ).with_columns(pl.col("quic.version").str.split(",").list.get(0))
    return df


# Generates parameterized task list for parallel
def generate_task_list(source, dest):
    with open(dest, "w") as file:
        for pcap in source[::-1]:

            # Tyry to find keylog file
            keylog = str(pcap.parent / ".." / "client" / "keys.log")
            if not os.path.isfile(keylog):
                keylog = str(pcap.parent / "key.log")

            out_file = pcap.parent / "pcap.csv"
            # Do not reprocess pcaps
            if os.path.isfile(out_file):
                continue
            line = f"./tools/tshark-extract-quic-fields.sh '{str(pcap)}' '{str(out_file)}' '{keylog}'\n"
            file.write(line)


# Read extracted information and save into parquet file
def process_all_files(files, out_file, refresh=False):
    current_df = None
    current_files = []

    if os.path.isfile(out_file) and not refresh:
        current_df = pl.scan_parquet(out_file)
        current_files = current_df.select("file").unique().collect()

    dfs = []
    for csv in (pbar := tqdm(files)):
        pbar.set_postfix({"file": csv})
        if csv in current_files:
            continue

        targets = csv.parent / "targets.zst"
        targets = read_targets(targets)

        df = load_parsed(csv)
        # Add metadata
        df = (
            df.with_columns(
                file=pl.lit(str(csv)),
                location=pl.lit(str(csv.parts[-4])),
                measurement_ts=pl.lit(str(csv.parts[-2])),
            )
            .with_columns(
                pl.col("measurement_ts").str.replace_all(",", ".").str.to_datetime(),
                pl.col(["quic.dcid", "quic.scid"]).str.split(",").list.get(0, null_on_oob=True),
            )
            .join(targets, how="left", left_on="quic.dcid", right_on="scid")
            .join(targets, how="left", left_on="quic.scid", right_on="scid", suffix="_scid")
            .with_columns(
                pl.coalesce(pl.col(["sni", "sni_scid"])).alias("sni"),
                pl.when(pl.col("udp.dstport") == 443)
                .then(pl.lit("requests"))
                .otherwise(pl.lit("responses"))
                .alias("kind"),
            )
            .drop(
                "sni_scid",
            )
        )

        dfs.append(df)
    df = pl.concat(dfs, how="diagonal")
    cv.sink_parquet_and_merge_if_exists(current_df, df, out_file)


# Make contained frame types human readable
frame_types = {
    "0": "PAD",
    "1": "PING",
    "2": "ACK",
    "3": "ACK",
    "4": "RESET_STREAM",
    "5": "STOP_SENDING",
    "6": "CRYPTO",
    "7": "NEW_TOKEN",
    "8": "STREAM",
    "9": "STREAM",
    "10": "STREAM",
    "11": "STREAM",
    "12": "STREAM",
    "13": "STREAM",
    "14": "STREAM",
    "15": "STREAM",
    "16": "MAX_DATA",
    "18": "MAX_STREAMS_BIDI",
    "24": "NEW_CID",
    "25": "STREAMS_BLOCKED_UNI",
    "26": "PATH_CHALLENGE",
    "28": "CC",
    "29": "CC",
    "30": "HANDSHAKE_DONE",
}


def translate_frame_types(df, col, new_col):
    return df.with_columns(
        # Split and replace with readable frame_type
        # Sort to shift ACK to the front and disregard order
        pl.col(col)
        .str.split(",")
        .list.eval(
            pl.element().replace_strict(
                frame_types,
            )
        )
        .list.unique()
        .list.sort()
        .list.join(",")
        .alias(new_col)
    )


# Converts city names and Vantage points information
def location_to_titlecase(df, location="location", new_col="geo_location"):
    return df.with_columns(
        pl.col(location)
        .str.replace("_", " ")
        .str.replace("-1", "")
        .str.replace("-2", "")
        .str.to_titlecase()
        .alias(new_col)
    )
