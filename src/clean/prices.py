"""Pure price rules: unit fix and quality flags. No file access, so easy to test.

Nothing here deletes a row. Each rule adds a flag column instead.
"""

import numpy as np
import pandas as pd

MIN_PENCE = 80.0
MAX_PENCE = 300.0
JUMP_LIMIT = 0.30  # a move of more than 30% between two readings of one station and fuel
STALE_DAYS = 30  # a price set more than 30 days before we first saw it


def fix_units(pence: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Turn prices written in pounds (1.339) into pence (133.9).

    Rule: a value from 0.8 to 3.0 that is not a whole number is pounds. Whole
    numbers (1.0, 2.0) are placeholders, not prices, so they are left alone and
    caught by the range flag. Returns the fixed prices and a True/False column
    saying which were changed.
    """
    is_pounds = (pence >= 0.8) & (pence <= 3.0) & (pence != pence.round())
    return pence.where(~is_pounds, (pence * 100).round(2)), is_pounds


def flag_out_of_range(pence: pd.Series) -> pd.Series:
    return (pence < MIN_PENCE) | (pence > MAX_PENCE) | pence.isna()


def flag_jumps(df: pd.DataFrame) -> pd.Series:
    """True where a price moves more than 30% from the same station's previous reading.

    Expects columns node_id, fuel_type, price_pence (after unit fix), ordered
    in time within each station and fuel. The previous reading is used whatever
    its quality, so a bad value flags both itself and the reading after it.
    """
    prev = df.groupby(["node_id", "fuel_type"], sort=False)["price_pence"].shift(1)
    change = (df["price_pence"] / prev - 1).abs()
    return (change > JUMP_LIMIT).fillna(False)


def flag_stale(source_updated_at: pd.Series, recorded_at: pd.Series) -> pd.Series:
    """True where the station set the price more than 30 days before we first saw it."""
    age = recorded_at - source_updated_at
    return (age > pd.Timedelta(days=STALE_DAYS)).fillna(False)


def flag_bad_coordinates(lat: pd.Series, lon: pd.Series) -> pd.Series:
    """True for missing, zero, or outside-the-UK coordinates (rough box, with sea margin)."""
    missing = lat.isna() | lon.isna() | ((lat == 0) & (lon == 0))
    outside = ~lat.between(49.8, 60.95) | ~lon.between(-8.8, 1.9)
    return missing | outside


def distance_km(lat1, lon1, lat2, lon2):
    """Straight-line distance over the earth's surface (haversine formula)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dlmb = p2 - p1, np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))
