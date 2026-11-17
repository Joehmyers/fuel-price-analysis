"""Daily regional price gaps and spread, from FuelCosts station prices.

For each day and fuel (E10, E5, diesel_standard, diesel_premium):
  - mean price for each country and each region
  - UK mean, two ways: over all stations (uk_station_mean) and the plain mean of
    the 12 region means (uk_region_mean)
  - gap_pence: region mean minus the station-weighted UK mean
  - spread across the 12 region means: standard deviation and range

Each day uses only prices published by the end of that day (see asof.py).

Run:  python -m src.features.regional
"""

import pandas as pd

from src import config
from src.features import asof

FUELS = ["E10", "E5", "diesel_standard", "diesel_premium"]
START = "2026-02-09"  # first full day after the first load on 7 Feb
MIN_STATIONS = 5  # a region-day with fewer stations is dropped


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = pd.read_parquet(config.CLEAN_DIR / "fuelcosts_prices.parquet")
    stations = pd.read_parquet(config.CLEAN_DIR / "stations.parquet")
    prices = asof.usable(prices)
    prices = prices[prices["fuel"].isin(FUELS)]
    open_ids = stations.loc[
        ~stations["is_permanently_closed"].fillna(False).astype(bool), "node_id"
    ]
    prices = prices[prices["node_id"].isin(open_ids)]
    days = pd.date_range(START, pd.Timestamp(prices["published_at"].max()).date())
    state = asof.daily_state(prices, days, config.UK_TZ)
    state = state.merge(stations[["node_id", "country", "region"]], on="node_id")

    def summarise(by: str) -> pd.DataFrame:
        g = state.groupby(["day", "fuel", by])["price_pence"]
        out = g.agg(mean_pence="mean", n_stations="size").reset_index()
        out = out.rename(columns={by: "area"})
        out["level"] = by
        return out[out["n_stations"] >= MIN_STATIONS]

    areas = pd.concat([summarise("country"), summarise("region")], ignore_index=True)
    uk = state.groupby(["day", "fuel"])["price_pence"].agg(
        uk_station_mean="mean", uk_n_stations="size"
    )
    regions = areas[areas["level"] == "region"]
    uk["uk_region_mean"] = regions.groupby(["day", "fuel"])["mean_pence"].mean()
    areas = areas.merge(uk.reset_index(), on=["day", "fuel"])
    areas["gap_pence"] = areas["mean_pence"] - areas["uk_station_mean"]

    spread = regions.merge(uk.reset_index()[["day", "fuel", "uk_station_mean"]], on=["day", "fuel"])
    spread = spread.groupby(["day", "fuel"]).agg(
        regions=("area", "size"),
        spread_sd=("mean_pence", "std"),
        spread_range=("mean_pence", lambda s: s.max() - s.min()),
        uk_station_mean=("uk_station_mean", "first"),
    ).reset_index()
    return areas, spread


def main() -> None:
    areas, spread = build()
    areas.to_parquet(config.CLEAN_DIR / "regional_daily.parquet", index=False)
    spread.to_parquet(config.CLEAN_DIR / "spread_daily.parquet", index=False)
    print(f"regional_daily: {len(areas):,} rows; days {areas.day.min().date()} to {areas.day.max().date()}")
    print(f"spread_daily: {len(spread):,} rows")
    print(spread.groupby("fuel")[["uk_station_mean", "spread_sd", "spread_range", "regions"]].mean().round(2).to_string())


if __name__ == "__main__":
    main()
