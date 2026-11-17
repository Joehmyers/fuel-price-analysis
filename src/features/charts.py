"""Charts for the regional-variation report. Writes PNG files to reports/.

Run:  python -m src.features.charts
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402
from src.features import analysis  # noqa: E402

LABELS = {"E10": "E10 petrol", "diesel_standard": "Standard diesel", "E5": "E5 petrol",
          "diesel_premium": "Premium diesel"}  # fmt: skip
GREY, BLUE, ORANGE = "#8a8a8a", "#1f5fa8", "#d9822b"


def gap_chart(areas: pd.DataFrame, fuel: str):
    r = areas[(areas["level"] == "region") & (areas["fuel"] == fuel)]
    r = r[r["day"] >= analysis.SETTLED_FROM]
    wide = r.pivot(index="day", columns="area", values="gap_pence").rolling(7, min_periods=4).mean()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={"width_ratios": [2.2, 1]})
    for area in wide.columns.drop("Northern Ireland"):
        ax1.plot(wide.index, wide[area], color=GREY, lw=1, alpha=0.7)
        ax1.text(wide.index[-1], wide[area].iloc[-1], " " + area, fontsize=7, va="center")
    ax1.axhline(0, color="black", lw=0.8)
    ax1.set_title("English regions, Scotland and Wales")
    ax1.set_ylabel("Pence per litre above (+) or below (-) the UK average")
    ax1.set_xlim(wide.index[0], wide.index[-1] + pd.Timedelta(days=45))
    ax2.plot(wide.index, wide["Northern Ireland"], color=ORANGE, lw=1.6)
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_title("Northern Ireland")
    for ax in (ax1, ax2):
        ax.tick_params(axis="x", labelrotation=45)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{LABELS[fuel]}: gap to UK average by region (7-day average)")
    fig.tight_layout()
    path = config.REPORTS_DIR / f"gap_by_region_{fuel}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def spread_chart(areas: pd.DataFrame, spread: pd.DataFrame, fuel: str):
    s = spread[(spread["fuel"] == fuel) & (spread["day"] >= analysis.SETTLED_FROM)].set_index("day")
    r = areas[(areas["level"] == "region") & (areas["fuel"] == fuel) & (areas["area"] != "Northern Ireland")]
    sd_no_ni = r[r["day"] >= analysis.SETTLED_FROM].groupby("day")["mean_pence"].std()
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    top.plot(s.index, s["uk_station_mean"], color=BLUE, lw=1.6)
    top.set_ylabel("UK average price (p/litre)")
    bottom.plot(s.index, s["spread_sd"], color=ORANGE, lw=1.4, label="All 12 regions")
    bottom.plot(sd_no_ni.index, sd_no_ni, color=GREY, lw=1.4, label="Without Northern Ireland")
    bottom.set_ylabel("Spread across regions\n(standard deviation, p)")
    bottom.legend(frameon=False)
    bottom.tick_params(axis="x", labelrotation=45)
    for ax in (top, bottom):
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{LABELS[fuel]}: UK price (top) and regional spread (bottom)")
    fig.tight_layout()
    path = config.REPORTS_DIR / f"spread_vs_price_{fuel}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    config.REPORTS_DIR.mkdir(exist_ok=True)
    areas, spread, _ = analysis.load()
    for fuel in ("E10", "diesel_standard"):
        print(gap_chart(areas, fuel))
        print(spread_chart(areas, spread, fuel))


if __name__ == "__main__":
    main()
