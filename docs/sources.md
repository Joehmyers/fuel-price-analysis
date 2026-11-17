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
