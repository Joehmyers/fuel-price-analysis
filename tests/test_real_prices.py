import pandas as pd

from src.features import real_prices

CPI = pd.DataFrame(
    {
        "month": pd.to_datetime(["2026-07-01", "2026-08-01", "2026-09-01"]),
        "cpi_index": [100.0, 110.0, 120.0],
        "published_at": pd.to_datetime(
            ["2026-08-19 06:00", "2026-09-16 06:00", "2026-10-21 06:00"], utc=True
        ),
    }
)


def prices(published):
    return pd.DataFrame(
        {
            "price_date": [pd.Timestamp("2026-10-19").date()],
            "fuel": ["diesel"],
            "pence_per_litre": [150.0],
            "published_at": pd.to_datetime([published], utc=True),
        }
    )


def test_price_published_before_a_cpi_release_does_not_use_it():
    out = real_prices.add_real(prices("2026-10-20 09:30"), CPI)
    assert out["cpi_asof"].iloc[0] == 110.0  # August CPI; September is released on the 21st
    assert out["real_pence_asof"].iloc[0] == 150.0 * 100 / 110.0


def test_price_published_after_the_release_uses_it():
    out = real_prices.add_real(prices("2026-10-21 09:30"), CPI)
    assert out["cpi_asof"].iloc[0] == 120.0


def test_hindsight_uses_the_price_month_and_is_empty_when_that_month_is_not_out_yet():
    # The price is dated 19 October; October CPI does not exist in this table.
    assert pd.isna(real_prices.add_real(prices("2026-10-20 09:30"), CPI)["cpi_hindsight"].iloc[0])
    sept = prices("2026-10-20 09:30").assign(price_date=pd.Timestamp("2026-09-14").date())
    assert real_prices.add_real(sept, CPI)["cpi_hindsight"].iloc[0] == 120.0


def test_unknown_release_dates_are_assumed_to_be_the_15th_of_the_next_month():
    cpi = pd.DataFrame(
        {"month": pd.to_datetime(["2010-01-01"]), "cpi_index": [90.0], "published_at": [pd.NaT]}
    )
    out = real_prices.with_release_times(cpi)
    assert out["cpi_release_source"].iloc[0] == "assumed_15th"
    assert out["cpi_published_at"].iloc[0] == pd.Timestamp("2010-02-15 07:00", tz="UTC")
