from pathlib import Path
import polars as pl
import os
from instant_ack import config
import functools
import numpy as np


# Glob and return sorted output
def glob_sort_folder(folder: Path, pattern: str):
    return list(sorted(list(folder.glob(pattern))))


# Convenience function to load and combine different datasets
def load_data(
    name, skip_missing=False, default_ext=".pq.zst", search_dir=config.INTERIM_DATA_DIR, **kwargs
):
    if name == "qlog":
        name = glob_sort_folder(search_dir / name, "*.pq.zst")
    if name == "cloudflare":
        name = glob_sort_folder(search_dir / name, "cloudflare.*.pq.zst")
    if name == "cloudflare.header":
        name = glob_sort_folder(search_dir / "cloudflare", "header.*.pq.zst")
    if not isinstance(name, list):
        name = [name]

    # Ensure respective files exists.
    existing = []
    for file in name:
        if os.path.isfile(file):
            existing.append(file)
        elif os.path.isfile(search_dir / f"{file}{default_ext}"):
            existing.append(search_dir / f"{file}{default_ext}")
        elif os.path.isfile(search_dir / f"{file}"):
            existing.append(search_dir / f"{file}")

    if not skip_missing:
        assert len(existing) == len(name), f"Input files missing: {set(name) - set(existing)}"

    return pl.concat([pl.scan_parquet(file, **kwargs) for file in existing], how="diagonal")


# Packets comprising the second client flight
# There could be differences between WFC and IACK
snd_client_flight_wfc = {
    "aioquic": "2_3_4",
    "quiche": "2",
    "neqo": "2_3",
    "ngtcp2": "2_3_4",
    "quic-go": "2_3_4",
    "picoquic": "2_3_4_5",
    "mvfst": "2_3_4_5",
    "go-x-net": "2_3_4",
}
snd_client_flight_iack = {
    "aioquic": "2_3_4",
    "quiche": "2",
    "neqo": "2_3",
    "ngtcp2": "2_3_4",
    "quic-go": "2_3_4",
    "picoquic": "2_3_4_5",
    "mvfst": "2_3_4_5",
    "go-x-net": "2_3_4",
}


# Filter input dataset to include only specific measurement
def get_measurement(df: pl.DataFrame | pl.LazyFrame, measurement: str):
    if measurement in ["large_certificate", "certificate"]:
        return df.filter(
            pl.col("meta_name") == "certificate",
        )

    if measurement in ["all_latencies"]:
        return df.filter(
            pl.col("meta_name") == "all_latencies",
        )

    if measurement in ["remaining_first_server_flight"]:
        return df.filter(
            pl.col("meta_pair") == "1",
            pl.col("meta_name") == "tcdgroup2 2_3",
            (pl.col("meta_drop-to-client") == "2") & (pl.col("server_group") == "WFC")
            | (pl.col("meta_drop-to-client") == "2_3") & (pl.col("server_group") == "IACK"),
        )

    if measurement in ["second_client_flight"]:
        # Implementations send different packets depending on server packets: WFC and IACK case
        wfc_or = [
            (
                (pl.col("client") == key)
                & (pl.col("meta_drop-to-server") == val)
                & (pl.col("server_group") == "WFC")
            )
            for key, val in snd_client_flight_wfc.items()
        ]
        iack_or = [
            (
                (pl.col("client") == key)
                & (pl.col("meta_drop-to-server") == val)
                & (pl.col("server_group") == "IACK")
            )
            for key, val in snd_client_flight_iack.items()
        ]
        f = functools.reduce(lambda a, b: a | b, wfc_or + iack_or)

        return df.filter(f)

    if measurement in ["rtt_samples"]:
        rfc_updates = (pl.col("file_size") == "10MB") & (pl.col("cc_pto") != pl.lit(None))

        # no 0/default/initialization updates should be included
        default_update = (
            (pl.col("client") != "quic-go")
            | (pl.col("data_smoothed_rtt") != 0)
            | (pl.col("data_rtt_variance") != 0)
        )
        exposes_updates = (
            (pl.col("name") == "recovery:metrics_updated") & (pl.col("time_since_first_ms") != 0)
        ) & default_update
        return df.filter(rfc_updates | expodes_updates)

    if measurement in ["rfc_pto_updates"]:
        return df.filter(pl.col("cc_pto").is_not_null())

    if measurement in ["first_pto"]:
        return get_measurement(df, "rfc_pto_updates").filter(
            (pl.col("time_since_first_ms") == pl.col("time_since_first_ms").min()).over("file"),
            pl.col("meta_name") == "all_latencies",
        )

    raise Exception("Measurement not found")


