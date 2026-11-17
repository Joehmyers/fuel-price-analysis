"""Tidy the raw ONS CPI series into data/clean/cpi_monthly.parquet.

Columns: month (first day), cpi_index (2015=100), published_at (UTC).
A month's figure is published on the first ONS release date after that month
ends. ONS releases at 07:00 UK time. Months before the earliest listed release
(Dec 2015) have no known date, so published_at is empty for them.

Run:  python -m src.clean.cpi
"""

import io
import re
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from src import config
from src.fetch import ons_cpi

RELEASE_TIME = time(7, 0)


def latest(pattern: str):
    return sorted((config.RAW_DIR / ons_cpi.SOURCE).glob(pattern))[-1]


def parse_series(csv_text: str) -> tuple[pd.DataFrame, date]:
    """Monthly rows ('2026 SEP') and the current release date from the header."""
    release = re.search(r'"Release date","(\d\d-\d\d-\d{4})"', csv_text).group(1)
    current = datetime.strptime(release, "%d-%m-%Y").date()
    rows = [
        line for line in csv_text.splitlines() if re.match(r'"\d{4} [A-Z]{3}","', line)
    ]
    df = pd.read_csv(io.StringIO("\n".join(rows)), header=None, names=["label", "cpi_index"])
    df["month"] = pd.to_datetime(df["label"], format="%Y %b").dt.date
    return df[["month", "cpi_index"]], current


def first_release_after(month_end: date, releases: list[date]) -> date | None:
    return next((r for r in releases if r > month_end), None)


def build() -> pd.DataFrame:
    df, current = parse_series(latest("*__series.csv").read_text(encoding="utf-8"))
    previous = ons_cpi.release_dates(latest("*__previous_versions.html").read_text("utf-8"))
    releases = sorted(set(previous) | {current})
    uk = ZoneInfo(config.UK_TZ)

    def stamp(month: date):
        end = (pd.Timestamp(month) + pd.offsets.MonthEnd(0)).date()
        release = first_release_after(end, releases)
        if release is None or release < releases[0]:
            return pd.NaT
        return pd.Timestamp(datetime.combine(release, RELEASE_TIME, tzinfo=uk)).tz_convert("UTC")

    df["published_at"] = df["month"].map(stamp)
    # The earliest listed release cannot be the first release of an older month.
    df.loc[df["month"] < date(2015, 11, 1), "published_at"] = pd.NaT
    return df


def main() -> None:
    df = build()
    config.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CLEAN_DIR / "cpi_monthly.parquet"
    df.to_parquet(path, index=False)
    known = df.dropna(subset=["published_at"])
    print(f"wrote {path}: {len(df)} months, {df.month.min()} to {df.month.max()}")
    print(f"with release date: {len(known)}; without: {len(df) - len(known)}")
    print(df.tail(3).to_string())


if __name__ == "__main__":
    main()
