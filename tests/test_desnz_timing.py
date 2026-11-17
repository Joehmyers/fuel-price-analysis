from datetime import date, datetime, timezone
from pathlib import Path

from src.fetch import desnz

HTML = (Path(__file__).parent / "fixtures/desnz/update-log.html").read_text()


def test_reads_only_csv_links():
    assert desnz.csv_links(HTML) == ["https://assets.publishing.service.gov.uk/media/a/weekly_2003_to_2017.csv"]


def test_log_gives_release_dates():
    log = desnz.parse_update_log(HTML)
    assert log[date(2026, 8, 31)] == date(2026, 9, 2)


def test_mislabelled_week_is_matched_by_release_date():
    log = desnz.parse_update_log(HTML)
    # Data row is Monday 16 Nov; the log says "17 November" but the release is 17 Nov.
    when, how = desnz.published_at(date(2026, 11, 16), log)
    assert how == "update_log_date_assumed_0930"
    assert when == datetime(2026, 11, 17, 9, 30, tzinfo=timezone.utc)  # GMT in November


def test_summer_release_is_converted_to_utc():
    log = desnz.parse_update_log(HTML)
    when, _ = desnz.published_at(date(2026, 8, 31), log)  # Wednesday after bank holiday
    assert when == datetime(2026, 9, 2, 8, 30, tzinfo=timezone.utc)  # 09:30 BST


def test_fallback_is_tuesday_and_wednesday_after_bank_holiday():
    assert desnz.assumed_release_date(date(2026, 11, 9)) == date(2026, 11, 10)
    assert desnz.assumed_release_date(date(2026, 8, 31)) == date(2026, 9, 2)  # summer bank holiday
    assert desnz.assumed_release_date(date(2026, 4, 6)) == date(2026, 4, 8)  # Easter Monday
