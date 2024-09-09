from instant_ack import vh
from instant_ack import config
import matplotlib.ticker as ticker
import seaborn as sns
import polars as pl
import pandas as pd
import numpy as np
from matplotlib.offsetbox import AnchoredText
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from instant_ack.data import validation as v
from datetime import datetime



# Defaults
tab20 = sns.color_palette("tab20")
palette = {
    "ACK": tab20[2],
    "IACK": tab20[2],
    "ACK,SH": tab20[0],
    "ACK,CRYPTO": tab20[0],
    "CRYPTO": tab20[3],
    "SH": tab20[3],
    "ACK,PING": tab20[5],
}



# Plotting functions below will generally follow the following structure
# 1. Validate plotting data (Is there the expected number of datapoints)
# 2. Plot
# 3. Configure ax
# 4. Save plot


# Generate Stripplot
def strip(
    df,
    xlabel="Time to First Byte (TTFB) [ms]",
    x="time_since_first_ms",
    y="client",
    ylabel="Client",
    hue="server_group",
    legend_label=None,
    legend_pos="upper center",
    legend_ncol=3,
    xMinorLocator=ticker.MultipleLocator(1),
    xMajorLocator=ticker.MultipleLocator(5),
    xlim=None,
    dest=None,
    figsize=(6, 1.4),
    median=True,
    fig=None,
    ax=None,
    legend=True,
    validate=100,
    validate_ignore=[],
    xscale=None,
):
    if (fig is None) and (ax is None):
        fig, ax = vh.fig_ax(figsize)

    if validate:
        v.validate(df, [y, hue], expected_repetitions=validate, ignore=validate_ignore)

    df = df.select(x, y, hue)

    sns.stripplot(
        df.sort(hue, descending=True),
        x=x,
        y=y,
        hue=hue,
        jitter=False,
        dodge=True,
        marker="d",
        alpha=0.15,
        ax=ax,
    )

    # Show median marker
    if median:
        median = df.group_by([y, hue]).agg(pl.col(x).median()).sort(hue, descending=True)
        # Overlay median values
        sns.stripplot(
            median,
            x=x,
            y=y,
            hue=hue,
            ax=ax,
            palette="dark:black",
            zorder=100,
            dodge=True,
            jitter=False,
            marker="|",
            linewidth=1,
        )

        h, l = ax.get_legend_handles_labels()
        for handle in h:
            handle.set_alpha(1)
        h = h[:3]
        l = l[:3]
        l[-1] = "Median"

        if legend:
            ax.legend(
                h,
                l,
                title=legend_label,
                ncol=legend_ncol,
                loc=legend_pos,
            )

    if not legend:
        ax.legend().remove()

    ax.set(xlabel=xlabel)
    ax.set(ylabel=ylabel)

    if xscale:
        ax.set(xscale=xscale)
    
    if xMajorLocator:
        ax.xaxis.set_major_locator(xMajorLocator)
    if xMinorLocator:
        ax.xaxis.set_minor_locator(xMinorLocator)
    ax.set(xlim=xlim)

    if dest is not None:
        vh.save_plot(fig, dest)


# Heatmap
def ack_hm(df, figsize=(5.5, 1.2), round_pos=1, dest=None):
    fig, ax = vh.fig_ax(figsize=figsize)

    d = df.with_columns(
        (pl.all().exclude("frame_type") / pl.all().exclude("frame_type").sum() * 100).round(
            round_pos
        )
    )

    # Replace values for better readability
    annot = (
        d.to_pandas()
        .set_index("frame_type")
        .replace({0.0: "<0.1"})
        .astype("str")
        .replace({"NaN": np.nan, "100.0": "100"})
    )

    sns.heatmap(
        d.to_pandas().set_index("frame_type"),
        yticklabels=True,
        cbar_kws={"label": "Frequency [%]", "ticks": [100, 80, 60, 40, 20, 0]},
        cmap="coolwarm",
        annot=annot,
        fmt="s",
    )

    ax.set(ylabel="Frame(s) in \nfirst packet")
    ax.set(xlabel="CDN (# domains)")
    ax.tick_params(
        axis="x",
        rotation=40,
    )
    ax.set_xticklabels(ax.get_xticklabels(), ha="right", va="top", rotation_mode="anchor")
    vh.save_plot(fig, dest)


