"""Clean the FuelCosts price history into data/clean/fuelcosts_prices.parquet.

Keeps every row. Adds: fixed pence, a unit-fixed marker and four flag columns.

Two times per price:
  price_date    the day the price covers (the day the station set it, UK time)
  published_at  when it became public to us: the time FuelCosts first recorded it
                (never earlier than the station's own set time)

Run:  python -m src.clean.fuelcosts
"""

import pandas as pd

from src import config
from src.clean import prices

FUEL_NAMES = {
    "E10": "E10",
    "E5": "E5",
    "B7_STANDARD": "diesel_standard",
    "B7_PREMIUM": "diesel_premium",
    "HVO": "hvo",
    "B10": "b10",
}


def clean(raw: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["source_updated_at"] = pd.to_datetime(df["source_updated_at"], utc=True, format="ISO8601")
    df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True, format="ISO8601")
    df["fuel"] = df["fuel_type"].map(FUEL_NAMES).fillna(df["fuel_type"].str.lower())
    df = df.sort_values(
        ["node_id", "fuel_type", "source_updated_at", "recorded_at"], kind="stable"
    ).reset_index(drop=True)

    df["price_pence_raw"] = df["price_pence"]
    df["price_pence"], df["unit_fixed"] = prices.fix_units(df["price_pence_raw"])
    df["flag_out_of_range"] = prices.flag_out_of_range(df["price_pence"])
    df["flag_jump"] = prices.flag_jumps(df)
    df["flag_stale"] = prices.flag_stale(df["source_updated_at"], df["recorded_at"])

    df["price_date"] = df["source_updated_at"].dt.tz_convert(config.UK_TZ).dt.date
    df["published_at"] = df[["source_updated_at", "recorded_at"]].max(axis=1)

    bad_station = stations.set_index("node_id")["flag_bad_coordinates"]
    df["flag_bad_coordinates"] = df["node_id"].map(bad_station).fillna(True).astype(bool)
    keep = [
        "node_id", "fuel", "price_pence_raw", "price_pence", "unit_fixed", "price_date",
        "published_at", "source_updated_at", "recorded_at", "flag_out_of_range", "flag_jump",
        "flag_stale", "flag_bad_coordinates",
    ]  # fmt: skip
    return df[keep]


def main() -> None:
    path = sorted((config.RAW_DIR / "fuelcosts").glob("*__price_history.csv"))[-1]
    raw = pd.read_csv(path)
    stations = pd.read_parquet(config.CLEAN_DIR / "stations.parquet")
    df = clean(raw, stations)
    out = config.CLEAN_DIR / "fuelcosts_prices.parquet"
    df.to_parquet(out, index=False)
    print(f"wrote {out}: {len(df):,} rows (raw had {len(raw):,})")
    print(f"price_date {df.price_date.min()} to {df.price_date.max()}")
    print(f"published_at {df.published_at.min()} to {df.published_at.max()}")
    print(df["fuel"].value_counts().to_string())
    flags = [c for c in df.columns if c.startswith("flag_")] + ["unit_fixed"]
    print(df[flags].sum().to_string())
    print("rows with no station match:", int((~df.node_id.isin(stations.node_id)).sum()))


if __name__ == "__main__":
    main()
