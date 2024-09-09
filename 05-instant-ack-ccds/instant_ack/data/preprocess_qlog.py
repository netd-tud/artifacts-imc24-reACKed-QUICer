from tqdm.auto import tqdm
import polars as pl
from pathlib import Path
from instant_ack import config
from instant_ack.data import convenience as cv
import os


# Extract key value elements from foldername
def extract_key_val(fname):
    # Split log prefix in the beginning
    fname = fname.split("_", maxsplit=1)[1]
    # Split timestamps in the end
    fname = fname.rsplit("_", maxsplit=1)[0]

    # Extract key-val pairs
    val = {}
    for key_val in fname.split(","):
        key, value = key_val.split("=")
        val[key] = value
    return val


# Extract client/server from folder name
def extract_client_server(file):
    server, client = file.parts[-6].split("_", 1)
    return server, client


#  Extract scenario from folder name
def extract_scenario(file):
    return file.parts[-5]


# Combine extracted information
def extract_run_meta(file):
    s, c = extract_client_server(file)
    scenario = extract_scenario(file)

    return {
        "client": c,
        "server": s,
        "scenario": scenario,
    }


# Implementations may expose acknowledgment delay differently, scale accordingly
# If required the ack_delay should be extracted from the client/server communicated ACK delay during the handshake
c_frame_ack_delay_scale = {
    # Unit conversions
    "quic-go": 1000,
    "aioquic": 1000,
    # Fixed but observed values:
    "neqo": 2**3,
    "picoquic": 2**3,
    "quiche": 1000 * 2**3,
    "chrome": 1000,
    "mvfst": 1,
    "go-x-net": 1000,
    "ngtcp2": 1000,
}

# convert time to ms, which polars can convert to datetime
c_time_to_ms = {
    "quic-go": 1000,
    "aioquic": 1000,
    "quiche": 1000,
    "picoquic": 1,
    "neqo": 1,
    "ngtcp2": 1000,
    "chrome": 1000,
    "mvfst": 1,
    "go-x-net": 1000,
}

c_rtt_scale_to_ms = {"mvfst": 1 / 1000}


# Calculate time since the first packet was sent, according to the implementation
def add_time_since_first(df, cols="^time|cc_max_ack_sent_time$"):
    first_packet_sent = (
        df.filter(pl.col("name") == "transport:packet_sent")
        .select(pl.col("time").min())
        .item(0, 0)
    )

    return df.with_columns(
        ((pl.col(cols) - first_packet_sent).dt.total_microseconds() / 1000).name.suffix(
            "_since_first_ms"
        ),
    )


# Add marker col, when the handshake is considered done
def add_handshake_done_markers(df):
    return df.with_columns(
        handshake_done=pl.col("frame_frame_type")
        .str.contains("handshake_done")
        .forward_fill()
        .fill_null(False),
        first_1rtt_ack=(
            pl.col("frame_frame_type").str.contains("ack")
            & (pl.col("data_header_packet_type") == "1RTT")
        )
        .forward_fill()
        .fill_null(False),
    ).with_columns(
        # cc = custom calculation (information not provided directly by the implementations)
        cc_handshake_done=pl.col("handshake_done")
        | pl.col("first_1rtt_ack")
    )


# Get RTT samples, calculate current_rtt and min_rtt
def filter_samples_and_calculate_rtts(df):

    return (
        df.filter(
            # RTT Samples
            pl.col("cc_newly_acked_ack_eliciting")
            == True
        )
        .with_columns(
            # Time between sending packet and receiving ACK
            cc_current_rtt=pl.col("time_since_first_ms")
            - pl.col("cc_max_ack_sent_time_since_first_ms"),
        )
        .with_columns(
            cc_min_rtt=pl.col("cc_current_rtt").cum_min(),
        )
        .filter(
            # This ensures that skipping acks, and when acks acknowledge a packet that was never sent, the record is ignored.
            pl.col("cc_current_rtt").is_not_null(),
        )
    )


"""
RFC9002:
   On the first RTT sample after initialization, smoothed_rtt and rttvar
   are set as follows:

   smoothed_rtt = latest_rtt
   rttvar = latest_rtt / 2
"""


