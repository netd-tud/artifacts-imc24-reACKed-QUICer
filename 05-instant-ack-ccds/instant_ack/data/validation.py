import polars as pl


# Validate the number of datapoints within the group to match expected_repetitions
def validate(
    df: pl.DataFrame,
    group=["folder", "scenario"],
    unique_prop: str = "file",
    expected_repetitions: str = 100,
    ignore: list[str] = [],
):
    res = df
    if "folder" in df.columns:
        res = (
            df.filter(
                ~pl.selectors.by_name("folder").is_in(ignore),
            )
            .group_by(group)
            .agg(
                pl.col(unique_prop).n_unique().name.suffix("_n"),
                pl.col("folder").unique().name.suffix("_unique"),
            )
            .with_columns(
                pl.selectors.by_name(["folder_unique"], require_all=False)
                .list.len()
                .name.suffix("_len")
            )
            .lazy()
            .collect()
        )
    else:
        res = (
            df.group_by(group)
            .agg(
                pl.col(unique_prop).n_unique().name.suffix("_n"),
            )
            .lazy()
            .collect()
        )

    all_expected = res.select((pl.col(unique_prop + "_n") == expected_repetitions).all())[0, 0]

    if all_expected:
        print(f"All groups of {group} had {expected_repetitions} unique {unique_prop}s. All OK!")
        return None
    else:
        print(
            f"NOT all groups of {group} had {expected_repetitions} unique {unique_prop}s. You may want to verify what happened to the subsequent folders"
        )
        display(res.filter(pl.col(unique_prop + "_n") != expected_repetitions).sort(group[0]))

    return res
