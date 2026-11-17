import pandas as pd

from src import config


def read(name):
    return pd.read_parquet(config.PUBLIC_DIR / name)


def test_fuel_snapshot_has_two_fuels_and_unique_weeks():
    df = read("desnz_real.parquet")
    assert set(df["fuel"]) == {"unleaded_petrol", "diesel"}
    assert not df.duplicated(["price_date", "fuel"]).any()
    assert len(df) == 2448


def test_every_price_has_a_publication_time_after_its_monday():
    df = read("desnz_real.parquet")
    assert df["published_at"].notna().all()
    monday_start = pd.to_datetime(df["price_date"]).dt.tz_localize("UTC")
    assert (df["published_at"] > monday_start).all()


def test_the_cpi_used_was_public_before_the_price():
    df = read("desnz_real.parquet")
    assert (df["cpi_published_at"] <= df["published_at"]).all()


def test_cpi_snapshot_covers_1988_to_2026():
    df = read("cpi_monthly.parquet")
    assert df["month"].min().year == 1988 and df["month"].max().year == 2026
    assert df["cpi_index"].notna().all()