def first_smoothed_and_variance(df_samples):

    first_acked_ack_eliciting = (
        df_samples.filter(pl.col("cc_newly_acked_ack_eliciting") == True)
        .select(pl.col("id").min())
        .item(0, 0)
    )

    return (
        df_samples.with_columns(
            cc_smoothed_rtt=pl.when(pl.col("id") == first_acked_ack_eliciting).then(
                pl.col("cc_current_rtt")
            ),
            # Can be used for comparison: calculation disregarding min_rtt + ack_delay rtt adjustment.
            cc_smoothed_rtt_not_adjusted=pl.when(pl.col("id") == first_acked_ack_eliciting).then(
                pl.col("cc_current_rtt")
            ),
            cc_rtt_var=pl.when(pl.col("id") == first_acked_ack_eliciting).then(
                pl.col("cc_current_rtt") / 2
            ),
            cc_first=pl.when(pl.col("id") == first_acked_ack_eliciting).then(pl.lit(True)),
            # We use only a single server (quic-go), which uses 26 ms
            cc_max_ack_delay=pl.lit(26),
        )
        .with_columns(
            cc_ack_delay_adjusted=pl.when(pl.col("cc_handshake_done"))
            .then(pl.min_horizontal("frame_ack_delay", "cc_max_ack_delay"))
            .otherwise(pl.col("frame_ack_delay")),
        )
        .with_columns(
            # RFC9002
            #       if (latest_rtt >= min_rtt + ack_delay):
            #           adjusted_rtt = latest_rtt - ack_delay
            cc_adjusted_rtt=pl.when(
                pl.col("cc_current_rtt")
                >= (pl.col("cc_min_rtt") + pl.col("cc_ack_delay_adjusted"))
            )
            .then(pl.col("cc_current_rtt") - pl.col("cc_ack_delay_adjusted"))
            .otherwise(pl.col("cc_current_rtt")),
        )
        .with_columns(
            # RFC9002:
            #      Therefore, prior to handshake confirmation, an endpoint MAY ignore RTT samples
            #      if adjusting the RTT sample for acknowledgment delay causes the sample to be less than the min_rtt.
            #  Mark samples, that may be ignored
            cc_potentially_ignored_sample=pl.when(
                (pl.col("cc_adjusted_rtt") < pl.col("cc_min_rtt"))
                & (pl.col("cc_handshake_done") == False)
            )
            .then(pl.lit(True))
            .otherwise(pl.lit(False)),
        )
    )


"""
RFRC9002:
rttvar_sample = abs(smoothed_rtt - adjusted_rtt)
rttvar = 3/4 * rttvar + 1/4 * rttvar_sample
smoothed_rtt = 7/8 * smoothed_rtt + 1/8 * adjusted_rtt
"""


def calculate_smoothed_rtt_and_variance(df_samples):
    smoothed = []
    smoothed_n_a = []
    rtt_var = []
    prev = None
    for row in df_samples[
        [
            "cc_smoothed_rtt",
            "cc_adjusted_rtt",
            "cc_current_rtt",
            "cc_smoothed_rtt_not_adjusted",
            "cc_rtt_var",
        ]
    ].iter_rows(named=True):
        if prev == None:
            # Keep first value
            smoothed.append(row["cc_smoothed_rtt"])
            smoothed_n_a.append(row["cc_smoothed_rtt_not_adjusted"])
            rtt_var.append(row["cc_rtt_var"])
            prev = row
            continue

        rtt_var_sample = abs(prev["cc_smoothed_rtt"] - prev["cc_adjusted_rtt"])
        row["cc_rtt_var"] = 3 / 4 * prev["cc_rtt_var"] + 1 / 4 * rtt_var_sample
        row["cc_smoothed_rtt"] = 7 / 8 * prev["cc_smoothed_rtt"] + 1 / 8 * row["cc_adjusted_rtt"]
        row["cc_smoothed_rtt_not_adjusted"] = (
            7 / 8 * prev["cc_smoothed_rtt_not_adjusted"] + 1 / 8 * row["cc_current_rtt"]
        )

        smoothed.append(row["cc_smoothed_rtt"])
        smoothed_n_a.append(row["cc_smoothed_rtt_not_adjusted"])
        rtt_var.append(row["cc_rtt_var"])

        prev = row

    df_samples = df_samples.with_columns(
        cc_smoothed_rtt=pl.Series("cc_smoothed_rtt", smoothed),
        cc_smoothed_rtt_not_adjusted=pl.Series("cc_smoothed_rtt_not_adjusted", smoothed_n_a),
        cc_rtt_var=pl.Series("cc_rtt_var", rtt_var),
    )

    return df_samples


