# UK fuel prices as a forecasting feature (stage 1)

This repo tests one question: do UK fuel prices differ enough by country and
region to be worth using as a feature when forecasting breakdown demand?

**Stage 1 (here):** fetch public fuel price data, clean it, and measure how far
regional prices sit from the UK price.
**Stage 2 (later, in another environment):** join the prices to call-out data.
So the code is plain Python, the data is parquet (a compact table file), and
every path is set in `src/config.py`.

**Running the experiment on AA data? Start with [FUEL_PRICE_EXPERIMENT.md](FUEL_PRICE_EXPERIMENT.md).**

## Rules

- No private or client data, and no credentials, ever enter this repo.
  `data/` is ignored by git.
- Raw downloads are never edited. Each is saved with the time it was fetched.
- Every price carries two dates: the day it covers (`price_date`) and the time
  it became public (`published_at`). Later steps only use prices already public.
- Every source's licence and credit is in [docs/sources.md](docs/sources.md).

## Layout

| Folder | Holds |
|---|---|
| `src/fetch/` | One script per source |
| `src/clean/` | Unit fixes, flags, region lookup |
| `src/features/` | Daily regional averages, gaps and spread |
| `notebooks/` | The analysis |
| `reports/` | The one-page answer |
| `data/raw`, `data/clean` | Downloads and cleaned tables (not in git) |
| `datasets/public/` | Two small public tables, committed so the repo runs without a download |
| `tests/` | Tests |
| `docs/` | Sources, plans, decisions (from the template) |

## Run order

```bash
python -m src.fetch.desnz && python -m src.fetch.fuelcosts && python -m src.fetch.ons_cpi
python -m src.clean.desnz && python -m src.clean.cpi
python -m src.clean.stations && python -m src.clean.fuelcosts
python -m src.features.regional && python -m src.features.charts
```

The answer is in `reports/regional-variation-answer.md`. The official Fuel
Finder collector (`src/fetch/fuel_finder.py`) needs the link from the
subscription email; see `docs/sources.md`.

## Use

```bash
ops/setup.sh    # install packages
ops/check.sh    # lint, test, build
```

The template's own guide to agent files, skills and CI is in `AGENTS.md`.
