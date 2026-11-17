# Fuel price experiment: start here

This file is for whoever runs the fuel price experiment inside the AA Databricks
workspace, a person or an AI assistant such as Genie. Read it first. The full plan is in
[docs/plans/fuel-price-experiment.md](docs/plans/fuel-price-experiment.md).

## The task

Test whether public UK fuel prices improve the daily breakdown demand forecast.
Stage 1 (outside the AA) is finished: it built the public price data and
showed what to test. Your job is stage 2: join those prices to AA demand and run
the experiments in section D of the plan.

## Rules that never bend

1. **No AA or client data in the repo.** Demand tables, call-out counts, member
   data and model outputs stay in Databricks tables and volumes. Commit code and
   documents only. Before a commit, check that no output cell, CSV or parquet
   file holds AA data.
2. **No credentials or tokens in the repo.**
3. **Never use a price before it was public.** Every row has `published_at`.
   For a forecast made at time T, use only rows with `published_at <= T`. The
   test `tests/test_asof.py` shows the pattern; extend it, do not skip it.
4. **Use price changes, not price levels.** People respond to changes. Build
   features from weekly change, 4- and 8-week change, and rises and falls
   separately, at lags of 0 to 12 weeks. Levels are a comparison only.
5. **Use `real_pence_asof`, never `real_pence_hindsight`,** when you want an
   inflation-adjusted price in a forecast.
6. **Do not change a test to make it pass.** Fix the code.
7. **Write in plain English** (`docs/style-guide.md`): short words, define terms,
   British spelling, no em dashes.

## What is in the repo

| Path | What |
|---|---|
| `datasets/public/` | The two public tables you need, with a column guide in its README. No download required. |
| `src/config.py` | All paths. `PUBLIC_DIR` points at `datasets/public/`; set `FUEL_PUBLIC_DIR` to move it |
| `src/features/asof.py` | As-of views: only what was public at a given time (written for station prices; same idea applies) |
| `src/features/real_prices.py` | How the inflation-adjusted price was built |
| `docs/research/desnz-retreat.md` | Why we use the national UK weekly price, with the numbers |
| `docs/research/traffic-elasticity.md` | Reported traffic response to price (unverified figures) |
| `docs/plans/fuel-price-experiment.md` | The plan: steps B to E are yours |
| `src/fetch/`, `src/clean/` | Fetchers for the public data. Only needed to refresh the snapshot |

Not needed in Databricks: the station-level code (`src/clean/stations.py`,
`src/clean/fuelcosts.py`, `src/features/regional.py`, `src/features/charts.py`).
It covers regional gaps, which are parked.

## First steps

1. In a notebook: `import sys; sys.path.insert(0, "<repo path>")`, then
   `from src import config; import pandas as pd;`
   `pd.read_parquet(config.PUBLIC_DIR / "desnz_real.parquet")`.
2. Run the tests from a terminal in the repo: `python -m pytest -q` (the full
   `ops/check.sh` also runs ruff and shell checks and may need packages from
   `requirements.txt`). Expect 30 tests to pass. If a path or version breaks,
   fix it in `src/config.py` first.
3. Write the weekly prices to a Delta table (a Databricks table with a change
   history), keeping `published_at`.
4. Follow sections B to E of the plan. Do D0 (can the data detect the effect?)
   before anything else, and stop there if it cannot.

## Key facts to carry

- **Two fuels:** `unleaded_petrol` and `diesel`. Weekly changes correlate 0.89
  over 23 years, so test them separately or use one plus the difference.
- **Price shocks in the data:** weeks with a move over 3 p: 4 in 2008, 13 in
  2022, 14 in 2026. About three independent episodes. Report each alone.
- **Reported traffic response** (unverified, from a research report): -0.07 to
  -0.29. A 20% price rise implies 1.4% to 5.8% less traffic.
- **Release times are partly assumed.** `published_at_source` says which.
- **Demand measure:** use created demand, de-duplicated, by creation date and
  breakdown location (the team's earlier decision).

## When to stop and ask the human

- Before using any data or service not named in the plan.
- If the AA demand history is shorter than two years or has no price shock.
- If any check shows a price used before its `published_at`.
- Before sharing any number outside the workspace.

## Not verified

- Whether the workspace can reach gov.uk or ons.gov.uk (the snapshot avoids the need).
- Whether Genie reads this file automatically. Point it here at the start.
- The elasticity figures, and the success rule in plan step E1.
