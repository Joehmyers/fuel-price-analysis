"""Place each FuelCosts station in a country and region, with postcodes.io.

postcodes.io is a free lookup with no sign-up. The bulk call takes up to 100
postcodes at a time. Each reply is saved untouched under data/raw/postcodes_io/.
Stations whose postcode fails are tried again by their coordinates.

Region rule: England uses its nine regions (North East ... South West).
Scotland, Wales and Northern Ireland have no English region, so each is its
own region. That gives 12 regions in all.

Run:  python -m src.clean.stations
"""

import json
from datetime import datetime, timezone

import pandas as pd
import requests

from src import config
from src.clean import prices
from src.fetch import common

URL = "https://api.postcodes.io/postcodes"
BATCH = 100
SOURCE = "postcodes_io"


def _post(payload: dict) -> list[dict]:
    fetched = datetime.now(timezone.utc)
    response = requests.post(
        URL, json=payload, headers={"User-Agent": config.USER_AGENT}, timeout=config.TIMEOUT_SECONDS
    )
    response.raise_for_status()
    common.save_raw(SOURCE, "bulk.json", response.content, fetched)
    common.time.sleep(config.REQUEST_PAUSE_SECONDS)
    return response.json()["result"]


def place(result: dict | None) -> dict:
    """Country and region from one postcodes.io result (None when unknown)."""
    if not result:
        return {"country": None, "region": None, "pc_lat": None, "pc_lon": None}
    country = result.get("country")
    region = result.get("region") or country  # only England has a region
    return {
        "country": country,
        "region": region,
        "pc_lat": result.get("latitude"),
        "pc_lon": result.get("longitude"),
    }


def lookup_postcodes(postcodes: list[str]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for i in range(0, len(postcodes), BATCH):
        chunk = postcodes[i : i + BATCH]
        for item in _post({"postcodes": chunk}):
            found[item["query"]] = place(item["result"])
    return found


def lookup_coordinates(rows: list[tuple[str, float, float]]) -> dict[str, dict]:
    """Nearest postcode (within 1 km) for stations whose own postcode failed."""
    found: dict[str, dict] = {}
    for i in range(0, len(rows), BATCH):
        chunk = rows[i : i + BATCH]
        geos = [{"longitude": lon, "latitude": lat, "limit": 1, "radius": 1000} for _, lat, lon in chunk]
        for (node, _, _), item in zip(chunk, _post({"geolocations": geos}), strict=True):
            hits = item["result"] or []
            found[node] = place(hits[0] if hits else None)
    return found


def build() -> pd.DataFrame:
    path = sorted((config.RAW_DIR / "fuelcosts").glob("*__stations.csv"))[-1]
    st = pd.read_csv(path, low_memory=False).drop_duplicates("node_id", keep="last")
    st["postcode_clean"] = st["postcode"].astype("string").str.upper().str.strip()
    pcs = sorted(st["postcode_clean"].dropna().unique())
    by_pc = lookup_postcodes(pcs)
    placed = st["postcode_clean"].map(lambda p: by_pc.get(p, place(None)))
    st = pd.concat([st, pd.DataFrame(list(placed), index=st.index)], axis=1)
    st["placed_by"] = st["country"].notna().map({True: "postcode", False: None})

    missing = st[st["country"].isna() & st["latitude"].notna()]
    if len(missing):
        rows = list(zip(missing["node_id"], missing["latitude"], missing["longitude"], strict=True))
        by_geo = lookup_coordinates(rows)
        for node, info in by_geo.items():
            if info["country"]:
                idx = st.index[st["node_id"] == node]
                for key, value in info.items():
                    st.loc[idx, key] = value
                st.loc[idx, "placed_by"] = "coordinates"

    bad = prices.flag_bad_coordinates(st["latitude"], st["longitude"])
    far = prices.distance_km(st["latitude"], st["longitude"], st["pc_lat"], st["pc_lon"]) > 20
    st["flag_bad_coordinates"] = bad | far.fillna(False)
    st["is_placed"] = st["country"].notna()
    return st


def main() -> None:
    st = build()
    config.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    keep = [
        "node_id", "trading_name", "brand_name", "postcode", "latitude", "longitude",
        "is_motorway", "is_supermarket", "is_temporarily_closed", "is_permanently_closed",
        "country", "region", "placed_by", "is_placed", "flag_bad_coordinates",
    ]  # fmt: skip
    path = config.CLEAN_DIR / "stations.parquet"
    st[keep].to_parquet(path, index=False)
    print(f"wrote {path}: {len(st):,} stations")
    print(st["placed_by"].value_counts(dropna=False).to_string())
    print(st["country"].value_counts(dropna=False).to_string())
    print(st["region"].value_counts(dropna=False).to_string())
    print("bad coordinates:", int(st["flag_bad_coordinates"].sum()))
    unplaced = st[~st["is_placed"]]
    print(f"unplaced stations: {len(unplaced)}")
    unplaced[["node_id", "trading_name", "postcode", "latitude", "longitude"]].to_csv(
        config.CLEAN_DIR / "stations_unplaced.csv", index=False
    )
    print(json.dumps({"unplaced_file": "data/clean/stations_unplaced.csv"}))


if __name__ == "__main__":
    main()
