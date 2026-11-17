# Public data snapshot

Two small tables, committed so the repo runs anywhere without a download. Both
are public government statistics under the Open Government Licence v3.0. They
hold no AA or client data. The folder is set by `PUBLIC_DIR` in `src/config.py`
(or the environment variable `FUEL_PUBLIC_DIR`).

Snapshot taken on 17 November 2026. To rebuild: `python -m src.fetch.desnz`,
`python -m src.fetch.ons_cpi`, `python -m src.clean.desnz`, `python -m src.clean.cpi`,
`python -m src.features.real_prices`, then copy from `data/clean/`.

## `desnz_real.parquet`: 2,448 rows (1,224 weeks x 2 fuels), 96 KB

UK weekly pump price, 9 June 2003 to 16 November 2026. Credit: Department for
Energy Security and Net Zero, Weekly road fuel prices.

| Column | Meaning |
|---|---|
| `price_date` | The Monday the price covers |
| `fuel` | `unleaded_petrol` or `diesel` |
| `pence_per_litre` | Price in pence as published (not adjusted for inflation) |
| `duty_pence`, `vat_percent` | Fuel duty and VAT rates |
| `published_at` | When the price became public (UTC). **Use only prices with `published_at` at or before the forecast time.** |
| `published_at_source` | `update_log_date_assumed_0930` (date from the GOV.UK log, 09:30 UK assumed) or `assumed_rule` (Tuesday 09:30, Wednesday after a bank holiday) |
| `cpi_month`, `cpi_asof` | The CPI month and value that were public when the price was published |
| `cpi_published_at`, `cpi_release_source` | When that CPI was released (UTC); `ons_release_list` or `assumed_15th` (before Nov 2015) |
| `real_pence_asof` | Price in pence of 2015, using `cpi_asof`. Safe to use in a forecast |
| `cpi_hindsight`, `real_pence_hindsight` | Same, using the CPI of the price's own month. **Not safe in a forecast**: comparison only |

## `cpi_monthly.parquet`: 465 rows, 8 KB

ONS consumer price index, all items, series D7BT (2015 = 100), January 1988 to
September 2026. Credit: Office for National Statistics.

| Column | Meaning |
|---|---|
| `month` | First day of the month |
| `cpi_index` | CPI, 2015 = 100 |
| `published_at` | ONS release time (UTC). Empty before November 2015 |

Not included: the station-level data (FuelCosts, 1.3 million rows). It is
large, unofficial, and the plan no longer uses it. See
`docs/research/desnz-retreat.md`.
