import pandas as pd

from src.clean import prices


def test_pounds_become_pence():
    fixed, changed = prices.fix_units(pd.Series([1.339, 133.9, 1.0, 2.0, 0.0]))
    assert fixed.tolist() == [133.9, 133.9, 1.0, 2.0, 0.0]
    assert changed.tolist() == [True, False, False, False, False]


def test_range_flag_edges_are_inclusive_of_80_and_300():
    flags = prices.flag_out_of_range(pd.Series([79.9, 80.0, 300.0, 300.1, 1.0, float("nan")]))
    assert flags.tolist() == [True, False, False, True, True, True]


def test_jump_flag_uses_previous_reading_of_same_station_and_fuel():
    df = pd.DataFrame(
        {
            "node_id": ["a", "a", "a", "b", "a"],
            "fuel_type": ["E10", "E10", "E10", "E10", "B7"],
            "price_pence": [100.0, 129.0, 170.0, 300.0, 100.0],
        }
    )
    # a/E10: 100 -> 129 is +29% (ok); 129 -> 170 is +31.8% (flag). b and a/B7 have no previous.
    assert prices.flag_jumps(df).tolist() == [False, False, True, False, False]


def test_stale_flag_after_30_days():
    seen = pd.Series(pd.to_datetime(["2026-03-31", "2026-03-31"], utc=True))
    set_at = pd.Series(pd.to_datetime(["2026-03-01", "2026-03-02"], utc=True))
    # 30 days exactly is fine; 31 days is stale.
    assert prices.flag_stale(set_at, seen).tolist() == [False, False]
    set_at2 = pd.Series(pd.to_datetime(["2026-02-28", "2026-03-30"], utc=True))
    assert prices.flag_stale(set_at2, seen).tolist() == [True, False]


def test_bad_coordinates():
    lat = pd.Series([52.98, 0.0, 52.98, 12.0, None])
    lon = pd.Series([-2.12, 0.0, 2.12, -2.0, -2.0])
    assert prices.flag_bad_coordinates(lat, lon).tolist() == [False, True, True, True, True]
