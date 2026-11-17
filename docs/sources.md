# Sources

Every source, with its link, licence, release timing and quirks. All are free
and public. Credit each one when you publish a result.

Terms used here:

- **Open Government Licence v3.0 (OGL)**: a UK licence that lets you copy,
  adapt and use the data, even commercially, if you credit the source.
- **Price date**: the day a price covers.
- **Published at**: the time the price became public. Later steps may only use
  a price once its published time has passed.

This file fills in as each fetcher is built.

## Planned, not built

- **Brent crude oil price** and **exchange rates**: not fetched yet. A stub
  will sit in `src/fetch/` when we need them.

## 1. DESNZ weekly road fuel prices

- **What:** average UK pump price of petrol (ULSP, ultra low sulphur unleaded)
  and diesel (ULSD), in pence per litre, every Monday from 9 June 2003.
  Also duty and VAT rates.
- **Link:** <https://www.gov.uk/government/statistics/weekly-road-fuel-prices>
- **Licence:** Open Government Licence v3.0. Credit: "Department for Energy
  Security and Net Zero, Weekly road fuel prices".
- **Files:** two CSVs on the page (2003 to 2017, and 2018 onwards), plus an
  Excel file that repeats the same figures. We keep the CSVs. File links change
  weekly, so `src/fetch/desnz.py` reads them from the page.
- **Rows read (17 Nov 2026):** 1,224 weeks per fuel, 9 Jun 2003 to 16 Nov 2026.
- **Release time:** the page's update log gives a date for each release but no
  time of day. It covers 256 weeks, from 15 Nov 2021. We assume 09:30 UK time on
  the logged date. Older weeks use the fallback: Tuesday 09:30, or Wednesday if
  the Monday or Tuesday is a bank holiday. The column `published_at_source`
  says which rule gave each time. Times are stored in UTC.
- **Quirk:** the log wrote "week commencing Monday 17 November 2026" for the
  week whose data row is dated Monday 16 November. So weeks are matched on the
  release date, not on the log's week label.
- **Fuel types:** petrol and diesel only, so no E10/E5 or premium split here.

## 2. FuelCosts open data (the back-fill)

- **What:** an unofficial copy of the official Fuel Finder feed (station
  forecourt prices). Not run by the government.
- **Link:** <https://fuelcosts.co.uk/download> (files at `/api/download/price-history`
  and `/api/download/stations`; no sign-up).
- **Licence:** the underlying data is Open Government Licence v3.0. Credit:
  "FuelCosts.co.uk. UK Fuel Price Data. Source: UK Government Fuel Finder,
  Open Government Licence v3.0."
- **What we read on 17 Nov 2026:**
  - `price_history.csv`: 1,281,662 rows, 174 MB. Columns: `id`, `node_id`
    (station), `fuel_type`, `price_pence`, `recorded_at`, `source_updated_at`.
    8,325 stations. `recorded_at` runs 7 Feb 2026 to 17 Nov 2026.
  - `stations.csv`: 8,525 rows, 21 columns, including `postcode`, `latitude`,
    `longitude` (none missing), `is_motorway`, `is_supermarket`, closure flags.
  - Fuel types: B7_STANDARD 462,712 rows; E10 399,193; E5 233,762;
    B7_PREMIUM 182,783; HVO 1,624; B10 1,588.
- **Only price changes are stored**, so a day's price for a station is the last
  change before that day (carried forward).
- **Two times per row:** `source_updated_at` is when the station set the price
  (it reaches back to 1 Feb 2025). `recorded_at` is when FuelCosts first saw it
  (median 3.5 minutes later). The history before 7 Feb 2026 is therefore a
  one-off snapshot of older prices, not a true record. For "when did it become
  public" we use `recorded_at`, not `source_updated_at`.
- **Dirty values:** 311 prices below 10p, 641 below 80p, 549 above 300p; the
  maximum is 2,009.9. Flagged in cleaning, not deleted.

### Comparison of the copies of this data