# ECDF
def ecdf(
    df,
    x="diff_ms",
    hue="CDN",
    figsize=(6, 1.7),
    legend_ncol=2,
    dest=None,
    legend_pos="lower left",
    ax=None,
    legend=None,
    bbox_to_anchor=None,
    xMinorLocator=None,
    xMajorLocator=None,
    xlabel="Delay between ACK and SH [ms]",
    ylabel="CDF",
    y=None,
    fig=None,
    xlim=None,
    xscale="log",
    **kwargs,
):
    if ax is None:
        fig, ax = vh.fig_ax(figsize=figsize)

    sns.ecdfplot(df.sort(hue), x=x, hue=hue, ax=ax, **kwargs)

    ax.set(ylim=(-0.05, 1.05))
    if xlim:
        ax.set(xlim=xlim)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.25))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.05))
    ax.set(xlabel=xlabel)
    ax.set(ylabel=ylabel)
    ax.set(xscale=xscale)
    if legend:
        sns.move_legend(
            ax,
            legend_pos,
            ncol=legend_ncol,
            title=None,
            bbox_to_anchor=bbox_to_anchor,
            columnspacing=0.5,
        )
    else:
        ax.get_legend().remove()

    if fig is not None:
        vh.save_plot(fig, dest)


# Lineplot
def line(
    df,
    x="measurement_ts",
    y="median",
    hue="frame_type",
    figsize=(6, 1.3),
    legend_ncol=3,
    dest=None,
    legend_pos="lower left",
    ax=None,
    legend=None,
    bbox_to_anchor=None,
    palette=palette,
    ylabel="Median time since\nClientHello [ms]",
    xMajorFormatter=mdates.DateFormatter("%m-%d"),
    xMinorFormatter=mdates.HourLocator(interval=4),
    xMinorLocator=None,
    xMajorLocator=None,
    yMinorLocator=None,
    yMajorLocator=None,
    xlabel="Date MM-DD [h]",
    fig=None,
    xlim=None,
    ylim=None,
    **kwargs,
):

    if ax is None:
        fig, ax = vh.fig_ax(figsize=figsize)

    sns.lineplot(df, x=x, y=y, ax=ax, hue=hue, palette=palette, **kwargs)
    if legend:
        ax.legend(
            title=None,
            ncol=legend_ncol,
            loc=legend_pos,
            bbox_to_anchor=bbox_to_anchor,
        )
    else:
        ax.get_legend().remove()
    ax.set(ylabel=ylabel)

    if xMajorFormatter:
        ax.xaxis.set_major_formatter(xMajorFormatter)
        ax.xaxis.set_minor_locator(xMinorFormatter)
    if yMajorLocator:
        ax.yaxis.set_major_locator(yMajorLocator)
        ax.yaxis.set_minor_locator(yMinorLocator)

    if xlim:
        ax.set(xlim=xlim)
    else:
        ax.set(xlim=(df[x].min(), df[x].max()))
    ax.set(ylim=ylim)

    ax.set(xlabel=xlabel)

    vh.save_plot(fig, dest)


