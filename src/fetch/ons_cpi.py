"""Fetch the ONS consumer price index (CPI), all items, monthly.

Series D7BT in dataset MM23: "CPI INDEX 00: ALL ITEMS 2015=100".
Saves the series CSV and the 'previous versions' page untouched. That page
lists the date of every earlier release, which gives each month's release date.

Run:  python -m src.fetch.ons_cpi
"""

from datetime import date, datetime

from bs4 import BeautifulSoup

from src.fetch import common

SOURCE = "ons_cpi"
SERIES = "d7bt"
DATASET = "mm23"
BASE = "https://www.ons.gov.uk"
SERIES_PATH = f"/economy/inflationandpriceindices/timeseries/{SERIES}/{DATASET}"
CSV_URL = f"{BASE}/generator?format=csv&uri={SERIES_PATH}"
PREVIOUS_URL = f"{BASE}{SERIES_PATH}/previous"


def release_dates(previous_page_html: str) -> list[date]:
    """Every release date listed on the 'previous versions' page, oldest first.

    A version's 'date superseded' is the day the next release replaced it, so it
    is that next release's date. The current release date is added by the caller.
    """
    soup = BeautifulSoup(previous_page_html, "lxml")
    out = set()
    for row in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if len(cells) >= 3:
            out.add(datetime.strptime(cells[-1], "%d %B %Y").date())
    return sorted(out)


def main() -> None:
    for name, url in {"series.csv": CSV_URL, "previous_versions.html": PREVIOUS_URL}.items():
        response = common.get(url)
        path = common.save_raw(SOURCE, name, response.content)
        print(f"saved {path.name}: {len(response.content):,} bytes")


if __name__ == "__main__":
    main()