| Copy | What it holds | Verdict |
|---|---|---|
| FuelCosts API | Every price change since 7 Feb 2026, with two timestamps. | **Use this.** Longest history, and it carries the "seen at" time we need. |
| Hugging Face `jamesb7/fuel-prices-uk` | The same two files, uploaded daily (price file 173.5 MB when checked, slightly older than the live download). Licence listed as "other: OGL v3". | Same data, a day behind. Not needed. |
| Kaggle `jamesb7/fuel-prices-uk` | Same author and the same files as Hugging Face per the FuelCosts page. Page loads but I did not download it (needs a login). | Not checked directly. Not needed. |
| GitHub `matthewgall/fuelfinder-archive` (MIT) | Hourly Go job, 566 commits from 15 Feb 2026. `data.csv` (7.9 MB) holds only the current prices; the first data commit is 16 Feb 2026. History lives in the commit log, one snapshot per commit. | A second, independent record from 16 Feb. Worth using later to spot-check FuelCosts, but each snapshot needs its own download. |

None of the copies holds anything from before February 2026. The official
feed itself is new, so the station-level history is about nine months long.
That is the main limit on this work. The DESNZ weekly series (2003 onward) is
the only long record.

## 3. Official Fuel Finder CSV (our own growing archive)

- **What:** current prices and forecourt details for every UK station, updated
  twice a day. GOV.UK says prices appear within 30 minutes of a change.
- **Link:** GOV.UK "Access the latest fuel prices and forecourt data"
  <https://www.gov.uk/guidance/access-the-latest-fuel-prices-and-forecourt-data-via-api-or-email>,
  which leads to <https://www.developer.fuel-finder.service.gov.uk/fuel-finder/access-latest-fuelprices>.
- **Licence:** Open Government Licence v3.0 (stated at the foot of every GOV.UK
  page). Credit: "UK Government, Fuel Finder".
- **How we get it:** the page has no plain link. Its download link is filled in
  by JavaScript from an undocumented endpoint that returns a token, so we do not
  build on that. The official routes are an email subscription (needs a sign-up,
  done by you, not by this code) or the API (not used yet). Once you subscribe,
  put the link from the email in `FUEL_FINDER_CSV_URL` (environment or `.env`).
  Then run `python -m src.fetch.fuel_finder` twice a day. Each run saves one
  untouched snapshot with its fetch time under `data/raw/fuel_finder/`.
- **Not yet confirmed:** whether the emailed link is permanent or expires, the
  column names (we will read them from the first file), and the exact release times.
- **Status:** collector written and tested with a stand-in download; it has
  not run against the real file because no link exists yet.

## 4. ONS consumer price index (CPI)

- **What:** monthly CPI, all items, "CPI INDEX 00: ALL ITEMS 2015=100".
- **Series:** ID `D7BT`, dataset `MM23`, base year 2015 = 100 (confirmed in the
  file header). Link:
  <https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23>
- **Licence:** Open Government Licence v3.0. Credit: "Office for National
  Statistics".
- **Rows read (17 Nov 2026):** 465 months, January 1988 to September 2026,
  latest value 144.1. The next release is 18 November 2026 (October data).
- **Release dates:** the series file gives only the latest release date (21 Oct
  2026). The page of previous versions lists every earlier release since
  15 Dec 2015, 132 in all. A month is treated as public on the first release
  after the month ends, at 07:00 UK time (the usual ONS time; not stated in the
  files). Months before November 2015 have no known release date and are left
  empty, so they cannot be used as-of a date.
- **Limit:** CPI is rarely revised, so we keep only the value as it stands now.
  We have not checked first-release values against later ones.

## Cleaning results (17 Nov 2026 run)

- **Stations:** 8,525 placed with postcodes.io (8,403 by postcode, 122 by
  coordinates); none unplaced. England 6,546, Scotland 853, Northern Ireland
  601, Wales 525. Regions: the nine English regions plus Scotland, Wales and
  Northern Ireland as one region each (12 in all). Credit: postcodes.io, which
  carries ONS and Ordnance Survey data under the Open Government Licence.
- **Flags on 1,281,662 price rows (none deleted):** out of range 1,190; jump
  over 30% 1,585; stale 1,296; bad station coordinates 1,158 (56 stations;
  64 rows belong to a station missing from stations.csv and are flagged too).
- **Unit fix:** changed 0 rows. FuelCosts holds no prices in pounds. The
  rule exists for other feeds.
- **Not fixed:** values such as 999.9 and 1,549 may be pence-times-ten or
  placeholders; we cannot tell, so they are flagged only.