# Multiple subplots
def multi(
    df: pl.DataFrame,
    group_by: str,
    figsize,
    x: str,
    y: str,
    dest: str = None,
    legend_pos="upper center",
    legend_ncol=1,
    xlabel="TTFB [ms]",
    anc_text_prefix: str = "Emulated RTT: ",
    anc_text_suffix: str = " ms",
    anc_loc="lower center",
    inner=strip,
    auto_scale_x=True,
    xMinorLocator=None,
    xMajorLocator=None,
    sharex=True,
    ylim=None,
    xlim=None,
    supylabel=None,
    first_anc_loc=None,
    hk_special=False,
    anc=True,
    major=None,
    minor=None,
    **kwargs,
):

    ngroups = df.select(pl.col(group_by).n_unique()).item()

    fig, ax = vh.fig_ax(figsize=figsize, nrows=ngroups, sharex=sharex)
    for ind, (gname, gdata) in enumerate(df.group_by(group_by, maintain_order=True)):
        group_val = gname[0]

        current_ax = ax[ind]

        current_ylim = ylim
        if isinstance(ylim, list):
            current_ylim = ylim[ind]
            
        current_xlim = xlim
        if isinstance(xlim, list):
            current_xlim = xlim[ind]
            
        current_anc_loc = anc_loc
        legend = False
        if ind == 0:
            legend = True
            if first_anc_loc:
                current_anc_loc = first_anc_loc
        # Xlabel only for last row
        current_xlabel = xlabel
        if ind != ngroups - 1:
            current_xlabel = None

        # xdiff
        diff = gdata.select(pl.col(x).max() - pl.col(x).min()).item(0, 0)
        if auto_scale_x:
            major, minor = vh.tick_locations(diff)
            xMinorLocator = ticker.MultipleLocator(minor)
            xMajorLocator = ticker.MultipleLocator(major)
        else: 
            if isinstance(major, list) and isinstance(minor, list):
                xMinorLocator = ticker.MultipleLocator(minor[ind])
                xMajorLocator = ticker.MultipleLocator(major[ind])

        # Special case for vantage point outages
        # sns will otherwise connect lines
        if hk_special and ("Hongkong" in gname[0]):
            inner(
                gdata.filter(pl.col("measurement_ts") <= datetime(2024, 8, 19, 21)).with_columns(pl.col("geo_location").replace("Hongkong", "Hong Kong"))
,
                legend_pos=legend_pos,
                xMinorLocator=xMinorLocator,
                xMajorLocator=xMajorLocator,
                ax=current_ax,
                legend_ncol=legend_ncol,
                legend=legend,
                xlabel=current_xlabel,
                y=y,
                **kwargs,
            )

            inner(
                gdata.filter(
                    pl.col("measurement_ts") >= datetime(2024, 8, 20, 10),
                    pl.col("measurement_ts") <= datetime(2024, 8, 21, 19),
                ).with_columns(pl.col("geo_location").replace("Hongkong", "Hong Kong"))
,
                legend_pos=legend_pos,
                xMinorLocator=xMinorLocator,
                xMajorLocator=xMajorLocator,
                ax=current_ax,
                legend_ncol=legend_ncol,
                legend=legend,
                xlabel=current_xlabel,
                y=y,
                **kwargs,
            )
        else:
            inner(
                gdata,
                legend_pos=legend_pos,
                xMinorLocator=xMinorLocator,
                xMajorLocator=xMajorLocator,
                ax=current_ax,
                legend_ncol=legend_ncol,
                legend=legend,
                xlabel=current_xlabel,
                y=y,
                **kwargs,
            )
        current_ax.set(ylim=current_ylim)
        current_ax.set(xlim=current_xlim)

        text_box = AnchoredText(
            f"{anc_text_prefix}{group_val}{anc_text_suffix}",
            frameon=False,
            loc=current_anc_loc,
            pad=0,
            prop={"backgroundcolor": "lightgrey"},
        )
        if anc:
            current_ax.add_artist(text_box)
    if supylabel:
        fig.supylabel(supylabel, fontsize="medium")

    plt.tight_layout()
    vh.save_plot(fig, dest)


def scatter_improvement_factors(
    data,
    theo,
    theo2,
    y="median_improvement_factor",
    dest_file=None,
    ylim=None,
    xlim=None,
    figsize=(6, 1.5),
    legend=True,
    ncol=3,
):

    fig, ax = vh.fig_ax(figsize=(figsize))
    # Theoretical information
    label = "Theoretic\nImprovement"
    sns.lineplot(
        theo2,
        x="rtt",
        y="improvement_factor",
        ls=":",
        color="grey",
        label=None,
        ax=ax,
        alpha=0.8,
    )
    sns.lineplot(
        theo,
        x="rtt",
        y="improvement_factor",
        ls=":",
        color="grey",
        label=label,
        ax=ax,
        alpha=0.8,
    )
    ax.set(xlabel="Emulated RTT [ms]")
    ax.set(ylabel="Improvement Factor [#]")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

    # ax.text(theo.iloc[2].rtt, theo.iloc[0].improvement_factor, , color="grey", label,
    #        verticalalignment="center")

    # Real data
    data = data.rename({"client": "Client"})

    sns.scatterplot(
        data,
        x="rtt",
        y=y,
        hue="Client",
        ax=ax,
        palette="tab10",
        alpha=0.9,
        style="Client",
    )
    ax.set(xlabel="Emulated RTT [ms]")
    ax.set(ylabel="Median First PTO\nImprovement [RTT]")

    handles, labels = ax.get_legend_handles_labels()

    from matplotlib.patches import Patch

    handles = handles[1:] + handles[:1]
    labels = labels[1:] + labels[:1]

    # handles = handles[1:] + [Patch(color="none")] + handles[:1]
    # labels = labels[1:] + [""] + labels[:1]
    if not legend:
        ax.legend().remove()
    else:
        ax.legend(title=None, handles=handles, labels=labels, ncol=ncol)

    ax.set(xlim=xlim)
    ax.set(ylim=ylim)
    # ax.set(yscale="log")
    vh.save_plot(fig, dest_file, autoclose=False)
