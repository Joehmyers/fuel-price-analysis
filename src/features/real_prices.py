"""Inflation-adjusted (real) DESNZ fuel prices, using only CPI that was public in time.

For each weekly price, the CPI used is the latest monthly figure that ONS had
released by the time the price itself became public (`published_at`). So a
forecast made on a given day never uses an inflation figure from the future.

Real price (pence of 2015) = nominal pence x 100 / CPI (2015 = 100).
2015 pence is a fixed base, so old real prices do not change when new CPI arrives.

Months before November 2015 have no known ONS release date. We assume the
usual timing: the 15th of the following month at 07:00 UK time, and mark those
rows `cpi_release_source = "assumed_15th"`.

Run:  python -m src.features.real_prices
"""

import pandas as pd

from src import config


def with_release_times(cpi: pd.DataFrame) -> pd.DataFrame:
    """Add cpi_published_at to every month, assuming the 15th where ONS dates are unknown."""
    out = cpi.copy()
    out["month"] = pd.to_datetime(out["month"])
    known = out["published_at"].notna()
    assumed = (out["month"] + pd.offsets.MonthBegin(1) + pd.Timedelta(days=14)).dt.tz_localize(
        config.UK_TZ
    ).dt.tz_convert("UTC") + pd.Timedelta(hours=7)
    out["cpi_published_at"] = out["published_at"].where(known, assumed)
    out["cpi_release_source"] = known.map({True: "ons_release_list", False: "assumed_15th"})
    return out.drop(columns="published_at").rename(
        columns={"month": "cpi_month", "cpi_index": "cpi_asof"}
    )


def add_real(prices: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    """Attach the as-of CPI to each price and compute real pence (2015 prices).

    `real_pence_hindsight` uses the CPI of the price's own month instead (the final
    figure, known only later). It is for comparison, never for a forecast.
    """
    c = with_release_times(cpi).sort_values("cpi_published_at")
    p = prices.sort_values("published_at").copy()
    p["published_at"] = pd.to_datetime(p["published_at"], utc=True)
    merged = pd.merge_asof(
        p, c, left_on="published_at", right_on="cpi_published_at", direction="backward"
    )
    merged["real_pence_asof"] = merged["pence_per_litre"] * 100 / merged["cpi_asof"]
    final = c.set_index("cpi_month")["cpi_asof"]
    month = pd.to_datetime(merged["price_date"]).dt.to_period("M").dt.to_timestamp()
    merged["cpi_hindsight"] = month.map(final)
    merged["real_pence_hindsight"] = merged["pence_per_litre"] * 100 / merged["cpi_hindsight"]
    return merged.sort_values(["fuel", "price_date"]).reset_index(drop=True)


def main() -> None:
    prices = pd.read_parquet(config.CLEAN_DIR / "desnz_weekly.parquet")
    cpi = pd.read_parquet(config.CLEAN_DIR / "cpi_monthly.parquet")
    out = add_real(prices, cpi)
    path = config.CLEAN_DIR / "desnz_real.parquet"
    out.to_parquet(path, index=False)
    print(f"wrote {path}: {len(out):,} rows; {out.real_pence_asof.isna().sum()} without CPI")
    print(out["cpi_release_source"].value_counts().to_string())
    gap = (out["real_pence_asof"] / out["real_pence_hindsight"] - 1).abs() * 100
    print(f"as-of vs hindsight real price, percent difference: mean {gap.mean():.2f}, max {gap.max():.2f}")
    lag = (out["published_at"] - out["cpi_published_at"]).dt.days
    print(f"CPI age when each price is published (days): median {lag.median():.0f}, max {lag.max()}")
    print(out.groupby("fuel")[["pence_per_litre", "real_pence_asof"]].agg(["min", "max"]).round(1).to_string())
    print(out.tail(2)[["price_date", "fuel", "pence_per_litre", "cpi_month", "cpi_asof", "real_pence_asof"]].to_string())


if __name__ == "__main__":
    main()
