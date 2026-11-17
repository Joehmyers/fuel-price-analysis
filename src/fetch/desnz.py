"""Fetch DESNZ weekly road fuel prices from GOV.UK.

Saves each CSV untouched under data/raw/desnz/, and the landing page too (it
holds the update log we read release dates from). File links change every
week, so they are read from the page, never hard-coded.

Run:  python -m src.fetch.desnz
"""

import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import holidays
from bs4 import BeautifulSoup

from src import config
from src.fetch import common

PAGE_URL = "https://www.gov.uk/government/statistics/weekly-road-fuel-prices"
SOURCE = "desnz"
UK = ZoneInfo(config.UK_TZ)
RELEASE_TIME = time(9, 30)  # assumed: the update log gives a date, not a time

_LOG_LINE = re.compile(
    r"week commencing (?:Monday )?(\d{1,2} \w+ \d{4}) published", re.IGNORECASE
)


def csv_links(page_html: str) -> list[str]:
    """Every CSV file link on the landing page (the 2003-2017 and 2018- files)."""
    soup = BeautifulSoup(page_html, "lxml")
    links = {
        a["href"]
        for a in soup.find_all("a", href=True)
        if a["href"].lower().endswith(".csv") and a["href"].startswith("https://assets.")
    }
    return sorted(links)


def parse_update_log(page_html: str) -> dict[date, date]:
    """Map 'week commencing' Monday -> the day the page says it was published.

    The log gives dates only, never a time of day.
    """
    soup = BeautifulSoup(page_html, "lxml")
    out: dict[date, date] = {}
    for item in soup.select(".gem-c-metadata__change-history-item"):
        time_tag = item.find("time")
        text = item.get_text(" ", strip=True)
        match = _LOG_LINE.search(text)
        if not (time_tag and match and time_tag.get("datetime")):
            continue
        released = date.fromisoformat(time_tag["datetime"][:10])
        monday = datetime.strptime(match.group(1), "%d %B %Y").date()
        out[monday] = released
    return out


def assumed_release_date(price_date: date) -> date:
    """Tuesday after the price Monday, or Wednesday if that Monday is a bank holiday."""
    uk_holidays = holidays.UK(subdiv="ENG", years=price_date.year)
    tuesday = price_date + timedelta(days=1)
    if price_date in uk_holidays or tuesday in uk_holidays:
        return price_date + timedelta(days=2)
    return tuesday


def published_at(price_date: date, log: dict[date, date]) -> tuple[datetime, str]:
    """When the price became public (UTC) and where that time came from."""
    # The log's own "week commencing" dates are sometimes a day out (it says
    # Monday 17 November 2026 for the week of 16 November), so match on the
    # release date instead: the first logged release within 4 days after the price Monday.
    window = [r for r in log.values() if price_date < r <= price_date + timedelta(days=4)]
    if window:
        released, how = min(window), "update_log_date_assumed_0930"
    else:
        released, how = assumed_release_date(price_date), "assumed_rule"
    local = datetime.combine(released, RELEASE_TIME, tzinfo=UK)
    return local.astimezone(timezone.utc), how


def main() -> None:
    page = common.get(PAGE_URL)
    common.save_raw(SOURCE, "landing_page.html", page.content)
    links = csv_links(page.text)
    print(f"landing page ok; {len(links)} CSV links")
    for url in links:
        response = common.get(url)
        path = common.save_raw(SOURCE, url.rsplit("/", 1)[-1], response.content)
        print(f"saved {path.name}: {len(response.content):,} bytes")


if __name__ == "__main__":
    main()
