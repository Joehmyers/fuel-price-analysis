"""Charts for docs/research/desnz-retreat.md. Writes PNG files to docs/research/figures/.

Run:  python -m src.features.note_charts
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402
from src.features import analysis  # noqa: E402

OUT = config.ROOT / "docs" / "research" / "figures"
BLUE, ORANGE, GREY = "#1f5fa8", "#d9822b", "#8a8a8a"


def _clean(ax):
    ax.spines[["top", "right"]].set_visible(False)


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    path = OUT / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(path)


def coverage():
    rows = [
        ("ONS consumer prices (monthly, UK)", "1988-01-01", "2026-11-17", GREY),
        ("DESNZ weekly pump price (UK)", "2003-06-09", "2026-11-17", BLUE),
        ("FuelCosts station prices (all four countries)", "2026-02-09", "2026-11-17", ORANGE),
    ]
    fig, ax = plt.subplots(figsize=(9, 2.6))
    for i, (label, start, end, colour) in enumerate(rows):
        ax.barh(i, (pd.Timestamp(end) - pd.Timestamp(start)).days, left=mdates.date2num(pd.Timestamp(start)),
                color=colour, height=0.55)
        ax.text(mdates.date2num(pd.Timestamp("1986-01-01")), i, label + "  ", ha="right", va="center", fontsize=9)
    ax.set_yticks([])
    ax.xaxis_date()
    ax.set_xlim(mdates.date2num(pd.Timestamp("1988-01-01")), mdates.date2num(pd.Timestamp("2027-01-01")))
    ax.invert_yaxis()
    ax.set_title("How far back each source reaches", loc="left")
    _clean(ax)
    fig.subplots_adjust(left=0.42)
    fig.savefig(OUT / "coverage.png", dpi=150) if OUT.exists() else None
    plt.close(fig)


def long_series(desnz: pd.DataFrame):
    w = desnz.assign(d=pd.to_datetime(desnz["price_date"])).pivot(
        index="d", columns="fuel", values="pence_per_litre"
    )
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(w.index, w["unleaded_petrol"], color=BLUE, lw=1.4, label="Unleaded petrol")
    ax.plot(w.index, w["diesel"], color=ORANGE, lw=1.4, label="Diesel")
    ax.axvspan(pd.Timestamp("2026-02-09"), w.index[-1], color=GREY, alpha=0.25, lw=0)
    ax.annotate("Nine months of\nstation data", (pd.Timestamp("2026-02-09"), 85), xytext=(-95, 5),
                textcoords="offset points", fontsize=8, arrowprops={"arrowstyle": "-", "color": GREY})
    for when, text, y in [("2008-07-07", "2008", 137), ("2022-07-04", "2022", 200)]:
        ax.annotate(text, (pd.Timestamp(when), y), ha="center", fontsize=8)
    ax.set_ylabel("Pence per litre")
    ax.set_title("UK weekly pump price, June 2003 to November 2026", loc="left")
    ax.legend(frameon=False, loc="upper left")
    _clean(ax)
    _save(fig, "desnz_long_series.png")


def petrol_vs_diesel(desnz: pd.DataFrame):
    w = desnz.assign(d=pd.to_datetime(desnz["price_date"])).pivot(
        index="d", columns="fuel", values="pence_per_litre"
    )
    c = w.diff().dropna()
    r = c["unleaded_petrol"].corr(c["diesel"])
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.scatter(c["unleaded_petrol"], c["diesel"], s=8, color=BLUE, alpha=0.5, lw=0)
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_xlabel("Petrol: change since last week (p/litre)")
    ax.set_ylabel("Diesel: change since last week (p/litre)")
    ax.set_title(f"Weekly moves, 2003 to 2026: correlation {r:.2f}", loc="left", fontsize=10)
    _clean(ax)
    _save(fig, "petrol_vs_diesel_weekly.png")


def regional_gaps(areas: pd.DataFrame):
    a = areas[(areas["level"] == "region") & (areas["fuel"] == "E10") & (areas["day"] >= analysis.SETTLED_FROM)]
    t = a.groupby("area")["gap_pence"].agg(["mean", "min", "max"]).sort_values("mean")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for i, (area, row) in enumerate(t.iterrows()):
        colour = ORANGE if area == "Northern Ireland" else BLUE
        ax.plot([row["min"], row["max"]], [i, i], color=colour, lw=3, alpha=0.35, solid_capstyle="round")
        ax.plot(row["mean"], i, "o", color=colour)
    ax.set_yticks(range(len(t)), t.index)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Pence per litre against the UK average (dot = average, bar = lowest to highest day)")
    ax.set_title("E10 petrol: how far each region sits from the UK price, March to November 2026", loc="left", fontsize=10)
    _clean(ax)
    _save(fig, "regional_gaps_E10.png")


def relative_dispersion(areas: pd.DataFrame, spread: pd.DataFrame):
    """Regional spread as a percentage of the UK price, with and without Northern Ireland."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, fuel, title in zip(axes, ["E10", "diesel_standard"], ["E10 petrol", "Standard diesel"], strict=True):
        s = spread[(spread["fuel"] == fuel) & (spread["day"] >= analysis.SETTLED_FROM)].set_index("day")
        r = areas[(areas["level"] == "region") & (areas["fuel"] == fuel) & (areas["area"] != "Northern Ireland")]
        sd_gb = r[r["day"] >= analysis.SETTLED_FROM].groupby("day")["mean_pence"].std()
        ax.plot(s.index, s["spread_sd"] / s["uk_station_mean"] * 100, color=ORANGE, lw=1.4, label="All 12 regions")
        ax.plot(sd_gb.index, sd_gb / s["uk_station_mean"].reindex(sd_gb.index) * 100, color=GREY, lw=1.4,
                label="Without Northern Ireland")
        ax.set_title(title, loc="left", fontsize=10)
        ax.tick_params(axis="x", labelrotation=45)
        _clean(ax)
    axes[0].set_ylabel("Spread across regions,\nas % of the UK price")
    axes[0].legend(frameon=False, fontsize=8)
    fig.suptitle("Relative dispersion: regional spread as a share of the price", x=0.01, ha="left", fontsize=11)
    _save(fig, "relative_dispersion.png")


def real_vs_nominal():
    """Nominal and inflation-adjusted DESNZ prices, in the money of September 2026."""
    d = pd.read_parquet(config.CLEAN_DIR / "desnz_real.parquet")
    d["day"] = pd.to_datetime(d["price_date"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, fuel, title in zip(axes, ["unleaded_petrol", "diesel"], ["Unleaded petrol", "Diesel"], strict=True):
        x = d[d["fuel"] == fuel].set_index("day")
        ax.plot(x.index, x["pence_per_litre"], color=GREY, lw=1.2, label="As published")
        ax.plot(x.index, x["real_pence_asof"] * 144.1 / 100, color=BLUE, lw=1.4,
                label="Adjusted for inflation (Sep 2026 money)")
        ax.set_title(title, loc="left", fontsize=10)
        _clean(ax)
    axes[0].set_ylabel("Pence per litre")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("UK weekly pump price, as published and adjusted for inflation", x=0.01, ha="left", fontsize=11)
    _save(fig, "real_vs_nominal.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    areas, _, desnz = analysis.load()
    spread = analysis.load()[1]
    coverage()
    print(OUT / "coverage.png")
    long_series(desnz)
    petrol_vs_diesel(desnz)
    regional_gaps(areas)
    relative_dispersion(areas, spread)
    real_vs_nominal()


if __name__ == "__main__":
    main()
