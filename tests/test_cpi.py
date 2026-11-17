from datetime import date

from src.clean import cpi
from src.fetch import ons_cpi

SERIES = '''"Title","CPI INDEX 00: ALL ITEMS 2015=100"
"Release date","21-10-2026"
"2025","138.0"
"2026 AUG","143.6"
"2026 SEP","144.1"
'''

PREVIOUS = """<table><tr><th>Superseded files</th><th>Reason</th><th>Date superseded</th></tr>
<tr><td>x</td><td>Scheduled</td><td>16 September 2026</td></tr>
<tr><td>x</td><td>Scheduled</td><td>21 October 2026</td></tr></table>"""


def test_series_parser_keeps_months_and_reads_release_date():
    df, current = cpi.parse_series(SERIES)
    assert list(df["month"]) == [date(2026, 8, 1), date(2026, 9, 1)]
    assert list(df["cpi_index"]) == [143.6, 144.1]
    assert current == date(2026, 10, 21)


def test_release_dates_come_from_superseded_column():
    assert ons_cpi.release_dates(PREVIOUS) == [date(2026, 9, 16), date(2026, 10, 21)]


def test_month_is_public_on_first_release_after_month_end():
    releases = [date(2026, 9, 16), date(2026, 10, 21)]
    assert cpi.first_release_after(date(2026, 8, 31), releases) == date(2026, 9, 16)
    assert cpi.first_release_after(date(2026, 9, 30), releases) == date(2026, 10, 21)
    assert cpi.first_release_after(date(2026, 10, 31), releases) is None
