"""Numbers behind the regional-variation answer. Pure functions plus a printer.

Run:  python -m src.features.analysis
"""

import json

import numpy as np
import pandas as pd

from src import config

SETTLED_FROM = "2026-03-15"  # station coverage has stopped growing fast by mid-March
FUELS = ["E10", "E5", "diesel_standard", "diesel_premium"]


def load():
    c = config.CLEAN_DIR
    areas = pd.read_parquet(c / "regional_daily.parquet")
    spread = pd.read_parquet(c / "spread_daily.parquet")
    desnz = pd.read_parquet(c / "desnz_weekly.parquet")
    return areas, spread, desnz


def gap_table(areas: pd.DataFrame) -> pd.DataFrame:
    """Mean, day-to-day spread, and extremes of each area's gap to the UK, by fuel."""
    a = areas[areas["day"] >= SETTLED_FROM]
    t = a.groupby(["fuel", "level", "area"])["gap_pence"].agg(
        mean="mean", sd="std", low="min", high="max"
    )
    return t.round(2).reset_index()


def stability(areas: pd.DataFrame, spread: pd.DataFrame) -> pd.DataFrame:
    """Do gaps move with the price? Weekly UK change versus change in each region's gap.

    For each fuel and region: correlation of the absolute weekly UK change with the
    absolute weekly change in that region's gap, and the slope of gap change on UK change
    (pence of gap per pence of UK move; positive means gaps widen when prices rise).
    """
    a = areas[(areas["level"] == "region") & (areas["day"] >= SETTLED_FROM)]
    rows = []
    for (fuel, area), g in a.groupby(["fuel", "area"]):
        g = g.set_index("day").sort_index()
        wk = g[["uk_station_mean", "gap_pence"]].resample("W").last().diff().dropna()
        if len(wk) < 8:
            continue
        rows.append(
            {
                "fuel": fuel,
                "area": area,
                "weeks": len(wk),
                "corr_abs": wk["uk_station_mean"].abs().corr(wk["gap_pence"].abs()),
                "slope": np.polyfit(wk["uk_station_mean"], wk["gap_pence"], 1)[0],
            }
        )
    out = pd.DataFrame(rows)
    return out.round(3)


def spread_by_move(spread: pd.DataFrame) -> pd.DataFrame:
    """Average regional spread in calm weeks versus weeks with big UK price moves."""
    s = spread[spread["day"] >= SETTLED_FROM]
    out = []
    for fuel, g in s.groupby("fuel"):
        g = g.set_index("day").sort_index()
        wk = g.resample("W").agg({"uk_station_mean": "last", "spread_sd": "mean", "spread_range": "mean"})
        wk["move"] = wk["uk_station_mean"].diff().abs()
        wk = wk.dropna()
        big = wk["move"] >= wk["move"].quantile(2 / 3)
        small = wk["move"] <= wk["move"].quantile(1 / 3)
        out.append(
            {
                "fuel": fuel,
                "weeks": len(wk),
                "calm_move_p": wk.loc[small, "move"].mean(),
                "big_move_p": wk.loc[big, "move"].mean(),
                "calm_sd": wk.loc[small, "spread_sd"].mean(),
                "big_sd": wk.loc[big, "spread_sd"].mean(),
                "calm_range": wk.loc[small, "spread_range"].mean(),
                "big_range": wk.loc[big, "spread_range"].mean(),
                "corr_move_sd": wk["move"].corr(wk["spread_sd"]),
                "sd_over_price_pct": (wk["spread_sd"] / wk["uk_station_mean"] * 100).mean(),
            }
        )
    return pd.DataFrame(out).round(3)


def desnz_check(spread: pd.DataFrame, desnz: pd.DataFrame) -> pd.DataFrame:
    """FuelCosts UK station mean on each Monday against the DESNZ weekly figure."""
    pairs = {"E10": "unleaded_petrol", "E5": "unleaded_petrol", "diesel_standard": "diesel"}
    d = desnz.assign(day=pd.to_datetime(desnz["price_date"]))
    out = []
    for fuel, dz in pairs.items():
        f = spread[spread["fuel"] == fuel][["day", "uk_station_mean"]]
        m = f.merge(d[d["fuel"] == dz][["day", "pence_per_litre"]], on="day").sort_values("day")
        diff = m["uk_station_mean"] - m["pence_per_litre"]
        out.append(
            {
                "fuelcosts": fuel,
                "desnz": dz,
                "weeks": len(m),
                "mean_gap_p": diff.mean(),
                "sd_gap_p": diff.std(),
                "max_abs_gap_p": diff.abs().max(),
                "corr_levels": m["uk_station_mean"].corr(m["pence_per_litre"]),
                "corr_weekly_change": m["uk_station_mean"].diff().corr(m["pence_per_litre"].diff()),
                "first": m["day"].min().date(),
                "last": m["day"].max().date(),
            }
        )
    return pd.DataFrame(out).round(3)


def weighting_note(areas: pd.DataFrame) -> pd.DataFrame:
    """How far station-weighted and equal-region UK means differ (pence)."""
    u = areas.drop_duplicates(["day", "fuel"])
    d = (u["uk_station_mean"] - u["uk_region_mean"]).groupby(u["fuel"]).agg(["mean", "min", "max"])
    return d.round(2).reset_index()


def main() -> None:
    areas, spread, desnz = load()
    pd.set_option("display.width", 200)
    results = {
        "gaps": gap_table(areas),
        "stability": stability(areas, spread),
        "spread_by_move": spread_by_move(spread),
        "desnz_check": desnz_check(spread, desnz),
        "weighting": weighting_note(areas),
    }
    for name, df in results.items():
        print(f"\n== {name}")
        print(df.to_string(index=False))
    summary = {k: json.loads(v.to_json(orient="records", date_format="iso")) for k, v in results.items()}
    (config.CLEAN_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
