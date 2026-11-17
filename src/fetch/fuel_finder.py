"""Collect the official Fuel Finder CSV (current prices, updated twice a day).

Each run saves one snapshot, untouched, with the time it was fetched, so our
own archive grows from the first run. Run it twice a day (cron or similar).

The download link comes from the subscription email (see docs/sources.md) and
is read from the environment variable FUEL_FINDER_CSV_URL. It is never
stored in git.

Run:  python -m src.fetch.fuel_finder
"""

import sys

from src import config
from src.fetch import common

SOURCE = "fuel_finder"


def main() -> int:
    url = config.FUEL_FINDER_CSV_URL
    if not url:
        print(
            "FUEL_FINDER_CSV_URL is not set. Subscribe to the CSV by email "
            "(see docs/sources.md), then put the link in your environment or .env.",
            file=sys.stderr,
        )
        return 1
    response = common.get(url)
    path = common.save_raw(SOURCE, "fuel_finder.csv", response.content)
    print(f"saved {path.name}: {len(response.content):,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
