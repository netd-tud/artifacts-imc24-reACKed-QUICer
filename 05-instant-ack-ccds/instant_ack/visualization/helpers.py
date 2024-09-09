from instant_ack import config
import matplotlib.pyplot as plt
import os
import matplotlib.dates as mdates

# Configure defaults
c_default_fig_size = (6, 1.4)

c_date_formatter = mdates.DateFormatter("%Y-%m-%d")
c_date_formatter_m_d = mdates.DateFormatter("%m-%d")
c_day_locator = mdates.DayLocator()


def fig_ax(figsize=c_default_fig_size, **kwargs):
    if figsize is None:
        figsize = c_default_fig_size
    return plt.subplots(figsize=figsize, **kwargs)


# Save plot as pdf and png
def save_plot(fig, destination, folder=config.FIGURES_DIR, autoclose=False):
    if destination is not None:
        dir = os.path.dirname(folder / destination)
        os.makedirs(dir, exist_ok=True)

        fig.savefig(f"{folder / destination}.png", bbox_inches="tight", dpi=200)
        fig.savefig(f"{folder / destination}.pdf", bbox_inches="tight")

    if autoclose:
        plt.close()


# Autogenerate tick_locations for MultipleLocator
def tick_locations(diff: float):
    major = 2
    minor = 1
    if diff >= 4000:
        print("4k")
        major = 800
        minor = 200
    elif diff >= 2000:
        major = 400
        minor = 100
    elif diff >= 1000:
        major = 200
        minor = 50
    elif diff >= 300:
        major = 100
        minor = 25
    elif diff >= 60:
        major = 20
        minor = 5
    elif diff >= 30:
        major = 10
        minor = 2
    return major, minor