def add_pto_update_on_hs_confirmed(df_samples, df):
    # Add entry when handshake is confirmed, to adjust for max_ack_delay from that point
    hs_confirmed = (
        df.filter(
            pl.col("cc_handshake_done"),
        )
        .filter(
            pl.col("cc_newly_acked_ack_eliciting").is_null(), pl.col("id") == pl.col("id").min()
        )
        .select("id")
    )

    if len(hs_confirmed) > 0:
        insert_row = (
            df_samples.filter(pl.col("id") < hs_confirmed.item(0, 0))
            .tail(1)
            .with_columns(
                id=pl.lit(hs_confirmed.item(0, 0)).cast(pl.UInt32),
                cc_newly_acked_ack_eliciting=pl.lit(None),
                cc_max_ack_sent_time=pl.lit(None),
            )
        )

        df_samples = pl.concat([df_samples, insert_row]).sort("id")

    return df_samples


def calculate_ptos(df):
    df = add_handshake_done_markers(df)
    # Add ID and global granularity
    df = df.with_columns(
        cc_kGranularity=pl.lit(1),  # ms
    ).with_row_index("id")

    # If no markers added skip
    if ("cc_newly_acked_ack_eliciting" not in df) or (
        df.select(pl.col("cc_newly_acked_ack_eliciting").any()).item(0, 0) == False
    ):
        return df

    df_samples = filter_samples_and_calculate_rtts(df)

    # Seed smoothed_rtt and rtt variance
    df_samples = first_smoothed_and_variance(df_samples)

    df_samples = calculate_smoothed_rtt_and_variance(df_samples)

    # This adds an additional datapoint replicating the previous, but updating PTO when the handshake is confirmed.
    df_samples = add_pto_update_on_hs_confirmed(df_samples, df)

    df_samples = df_samples.with_columns(cc_rtt_var_4=pl.col("cc_rtt_var") * 4).with_columns(
        cc_pto=pl.when(pl.col("cc_handshake_done") == False)
        .then(
            pl.col("cc_smoothed_rtt")
            + pl.max_horizontal(["cc_rtt_var_4", "cc_kGranularity"])
            + pl.col("cc_max_ack_delay")
        )
        .otherwise(
            pl.col("cc_smoothed_rtt") + pl.max_horizontal(["cc_rtt_var_4", "cc_kGranularity"])
        ),
        cc_pto_not_adjusted=pl.when(pl.col("cc_handshake_done") == False)
        .then(
            pl.col("cc_smoothed_rtt_not_adjusted")
            + pl.max_horizontal(["cc_rtt_var_4", "cc_kGranularity"])
            + pl.col("cc_max_ack_delay")
        )
        .otherwise(
            pl.col("cc_smoothed_rtt_not_adjusted")
            + pl.max_horizontal(["cc_rtt_var_4", "cc_kGranularity"])
        ),
    )

    # Join the following columns
    cols = [
        "cc_smoothed_rtt",
        "cc_smoothed_rtt_not_adjusted",
        "cc_rtt_var",
        "cc_current_rtt",
        "cc_min_rtt",
        "cc_first",
        "cc_max_ack_delay",
        "cc_ack_delay_adjusted",
        "cc_adjusted_rtt",
        "cc_pto",
        "cc_pto_not_adjusted",
        "cc_potentially_ignored_sample",
        "id",
    ]

    return df.join(
        df_samples[cols],
        on="id",
        how="left",
    ).drop(["id"])


def adjust_rtt_vals(df, client):
    if client != "picoquic":
        return df
    return df.with_columns(pl.col("data_min_rtt", "data_smoothed_rtt", "data_latest_rtt") / 10**3)


def remove_unused_cols(df, client):

    remove_cols = [
        "meta_trace_common_fields_time_format",
        "common_fields_reference_time",
    ]
    generic_remove = ["vantage_point_name", "vantage_point_type", "time"]

    if client == "picoquic":
        remove_cols += list(
            pl.DataFrame({"cols": df.columns}).filter(
                pl.col("cols").str.contains("^data_[0-9a-f]{2,4}$")
            )["cols"]
        )

    return df.drop(remove_cols + generic_remove, strict=False)


def convert_dtypes(df, client):

    return df.with_columns(
        pl.col("^data_initial_max_.*|.*data_header_packet_number.*$").cast(pl.Float64),
        pl.col("^.*data_quantum_readiness.*|.*data_original_connection_id.*$").cast(pl.String()),
        pl.selectors.by_name(
            ["data_max_idle_timeout", "data_max_udp_payload_size", "data_max_ack_delay"],
            require_all=False,
        ).cast(pl.Int64),
        pl.selectors.by_name(
            [
                "data_disable_active_migration",
            ],
            require_all=False,
        ).cast(pl.String),
        pl.selectors.by_name(
            [
                "data_max_datagram_frame_size",
            ],
            require_all=False,
        )
        .str.replace("]", "")
        .cast(pl.Int64),
    )


