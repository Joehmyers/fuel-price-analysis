import pandas as pd

from src.features import asof


def make(rows):
    df = pd.DataFrame(
        rows, columns=["node_id", "fuel", "price_pence", "source_updated_at", "published_at"]
    )
    for col in ("source_updated_at", "published_at"):
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


PRICES = make(
    [
        ("s1", "E10", 150.0, "2026-03-01T08:00", "2026-03-01T08:05"),
        # Set on 2 March but only reported on 5 March: it must not be seen before then.
        ("s1", "E10", 160.0, "2026-03-02T09:00", "2026-03-05T09:00"),
    ]
)


def test_a_forecast_made_before_publication_sees_the_old_price():
    got = asof.state_as_of(PRICES, pd.Timestamp("2026-03-04T12:00", tz="UTC"))
    assert got["price_pence"].tolist() == [150.0]


def test_the_new_price_appears_once_published():
    got = asof.state_as_of(PRICES, pd.Timestamp("2026-03-05T09:00", tz="UTC"))
    assert got["price_pence"].tolist() == [160.0]


def test_nothing_is_visible_before_the_first_publication():
    assert asof.state_as_of(PRICES, pd.Timestamp("2026-03-01T08:04", tz="UTC")).empty


def test_daily_state_never_uses_a_price_published_after_that_day():
    days = pd.date_range("2026-03-01", "2026-03-06")
    got = asof.daily_state(PRICES, days, "Europe/London").set_index("day")["price_pence"]
    assert got[pd.Timestamp("2026-03-01")] == 150.0
    assert got[pd.Timestamp("2026-03-04")] == 150.0  # the 160 price covers 2 March, unseen yet
    assert got[pd.Timestamp("2026-03-05")] == 160.0


def test_old_prices_are_dropped():
    prices = make([("s1", "E10", 150.0, "2026-01-01T08:00", "2026-01-01T08:05")])
    got = asof.state_as_of(prices, pd.Timestamp("2026-03-01", tz="UTC"))
    assert got.empty
