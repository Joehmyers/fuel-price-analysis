"""Fetch the FuelCosts open data (price_history.csv and stations.csv).

FuelCosts is an unofficial copy of the official Fuel Finder feed. Files are
saved untouched under data/raw/fuelcosts/.

Run:  python -m src.fetch.fuelcosts
"""

from src.fetch import common

SOURCE = "fuelcosts"
FILES = {
    "price_history.csv": "https://fuelcosts.co.uk/api/download/price-history",
    "stations.csv": "https://fuelcosts.co.uk/api/download/stations",
}


def main() -> None:
    for name, url in FILES.items():
        response = common.get(url)
        path = common.save_raw(SOURCE, name, response.content)
        print(f"saved {path.name}: {len(response.content):,} bytes")


if __name__ == "__main__":
    main()