# Calculate theoretical improvement with IACK
def get_theoretical_improvement(iack_improvement=4, range=np.arange(0.5, 101, 0.5)):
    theoretical = (
        pl.DataFrame({"rtt": range})
        .with_columns(
            pto=(pl.col("rtt") + iack_improvement) * 3,
            pto_improved=pl.col("rtt") * 3,
            iack_improvement=pl.lit(iack_improvement),
        )
        .with_columns(
            improvement=pl.col("pto") - pl.col("pto_improved"),  # = 3*iack_improvement
            # Spurious retransmit if improved PTO is lower than delay to fetch certificate
            improved=pl.col("pto_improved") > iack_improvement,
        )
        .with_columns(improvement_factor=pl.col("improvement") / pl.col("rtt"))
    )
    return theoretical


# Combine two dfs with polars streaming API, to avoid exceeding the memory
def sink_parquet_and_merge_if_exists(
    current_df: pl.LazyFrame, new_df: pl.LazyFrame, out_file: str
):
    if current_df is not None:
        # Alternative of concat empty df, breaks parquet file: https://github.com/pola-rs/polars/issues/9016
        # requires temporary file (f"{out_file}.2"), because reading and sinking into the same file fails
        pl.concat([current_df, new_df.lazy()], how="diagonal").sink_parquet(f"{out_file}.2")
        os.rename(config.INTERIM_DATA_DIR / f"{out_file}.2", f"{out_file}")
    else:
        new_df.lazy().sink_parquet(out_file)


# Classify QUIC response frames
def classify_ack_and_sh_frames(df, unique):
    return (
        df.with_columns(
            # Connection close (CC) frame
            cc_in_group=pl.col("frame_type").str.contains("CC").any().over(unique),
            # ServerHello contained
            sh=pl.col("frame_type").str.contains("CRYPTO")
            & pl.col("quic.long.packet_type").str.contains("0")
            & pl.col("tls.handshake.type").str.split(",").list.contains("2"),
            # ACK in Initial
            ack=pl.col("frame_type").str.contains("ACK")
            & pl.col("quic.long.packet_type").str.contains("0"),
        )
        .with_columns(
            # Mark groups
            sh_any=pl.col("sh").any().over(unique),
            ack_any=pl.col("ack").any().over(unique),
        )
        .with_columns(
            # First ACK/SH value per group
            # & pl.col ensures that only when a value is found, the marker is set
            (
                (pl.int_range(pl.len()) == pl.col("ack").arg_max()).over(unique) & pl.col("ack")
            ).alias("ack_first"),
            ((pl.int_range(pl.len()) == pl.col("sh").arg_max()).over(unique) & pl.col("sh")).alias(
                "sh_first"
            ),
        )
        .with_columns(
            # quic-go starts PKN at 0, Initial ACKs must ACK the first packet
            # True if not an ACK
            pl.when(pl.col("ack_first"))
            .then(
                pl.col("quic.ack.first_ack_range") == "0",
            )
            .otherwise(
                # True if not the ACK packet
                pl.lit(True)
            )
            .alias("first_ack_number")
        )
    )


# Add columns comparing median differences between IACK and WFC, and potential implications on the PTO
def get_pto_improvement(
    df,
    group=["scenario", "server_group"],
    col="time_since_first_ms",
    new_col="pto_improvement",
    new_col2="improvement",
):
    return (
        df.group_by(group)
        .agg(
            pl.col(col).median(),
        )
        .pivot(group[-1], index=group[:-1])
        .sort(group[:-1])
        .with_columns(
            ((pl.col("WFC") - pl.col("IACK")) * 3).alias(new_col),
            ((pl.col("WFC") - pl.col("IACK"))).alias(new_col2),
        )
    )