def rename_recovery_metric_update(df):
    return df.with_columns(
        # mvfst uses different name...
        pl.col("name").replace({"recovery:metric_update": "recovery:metrics_updated"})
    )


def scale_recovery_metrics(df, client):
    if client in c_rtt_scale_to_ms:
        return df.with_columns(
            pl.col(["data_latest_rtt", "data_min_rtt", "data_smoothed_rtt"])
            * c_rtt_scale_to_ms[client]
        )
    return df


# Process a single qlog file
def process_qlog(file):
    meta = extract_run_meta(file)
    c = meta["client"]

    df = pl.read_json(file, schema_overrides=get_client_schema(c))

    df = df.with_columns(
        # Convert time and cc_mack_sent_time to ms.
        (pl.col("^time|cc_max_ack_sent_time$").cast(pl.Float64()) * c_time_to_ms[c]).cast(
            pl.Datetime()
        ),
        # There can only be one ack_delay per packet, remove all separators
        pl.col("frame_ack_delay")
        .str.replace_all(",|\\|", "")
        .replace("", None)
        .cast(
            pl.Float64(),
        )
        * c_frame_ack_delay_scale[c],
        file=pl.lit(str(file)),
    )
    df = add_time_since_first(df)
    df = rename_recovery_metric_update(df)
    df = scale_recovery_metrics(df, c)
    df = calculate_ptos(df)

    # Scale recovery_metric updates uniformly
    df = adjust_rtt_vals(df, c)

    df = remove_unused_cols(df, c)
    df = convert_dtypes(df, c)

    df = df.join(pl.from_dict(meta), how="cross")

    return df


fpd = "delay-first-packet"
ia = "instant-ack"


# Process a folder produced by QIR
def folder_to_df(folder: Path, df_files: pl.DataFrame) -> pl.DataFrame:

    folder_meta = extract_key_val(folder.parts[-1])
    meta = (
        pl.from_dicts([folder_meta])
        .rename(lambda x: f"meta_{x}")
        .with_columns(
            pl.col("meta_delay").str.replace("ms", "").cast(pl.Float64),
        )
        .with_columns(
            rtt=pl.col("meta_delay") * 2,
        )
    )

    files = cv.glob_sort_folder(folder, config.PAT_REPEATED_MEASUREMENT)
    dfs = []
    for file in (bar := tqdm(files, leave=False)):
        bar.set_postfix({"file": file.parts[-1]}, refresh=True)
        if str(file) in df_files["file"]:
            continue
        df = process_qlog(file)

        dfs.append(df)
    if len(dfs) > 0:
        iack = (ia in folder_meta) and (fpd not in folder_meta)
        wfc = (ia not in folder_meta) and (fpd in folder_meta)
        df = (
            pl.concat(dfs, how="diagonal")
            .join(meta, how="cross")
            .with_columns(
                server_group=pl.when(iack)
                .then(pl.lit("IACK"))
                .when(wfc)
                .then(pl.lit("WFC"))
                .otherwise(pl.lit(None))
            )
        )
        return df
    return None


def get_client_schema(client: str):
    schema = {
        "data_grease_quic_bit": pl.String,
        "data_smoothed_rtt": pl.Float64,
        "data_rtt_variance": pl.Float64,
        "data_latest_rtt": pl.Float64,
        "data_min_rtt": pl.Float64,
        "configuration_time_offset": pl.String,
    }

    # Fields that do not exist cause polars to abort the transformation... remove these
    if client in ["picoquic", "mvfst"]:
        del schema["data_rtt_variance"]
    if client in ["aioquic", "go-x-net", "mvfst", "neqo", "quic-go", "quiche", "chrome"]:
        del schema["data_grease_quic_bit"]
    if client in ["neqo", "chrome"]:
        del schema["data_rtt_variance"]
    if client in ["mvfst", "chrome"]:
        del schema["data_smoothed_rtt"]
        del schema["data_latest_rtt"]
        del schema["data_min_rtt"]
    if client in ["aioquic", "go-x-net", "ngtcp2", "picoquic", "quic-go", "quiche", "chrome"]:
        del schema["configuration_time_offset"]
    return schema


# Get information of already parsed files or empty dataframe if not yet parsed
# This allows incrementally combining information into a single parquet file
def get_files_if_dest_exists(dest: Path, refresh=False):
    parquet_file = dest
    if os.path.exists(parquet_file) and (refresh == False):
        df = pl.scan_parquet(parquet_file)
        return df.select("file").unique("file").collect(), df
    return pl.DataFrame({"file": []}, schema_overrides={"file": pl.String}), None
