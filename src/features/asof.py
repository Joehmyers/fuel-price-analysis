"""Point-in-time views of prices: only what was public at a given moment.

This is the guard against look-ahead. A price counts only once its
`published_at` time has passed, whatever day it covers.
"""

import pandas as pd

MAX_PRICE_AGE_DAYS = 30  # a price older than this when we look is dropped as out of date


def usable(prices: pd.DataFrame) -> pd.DataFrame:
    """Rows with none of the quality flags set (flags never delete rows; this filters a view)."""
    bad = prices[["flag_out_of_range", "flag_jump", "flag_bad_coordinates"]].any(axis=1)
    return prices[~bad]


def state_as_of(prices: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """The latest published price per station and fuel at time `as_of` (UTC).

    A row is visible only if published_at <= as_of. Among visible rows the one
    published latest wins; ties go to the row whose price was set later.
    """
    visible = prices[prices["published_at"] <= as_of]
    visible = visible.sort_values(["published_at", "source_updated_at"])
    latest = visible.groupby(["node_id", "fuel"], sort=False).tail(1).copy()
    latest["age_days"] = (as_of - latest["source_updated_at"]).dt.total_seconds() / 86400
    return latest[latest["age_days"] <= MAX_PRICE_AGE_DAYS]


def daily_state(prices: pd.DataFrame, days: pd.DatetimeIndex, tz: str) -> pd.DataFrame:
    """For each local day, the state of every station and fuel at the end of that day.

    Row for day D uses only prices with published_at before the end of D, so it
    can be used to explain day D but not earlier days. `days` are naive dates.
    """
    keys = prices[["node_id", "fuel"]].drop_duplicates()
    grid = keys.merge(pd.DataFrame({"day": days}), how="cross")
    grid["day_end"] = (
        grid["day"].dt.tz_localize(tz) + pd.Timedelta(days=1)
    ).dt.tz_convert("UTC")
    left = grid.sort_values("day_end")
    right = prices.sort_values("published_at")
    # merge_asof takes the last price published at or before the end of the day.
    merged = pd.merge_asof(
        left,
        right[["node_id", "fuel", "published_at", "source_updated_at", "price_pence"]],
        left_on="day_end",
        right_on="published_at",
        by=["node_id", "fuel"],
        direction="backward",
    )
    merged["age_days"] = (merged["day_end"] - merged["source_updated_at"]).dt.total_seconds() / 86400
    merged = merged.dropna(subset=["price_pence"])
    return merged[merged["age_days"] <= MAX_PRICE_AGE_DAYS]
