"""Turn the raw DESNZ weekly CSVs into one tidy parquet table.

Reads the newest raw landing page and CSVs under data/raw/desnz/ and writes
data/clean/desnz_weekly.parquet with one row per week and fuel.

Run:  python -m src.clean.desnz
"""

from pathlib import Path

import pandas as pd

from src import config
from src.fetch import desnz as fetch_desnz

FUELS = {"ULSP": "unleaded_petrol", "ULSD": "diesel"}


def latest(pattern: str) -> Path:
    return sorted((config.RAW_DIR / "desnz").glob(pattern))[-1]


def read_csv(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path, encoding="utf-8-sig")
    out = []
    for code, fuel in FUELS.items():
        cols = [c for c in raw.columns if c.startswith(code + " ")]
        price = next(c for c in cols if "Pump price" in c)
        duty = next(c for c in cols if "Duty rate" in c)
        vat = next(c for c in cols if "VAT" in c)
        out.append(
            pd.DataFrame(
                {
                    "price_date": pd.to_datetime(raw["Date"], format="%d/%m/%Y").dt.date,
                    "fuel": fuel,
                    "pence_per_litre": raw[price],
                    "duty_pence": raw[duty],
                    "vat_percent": raw[vat],
                }
            )
        )
    return pd.concat(out, ignore_index=True)


def build() -> pd.DataFrame:
    page_html = latest("*__landing_page.html").read_text(encoding="utf-8")
    log = fetch_desnz.parse_update_log(page_html)
    frames = [read_csv(latest("*2003_to_2017.csv")), read_csv(latest("*CSV__2018*.csv"))]
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["price_date", "fuel"])
    stamps = {d: fetch_desnz.published_at(d, log) for d in df["price_date"].unique()}
    df["published_at"] = df["price_date"].map(lambda d: stamps[d][0])
    df["published_at_source"] = df["price_date"].map(lambda d: stamps[d][1])
    return df.sort_values(["fuel", "price_date"]).reset_index(drop=True)


def main() -> None:
    df = build()
    config.CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    path = config.CLEAN_DIR / "desnz_weekly.parquet"
    df.to_parquet(path, index=False)
    print(f"wrote {path}: {len(df):,} rows")
    print(f"price_date {df.price_date.min()} to {df.price_date.max()}")
    print(df.groupby("fuel").size().to_string())
    print(df.groupby("published_at_source").size().to_string())
    print(df.tail(4).to_string())


if __name__ == "__main__":
    main()
